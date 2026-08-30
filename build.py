#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
import struct
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"
DIST = ROOT / "dist"
SRC = ROOT / "src" / "skip_intro.c"
HEADER_DIR = ROOT / "include"
LINKER = ROOT / "mod.ld"
MANIFEST = ROOT / "mod.json"

CODE_VRAM = 0x81000000
EVENT_NAME = "recomp_on_init"
DEPENDENCY_NAME = "*"


def find_tool(*names: str) -> str:
    for name in names:
        path = shutil.which(name)
        if path:
            return path
    raise SystemExit(f"Missing required build tool: {' / '.join(names)}")


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def u32(data: bytes, off: int) -> int:
    return struct.unpack_from("<I", data, off)[0]


def make_syms(code_size: int) -> bytes:
    # N64RSYMS v1 layout for one callback function on recomp_on_init.
    strings = bytearray()
    dep_start = len(strings)
    strings += DEPENDENCY_NAME.encode("utf-8")
    event_start = len(strings)
    strings += EVENT_NAME.encode("utf-8")
    while len(strings) % 4:
        strings.append(0)

    magic = b"N64RSYMS"
    version = struct.pack("<I", 1)
    subheader = struct.pack(
        "<10I",
        1,  # num_sections
        1,  # num_dependencies
        0,  # num_imports
        1,  # num_dependency_events
        0,  # num_replacements
        0,  # num_exports
        1,  # num_callbacks
        0,  # num_provided_events
        0,  # num_hooks
        len(strings),
    )

    section = struct.pack(
        "<7I",
        0,          # flags
        0,          # file_offset into mod_binary.bin
        CODE_VRAM,  # vram
        code_size,  # rom_size
        0,          # bss_size
        1,          # num_funcs
        0,          # num_relocs
    )
    func = struct.pack("<2I", 0, code_size)
    dependency = struct.pack("<B3xII", 0, dep_start, len(DEPENDENCY_NAME))
    dep_event = struct.pack("<3I", event_start, len(EVENT_NAME), 0)
    callback = struct.pack("<2I", 0, 0)

    syms = magic + version + subheader + bytes(strings) + section + func + dependency + dep_event + callback

    # Structural checks so a malformed symbols file is never packaged silently.
    assert syms[:8] == b"N64RSYMS"
    assert u32(syms, 8) == 1
    assert EVENT_NAME.encode() in syms
    return syms


def main() -> None:
    clang = find_tool("clang")
    lld = find_tool("ld.lld", "lld")
    objcopy = find_tool("llvm-objcopy")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    version = manifest["version"]
    out_name = f"DK64-Skip-Intro-v{version}.nrm"

    BUILD.mkdir(exist_ok=True)
    DIST.mkdir(exist_ok=True)

    obj = BUILD / "skip_intro.o"
    elf = BUILD / "mod.elf"
    map_file = BUILD / "mod.map"
    binary = BUILD / "mod_binary.bin"
    syms_file = BUILD / "mod_syms.bin"
    built_manifest = BUILD / "mod.json"
    out_nrm = DIST / out_name

    run([
        clang,
        "--target=mips-linux-gnu",
        "-march=mips2",
        "-mabi=32",
        "-mno-abicalls",
        "-fno-pic",
        "-G0",
        "-ffreestanding",
        "-fno-builtin",
        "-nostdlib",
        "-O2",
        "-Wall",
        "-Wextra",
        f"-I{HEADER_DIR}",
        "-c",
        str(SRC),
        "-o",
        str(obj),
    ])

    run([
        lld,
        "-m",
        "elf32btsmip",
        "-T",
        str(LINKER),
        f"-Map={map_file}",
        str(obj),
        "-o",
        str(elf),
    ])

    run([objcopy, "-O", "binary", str(elf), str(binary)])

    code = binary.read_bytes()
    if len(code) != 0x40:
        raise SystemExit(f"Unexpected callback size: 0x{len(code):X}; expected 0x40")

    # The v1.0.5 implementation makes no J/JAL calls into DK64. It only writes
    # the startup globals consumed by DK64 Recompiled's normal frame loop.
    words = [struct.unpack_from(">I", code, i)[0] for i in range(0, len(code), 4)]
    required = {
        0x24030050: "Main Menu map 0x50",
        0x24040005: "Main Menu mode 5",
        0x24020006: "transition state 6",
        0x3C018074: "0x8074 global page",
        0x3C028075: "0x8075 global page",
    }
    for word, desc in required.items():
        if word not in words:
            raise SystemExit(f"Validation failed: missing {desc} (0x{word:08X})")
    if any(((word >> 26) & 0x3F) in (2, 3) for word in words):
        raise SystemExit("Validation failed: unexpected J/JAL instruction")

    syms = make_syms(len(code))
    syms_file.write_bytes(syms)
    built_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    with zipfile.ZipFile(out_nrm, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(syms_file, "mod_syms.bin")
        zf.write(binary, "mod_binary.bin")
        zf.write(built_manifest, "mod.json")

    with zipfile.ZipFile(out_nrm, "r") as zf:
        if set(zf.namelist()) != {"mod_syms.bin", "mod_binary.bin", "mod.json"}:
            raise SystemExit("Validation failed: unexpected files inside NRM")
        packed_manifest = json.loads(zf.read("mod.json"))
        if packed_manifest["version"] != version:
            raise SystemExit("Validation failed: packed manifest version mismatch")

    digest = hashlib.sha256(out_nrm.read_bytes()).hexdigest()
    (DIST / f"{out_name}.sha256").write_text(f"{digest}  {out_name}\n", encoding="utf-8")

    print(f"Built: {out_nrm}")
    print(f"SHA-256: {digest}")
    print("Validation: PASS")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
