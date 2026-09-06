"""
DevToolbox — A Swiss Army knife CLI for developers.

Zero external dependencies. Pure Python 3.8+.
One tool for: format conversion, encoding, hashing, JWT, timestamps, UUID, colors.

Usage:
    python -m devtoolbox convert data.json --to yaml
    python -m devtoolbox base64 encode "hello"
    python -m devtoolbox hash sha256 file.txt
    python -m devtoolbox jwt decode <token>
    python -m devtoolbox time 1694000000
    python -m devtoolbox uuid
    python -m devtoolbox color "#06b6d4" --to hsl

Author: solcat1007
License: MIT
"""

__version__ = "1.0.0"
