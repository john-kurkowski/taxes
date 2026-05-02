## Tests

- Before running checks or tests in a fresh or uncertain environment, run
  `just bootstrap`.
- Run static checks with `just check --fix`.
  - Static checks should run repo-wide, regardless of which files changed.
- Run focused tests with `just test` for the code you changed.
  - Run `just cibuild` when changes are cross-cutting.
  - CI runs `just check` without `--fix` to verify the checked-in tree is
    already formatted and lint-clean.
