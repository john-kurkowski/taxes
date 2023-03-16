# List recipes
default:
  just --list

# Install/update all dependencies
bootstrap:
  pip install --upgrade pip
  pip install --editable '.[testing]'
  pre-commit install

# Run tests in CI
@cibuild:
  just check
  just test --snapshot-warn-unused

# Run checks
@check:
  pre-commit run --all-files

# Install package for use in the local system
@install:
  pip install .

# Run tests. Options are forwarded to `pytest`.
[no-exit-message]
@test *options:
  PYTHONPATH=. pytest {{options}}

# Run tests and watch for changes. Options are forwarded to `pytest`.
test-watch *options:
  #!/usr/bin/env sh
  export CMD='just test {{options}}'
  "$SHELL" -c "$CMD"
  fswatch --one-per-batch $(git ls-files .) | xargs -n1 -I{} "$SHELL" -c "$CMD"
