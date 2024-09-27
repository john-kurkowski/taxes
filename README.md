# taxes

## Prerequisites

- [`git-crypt`](https://github.com/AGWA/git-crypt)
- [`just`](https://github.com/casey/just)
- Python >=3.10

## Install

Make the commands listed in the next section available on your system with the
following.

```zsh
just install
```

### Decrypt

Some test input files in the repo are encrypted for privacy. If you know you
need them:

```zsh
git-crypt unlock
```

## Commands

### statements2csv

Convert bank statement PDFs from the banks I use, listed as arguments, to plain
text CSV on stdout. Example usage:

```zsh
$ statements2csv input1.pdf input2.pdf
Date,Description,Amount
08/31/2021,Output Inc. 1418 N Spring St Los Angeles 90012 CA USA,$10.00
…
```

Run `statements2csv --help` for more details. You can get a little more
debugging info by reducing the env var `LOGLEVEL`, which defaults to `WARNING`.

#### Motivation

My banks' official transaction search UIs suck. Mint stopped aggregating all my
bank transactions; its search was slow, besides. I save all my digital
statements anyway, for tax purposes. I figured, I can use fast grep on the
locally synced PDFs (like `greptransactions`, below), instead of the official
UIs. I can pipe to other Unix commands. I can copy and paste to my spreadsheet
software.

### greptransactions (gt)

Grep CSV transactions for the given year and pattern.

Requires decrypted test input files. See above.

Example usage:

```sh
$ gt amazon | head -2
2022-02-08,Amazon.com*JQ87H3XZ3 Amzn.com/bill WA,4.34
2022-02-16,Amazon.com*5U8Z05QS3 Amzn.com/bill WA,51.13

$ gt --year 2021 amazon | head -2
2021-01-21,Amazon.com*T17O517I3 Amzn.com/bill WA,35.15
2021-03-03,Amazon.com*LJ4J51LF3 Amzn.com/bill WA,3.68
```

Executes the given regex pattern against a pre-existing snapshot of
`statements2csv`, across all bank statements. A thin wrapper around Ripgrep,
this command basically just makes the grep command easier to type. Defaults to
transactions from the previous calendar year, if year not provided.

## Contribute

Install for local development:

```sh
just bootstrap
```

### Tests

```sh
just test
```

This skips tests that rely on decrypted files that are still encrypted. See
above how to decrypt test input files.

Besides tests, checks are run on commit, after installing the pre-commit hook
above, and on push. You can also run them manually.

```sh
just check
```
