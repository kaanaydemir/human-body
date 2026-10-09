#!/usr/bin/env python3
"""Regenerates every submarine SVG into public/assets/svg/player/ (or into --out DIR).

    python3 -I tools/art/submarine/gen_submarine.py [--out DIR]

Stdlib only and deterministic (fixed RNG seeds, no clock): a re-run reproduces the files byte for byte.
"""
import os
import sys

sys.dont_write_bytecode = True  # keep the tools/art tree free of __pycache__
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_sub  # noqa: E402
import gen_explorer  # noqa: E402
import gen_fx  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))


def main(argv):
    out = os.path.join(ROOT, 'public', 'assets', 'svg', 'player')
    if '--out' in argv:
        out = os.path.abspath(argv[argv.index('--out') + 1])
    os.makedirs(out, exist_ok=True)
    gen_sub.write(out)
    gen_explorer.write(out)
    gen_fx.write(out)
    names = sorted(n for n in os.listdir(out) if n.endswith('.svg'))
    print('wrote %d SVGs to %s: %s' % (len(names), os.path.relpath(out, ROOT), ' '.join(names)))


if __name__ == '__main__':
    main(sys.argv[1:])
