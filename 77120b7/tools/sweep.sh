#!/usr/bin/env bash
# Truncation sweep: shift a >60000-byte report by 0..45 bytes so the cut lands at every
# offset of a table row; count runs that fail or send invalid UTF-8. Usage: sweep.sh <script>
script=$1; dir=$(mktemp -d); cd "$dir" && mkdir bin
printf '#!/bin/sh\ncase "$*" in *-X*) cp body.md sent.md;; esac\n' > bin/gh && chmod +x bin/gh
bad=0
for n in $(seq 0 45); do
  python3 -c "
import sys; n=int(sys.argv[1]); row = '| \`fit\` | \`(x)\` → \`(y)\` | \`q.md:1\` |\n'
open('drift-report.md','w').write('<!-- docs-guardian:drift-report changes=900 drift-pages=1 -->\n' + 'b'*n + row * 3000)" "$n"
  rm -f sent.md
  if ! PATH=$PWD/bin:$PATH GITHUB_REPOSITORY=o/r PR=1 GITHUB_RUN_ID=9 bash "$script" drift-report.md > /dev/null 2>&1; then
    echo "shift $n: the step failed"; bad=$((bad+1)); continue; fi
  python3 -c "open('sent.md','rb').read().decode()" 2>/dev/null || { echo "shift $n: sent body is not valid UTF-8: ...$(tail -c 12 sent.md | od -An -c | tr -s ' ')"; bad=$((bad+1)); }
done
echo "$bad of 46 alignments failed"
