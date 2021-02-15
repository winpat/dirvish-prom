with import <nixpkgs> {};

mkShell {
  buildInputs = [
    python38
    python38Packages.pytest
    python38Packages.pytest-lazy-fixture
  ];
}
