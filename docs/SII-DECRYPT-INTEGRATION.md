# SII_Decrypt integration

Status: **implemented for supplied ATS/ETS 1.61 fixtures** (2026-09-18).

## Official decoder selected

The single bundled decoder is the official upstream console artifact from
`https://github.com/TheLazyTomcat/SII_Decrypt`, branch `bin`, version **1.5.3**,
Lazarus Release x64. SHA-256: `3ad9389b328ac47bd2d069068a94abdb816adae26a777c33b627554882fea45f`.
The upstream `license.txt` is retained verbatim at
`src/tsse/infrastructure/decoder/resources/licenses/SII_Decrypt-MPL-2.0.txt`.

This version documents type `0x07` support in 1.5.2 and BSII format version 3
support in 1.5.3. On temporary copies, it decoded both supplied ScsC fixtures
to SiiN: ATS produced 5,952,903 bytes / 17,672 parsed blocks; ETS2 produced
13,200,677 bytes / 43,027 parsed blocks. Both originals were unchanged.

## Upstream reproduction attempt

## Candidate current upstream version

The official upstream repository `TheLazyTomcat/SII_Decrypt` is marked
discontinued. Its published program documentation identifies **1.5.3** as the
latest version and retains the console CLI `SII_Decrypt.exe -i InputFile -o
OutputFile`, ScsC decryption, BSII decoding, 3nK decoding, ATS/ETS support,
and MPL-2.0. Crucially, its 1.5.2 changelog explicitly adds BSII value types
`0x2F` and `0x07`, and 1.5.3 adds BSII version 3. The upstream documentation states that release binaries are
on its official `bin` branch. No v1.5.2 source or binary has been downloaded
in this worktree yet; it requires explicit authorization before download.

The retained upstream archive is `TLExpress/SII_Decrypt` tag `v1.4.2-rc0`.
Its Lazarus project (`Program_Console/Lazarus/SII_Decrypt.lpi`) defines Release
build modes for x86/i386 and x64/x86_64, optimization level 3, smart linking,
and no debug info. It requires Lazarus `LazUtils` and Free Pascal. Neither
`fpc`, `lazbuild`, nor `msbuild` is installed on this machine, so no locally
reproducible compile was possible and no tools were installed.

The upstream archive includes Release artifacts. Their hashes are:

| target | SHA-256 |
| --- | --- |
| Lazarus Release x86 | `b36b75e083a34d13aadb3817c3c3f423aa0b863a85c376b8103b8ee7e66961a7` |
| Lazarus Release x64 | `edbb848803d75a7208a98b38d43deddefb31a19a42d7f58d7ef21833738b34db` |

CLI investigation found that the prior `Input file not set` result was caused
by the invocation wrapper rather than the save: starting the console program
directly under `cmd.exe` with `-i game.sii -o result.sii` reaches the actual
decoder. The positional form was inconsistent in this environment; the
documented `-i/-o` form is the reproducible form. On copied ATS and ETS 1.61
fixtures, v1.4.2 then returns `TSIIBin_Decoder.LoadLayoutBlockLocal:
Unsupported value type (0x00000007)`, exit `-1`, stdout only, no output file.
The source changelog says type `0x07` was added only in v1.5.2. This identifies
the genuine compatibility boundary: upstream v1.4.2 cannot decode these BSII
payloads. It remains historical reference only; the official 1.5.3 artifact
above replaces it for the application and PyInstaller preparation.

The infrastructure boundary is `SiiDecoder -> LegacySiiDecryptAdapter`.
`SiiDecoder` sends `SiiNunit` files straight to the Python parser. Every other
identified format is copied to a `TemporaryDirectory` before the adapter is
called; no original save path is ever supplied to the executable.

## Supplied binary

All three supplied copies are identical and one canonical development copy is
kept at `src/tsse/infrastructure/decoder/resources/SII_Decrypt.exe`:

| property | value |
| --- | --- |
| SHA-256 | `c3af317386353c7b22ea6d91acf66f054b0ff1fd7e5192274ee1ff89476146f7` |
| size | 241,664 bytes |
| banner | SII Decrypt program 1.4.2 (2016-2018 Frantisek Milt) |
| PE architecture | x86 (PE machine `0x014c`) |
| Windows version resource | absent |

The binary identifies its command-line contract as `InputFile [OutputFile]` or
`[commands] -i InputFile [-o OutputFile]`. Its source explains that omitted
output writes in-place, so the adapter always supplies a separate output name.
The adapter now copies the executable as well as `game.sii` into its private
temporary directory before execution. This prevents the legacy process from
seeing external paths and makes its working directory deterministic. It
captures stdout/stderr/exit code and rejects missing or non-SiiN output.

The source contract claims automatic ScsC decrypt + BSII decode, 3nK decoding,
and pass-through for plaintext; `--no_decode`, `--sw_aes`, `--on_file`, and
`--wait` are documented options. ScsC/BSII/3nK have not passed an end-to-end
run with this exact binary. SiiN is intentionally bypassed without execution.

## License and packaging

The legacy C# About dialog names `https://github.com/ncs-sniper/SII_Decrypt`.
The official 1.5.3 archive includes Frantisek Milt's MPL-2.0 license text.
MPL-2.0 redistribution remains subject to its notice/source obligations; the
verbatim license is bundled and this document records the upstream URL/hash.

`scripts/build.ps1` includes the resource through PyInstaller `--add-data` and
`--onefile`. The adapter resolves a package-relative resource and copies it to
its private runtime directory, so no developer-machine path is used.

## Experimental Python work

`ScsContainerDecoder` and `BinarySiiDecoder` remain isolated experimental code.
They are not selected by `SiiDecoder` and must not become the main decoding
path for Task 11A. `cryptography` is still imported by the experimental ScsC
implementation and its regression tests; do not treat it as required by the
official legacy-adapter path.
