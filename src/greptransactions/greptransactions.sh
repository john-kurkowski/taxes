#!/usr/bin/env bash

# Grep CSV transactions for the given year regex (perhaps a |-delimited list of
# years) and given pattern regex, against the given file.

year="$1"
pattern="$2"
file="$3"
rg --no-line-number --no-filename "^\s*($year)-" "$file" | # find leading year
  xsv fmt --out-delimiter "\t" |                           # increase terminal readability, improve paste into Google Sheets
  rg --pcre2 "($pattern)"                                  # highlight only the user's pattern
