"""Console output is always UTF-8, whatever the Windows console code page is."""
import sys


def use_utf8_stdio():
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")
