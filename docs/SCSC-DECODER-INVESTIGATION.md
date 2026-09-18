# ScsC decoder investigation

Status: investigated on 2026-09-18; no decoder incorporated.

## Local evidence

The legacy C# source only P/Invokes `SII_Decrypt.dll`; it does not contain the
algorithm or the binary's source/license. Its About dialog points to the
original `ncs-sniper/SII_Decrypt` project. Real ATS fixture files under
`projeto_atual/ATS/...` exist and begin with opaque `ScsC`; no original fixture
was modified during this investigation.

## Alternatives

| Alternative | License / redistribution | 1.61 evidence | One-file impact | Decision / risk |
| --- | --- | --- | --- | --- |
| Legacy `SII_Decrypt.dll` / EXE | Unknown provenance in this checkout | Not validated | Native sidecar/DLL, incompatible with clean one-file goal | Reject: source and redistributable license absent. |
| [SII-Decrypt-cpp](https://github.com/liam-dong/SII-Decrypt-cpp) | MIT stated by its repository | Claims newer versions and ScsC/BSII support; no local ATS validation yet | Could be a sidecar or source port; neither is currently integrated | Candidate only. Verify pinned source/release and decode copied ATS fixture before adoption. |
| [sii-decode-rs](https://github.com/fangyi-zhou/sii-decode-rs) | MIT stated by its repository | Supports ScsC, BSII and text; no local ATS validation yet | Rust sidecar or a Python binding would complicate PyInstaller | Candidate only; version/API and fixture compatibility need proof. |
| [DecryptTruck](https://github.com/CoffeSiberian/DecryptTruck) | MIT stated by its repository | ATS/ETS claim, no local 1.61 validation | Rust executable sidecar; not a clean PyInstaller-only implementation | Candidate for behavioral comparison, not incorporation yet. |
| Independent Python implementation | Algorithm is publicly described: ScsC header, AES-256-CBC and zlib, with possible BSII inner payload | Unimplemented and unvalidated | Best final one-file path if implemented with an audited permissive crypto dependency | Requires a complete BSII-to-text implementation and regression tests; do not claim support before fixture validation. |

## Format evidence

The independent `scs_tools` format document describes ScsC as a 56-byte header
followed by AES-256-CBC ciphertext and zlib data; the decrypted inner content
may be textual SII or BSII. The C++ MIT project documents the same pipeline
and includes a BSII decoder. This supports a legal independent implementation
direction, but is not evidence that current project fixtures decode correctly.

## Required next step

Select and pin a permissively licensed implementation/source after reviewing
its license file at the chosen revision, then run decode + parser tests against
a temporary copy of `projeto_atual/ATS/.../save/autosave/{info,game}.sii`.
The result must be parseable `SiiNunit` and preserve original fixtures before
Task 11 can be completed.
