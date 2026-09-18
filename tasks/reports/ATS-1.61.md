# ATS 1.61 compatibility report

Status: BLOCKED — ScsC decoding is not implemented or validated.

The Task 11 fixture requirement cannot be met with the current plaintext-only
decoder. The local legacy source contains only P/Invoke calls to an unlicensed
binary, so it cannot be redistributed. `docs/SCSC-DECODER-INVESTIGATION.md`
records MIT-licensed candidates and the required validation sequence. No ATS
fixture was modified and Task 11 is not complete.
