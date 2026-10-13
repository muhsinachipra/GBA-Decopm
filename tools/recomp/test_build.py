"""Regression checks for the ROM and output gates; uses synthetic bytes only."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from build import ROOT, baseline, private_output, verify_rom


class BuildGateTests(unittest.TestCase):
    def test_context_identity_is_unambiguous(self):
        values = baseline((ROOT / "PROJECT_CONTEXT.md").read_text(encoding="utf-8"))
        self.assertEqual(len(values["SHA1"]), 40)
        self.assertEqual(len(values["SHA256"]), 64)

    def test_wrong_sha256_rejected_even_with_matching_sha1(self):
        with tempfile.TemporaryDirectory() as directory:
            rom = Path(directory) / "synthetic.gba"
            data = (0xEA000030).to_bytes(4, "little") + bytes(252)
            rom.write_bytes(data)
            expected = {"SHA1": hashlib.sha1(data).hexdigest(), "SHA256": "0" * 64}
            with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
                verify_rom(rom, expected)

    def test_actual_header_entry_used_and_signed_branch_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            rom = Path(directory) / "synthetic.gba"
            for word, target in ((0xEA000030, 0x080000C8), (0xEAFFFFFE, None)):
                data = word.to_bytes(4, "little") + bytes(252)
                rom.write_bytes(data)
                expected = {key: hashlib.new(key.lower(), data).hexdigest()
                            for key in ("SHA1", "SHA256")}
                if target is None:
                    with self.assertRaisesRegex(ValueError, "entry is outside"):
                        verify_rom(rom, expected)
                else:
                    self.assertEqual(verify_rom(rom, expected), (256, target))

    def test_output_cannot_escape_ignored_work_directory(self):
        self.assertEqual(private_output(ROOT / "work/native"), ROOT / "work/native")
        for output in (ROOT, ROOT / "native", ROOT / "work/../generated", ROOT / "work-other"):
            with self.assertRaises(ValueError):
                private_output(output)


if __name__ == "__main__":
    unittest.main()
