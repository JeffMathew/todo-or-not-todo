#!/bin/bash
input=$(cat)
file=$(echo "$input" | jq -r '.tool_input.file_path // empty')

if [[ "$file" == *.py && -f "$file" ]]; then
  uv run black "$file"
fi
