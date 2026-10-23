#!/usr/bin/env python3
"""disas.py — 反汇编 libil2cpp.so 中指定 RVA（只读，用于理解序列化格式）

用法: python Tools/recon/disas.py <so> <rva_hex> [insn_count]
"""
from __future__ import annotations
import sys

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from elftools.elf.elffile import ELFFile


def rva_to_offset(path: str, rva: int) -> int:
    with open(path, "rb") as f:
        elf = ELFFile(f)
        for seg in elf.iter_segments():
            if seg["p_type"] != "PT_LOAD":
                continue
            va = seg["p_vaddr"]
            if va <= rva < va + seg["p_filesz"]:
                return rva - va + seg["p_offset"]
    raise ValueError(f"RVA {hex(rva)} not mapped")


def main() -> int:
    path = sys.argv[1]
    rva = int(sys.argv[2], 16)
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 80
    off = rva_to_offset(path, rva)
    with open(path, "rb") as f:
        f.seek(off)
        code = f.read(n * 4 + 64)
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    md.detail = False
    for i, ins in enumerate(md.disasm(code, rva)):
        if i >= n:
            break
        print(f"{ins.address:08x}  {ins.mnemonic:<8} {ins.op_str}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())