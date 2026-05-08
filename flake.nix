{
  description = "A flake that exposes a script to rasterize and compress PDFs";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      python = pkgs.python3.withPackages (ps: [
        ps.pymupdf
        ps.pillow
      ]);

      compress-script = pkgs.writeShellApplication {
        name = "rasterize-and-compress";
        runtimeInputs = [ python ];
        text = ''
          exec ${python}/bin/python ${./pdflat.py} "$@"
        '';
      };
    in {
      # The default package executable, which will be invoked by `nix run`
      packages.${system} = {
        default = compress-script;
      };
    };
}
