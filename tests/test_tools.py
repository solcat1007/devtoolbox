"""
Test suite for DevToolbox.

All tests use unittest (stdlib), no pytest required.
Run: python -m devtoolbox.tests.test_tools
"""

import io
import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from devtoolbox import tools


class TestBase64(unittest.TestCase):
    """Test base64 encode/decode."""

    def test_encode(self):
        args = MagicMock(action="encode", text="hello world")
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            tools.cmd_base64(args)
        self.assertEqual(out.getvalue().strip(), "aGVsbG8gd29ybGQ=")

    def test_decode(self):
        args = MagicMock(action="decode", data="aGVsbG8gd29ybGQ=")
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            tools.cmd_base64(args)
        self.assertEqual(out.getvalue().strip(), "hello world")

    def test_encode_unicode(self):
        args = MagicMock(action="encode", text="你好")
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            tools.cmd_base64(args)
        self.assertEqual(out.getvalue().strip(), "5L2g5aW9")

    def test_decode_unicode(self):
        args = MagicMock(action="decode", data="5L2g5aW9")
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            tools.cmd_base64(args)
        self.assertEqual(out.getvalue().strip(), "你好")


class TestHash(unittest.TestCase):
    """Test hash computation."""

    def test_md5_text(self):
        args = MagicMock(algorithm="md5", input="hello", text=True)
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            tools.cmd_hash(args)
        self.assertIn("5d41402abc4b2a76b9719d911017c592", out.getvalue())

    def test_sha256_text(self):
        args = MagicMock(algorithm="sha256", input="hello", text=True)
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            tools.cmd_hash(args)
        expected = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        self.assertIn(expected, out.getvalue())

    def test_sha512_text(self):
        args = MagicMock(algorithm="sha512", input="test", text=True)
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            tools.cmd_hash(args)
        self.assertIn("ee26b0dd4af7e749a", out.getvalue())

    def test_file_hash(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("hello")
            f.flush()
            fname = f.name
        try:
            args = MagicMock(algorithm="md5", input=fname, text=False)
            with patch("sys.stdout", new_callable=io.StringIO) as out:
                tools.cmd_hash(args)
            self.assertIn("5d41402abc4b2a76b9719d911017c592", out.getvalue())
        finally:
            os.unlink(fname)


class TestJWT(unittest.TestCase):
    """Test JWT decoding."""

    # A sample JWT: header={"alg":"HS256","typ":"JWT"}, payload={"sub":"1234567890","name":"John Doe","iat":1516239022}
    TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

    def test_decode(self):
        args = MagicMock(action="decode", token=self.TOKEN)
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            tools.cmd_jwt(args)
        output = out.getvalue()
        self.assertIn("HS256", output)
        self.assertIn("John Doe", output)
        self.assertIn("1234567890", output)

    def test_invalid_token(self):
        args = MagicMock(action="decode", token="invalid.token")
        with self.assertRaises(SystemExit):
            with patch("sys.stderr", new_callable=io.StringIO):
                tools.cmd_jwt(args)


class TestTime(unittest.TestCase):
    """Test timestamp conversion."""

    def test_timestamp(self):
        args = MagicMock(input="1609459200")  # 2021-01-01 00:00:00 UTC
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            tools.cmd_time(args)
        output = out.getvalue()
        self.assertIn("2021-01-01", output)
        self.assertIn("UTC", output)

    def test_now(self):
        args = MagicMock(input="now")
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            tools.cmd_time(args)
        output = out.getvalue()
        self.assertIn("Unix:", output)
        self.assertIn("ISO:", output)

    def test_iso_input(self):
        args = MagicMock(input="2024-01-15T12:00:00")
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            tools.cmd_time(args)
        output = out.getvalue()
        self.assertIn("Unix:", output)


class TestUUID(unittest.TestCase):
    """Test UUID generation."""

    def test_v4(self):
        args = MagicMock(version=4, namespace=None, name=None, count=1)
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            tools.cmd_uuid(args)
        result = out.getvalue().strip()
        self.assertEqual(len(result), 36)  # UUID format: 8-4-4-4-12

    def test_multiple(self):
        args = MagicMock(version=4, namespace=None, name=None, count=5)
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            tools.cmd_uuid(args)
        results = out.getvalue().strip().split("\n")
        self.assertEqual(len(results), 5)
        # All unique
        self.assertEqual(len(set(results)), 5)

    def test_v5(self):
        args = MagicMock()
        args.version = 5
        args.namespace = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
        args.name = "test.example.com"
        args.count = 1
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            tools.cmd_uuid(args)
        result = out.getvalue().strip()
        self.assertEqual(len(result), 36)


class TestColor(unittest.TestCase):
    """Test color conversion."""

    def test_hex_to_rgb(self):
        args = MagicMock(input="#06b6d4", to="rgb")
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            tools.cmd_color(args)
        self.assertIn("6", out.getvalue())
        self.assertIn("182", out.getvalue())
        self.assertIn("212", out.getvalue())

    def test_hex_to_hsl(self):
        args = MagicMock(input="#ff0000", to="hsl")
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            tools.cmd_color(args)
        self.assertIn("hsl(0", out.getvalue())

    def test_rgb_input(self):
        args = MagicMock(input="rgb(255, 128, 0)", to="hex")
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            tools.cmd_color(args)
        self.assertIn("#ff8000", out.getvalue().strip())

    def test_short_hex(self):
        args = MagicMock(input="#fff", to="rgb")
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            tools.cmd_color(args)
        self.assertIn("255", out.getvalue())

    def test_hsl_input(self):
        args = MagicMock(input="hsl(0, 100%, 50%)", to="hex")
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            tools.cmd_color(args)
        self.assertIn("#ff0000", out.getvalue().strip())

    def test_cmyk(self):
        args = MagicMock(input="#ffffff", to="cmyk")
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            tools.cmd_color(args)
        self.assertIn("cmyk(0%", out.getvalue())


class TestURL(unittest.TestCase):
    """Test URL encode/decode."""

    def test_encode(self):
        args = MagicMock(action="encode", text="hello world=foo")
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            tools.cmd_url(args)
        self.assertEqual(out.getvalue().strip(), "hello%20world%3Dfoo")

    def test_decode(self):
        args = MagicMock(action="decode", text="hello%20world%3Dfoo")
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            tools.cmd_url(args)
        self.assertEqual(out.getvalue().strip(), "hello world=foo")

    def test_encode_unicode(self):
        args = MagicMock(action="encode", text="你好世界")
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            tools.cmd_url(args)
        self.assertEqual(out.getvalue().strip(), "%E4%BD%A0%E5%A5%BD%E4%B8%96%E7%95%8C")


class TestConvert(unittest.TestCase):
    """Test format conversion."""

    def test_json_to_yaml(self):
        json_data = '{"name": "test", "version": 1.0, "active": true}'
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(json_data)
            fname = f.name
        try:
            args = MagicMock(input=fname, from_fmt=None, to_fmt="yaml", indent=2)
            with patch("sys.stdout", new_callable=io.StringIO) as out:
                tools.cmd_convert(args)
            output = out.getvalue()
            self.assertIn("name:", output)
            self.assertIn("test", output)
            self.assertIn("version:", output)
        finally:
            os.unlink(fname)

    def test_json_to_toml(self):
        json_data = '{"name": "test", "version": 1}'
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(json_data)
            fname = f.name
        try:
            args = MagicMock(input=fname, from_fmt=None, to_fmt="toml", indent=2)
            with patch("sys.stdout", new_callable=io.StringIO) as out:
                tools.cmd_convert(args)
            output = out.getvalue()
            self.assertIn("name =", output)
            self.assertIn("version =", output)
        finally:
            os.unlink(fname)

    def test_yaml_to_json(self):
        yaml_data = "name: test\nversion: 1\nactive: true\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
            f.write(yaml_data)
            fname = f.name
        try:
            args = MagicMock(input=fname, from_fmt=None, to_fmt="json", indent=2)
            with patch("sys.stdout", new_callable=io.StringIO) as out:
                tools.cmd_convert(args)
            output = json.loads(out.getvalue())
            self.assertEqual(output["name"], "test")
            self.assertEqual(output["version"], 1)
            self.assertTrue(output["active"])
        finally:
            os.unlink(fname)


class TestDiff(unittest.TestCase):
    """Test file diff."""

    def test_identical(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f1, \
             tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f2:
            f1.write("same content\n")
            f2.write("same content\n")
            f1_name, f2_name = f1.name, f2.name
        try:
            args = MagicMock(file1=f1_name, file2=f2_name, context=3)
            with patch("sys.stdout", new_callable=io.StringIO) as out:
                tools.cmd_diff(args)
            self.assertIn("identical", out.getvalue())
        finally:
            os.unlink(f1_name)
            os.unlink(f2_name)

    def test_different(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f1, \
             tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f2:
            f1.write("line one\nline two\n")
            f2.write("line one\nline changed\n")
            f1_name, f2_name = f1.name, f2.name
        try:
            args = MagicMock(file1=f1_name, file2=f2_name, context=3)
            with patch("sys.stdout", new_callable=io.StringIO) as out:
                tools.cmd_diff(args)
            output = out.getvalue()
            self.assertIn("line two", output)
            self.assertIn("line changed", output)
        finally:
            os.unlink(f1_name)
            os.unlink(f2_name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
