"""Compatibility entry point; prefer imagecollector.py or audiocollector.py."""
from __future__ import annotations

import sys

from collector_common import run_cli


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--audio-only" in argv:
        argv.remove("--audio-only")
        from audiocollector import main as collect
    else:
        from imagecollector import main as collect
    return collect(argv)


if __name__ == "__main__":
    run_cli(main)
