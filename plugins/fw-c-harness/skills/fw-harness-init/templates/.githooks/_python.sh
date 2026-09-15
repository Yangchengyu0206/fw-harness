# Sourced by the hooks and init.sh. Prints a command that runs Python 3.9+.
# On Windows, python may be the Microsoft Store stub, so the py launcher comes first.
harness_python() {
  for candidate in "py -3" python3 python; do
    if $candidate -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >/dev/null 2>&1; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}
