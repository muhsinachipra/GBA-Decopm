"""Verify the installed mGBA GDB stub without requiring a separate GDB executable."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "recomp"))
from build import ROOT, baseline, verify_rom


class Remote:
    def __init__(self, connection):
        self.connection = connection

    def read(self, size):
        result = bytearray()
        while len(result) < size:
            part = self.connection.recv(size - len(result))
            if not part:
                raise RuntimeError("GDB stub disconnected")
            result.extend(part)
        return bytes(result)

    def command(self, command):
        payload = command.encode("ascii")
        checksum = sum(payload) & 255
        self.connection.sendall(b"$" + payload + f"#{checksum:02x}".encode())
        while self.read(1) != b"$":
            pass
        response = bytearray()
        while True:
            value = self.read(1)
            if value == b"#":
                break
            response.extend(value)
        checksum = int(self.read(2), 16)
        if sum(response) & 255 != checksum:
            raise RuntimeError("GDB reply checksum mismatch")
        self.connection.sendall(b"+")
        return response.decode("ascii")


def main():
    rom = ROOT / "Road Rash - Jailbreak (USA).gba"
    verify_rom(rom, baseline((ROOT / "PROJECT_CONTEXT.md").read_text(encoding="utf-8")))
    out = ROOT / "work/mgba"
    out.mkdir(parents=True, exist_ok=True)
    executable = ROOT / "tools/bin/mgba/mGBA-0.10.5-win64/mgba-sdl.exe"
    env = os.environ.copy()
    env["SDL_VIDEODRIVER"] = "dummy"
    env["SDL_AUDIODRIVER"] = "dummy"
    env["SDL_RENDER_DRIVER"] = "software"
    connection = None
    with (out / "gdb.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen([str(executable), "-g", str(rom)], cwd=out, env=env,
                                   stdout=log, stderr=subprocess.STDOUT,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            deadline = time.monotonic() + 15
            while connection is None:
                if process.poll() is not None:
                    raise RuntimeError(f"mGBA exited {process.returncode}; inspect gdb.log")
                try:
                    connection = socket.create_connection(("127.0.0.1", 2345), timeout=1)
                except OSError:
                    if time.monotonic() > deadline:
                        raise RuntimeError("mGBA GDB stub startup timed out")
                    time.sleep(0.05)
            connection.settimeout(5)
            remote = Remote(connection)
            supported = remote.command("qSupported")
            stop = remote.command("?")
            registers = remote.command("g")
            # Verify the ROM identity through guest memory without exporting bytes.
            title = bytes.fromhex(remote.command("m80000a0,c")).rstrip(b"\0").decode("ascii")
            if title != "ROADRASHJAIL" or len(registers) < 16 * 8:
                raise RuntimeError("Unexpected ROM title or truncated ARM register packet")
            result = {"tool": "mGBA 0.10.5", "port": 2345, "supported": supported,
                      "stop_reply": stop, "register_packet_bytes": len(registers)//2,
                      "title": title, "status": "GDB stub handshake and ARM registers verified"}
            (out / "gdb-probe.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
            print(json.dumps(result, indent=2))
        finally:
            if connection:
                connection.close()
            if process.poll() is None:
                process.kill()
            process.wait()


if __name__ == "__main__":
    main()
