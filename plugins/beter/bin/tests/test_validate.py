"""Tests for validate.py. Run from this directory or from bin/:

    py -m unittest discover -s plugins/beter/bin/tests

All documents here are synthetic.
"""

import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
VALIDATE = os.path.join(os.path.dirname(HERE), "validate.py")

try:
    import jsonschema  # noqa: F401
    import yaml  # noqa: F401
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False

VALID_MAPPING = """\
version: 1
sport: 5
channel: trading
catalog:
  snapshot: test-snapshot
policy:
  on_unmapped: drop_market
markets: []
"""

# channel "trading" needs markets; "sport" must be an integer.
INVALID_MAPPING = """\
version: 1
sport: not-a-number
channel: trading
catalog:
  snapshot: test-snapshot
policy:
  on_unmapped: drop_market
"""

VALID_BINDINGS = """\
version: 1
bindings:
  - sport: 5
    channel: markets
    resolver: src/Resolver.cs#Resolve
    failure: throw
    digest: sha256:0000000000000000000000000000000000000000000000000000000000000000
"""

INVALID_BINDINGS = """\
version: 1
bindings:
  - sport: 5
    channel: odds
    resolver: src/Resolver.cs#Resolve
    failure: throw
    digest: sha256:abc
"""

# A planned row names a resolver generation will create, so it carries no digest;
# the timetable is bound under the row-list name "sports".
VALID_PLANNED_BINDINGS = """\
version: 1
bindings:
  - sport: 3
    channel: markets
    resolver: src/Sport3Resolver.cs#Resolve
    failure: throw
    policy_site: src/Consumer.cs#OnMarket
    status: proposed
  - sport: 3
    channel: sports
    resolver: src/SportResolver.cs#Resolve
    failure: throw
    digest: sha256:0000000000000000000000000000000000000000000000000000000000000000
"""

# "timetable" is the scope's word; a binding names the row list, "sports".
INVALID_TIMETABLE_BINDINGS = """\
version: 1
bindings:
  - sport: 3
    channel: timetable
    resolver: src/SportResolver.cs#Resolve
    failure: throw
"""

VALID_SCAFFOLD = """\
feed: other-feed
source:
  repository: example/repo
  read_from: code
key_shape: [market_type]
rows: []
"""


def load_module():
    spec = importlib.util.spec_from_file_location("beter_validate", VALIDATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ValidateCliTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)

    def write(self, name, text):
        path = os.path.join(self.dir.name, name)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        return path

    def run_cli(self, *args):
        proc = subprocess.run(
            [sys.executable, VALIDATE, *args],
            capture_output=True, text=True, encoding="utf-8",
        )
        return proc.returncode, proc.stdout, proc.stderr

    @unittest.skipUnless(HAVE_DEPS, "pyyaml and jsonschema not installed")
    def test_valid_document_exits_zero(self):
        rc, out, _ = self.run_cli(self.write("ok.yaml", VALID_MAPPING))
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.strip(), "")

    @unittest.skipUnless(HAVE_DEPS, "pyyaml and jsonschema not installed")
    def test_invalid_document_lists_path_and_exits_one(self):
        rc, out, _ = self.run_cli(self.write("bad.yaml", INVALID_MAPPING))
        self.assertEqual(rc, 1, out)
        self.assertIn("$.sport:", out)
        self.assertTrue(all(line.startswith("$") for line in out.strip().splitlines()))

    @unittest.skipUnless(HAVE_DEPS, "pyyaml and jsonschema not installed")
    def test_missing_required_property_is_listed_at_root(self):
        rc, out, _ = self.run_cli(self.write("bad.yaml", INVALID_MAPPING))
        self.assertEqual(rc, 1)
        self.assertIn("markets", out)

    @unittest.skipUnless(HAVE_DEPS, "pyyaml and jsonschema not installed")
    def test_schema_picked_from_shape(self):
        rc, _, err = self.run_cli(self.write("b.yaml", VALID_BINDINGS))
        self.assertEqual(rc, 0)
        self.assertIn("beter-bindings.schema.json", err)
        rc, _, err = self.run_cli(self.write("s.yaml", VALID_SCAFFOLD))
        self.assertEqual(rc, 0)
        self.assertIn("beter-scaffold.schema.json", err)
        rc, _, err = self.run_cli(self.write("m.yaml", VALID_MAPPING))
        self.assertEqual(rc, 0)
        self.assertIn("beter-mapping-spec.schema.json", err)

    @unittest.skipUnless(HAVE_DEPS, "pyyaml and jsonschema not installed")
    def test_invalid_bindings_list_indexed_paths(self):
        rc, out, _ = self.run_cli(self.write("b.yaml", INVALID_BINDINGS))
        self.assertEqual(rc, 1)
        self.assertIn("$.bindings[0].channel:", out)
        self.assertIn("$.bindings[0].digest:", out)

    @unittest.skipUnless(HAVE_DEPS, "pyyaml and jsonschema not installed")
    def test_planned_row_without_digest_and_sports_channel_are_valid(self):
        rc, out, _ = self.run_cli(self.write("b.yaml", VALID_PLANNED_BINDINGS))
        self.assertEqual(rc, 0, out)

    @unittest.skipUnless(HAVE_DEPS, "pyyaml and jsonschema not installed")
    def test_timetable_is_not_a_binding_channel(self):
        rc, out, _ = self.run_cli(self.write("b.yaml", INVALID_TIMETABLE_BINDINGS))
        self.assertEqual(rc, 1)
        self.assertIn("$.bindings[0].channel:", out)

    @unittest.skipUnless(HAVE_DEPS, "pyyaml and jsonschema not installed")
    def test_explicit_schema_overrides_shape(self):
        rc, out, _ = self.run_cli(
            self.write("m.yaml", VALID_MAPPING), "--schema", "scaffold")
        self.assertEqual(rc, 1)
        self.assertIn("feed", out)

    @unittest.skipUnless(HAVE_DEPS, "pyyaml and jsonschema not installed")
    def test_json_input(self):
        rc, out, _ = self.run_cli(
            self.write("m.json", '{"version": 1, "sport": "x", "channel": "trading"}'),
            "--schema", "mapping-spec")
        self.assertEqual(rc, 1)
        self.assertIn("$.sport:", out)

    @unittest.skipUnless(HAVE_DEPS, "pyyaml and jsonschema not installed")
    def test_unpickable_shape_exits_three(self):
        rc, out, _ = self.run_cli(self.write("u.yaml", "hello: world\n"))
        self.assertEqual(rc, 3)
        self.assertIn("--schema", out)

    @unittest.skipUnless(HAVE_DEPS, "pyyaml and jsonschema not installed")
    def test_ambiguous_document_exits_three_and_names_the_matches(self):
        doc = "bindings: []\nchannel: trading\nrows: []\n"
        rc, out, _ = self.run_cli(self.write("amb.yaml", doc))
        self.assertEqual(rc, 3, out)
        self.assertIn("ERROR: ambiguous document, matches bindings, scaffold, mapping-spec", out)
        self.assertIn("--schema", out)
        rc, _, _ = self.run_cli(self.write("amb.yaml", doc), "--schema", "bindings")
        self.assertEqual(rc, 1)

    @unittest.skipUnless(HAVE_DEPS, "pyyaml and jsonschema not installed")
    def test_missing_file_exits_three(self):
        rc, out, _ = self.run_cli(os.path.join(self.dir.name, "absent.yaml"))
        self.assertEqual(rc, 3)
        self.assertIn("no such file", out)

    @unittest.skipUnless(HAVE_DEPS, "pyyaml and jsonschema not installed")
    def test_unreadable_file_exits_three(self):
        module = load_module()
        path = self.write("locked.yaml", VALID_MAPPING)
        buf = io.StringIO()
        error = PermissionError("denied")
        with mock.patch.object(module, "load_document", side_effect=error):
            with contextlib.redirect_stdout(buf):
                rc = module.main([path])
        self.assertEqual(rc, 3)
        self.assertIn("cannot read", buf.getvalue())

    def test_no_arguments_prints_usage(self):
        rc, out, _ = self.run_cli()
        self.assertEqual(rc, 3)
        self.assertIn("usage:", out)


class MissingDependencyTest(unittest.TestCase):
    """Simulate PyYAML / jsonschema being absent by making the import fail."""

    def run_main(self, blocked, argv):
        module = load_module()
        stubs = {name: None for name in blocked}  # None in sys.modules => ImportError
        buf = io.StringIO()
        with mock.patch.dict(sys.modules, stubs), contextlib.redirect_stdout(buf):
            rc = module.main(argv)
        return rc, buf.getvalue()

    def test_missing_yaml_prints_missing_line_and_exits_two(self):
        rc, out = self.run_main(["yaml"], ["whatever.yaml"])
        self.assertEqual(rc, 2)
        self.assertEqual(len(out.strip().splitlines()), 1)
        self.assertTrue(out.startswith("MISSING: install pyyaml jsonschema"))
        self.assertIn("validate.mjs", out)
        self.assertIn("by hand", out)

    def test_missing_jsonschema_names_the_schema_file(self):
        rc, out = self.run_main(["jsonschema"], ["whatever.yaml", "--schema", "bindings"])
        self.assertEqual(rc, 2)
        self.assertIn("schemas/beter-bindings.schema.json", out)


if __name__ == "__main__":
    unittest.main()
