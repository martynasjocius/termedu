from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
import sys

from termedu.config import AppConfig, ConfigError, load_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="termedu", description="Run a termedu session.")
    parser.add_argument("name", nargs="?", help="Learner name.")
    return parser


def resolve_config(argv: Sequence[str] | None = None, *, config_path: Path | None = None) -> AppConfig:
    args = build_parser().parse_args(argv)
    config = load_config(config_path)

    if args.name:
        return AppConfig(name=args.name)

    return config


def main(argv: Sequence[str] | None = None) -> int:
    try:
        config = resolve_config(argv)
    except ConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    learner_name = config.name or "anonymous"
    print(f"Ready for learner: {learner_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
