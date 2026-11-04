# Manager executable builds

GitHub Actions builds Linux x64 and Windows x64 executables when tool code or build configuration changes, on pull requests, and through **Actions → Build Song Manager → Run workflow**. Download the platform archive from the completed run's **Artifacts** section.

Extract the Windows ZIP or Linux tar.gz, then launch `VividstasisSongManager.exe` or `VividstasisSongManager`. The Linux archive preserves executable permissions. It is built on Ubuntu 22.04; use Ubuntu 22.04 or a compatible newer Linux system. These are unsigned builds, and the executable is native to its target platform.

Python, PySide6 and the GML/C# patch templates are bundled. You still need:

- FFmpeg with `libvorbis`, available on PATH.
- A platform-compatible UndertaleModTool CLI distribution, including its supporting files. Place its folder as `UndertaleMTCLI` beside the manager or choose it during setup.
- The complete supported original game installation. On Linux, Wine is needed to launch its Windows executable.

The default workspace is `.song-manager` beside the executable, with the clean backup inside that workspace. Extract into a writable directory and keep the workspace when replacing the executable. Use `--workspace /path/to/workspace` to choose another location. The manager does not bundle game data, music, existing user packages, or UndertaleModTool.

To build locally on the target operating system:

```sh
python -m pip install -r requirements-build.txt
python -m PyInstaller --noconfirm --clean --onefile --name VividstasisSongManager --paths tools --add-data "tools/patches:patches" tools/song_manager.py
python tools/package_manager.py --platform linux-x64
```

On Windows, use `--platform windows-x64` for the packaging step. Executables are written to `dist/`; distributable archives and checksums are in `release/`. Run each platform build on that platform. The workflow runs the test suite with Qt offscreen rendering and checks that the packaged executable accepts `--help` before uploading its archive.

Resource and executable paths follow [PyInstaller's runtime conventions](https://pyinstaller.org/en/stable/runtime-information.html): read bundled templates relative to their module, and locate persistent user files relative to the executable. The pipeline has not been run on GitHub from this workspace; its first Actions run will validate the native builds and Qt tests.
