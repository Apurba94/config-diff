"""Command-line interface for config-diff."""
import argparse
import json
import os

from .core import diff, load_config, render_markdown, render_text


def main(argv=None):
    ap = argparse.ArgumentParser(prog="config-diff", description="Semantic diff of two configuration files.")
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("-i", "--ignore", action="append", default=[], help="glob of paths to ignore, e.g. 'paths.*'")
    ap.add_argument("--rel-tol", type=float, default=0.0, help="relative tolerance for numbers")
    ap.add_argument("-f", "--format", choices=["text", "markdown", "json"], default="text")
    args = ap.parse_args(argv)
    changes = diff(load_config(args.old), load_config(args.new), args.ignore, args.rel_tol)
    if args.format == "json":
        print(json.dumps([dict(kind=k, path=p, old=a, new=b) for k, p, a, b in changes], indent=2))
    elif args.format == "markdown":
        print(render_markdown(changes, os.path.basename(args.old), os.path.basename(args.new)), end="")
    else:
        print(render_text(changes) if changes else "configs are equivalent")
    return 1 if changes else 0
