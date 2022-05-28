# taxes

## Install

```zsh
pip install .
```

## statements2csv

This script converts bank statement PDFs from the banks I use, listed as
arguments, to plain text CSV on stdout. Example usage:

```zsh
$ statements2csv input1.pdf input2.pdf
Date,Description,Amount
08/31/2021,Output Inc. 1418 N Spring St Los Angeles 90012 CA USA,$10.00
…
```

Run `statements2csv --help` for more details. You can get a little
more debugging info by reducing the env var `LOGLEVEL`, which defaults to
`WARNING`.

### Motivation

My banks' official transaction search UIs suck. Mint stopped aggregating all my
bank transactions; its search was slow, besides. I save all my digital
statements anyway, for tax purposes. I figured, I can use fast grep on the
locally synced PDFs, instead of the official UIs. I can pipe to other Unix
commands. I can copy and paste to my spreadsheet software.

## Contribute

Install for local development:

   ```sh
   pip install --editable .
   pip install --editable '.[testing]'
   pre-commit install
   ```

### Tests

Checks are run on commit, after installing the pre-commit hook above, and on
push. You can also run them manually.

```sh
pre-commit run --all-files
```
