#!/usr/bin/env python3
from __future__ import annotations

import shutil


def _row(cmd: str) -> str:
    path = shutil.which(cmd)
    status = "found" if path else "not found"
    return f"{cmd:8} {status:9} {path or '-'}"


def main() -> int:
    print("command   status    path")
    print(_row("pdflatex"))
    print(_row("bibtex"))
    print(_row("latexmk"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
