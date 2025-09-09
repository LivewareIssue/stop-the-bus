#!/usr/bin/env bash
set -euo pipefail

dir="${1:-logs}"

shopt -s nullglob

files=("$dir"/*)
if ((${#files[@]} == 0)); then
  echo "No logfiles found in $dir/" >&2
  exit 1
fi

IFS=$'\n' read -r -d '' -a sorted < <(printf '%s\n' "${files[@]}" | sort && printf '\0')

latest=""
for ((i=${#sorted[@]}-1; i>=0; i--)); do
  if [[ -f "${sorted[i]}" ]]; then
    latest="${sorted[i]}"
    break
  fi
done

exec grc -c conf.cards tail -n +1 -F -- "$latest"
