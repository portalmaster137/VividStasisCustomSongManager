# Repository guidance

## Project overview

This repository provides a Python desktop manager and command-line tools for
building and installing custom Vividstasis songs. Python 3.11+ is required;
the desktop UI uses PySide6. Game archive patching uses UndertaleModTool CLI,
and audio conversion requires FFmpeg with libvorbis.

## Code map

- `tools/song_manager.py`: Qt desktop UI and background operations.
- `tools/manager_backend.py`: managed builds, installation transactions,
  immutable backups, recovery, and rollback.
- `tools/custom_songs.py` and `tools/song_registry.py`: song packages and registry.
- `tools/osz_import.py` and `tools/osu_to_vsb.py`: osu! archive import and
  4K/6K mania chart conversion.
- `tools/vsb.py`: binary chart parsing, writing, and inspection.
- `tools/patch_custom_song.py`: single-song command-line builder.
- `tools/patch_templates.py` and `tools/patches/`: template loading and GML/C#
  patch sources. Read `tools/patches/README.md` before modifying patches.
- `tools/cli_setup.py`: UndertaleModTool setup/download support.
- `tools/package_manager.py`: executable release packaging.
- `tools/test_*.py`: unittest suite, including transactional and Qt UI tests.
- `docs/`: format, manager, conversion, patching, and distribution guides.
- `.github/workflows/build-manager.yml`: Linux/Windows executable build workflow.
- `flake.nix`: Linux Nix package and app for x86_64 and aarch64.

## Development commands

Run commands from the repository root. Use an isolated Python environment
when installing dependencies.

```sh
python -m pip install -r requirements.txt
python tools/song_manager.py
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tools -p 'test_*.py'
```

For a focused test module:

```sh
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tools -p 'test_manager_backend.py'
```

The CI suite uses Python 3.12 and Qt offscreen rendering on Linux. Report
missing dependencies or skipped checks explicitly. Unit tests do not establish
that a patched archive works in the game.

For executable packaging, follow `docs/EXECUTABLE_BUILDS.md`; install
`requirements-build.txt` and preserve the bundled patch templates and certifi
data. Native executables must be built on their target platform. For Nix,
`nix build` builds the package and `nix run` launches the manager.

## Implementation conventions

- Follow the surrounding Python style; there is no repository-wide formatter
  or linter configuration. Avoid unrelated formatting changes.
- Preserve the existing script/module import conventions so direct commands
  and unittest discovery continue to work.
- Keep long-running UI work in the existing background-operation mechanism;
  use Qt signals for UI updates.
- Keep resource paths independent of the process working directory. Bundled
  templates are read relative to their module; persistent data must remain
  outside temporary PyInstaller resources and the read-only Nix store.
- Update the relevant documentation when changing commands, package behavior,
  supported chart conversion, or installation/build requirements.
- Add focused regression coverage for behavior changes, especially archive
  import validation, conversion, transactions, recovery, and rollback.

## Archive and patch invariants

- Preserve the exact clean-source archive hash checks. The backend targets
  Vividstasis 6.2.2.2; do not silently accept other or already-patched archives.
- Preserve immutable backups, installed-file verification, transaction journals,
  crash recovery, and stable song ID assignments. Exercise changes with
  temporary test fixtures rather than a user's installation.
- Treat GML anchor whitespace as significant. Preserve exact template
  parameters and the `gml()`/`cs()` escaping at language boundaries.
- Do not compile the stock `load_highscores` code: the toolchain can change
  its score constructor and cause boot failures. Preserve its original assembly
  and the saved-archive verification described in the patch README.
- GML behavior changes require compilation, reopening a representative saved
  archive, and an in-game check when the necessary game files and tools are
  available. State clearly which of these validations were actually performed.
- Use a copied game installation and backed-up profile for manual playback.
  Do not modify original game files as part of routine development checks.

## Local files and generated output

Do not commit game installations, extracted assets, downloaded CLI binaries,
manager workspaces, or generated build/release files. Existing ignored areas
include `vividstasis/`, `extraction/`, `testing/`, `out/`, `UndertaleMTCLI/`,
`analysis/`, `.song-manager/`, `build/`, `dist/`, and `release/`.
Preserve the existing root `.vsc` chart samples. Respect unrelated work in the
working tree and avoid changing generated Nix `result` links.
