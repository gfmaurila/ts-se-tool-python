# ScsC decoder investigation

Status: ScsC envelope decoding implemented on 2026-09-18; BSII/3nK remain open.

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

## Implemented ScsC envelope stage

`ScsContainerDecoder` is an independent Python implementation of the
documented ScsC AES-256-CBC, PKCS#7, and zlib stages. It declares
`cryptography` (Apache-2.0 OR BSD-3-Clause) as a normal Python dependency;
the product contains no third-party DLL, executable, or copied decoder code.

The MIT-licensed `liam-dong/SII-Decrypt-cpp` source was reviewed on
2026-09-18 to cross-check the envelope structure and key. Its MIT license
permits redistribution, but it is not incorporated in this repository.

Temporary-copy tests against supplied ATS and ETS 1.61 `game.sii` files prove
that their original bytes remain unchanged and that each ScsC envelope inflates
successfully. Both inner payloads start `BSII` version 3 rather than `SiiN`.
Accordingly the parser cannot consume them yet and ScsC remains **PARTIAL**.

## Required next step

Implement a lossless BSII v3-to-SiiN decoder and 3nK decoder, then run
decode + parser tests against temporary copies of both supplied 1.61 games.
The result must be parseable `SiiNunit` and preserve original fixtures before
Task 11A can be completed.
