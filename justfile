# List recipes
default:
  just --list

pip_install_args := (
  '--upgrade --editable ".[testing]"' +
  if env_var_or_default('CI', '') =~ '.+' { ' --system' } else { '' }
)

# Install/update all dependencies
bootstrap:
  pip install --upgrade uv
  uv pip install {{pip_install_args}}
  pre-commit install
  git-crypt unlock

# Run checks/tests in CI
@cibuild:
  just check
  just test --snapshot-warn-unused

# Run checks
@check:
  pre-commit run --all-files

# Install package for use in the local system
@install:
  uv pip install .

# Run tests. Options are forwarded to `pytest`.
[no-exit-message]
@test *options:
  PYTHONPATH=. pytest {{options}}
