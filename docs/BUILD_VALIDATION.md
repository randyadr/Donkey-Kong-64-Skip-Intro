# Build validation — v1.0.5

The build script performs the following checks before reporting success:

- Compiles a big-endian 32-bit MIPS-II object.
- Links the `recomp_on_init` callback at the mod's local VRAM base.
- Extracts exactly `0x40` bytes of callback machine code.
- Verifies constants for Main Menu map `0x50`, Main Menu mode `5`, and transition state `6` are present.
- Verifies the expected `0x8074` and `0x8075` global-address pages are materialized.
- Rejects the build if any MIPS `J` or `JAL` instruction is present.
- Generates an N64RSYMS v1 symbols file containing one dependency, one dependency event, and one callback.
- Packages exactly `mod_syms.bin`, `mod_binary.bin`, and `mod.json` inside the `.nrm`.
- Reopens the final `.nrm` and validates the packed manifest version.
- Writes a SHA-256 file next to the output.

The v1.0.5 source is the safer transition implementation from v1.0.4 with compatibility metadata set to `minimum_recomp_version = 0.0.0`.
