"""Bounded native debug capture. Dumps stay ignored; interpreter runs are labeled."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import time
import struct
import zlib

from build import ROOT, baseline, private_output, verify_rom


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bios", type=Path, required=True)
    parser.add_argument("--frames", type=int, default=10)
    parser.add_argument("--interp", action="store_true")
    parser.add_argument("--segment", action="append", default=[],
                        help="Append N:KEYINPUT frames with an active-low GBA button mask")
    parser.add_argument("--scenario", type=Path,
                        help="Hand-authored JSON containing frames and segment strings")
    parser.add_argument("--port", type=int, default=19842)
    parser.add_argument("--output", type=Path, default=ROOT / "work/native/probe")
    args = parser.parse_args()
    if args.scenario:
        schedule = json.loads(args.scenario.read_text(encoding="utf-8"))
        if args.segment:
            parser.error("Use either --scenario or --segment")
        args.frames, args.segment = schedule["frames"], schedule["segments"]
    if args.frames < 1 or args.frames > 10000:
        parser.error("--frames must be in [1,10000]")
    segments = []
    for value in args.segment:
        count, mask = (int(item, 0) for item in value.split(":"))
        if not 1 <= count <= 10000 or not 0 <= mask <= 0x3FF:
            parser.error("Each segment needs 1..10000 frames and a mask in 0..0x3FF")
        segments.append((count, mask))
    if args.frames + sum(count for count, _ in segments) > 10000:
        parser.error("Total capture must be at most 10000 frames")
    rom = ROOT / "Road Rash - Jailbreak (USA).gba"
    verify_rom(rom, baseline((ROOT / "PROJECT_CONTEXT.md").read_text(encoding="utf-8")))
    out = private_output(args.output)
    out.mkdir(parents=True, exist_ok=True)
    bios = args.bios.resolve()
    bios_sha1 = hashlib.sha1(bios.read_bytes()).hexdigest()
    env = os.environ.copy()
    env["GBARECOMP_FORCE_INTERP"] = "1" if args.interp else "0"
    env["GBARECOMP_STRICT_STATIC"] = "0" if args.interp else "1"
    env["GBARECOMP_SELFHEAL_RECOMPILE"] = "0"
    env["GBARECOMP_MMIO_CAP"] = "1"
    with (out / "runtime.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen([
            str(ROOT / "work/native/build/RoadRashJailbreakRecomp.exe"),
            "--rom", str(rom), "--bios", str(bios), "--bios-sha1", bios_sha1,
            "--bios-hle", "--tcp", str(args.port), "--dump-png", str(out / "frame.png")],
            cwd=out, env=env, stdout=log, stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW)
        connection = None
        try:
            deadline = time.monotonic() + 15
            while connection is None:
                if process.poll() is not None:
                    raise RuntimeError(f"Runner exited {process.returncode}; see {out / 'runtime.log'}")
                try:
                    connection = socket.create_connection(("127.0.0.1", args.port), timeout=1)
                except OSError:
                    if time.monotonic() > deadline:
                        raise RuntimeError("Debug server startup timed out")
                    time.sleep(0.05)
            connection.settimeout(45)
            stream = connection.makefile("rb")
            def command(cmd, **fields):
                connection.sendall((json.dumps({"cmd": cmd, **fields}) + "\n").encode())
                line = stream.readline()
                if not line:
                    raise RuntimeError(f"Debug server disconnected during {cmd}; inspect runtime.log")
                response = json.loads(line)
                if not response.get("ok"):
                    raise RuntimeError(f"{cmd}: {response}")
                return response
            result = {"backend": "interpreter" if args.interp else "strict-static",
                      "bios_sha1": bios_sha1, "run": command("run_frames", n=args.frames)}
            result["segments"] = [{"keyinput": mask, "run": command("run_frames", n=count, keyinput=mask)}
                                  for count, mask in segments]
            for cmd in ("registers", "ppu_state", "counters", "mmio_cap"):
                result[cmd] = command(cmd)
            ram = bytearray()
            for offset in range(0, 32768, 4096):
                ram.extend(bytes.fromhex(command("read_iwram", addr=0x03000000 + offset,
                                                len=4096)["data"]))
            (out / "iwram.bin").write_bytes(ram)
            result["iwram_sha256"] = hashlib.sha256(ram).hexdigest()
            ewram = bytearray()
            for offset in range(0, 262144, 4096):
                ewram.extend(bytes.fromhex(command("read_ewram", addr=0x02000000 + offset,
                                                  len=4096)["data"]))
            (out / "ewram.bin").write_bytes(ewram)
            result["ewram_sha256"] = hashlib.sha256(ewram).hexdigest()
            screenshot = command("screenshot")
            pixels = bytes.fromhex(screenshot["data"])
            width, height = screenshot["w"], screenshot["h"]
            channels = len(pixels) // (width * height)
            if channels not in (3, 4) or len(pixels) != width * height * channels:
                raise RuntimeError("Unexpected screenshot format")
            def chunk(kind, payload):
                return (struct.pack(">I", len(payload)) + kind + payload +
                        struct.pack(">I", zlib.crc32(kind + payload)))
            rows = b"".join(b"\0" + pixels[y*width*channels:(y+1)*width*channels] for y in range(height))
            png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2 if channels == 3 else 6, 0, 0, 0)) +
                   chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))
            (out / "frame.png").write_bytes(png)
            result["framebuffer_sha256"] = hashlib.sha256(pixels).hexdigest()
            (out / "capture.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
            command("quit")
            process.wait(timeout=10)
            print(f"Captured {args.frames + sum(count for count, _ in segments)} frames ({result['backend']}) in {out}")
        finally:
            if connection:
                connection.close()
            if process.poll() is None:
                process.kill()
                process.wait()


if __name__ == "__main__":
    main()
