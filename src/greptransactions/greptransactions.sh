#!/usr/bin/env bash

year="$1"
pattern="$2"
file="$3"
rg --no-line-number --no-filename "^\s*($year)-.*($pattern)" "$file" | gsed 's/-\s*\$/$/g'
