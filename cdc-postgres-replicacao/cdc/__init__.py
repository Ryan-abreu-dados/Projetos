import sys

# acentos certos no terminal do Windows (no Linux já é UTF-8)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
