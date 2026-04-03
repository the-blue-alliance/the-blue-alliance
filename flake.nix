{
  description = "The Blue Alliance development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            # Python
            python313

            # Node.js (for webpack/frontend)
            nodejs_24

            # Python package management
            uv

            # Build tools
            gnumake

            # Docker (for local dev services)
            docker
            docker-compose

            # Google Cloud SDK
            google-cloud-sdk

            # Native libraries for pyarrow
            arrow-cpp

            # Bash linting
            shellcheck
            shfmt

            # Pre-commit hooks
            pre-commit
          ];

          shellHook = ''
            echo "The Blue Alliance dev environment loaded"
            echo "  Python:  $(python3 --version)"
            echo "  Node:    $(node --version)"
            echo "  uv:      $(uv --version)"
            echo ""
            echo "Run 'make sync' to install Python dependencies"
            echo "Run 'docker compose up --build' to start dev services"
          '';
        };
      });
}
