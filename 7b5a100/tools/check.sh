# check <name> <dir> <command...>: run in <dir>, save "$ cmd" + output (ANSI stripped) to <name>.txt
check() {
  local name=$1 dir=$2; shift 2
  { echo "\$ (cd $(basename "$dir") && $*)"; (cd "$dir" && eval "$@") 2>&1; echo "[exit $?]"; } \
    | sed -E 's/\x1b\[[0-9;]*[mK]//g' > "$EV/$name.txt"
}
