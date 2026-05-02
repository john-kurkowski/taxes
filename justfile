# List recipes
default:
  just --list

# Install/update all dependencies
bootstrap:
  pip install --upgrade uv
  uv sync --all-extras

# Run checks/tests in CI
@cibuild:
  just check
  just test --snapshot-warn-unused

# Run checks
@check *args:
  uv run --all-extras python scripts/check.py {{args}}

# Install package for use in the local system
@install:
  uv sync

# Run tests. Options are forwarded to `pytest`.
[no-exit-message]
@test *options:
  uv run --all-extras pytest {{options}}
