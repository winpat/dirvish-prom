with import <nixpkgs> {};

mkShell {
  buildInputs = [
    python38
    python38Packages.requests
    python38Packages.pytest
  ];
}
