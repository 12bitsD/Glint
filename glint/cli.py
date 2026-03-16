from __future__ import annotations

import sys


def main() -> None:
    args = sys.argv[1:]

    if not args:
        print("Usage: glint -- <command> [args...]", file=sys.stderr)
        print("Example: glint -- claude", file=sys.stderr)
        sys.exit(1)

    if args[0] == "--":
        args = args[1:]

    if not args:
        print("glint: no command specified after '--'", file=sys.stderr)
        sys.exit(1)

    from glint.app import GlintApp

    app = GlintApp(command=args)
    app.run()
