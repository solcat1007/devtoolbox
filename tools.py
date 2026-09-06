"""
All DevToolbox tool implementations.

Each function takes parsed argparse args and prints results to stdout.
Zero external dependencies — uses only Python standard library.
"""

import base64
import binascii
import colorsys
import csv
import difflib
import hashlib
import io
import json
import os
import re
import sys
import time
import urllib.parse
import uuid as uuid_mod
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Format Converter: JSON ↔ YAML ↔ TOML ↔ CSV
# ---------------------------------------------------------------------------

def cmd_convert(args):
    """Convert between JSON, YAML, TOML, and CSV formats."""
    # Read input
    if args.input == "-":
        raw = sys.stdin.read()
    else:
        with open(args.input, "r", encoding="utf-8") as f:
            raw = f.read()

    # Auto-detect source format from file extension
    from_fmt = args.from_fmt
    if from_fmt is None:
        if args.input == "-":
            # Try to guess from content
            stripped = raw.strip()
            if stripped.startswith("{") or stripped.startswith("["):
                from_fmt = "json"
            elif "=" in stripped and "[" not in stripped:
                from_fmt = "toml"
            else:
                from_fmt = "yaml"
        else:
            ext = os.path.splitext(args.input)[1].lower()
            from_fmt = {".json": "json", ".yaml": "yaml", ".yml": "yaml",
                        ".toml": "toml", ".csv": "csv"}.get(ext, "json")

    # Parse input into a Python dict/list
    data = _parse_format(raw, from_fmt)

    # Serialize to target format
    result = _serialize_format(data, args.to_fmt, indent=args.indent)
    print(result)


def _parse_format(raw, fmt):
    """Parse raw text into a Python object based on format."""
    if fmt == "json":
        return json.loads(raw)
    elif fmt == "yaml":
        return _parse_yaml(raw)
    elif fmt == "toml":
        return _parse_toml(raw)
    elif fmt == "csv":
        reader = csv.DictReader(io.StringIO(raw))
        return list(reader)
    else:
        raise ValueError(f"Unknown format: {fmt}")


def _serialize_format(data, fmt, indent=2):
    """Serialize Python object to a format string."""
    if fmt == "json":
        return json.dumps(data, indent=indent, ensure_ascii=False)
    elif fmt == "yaml":
        return _serialize_yaml(data)
    elif fmt == "toml":
        return _serialize_toml(data)
    elif fmt == "csv":
        return _serialize_csv(data)
    else:
        raise ValueError(f"Unknown format: {fmt}")


def _parse_yaml(raw):
    """Minimal YAML parser — handles key: value, lists, nesting.

    This is NOT a full YAML parser. It handles the common subset:
    - key: value
    - nested objects (indentation-based)
    - simple lists (- item)
    - quoted strings
    - numbers and booleans
    """
    lines = raw.split("\n")
    result, _ = _yaml_parse_block(lines, 0, 0)
    return result


def _yaml_parse_block(lines, start, indent):
    """Parse a YAML block starting at line `start` with given indentation."""
    result = {}
    i = start
    while i < len(lines):
        line = lines[i]
        # Skip empty lines and comments
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        current_indent = len(line) - len(line.lstrip())
        if current_indent < indent:
            break
        if current_indent > indent:
            i += 1
            continue

        # List item
        if stripped.startswith("- "):
            if not isinstance(result, list):
                result = []
            value = stripped[2:].strip()
            result.append(_yaml_scalar(value))
            i += 1
            continue

        # Key: value
        if ":" in stripped:
            colon_idx = stripped.index(":")
            key = stripped[:colon_idx].strip().strip('"\'')
            value = stripped[colon_idx + 1:].strip()

            if not value:
                # Nested block
                nested, next_i = _yaml_parse_block(lines, i + 1, indent + 2)
                result[key] = nested
                i = next_i
            else:
                result[key] = _yaml_scalar(value)
                i += 1
            continue

        i += 1

    return result, i


def _yaml_scalar(value):
    """Parse a YAML scalar value into Python type."""
    if not value:
        return ""
    # Remove quotes
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    # Boolean
    if value.lower() in ("true", "yes"):
        return True
    if value.lower() in ("false", "no"):
        return False
    if value.lower() in ("null", "none", "~"):
        return None
    # Number
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def _serialize_yaml(data, indent=0):
    """Serialize Python object to YAML string."""
    lines = []
    prefix = "  " * indent

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{prefix}{key}:")
                lines.append(_serialize_yaml(value, indent + 1))
            else:
                lines.append(f"{prefix}{key}: {_yaml_format_scalar(value)}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.append(_serialize_yaml(item, indent + 1))
            else:
                lines.append(f"{prefix}- {_yaml_format_scalar(item)}")

    return "\n".join(lines)


def _yaml_format_scalar(value):
    """Format a Python scalar for YAML output."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, str):
        if " " in value or ":" in value:
            return f'"{value}"'
        return value
    return str(value)


def _parse_toml(raw):
    """Minimal TOML parser."""
    result = {}
    current_table = result
    for line in raw.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            table_name = line[1:-1].strip()
            parts = table_name.split(".")
            current_table = result
            for part in parts:
                part = part.strip().strip('"\'')
                if part not in current_table:
                    current_table[part] = {}
                current_table = current_table[part]
            continue
        if "=" in line:
            eq_idx = line.index("=")
            key = line[:eq_idx].strip().strip('"\'')
            value = line[eq_idx + 1:].strip()
            current_table[key] = _toml_scalar(value)
    return result


def _toml_scalar(value):
    """Parse a TOML scalar."""
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def _serialize_toml(data):
    """Serialize Python object to TOML string."""
    lines = []

    def serialize_table(d, prefix=""):
        for key, value in d.items():
            if isinstance(value, dict):
                new_prefix = f"{prefix}.{key}" if prefix else key
                lines.append(f"\n[{new_prefix}]")
                serialize_table(value, new_prefix)
            else:
                lines.append(f"{key} = {_toml_format_scalar(value)}")

    serialize_table(data)
    return "\n".join(lines)


def _toml_format_scalar(value):
    """Format a Python scalar for TOML output."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return '""'
    if isinstance(value, str):
        return f'"{value}"'
    return str(value)


def _serialize_csv(data):
    """Serialize list of dicts to CSV."""
    if not isinstance(data, list):
        data = [data]
    if not data:
        return ""
    output = io.StringIO()
    fieldnames = list(data[0].keys()) if isinstance(data[0], dict) else ["value"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in data:
        if not isinstance(row, dict):
            row = {"value": row}
        writer.writerow(row)
    return output.getvalue()


# ---------------------------------------------------------------------------
# Base64
# ---------------------------------------------------------------------------

def cmd_base64(args):
    """Base64 encode/decode."""
    if args.action == "encode":
        data = args.text.encode("utf-8")
        print(base64.b64encode(data).decode("ascii"))
    elif args.action == "decode":
        try:
            raw = base64.b64decode(args.data)
            try:
                print(raw.decode("utf-8"))
            except UnicodeDecodeError:
                print(f"[binary data, {len(raw)} bytes]")
                print(f"hex: {raw.hex()}")
        except (binascii.Error, ValueError) as e:
            print(f"Error: invalid base64 — {e}", file=sys.stderr)
            sys.exit(1)


# ---------------------------------------------------------------------------
# Hash
# ---------------------------------------------------------------------------

def cmd_hash(args):
    """Calculate hash of a file or string."""
    algorithm = args.algorithm
    hasher = hashlib.new(algorithm)

    if args.text:
        hasher.update(args.input.encode("utf-8"))
    else:
        if not os.path.exists(args.input):
            print(f"Error: file not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        with open(args.input, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)

    print(f"{hasher.hexdigest()}  {args.input}")


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

def cmd_jwt(args):
    """Decode a JWT token (header + payload, no signature verification)."""
    if args.action == "decode":
        token = args.token.strip()
        parts = token.split(".")
        if len(parts) != 3:
            print("Error: JWT must have 3 parts separated by '.'", file=sys.stderr)
            sys.exit(1)

        def decode_part(part):
            # JWT uses base64url without padding
            padded = part + "=" * (4 - len(part) % 4)
            raw = base64.urlsafe_b64decode(padded)
            return json.loads(raw.decode("utf-8"))

        header = decode_part(parts[0])
        payload = decode_part(parts[1])

        print("Header:")
        print(json.dumps(header, indent=2, ensure_ascii=False))
        print("\nPayload:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))

        # Check for expiry
        if "exp" in payload:
            exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
            now = datetime.now(tz=timezone.utc)
            status = "EXPIRED" if now > exp_time else "VALID"
            print(f"\nExpiry: {exp_time.isoformat()} [{status}]")

        if "iat" in payload:
            iat_time = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
            print(f"Issued: {iat_time.isoformat()}")

        if "sub" in payload:
            print(f"Subject: {payload['sub']}")
        if "iss" in payload:
            print(f"Issuer: {payload['iss']}")


# ---------------------------------------------------------------------------
# Time / Timestamp
# ---------------------------------------------------------------------------

def cmd_time(args):
    """Time and timestamp conversion."""
    inp = args.input

    if inp == "now":
        now = datetime.now(tz=timezone.utc)
        local = datetime.now()
        print(f"UTC:    {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"Local:  {local.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Unix:   {int(now.timestamp())}")
        print(f"ISO:    {now.isoformat()}")
        return

    # Try parsing as unix timestamp
    try:
        ts = float(inp)
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        local = datetime.fromtimestamp(ts)
        print(f"UTC:    {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"Local:  {local.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"ISO:    {dt.isoformat()}")
        return
    except ValueError:
        pass

    # Try parsing as ISO date
    try:
        dt = datetime.fromisoformat(inp)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        print(f"Unix:   {int(dt.timestamp())}")
        print(f"UTC:    {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"ISO:    {dt.isoformat()}")
        return
    except ValueError:
        pass

    print(f"Error: could not parse '{inp}' as timestamp or date", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# UUID
# ---------------------------------------------------------------------------

def cmd_uuid(args):
    """Generate UUIDs."""
    for _ in range(args.count):
        if args.version == 4:
            print(str(uuid_mod.uuid4()))
        elif args.version == 1:
            print(str(uuid_mod.uuid1()))
        elif args.version in (3, 5):
            if not args.namespace:
                print("Error: --namespace required for v3/v5", file=sys.stderr)
                sys.exit(1)
            if not args.name:
                print("Error: --name required for v3/v5", file=sys.stderr)
                sys.exit(1)
            ns = uuid_mod.UUID(args.namespace)
            if args.version == 3:
                print(str(uuid_mod.uuid3(ns, args.name)))
            else:
                print(str(uuid_mod.uuid5(ns, args.name)))


# ---------------------------------------------------------------------------
# Color
# ---------------------------------------------------------------------------

def cmd_color(args):
    """Convert between color formats."""
    inp = args.input.strip()
    target = args.to

    # Parse input to RGB
    r, g, b = _parse_color(inp)

    # Convert to target format
    if target == "hex":
        print(f"#{r:02x}{g:02x}{b:02x}")
    elif target == "rgb":
        print(f"rgb({r}, {g}, {b})")
    elif target == "hsl":
        hr, hg, hb = r / 255, g / 255, b / 255
        h, l, s = colorsys.rgb_to_hls(hr, hg, hb)
        print(f"hsl({int(h * 360)}, {int(s * 100)}%, {int(l * 100)}%)")
    elif target == "cmyk":
        c, m, y, k = _rgb_to_cmyk(r, g, b)
        print(f"cmyk({int(c * 100)}%, {int(m * 100)}%, {int(y * 100)}%, {int(k * 100)}%)")


def _parse_color(inp):
    """Parse a color string to (R, G, B) tuple."""
    # Hex: #06b6d4 or #f0f
    if inp.startswith("#"):
        hex_val = inp[1:]
        if len(hex_val) == 3:
            hex_val = "".join(c * 2 for c in hex_val)
        if len(hex_val) != 6:
            raise ValueError(f"Invalid hex color: {inp}")
        r = int(hex_val[0:2], 16)
        g = int(hex_val[2:4], 16)
        b = int(hex_val[4:6], 16)
        return r, g, b

    # rgb(r, g, b)
    match = re.match(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", inp)
    if match:
        return int(match.group(1)), int(match.group(2)), int(match.group(3))

    # hsl(h, s%, l%)
    match = re.match(r"hsl\(\s*(\d+)\s*,\s*(\d+)%\s*,\s*(\d+)%\s*\)", inp)
    if match:
        h = int(match.group(1)) / 360
        s = int(match.group(2)) / 100
        l = int(match.group(3)) / 100
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return int(r * 255), int(g * 255), int(b * 255)

    raise ValueError(f"Could not parse color: {inp}")


def _rgb_to_cmyk(r, g, b):
    """Convert RGB to CMYK."""
    r, g, b = r / 255, g / 255, b / 255
    k = 1 - max(r, g, b)
    if k == 1:
        return 0, 0, 0, 1
    c = (1 - r - k) / (1 - k)
    m = (1 - g - k) / (1 - k)
    y = (1 - b - k) / (1 - k)
    return c, m, y, k


# ---------------------------------------------------------------------------
# URL Encode/Decode
# ---------------------------------------------------------------------------

def cmd_url(args):
    """URL encode/decode."""
    if args.action == "encode":
        print(urllib.parse.quote(args.text, safe=""))
    elif args.action == "decode":
        print(urllib.parse.unquote(args.text))


# ---------------------------------------------------------------------------
# Diff
# ---------------------------------------------------------------------------

def cmd_diff(args):
    """Line-by-line file diff."""
    with open(args.file1, "r", encoding="utf-8") as f:
        lines1 = f.readlines()
    with open(args.file2, "r", encoding="utf-8") as f:
        lines2 = f.readlines()

    diff = difflib.unified_diff(
        lines1, lines2,
        fromfile=args.file1, tofile=args.file2,
        n=args.context,
    )

    result = "".join(diff)
    if result:
        print(result, end="")
    else:
        print("Files are identical")
