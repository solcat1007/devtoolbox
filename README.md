# DevToolbox

> A developer's Swiss Army knife. One CLI, 9 tools, zero dependencies.

## Why

Every developer wastes time jumping between browser tabs to base64-encode a string, decode a JWT, convert a timestamp, or figure out what color `#06b6d4` is in HSL. DevToolbox puts all these daily-use tools into one CLI — no installation, no internet, no dependencies.

```bash
pip install devtoolbox     # or just: python -m devtoolbox
```

## Tools

| Tool | What it does | Example |
|------|-------------|---------|
| **convert** | JSON ↔ YAML ↔ TOML ↔ CSV | `devtoolbox convert data.json --to yaml` |
| **base64** | Encode/decode base64 | `devtoolbox base64 encode "hello"` |
| **hash** | MD5/SHA1/SHA256/SHA512/SHA3 | `devtoolbox hash sha256 file.txt` |
| **jwt** | Decode JWT header+payload | `devtoolbox jwt decode <token>` |
| **time** | Unix timestamp ↔ human readable | `devtoolbox time 1694000000` |
| **uuid** | Generate v1/v3/v4/v5 UUIDs | `devtoolbox uuid --count 5` |
| **color** | Hex ↔ RGB ↔ HSL ↔ CMYK | `devtoolbox color "#06b6d4" --to hsl` |
| **url** | URL encode/decode | `devtoolbox url encode "a b=c"` |
| **diff** | Unified diff of two files | `devtoolbox diff file1.txt file2.txt` |

## Quick Start

```bash
# Clone and use directly — no install needed
git clone https://github.com/solcat1007/devtoolbox.git
cd devtoolbox
python -m devtoolbox --help
```

## Examples

### Convert formats
```bash
# JSON to YAML
python -m devtoolbox convert config.json --to yaml

# YAML to JSON (pretty-printed)
python -m devtoolbox convert config.yaml --to json --indent 4

# Pipe from stdin
cat data.json | python -m devtoolbox convert - --to csv
```

### Base64
```bash
python -m devtoolbox base64 encode "hello world"
# aGVsbG8gd29ybGQ=

python -m devtoolbox base64 decode aGVsbG8=
# hello
```

### Hash
```bash
# Hash a file
python -m devtoolbox hash sha256 photo.jpg

# Hash a string
python -m devtoolbox hash md5 "hello" --text
```

### JWT
```bash
python -m devtoolbox jwt decode eyJhbGci...
# Header:
# {
#   "alg": "HS256",
#   "typ": "JWT"
# }
#
# Payload:
# {
#   "sub": "1234567890",
#   "name": "John Doe",
#   "iat": 1516239022
# }
#
# Issued: 2018-01-18T01:30:22+00:00
```

### Time
```bash
# Timestamp to human
python -m devtoolbox time 1694000000
# UTC:    2023-09-06 03:06:40 UTC
# Local:  2023-09-06 11:06:40
# ISO:    2023-09-06T03:06:40+00:00

# Current time
python -m devtoolbox time now

# ISO date to timestamp
python -m devtoolbox time 2024-01-15T12:00:00
```

### UUID
```bash
python -m devtoolbox uuid
python -m devtoolbox uuid --count 10
python -m devtoolbox uuid --version 5 --namespace 6ba7b810-9dad-11d1-80b4-00c04fd430c8 --name "example.com"
```

### Color
```bash
python -m devtoolbox color "#06b6d4" --to hsl
# hsl(187, 98%, 43%)

python -m devtoolbox color "rgb(255, 128, 0)" --to hex
# #ff8000

python -m devtoolbox color "#fff" --to cmyk
# cmyk(0%, 0%, 0%, 0%)
```

### URL
```bash
python -m devtoolbox url encode "hello world=foo"
# hello%20world%3Dfoo

python -m devtoolbox url decode hello%20world
# hello world
```

### Diff
```bash
python -m devtoolbox diff original.txt modified.txt
python -m devtoolbox diff original.txt modified.txt --context 5
```

## Testing

```bash
python -m devtoolbox.tests.test_tools -v
```

All 30 tests pass:
```
Ran 30 tests in 0.020s
OK
```

## Design Principles

1. **Zero dependencies** — Pure Python 3.8+ standard library. No pip install needed.
2. **Unix philosophy** — Each tool does one thing well. Compose with pipes.
3. **Fast** — No startup overhead. No HTTP. Everything is local.
4. **Readable output** — Formatted for humans, not machines.
5. **Stdin support** — Pipe data between tools.

## Project Structure

```
devtoolbox/
├── __init__.py        Version info
├── __main__.py        CLI entry point (argparse)
├── tools.py           All 9 tool implementations
└── tests/
    └── test_tools.py  30 test cases, all passing
```

## License

MIT

## Author

solcat1007
