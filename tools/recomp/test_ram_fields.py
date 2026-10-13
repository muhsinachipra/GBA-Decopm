"""Compile and execute the mutable-field emitter against ARM shift/condition cases."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

from build import ROOT
from ram_fields import transform


class NativeRamFieldTests(unittest.TestCase):
    def test_emitted_operations_and_mutation_guards(self):
        pc = 0x02000040
        word = 0xE0000000 | (4 << 21) | (1 << 16) | (2 << 12) | (3 << 7) | (1 << 5) | 3
        shift = transform("uint32_t _op2_02000040, _co_02000040;\n"
                          "_op2_02000040 = _rm_02000040 >> 3;\n"
                          "_co_02000040 = (_rm_02000040 >> 2) & 1u;\n", pc, word, "lsr_immediate")
        branch_word = 0x5B000010
        branch = transform("if (arm_cond_passes(0x5u)) { return true; }\nreturn false;\n",
                           pc, branch_word, "condition")
        source = f'''#include <cstdint>
#include <stdexcept>
#include <cassert>
#include <utility>
uint32_t opcode; bool negative;
uint32_t bus_read_u32(uint32_t) {{ return opcode; }}
void runtime_unimplemented_op(const char*, uint32_t) {{ throw std::runtime_error("guard"); }}
bool arm_cond_passes(uint32_t cond) {{ return cond == 4 ? negative : !negative; }}
std::pair<uint32_t,uint32_t> shift(uint32_t _rm_02000040) {{
{shift}
return {{_op2_02000040, _co_02000040}};
}}
bool branch() {{ {branch} }}
int main() {{
for (uint32_t value : {{0u, 1u, 0x80000000u, 0xffffffffu, 0x12345678u}}) {{
 for (unsigned n=0; n<32; ++n) {{
  opcode=({word}u & ~0xf80u) | (n<<7);
  auto result=shift(value);
  assert(result.first == (n ? value>>n : 0));
  assert(result.second == ((value >> (n ? n-1 : 31)) & 1));
 }}
}}
opcode={word}u ^ 1u;
bool rejected=false; try {{ shift(1); }} catch(const std::runtime_error&) {{ rejected=true; }}
assert(rejected);
for (bool n : {{false,true}}) {{
 negative=n; opcode=0x4b000010u; assert(branch()==n);
 opcode=0x5b000010u; assert(branch()==!n);
}}
for (uint32_t invalid : {{0x6b000010u, 0x5b000011u}}) {{
 opcode=invalid; rejected=false; try {{ branch(); }} catch(const std::runtime_error&) {{ rejected=true; }}
 assert(rejected);
}}
}}
'''
        (ROOT / "work").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / "work") as directory:
            directory = Path(directory)
            cpp, exe = directory / "fields.cpp", directory / "fields.exe"
            cpp.write_text(source, encoding="utf-8")
            env = os.environ.copy()
            env["PATH"] = "C:/msys64/mingw64/bin" + os.pathsep + env["PATH"]
            subprocess.run(["C:/msys64/mingw64/bin/g++.exe", "-std=c++20", "-O2", str(cpp), "-o", str(exe)], check=True, env=env)
            subprocess.run([str(exe)], check=True, env=env)

    def test_unknown_emitter_shape_rejected(self):
        with self.assertRaises(ValueError):
            transform("unexpected output", 0x02000040, 0xE08121A3, "lsr_immediate")


if __name__ == "__main__":
    unittest.main()
