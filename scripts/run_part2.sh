#!/usr/bin/env bash
# Run every live demo in slide order. Ctrl-C to stop between scripts.
set -euo pipefail
cd "$(dirname "$0")"
for f in 01_single_node.py 02_chain.py 03_structured_why.py \
         04_structured_schema.py 05_structured_between_nodes.py \
         06_loop.py 07_recap.py; do
  echo
  echo "######## $f ########"
  python "$f"
done
