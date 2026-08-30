# DK64 Skip Intro

A small mod for **Donkey Kong 64: Recompiled** that skips the normal DK64 frontend startup chain by queueing the Main Menu during `recomp_on_init`.

Current version: **1.0.5**

## What it does

At startup the mod writes DK64's existing transition state instead of directly calling map-loading functions:

- `next_map = 0x50` — Main Menu
- `next_exit = 0`
- `game_mode_copy = 5` — Main Menu
- `game_mode = 5` — Main Menu
- transition state = `6` — tells DK64's normal frame loop to perform the map load

The transition state is written last so the rest of the request is already populated when the base game consumes it.

The earliest DK64 Recompiled/platform splash can still appear because `recomp_on_init` happens after that earliest startup stage.

## Install

Use the prebuilt file in [`dist/`](dist/):

`DK64-Skip-Intro-v1.0.5.nrm`

Install it through DK64 Recompiled's Mods menu, enable it, then fully restart DK64 Recompiled.

Remove or disable older Skip Intro builds before testing this version.

## Build from source

Requirements:

- Python 3
- Clang with MIPS target support
- LLD (`ld.lld`)
- `llvm-objcopy`

Linux/macOS shell:

```sh
./build.sh
```

Windows:

```bat
build.bat
```

Or directly:

```sh
python3 build.py
```

The finished `.nrm` is written to `dist/`.

## Repository layout

```text
src/skip_intro.c       Mod source
include/modding.h      N64Recomp modding macros
mod.json               Mod manifest
mod.ld                 MIPS linker script
build.py               Reproducible build + NRM packer
build.sh / build.bat   Convenience wrappers
dist/                  Prebuilt v1.0.5 NRM
docs/                   Validation and implementation notes
```

## Technical note

This version intentionally makes **no direct DK64 engine function calls** from the callback. The compiled callback only writes the startup globals that DK64 Recompiled's existing frame loop consumes.

See [`docs/BUILD_VALIDATION.md`](docs/BUILD_VALIDATION.md) for the checks performed by the build script.

## Runtime status

The package and machine code can be statically validated, but this repository's automated build does not launch DK64 Recompiled. Final runtime behavior should be tested in-game.
