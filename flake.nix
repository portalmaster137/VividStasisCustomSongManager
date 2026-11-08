{
  description = "Vividstasis Song Manager";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in {
      packages = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
          python = pkgs.python3.withPackages (ps: [ ps.pyside6 ps.certifi ]);
        in {
          default = pkgs.stdenvNoCC.mkDerivation {
            pname = "vividstasis-song-manager";
            version = "0-unstable";
            src = ./tools;
            nativeBuildInputs = [ pkgs.makeWrapper pkgs.qt6.wrapQtAppsHook ];
            buildInputs = [ pkgs.qt6.qtbase pkgs.qt6.qtwayland ];
            dontUnpack = true;
            dontWrapQtApps = true;
            installPhase = ''
              runHook preInstall
              mkdir -p $out/lib/song-manager/tools $out/bin
              cp -r $src/*.py $src/patches $out/lib/song-manager/tools/
              # The store is read-only; retain the upstream default elsewhere.
              substituteInPlace $out/lib/song-manager/tools/song_manager.py \
                --replace-fail "default=PROJECT / '.song-manager'" \
                "default=Path.home() / '.local/share/vividstasis-song-manager'"
              makeWrapper ${python}/bin/python $out/bin/vividstasis-song-manager \
                --add-flags "$out/lib/song-manager/tools/song_manager.py" \
                --prefix PATH : ${pkgs.lib.makeBinPath [ pkgs.ffmpeg ]} \
                "''${qtWrapperArgs[@]}"
              runHook postInstall
            '';
            doInstallCheck = true;
            installCheckPhase = ''
              $out/bin/vividstasis-song-manager --help
            '';
            meta = {
              description = "Desktop editor and installer for Vividstasis custom songs";
              mainProgram = "vividstasis-song-manager";
              platforms = systems;
            };
          };
        });
      apps = forAllSystems (system: {
        default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/vividstasis-song-manager";
        };
      });
    };
}
