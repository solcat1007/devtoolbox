#!/usr/bin/env python3
"""
CLI entry point for DevToolbox.

Uses only the standard library: argparse for CLI parsing, no external deps.
"""

import argparse
import sys

from . import __version__


def main():
    parser = argparse.ArgumentParser(
        prog="devtoolbox",
        description="DevToolbox — developer's Swiss Army knife. Zero dependencies.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s convert data.json --to yaml        Convert JSON file to YAML
  %(prog)s base64 encode "hello world"         Base64 encode a string
  %(prog)s base64 decode aGVsbG8=              Base64 decode
  %(prog)s hash sha256 file.txt                 SHA-256 hash of a file
  %(prog)s hash md5 "text"                      MD5 hash of a string
  %(prog)s jwt decode <token>                    Decode JWT header+payload
  %(prog)s time 1694000000                      Unix timestamp to human
  %(prog)s time now                              Current time in multiple zones
  %(prog)s uuid                                  Generate a UUID v4
  %(prog)s color "#06b6d4" --to hsl             Hex to HSL
  %(prog)s url encode "a b=c"                    URL-encode
  %(prog)s diff file1.txt file2.txt              Line diff

Version: {}
""".format(__version__),
    )
    parser.add_argument("--version", action="version", version=f"DevToolbox {__version__}")
    sub = parser.add_subparsers(dest="command", help="Available tools")

    # convert
    p_conv = sub.add_parser("convert", help="Convert between JSON/YAML/TOML/CSV")
    p_conv.add_argument("input", help="Input file path (or - for stdin)")
    p_conv.add_argument("--from", dest="from_fmt", default=None, help="Source format (auto-detect if omitted)")
    p_conv.add_argument("--to", dest="to_fmt", required=True, choices=["json", "yaml", "toml", "csv"])
    p_conv.add_argument("--indent", type=int, default=2, help="Indentation (JSON)")

    # base64
    p_b64 = sub.add_parser("base64", help="Base64 encode/decode")
    p_b64_sub = p_b64.add_subparsers(dest="action", required=True)
    p_b64_sub.add_parser("encode", help="Encode text").add_argument("text", help="Text to encode")
    p_b64_dec = p_b64_sub.add_parser("decode", help="Decode base64")
    p_b64_dec.add_argument("data", help="Base64 string to decode")

    # hash
    p_hash = sub.add_parser("hash", help="Calculate hash")
    p_hash.add_argument("algorithm", choices=["md5", "sha1", "sha256", "sha512", "sha3_256"])
    p_hash.add_argument("input", help="File path or string (use --text for string mode)")
    p_hash.add_argument("--text", action="store_true", help="Treat input as text, not file")

    # jwt
    p_jwt = sub.add_parser("jwt", help="Decode JWT tokens")
    p_jwt_sub = p_jwt.add_subparsers(dest="action", required=True)
    p_jwt_dec = p_jwt_sub.add_parser("decode", help="Decode JWT")
    p_jwt_dec.add_argument("token", help="JWT token string")

    # time
    p_time = sub.add_parser("time", help="Time/timestamp tools")
    p_time.add_argument("input", nargs="?", default="now", help="Unix timestamp, ISO date, or 'now'")

    # uuid
    p_uuid = sub.add_parser("uuid", help="Generate UUIDs")
    p_uuid.add_argument("--version", type=int, default=4, choices=[1, 3, 4, 5], help="UUID version")
    p_uuid.add_argument("--namespace", default=None, help="Namespace UUID (for v3/v5)")
    p_uuid.add_argument("--name", default=None, help="Name string (for v3/v5)")
    p_uuid.add_argument("--count", type=int, default=1, help="Number of UUIDs to generate")

    # color
    p_color = sub.add_parser("color", help="Color format conversion")
    p_color.add_argument("input", help="Color value (e.g. #06b6d4, rgb(6,182,212), hsl(187,98,43))")
    p_color.add_argument("--to", choices=["hex", "rgb", "hsl", "cmyk"], default="hex", help="Target format")

    # url
    p_url = sub.add_parser("url", help="URL encode/decode")
    p_url_sub = p_url.add_subparsers(dest="action", required=True)
    p_url_enc = p_url_sub.add_parser("encode", help="URL-encode")
    p_url_enc.add_argument("text", help="Text to encode")
    p_url_dec = p_url_sub.add_parser("decode", help="URL-decode")
    p_url_dec.add_argument("text", help="Text to decode")

    # diff
    p_diff = sub.add_parser("diff", help="Line-by-line file diff")
    p_diff.add_argument("file1", help="First file")
    p_diff.add_argument("file2", help="Second file")
    p_diff.add_argument("--context", type=int, default=3, help="Context lines")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Dispatch
    from . import tools
    dispatch = {
        "convert": tools.cmd_convert,
        "base64": tools.cmd_base64,
        "hash": tools.cmd_hash,
        "jwt": tools.cmd_jwt,
        "time": tools.cmd_time,
        "uuid": tools.cmd_uuid,
        "color": tools.cmd_color,
        "url": tools.cmd_url,
        "diff": tools.cmd_diff,
    }
    handler = dispatch.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
