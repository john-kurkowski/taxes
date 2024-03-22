#!/usr/bin/env bash

year="$1"
pattern="$2"
file="$3"
rg --no-line-number --no-filename "^\s*($year)-" "$file" | rg --pcre2 "($pattern)"
