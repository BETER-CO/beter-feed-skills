# Generation contract

Step 6 of mapping mode. What must exist in this repository after generation, stated
independently of how any language spells it.

There is no generator per language here and none is carried anywhere else. An
integration is a component in its own repository, so the language is a property of the
repository this skill is running in. **Detecting it is the first step of generation, not a question** put to the developer — asking a developer which language their own
repository is written in is asking them to confirm something already on disk, and the
answer they give is the one this skill should have read.

## Parts

Read this file, then every part in order, before writing any file: generation writes the
code and the tests in one pass, and each part states what one of them must satisfy.

| Part | Covers |
|---|---|
| `references/generation-contract/01-detect.md` | *Detect first*; *Collisions fail generation*; *Named generator cases* |
| `references/generation-contract/02-resolver.md` | *What must exist*; *The projection*; *Exactly one decision*; *Unmapped is a value*; *Policy at the boundary*; *The sport resolver* |
| `references/generation-contract/03-emission.md` | *Parameter rules*; *Incident parameter carriage*; *The two rules*; *Emission is deterministic*; *The catalog digest*; *Adopting existing code* |
| `references/generation-contract/04-tests.md` | *Correctness is defined per class* and the nine classes; *Failure policies*; *The generated coverage check* |
| `references/generation-contract/05-failures-and-report.md` | *When a generated test fails*; *Re-entry, and adding a discipline*; *What generation reports* |
