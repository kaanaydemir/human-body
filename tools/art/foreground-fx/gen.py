#!/usr/bin/env python3
"""foreground-fx: regenerate every SVG this group owns, straight into public/assets/svg/.

    python3 -I tools/art/foreground-fx/gen.py              # from the repo root
    python3 -I tools/art/foreground-fx/gen.py --out DIR    # write everything into DIR instead (for diffs)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_fg  # noqa: E402
import gen_misc  # noqa: E402

if __name__ == '__main__':
    args = sys.argv[1:]
    gen_fg.main(list(args))
    gen_misc.main(list(args))
