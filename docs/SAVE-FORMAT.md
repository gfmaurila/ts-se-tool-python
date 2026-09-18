# Save Format Notes

## Task 03 evidence

The supplied ATS and ETS profile/save fixtures include opaque files beginning
with `ScsC`; a supplied decrypted ETS game fixture begins with `SiiNunit` and
is UTF-8 plaintext. The legacy native interface labels plaintext, encrypted,
binary, and 3NK result types, but its decoder binary has no supplied source or
license provenance.

`ScsC` is therefore detected as an opaque SCS container, not claimed to be a
specific encryption type. `SiiNunit` is accepted unchanged by `PlaintextDecoder`.
`3nK` is recognized from the legacy result taxonomy but has no current fixture.
All non-plaintext recognized headers produce `ExternalDecoderRequiredError`
until a separately licensed decoder is injected through the infrastructure
adapter. Unknown headers produce `UnsupportedSaveFormatError`.

## Task 04 plaintext AST

The parser accepts a `SiiNunit` document with an outer brace pair and ordered
`type : identifier { ... }` blocks. Fields and indexed list fields are exposed
without coercing their values; any unrecognized line inside a block is retained.
The document also keeps the complete original source, so unedited
`parse_sii(source).serialize()` is byte-for-byte stable for UTF-8 fixtures.

## Task 09 garage evidence

Plaintext ETS fixture blocks use `garage : garage.<city>` and an integer
`status`; the legacy reads and changes garage statuses. The implementation
therefore limits edits to that field. Company and market regeneration is not
implemented without stronger 1.61 format evidence.

Preenchido incrementalmente pelas tasks 03/04/11/12. Não afirmar formato sem evidência de fixture/source.
