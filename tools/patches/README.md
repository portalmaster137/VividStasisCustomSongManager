# Patch source templates

`manager/` contains the multi-song catalog, launch, difficulty-selection and APOTHEOSIS patches. Start with `apply_patches.csx` to see the target resources and replacement anchors. `apotheosis_transition.gml` supplies the transition-screen metadata that caused the earlier launch crash.

`single/` contains the original single-song CLI patches. `shared/` provides compiler setup and audio import; cover import is shared through the single builder's helper.

GML bodies and replacement expressions are plain `.gml` files. `.csx` files apply patches or verify saved resources. Some `.gml` files are fragments or anchors rather than standalone scripts; preserve their whitespace because anchors are matched exactly.

`@@name@@` marks a value supplied by Python. The loader requires every parameter to match exactly and substitutes once, so replacement text is never interpreted as another template. Python still escapes user data with `gml()` and `cs()` at the language boundary.

`@@include_cs:manager/example.gml@@` includes a static GML fragment as an escaped C# verbatim string. Template paths resolve relative to this directory, independent of the process working directory. Include fragments must not require runtime parameters. Generated build scripts remain self-contained and require no template files when run by UndertaleModTool.

Keep this directory alongside the tools when distributing them. After editing a patch, run the existing tests; changes to GML behavior also require compiling and reopening a representative archive and an in-game check. This extraction was checked against the previous generators byte for byte, including multiple songs, optional covers, Unicode metadata, sparse difficulties and APOTHEOSIS.
