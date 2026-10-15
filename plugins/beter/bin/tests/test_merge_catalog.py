"""Tests for merge-catalog.py and merge-catalog.mjs. Run from the repository root:

    py -m unittest discover -s plugins/beter/bin/tests

All documents here are synthetic. The parity test runs merge-catalog.mjs on
the same fixtures and is skipped when node or js-yaml is not available.
"""

import contextlib
import importlib.util
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.dirname(HERE)
MERGE = os.path.join(BIN, "merge-catalog.py")
MERGE_MJS = os.path.join(BIN, "merge-catalog.mjs")

try:
    import yaml
    HAVE_DEPS = True
except ImportError:
    yaml = None
    HAVE_DEPS = False

SPORTS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 19]


def index_doc(sports, date="2026-10-01"):
    lines = ["version: 1", "snapshot_date: %s" % date, "disciplines:"]
    for sport in sports:
        lines.append('  - {sport: %d, name: "Sport %d", slug: sport-%d}' % (sport, sport, sport))
    return "\n".join(lines) + "\n"


SPORT_6 = """\
version: 1
sport: 6
name: "eFootball"
slug: efootball
snapshot_date: 2026-10-01

trading:
  market_types:  [{code: 1, name: "Match result"}, {code: 3, name: "Total"}]
  result_types:  [{code: 1, name: "Goal"}]
  documented_markets:
    - {marketType: 1, resultType: 1, interval: 1, name: "Result"}
    - {marketType: 1, resultType: 1, interval: 1, subInterval: 2, name: "Result, half"}

incidents:
  types:
    - code: 4
      name: "Goal"
      source: {band: below_1000, code: 1}

unresolved:
  - {field: incident.type, code: 77, looked_on: feed/incident-feed/incidents}
"""

META = """\
version: 1
snapshot_date: 2026-10-01
changelog_seen: 2026-09-30
gaps: ["sport 6 scoreboard stages not published"]
source:
  base: https://docs.example.invalid/public/
  pages:
    - path: feed/trading-feed/meta-data
      fetched_at: 2026-10-01T08:41:07Z
      sha256: aaaa
      provides: [discipline-index, sport-6/trading]
    - path: feed/incident-feed/incidents
      fetched_at: 2026-10-01T08:41:22Z
      sha256: bbbb
      provides: [sport-6/incidents]
"""

# A single-page re-fetch: one page record, newer dates, a new gap, no base.
META_PARTIAL = """\
version: 1
snapshot_date: 2026-10-08
changelog_seen: 2026-10-07
gaps: ["sport 2 incident params not published"]
source:
  pages:
    - path: feed/incident-feed/incidents
      fetched_at: 2026-10-08T09:00:00Z
      sha256: cccc
      provides: [sport-6/incidents]
"""

META_FULL = META.replace("snapshot_date: 2026-10-01", "snapshot_date: 2026-10-08").replace(
    "changelog_seen: 2026-09-30", "changelog_seen: 2026-10-07").replace("sha256: aaaa", "sha256: dddd")

# Every list a discipline file can carry, each holding code 9, for the field-to-list rule.
ALL_LISTS = """\
version: 1
sport: 6
trading:
  market_types:  [{code: 9, name: "m"}]
  result_types:  [{code: 9, name: "r"}]
  intervals:     [{code: 9, name: "i"}]
  sub_intervals: [{code: 9, name: "s"}]
  outcome_types: [{code: 9, name: "o"}]
scoreboard:
  stages:    [{code: 9, name: "st"}]
  intervals: [{code: 9, name: "si"}]
incidents:
  types: [{code: 9, name: "t"}]
unresolved: []
"""

RESOLVING_FIELDS = ["incident.type", "stage", "trading.interval", "scoreboard.interval",
                    "market_type", "marketType", "result_type", "sub_interval", "outcome_type"]
STAYING_FIELDS = ["interval", "incidentType", "incident.types.code", "market"]

NESTED_MARKETS = SPORT_6.replace(
    "  documented_markets:\n"
    "    - {marketType: 1, resultType: 1, interval: 1, name: \"Result\"}\n"
    "    - {marketType: 1, resultType: 1, interval: 1, subInterval: 2, name: \"Result, half\"}\n",
    "  documented_markets:\n"
    "    match:\n"
    "      - {marketType: 2, resultType: 43, interval: 1, name: \"Corners\"}\n")

RESOLVED_77 = SPORT_6.replace(
    '      source: {band: below_1000, code: 1}\n',
    '      source: {band: below_1000, code: 1}\n'
    '    - {code: 77, name: "Var check", source: {band: below_1000, code: 77}}\n',
).replace(
    "unresolved:\n  - {field: incident.type, code: 77, looked_on: feed/incident-feed/incidents}\n",
    "unresolved: []\n")

# Fixtures shared by the scenario tests and the parity test:
# name -> (committed files, staging files, extra arguments).
SCENARIOS = {
    "regressed_index": ({"discipline-index.yaml": index_doc(SPORTS)},
                        {"discipline-index.yaml": index_doc([0, 19], "2026-10-07")}, []),
    "added_renamed_changed": (
        {"sport-6-efootball.yaml": SPORT_6},
        {"sport-6-efootball.yaml": SPORT_6
            .replace('[{code: 1, name: "Goal"}]', '[{code: 43, name: "Corner"}, {code: 1, name: "Goal"}]')
            .replace('name: "Total"', 'name: "Total goals"')
            .replace('name: "Goal"\n      source: {band: below_1000, code: 1}',
                     'name: "Goal scored"\n      source: {band: below_1000, code: 2}')},
        []),
    "new_and_missing_files": (
        {"sport-6-efootball.yaml": SPORT_6, "sport-7-other.yaml": SPORT_6.replace("sport: 6", "sport: 7")},
        {"sport-6-efootball.yaml": SPORT_6,
         "sport-11-basketball.yaml": SPORT_6.replace("sport: 6", "sport: 11")}, ["--dry-run"]),
    "partial_meta": ({"meta.yaml": META}, {"meta.yaml": META_PARTIAL}, []),
    "resolved": ({"sport-6-efootball.yaml": SPORT_6}, {"sport-6-efootball.yaml": RESOLVED_77}, []),
    "first_extraction": ({}, {"meta.yaml": META, "sport-6-efootball.yaml": SPORT_6}, []),
    "type_mismatch": ({"sport-6-efootball.yaml": SPORT_6},
                      {"sport-6-efootball.yaml": SPORT_6.replace('{code: 3, name: "Total"}',
                                                                 '{code: "3", name: "Total"}')}, []),
    "empty_meta": ({"meta.yaml": META}, {"meta.yaml": "{}\n"}, []),
    "full_meta": ({"meta.yaml": META}, {"meta.yaml": META_FULL}, ["--refresh"]),
    "nested_markets": ({"sport-6-efootball.yaml": NESTED_MARKETS},
                       {"sport-6-efootball.yaml": NESTED_MARKETS.replace(
                           '      - {marketType: 2, resultType: 43, interval: 1, name: "Corners"}\n',
                           '      - {marketType: 2, resultType: 43, interval: 1, name: "Corners"}\n'
                           '      - {marketType: 2, resultType: 43, interval: 1, subInterval: 1, '
                           'name: "Corners, half"}\n')}, []),
}


def load_module():
    spec = importlib.util.spec_from_file_location("beter_merge_catalog", MERGE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_tree(directory, files):
    os.makedirs(directory, exist_ok=True)
    for name, text in files.items():
        with open(os.path.join(directory, name), "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)


@unittest.skipUnless(HAVE_DEPS, "pyyaml not installed")
class MergeCatalogTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.fresh = os.path.join(self.dir.name, "fresh")
        self.into = os.path.join(self.dir.name, "catalog")
        os.makedirs(self.fresh)
        os.makedirs(self.into)

    def write(self, directory, name, text):
        write_tree(directory, {name: text})

    def scenario(self, name):
        committed, fresh, extra = SCENARIOS[name]
        write_tree(self.into, committed)
        write_tree(self.fresh, fresh)
        return extra

    def read(self, name):
        with open(os.path.join(self.into, name), "r", encoding="utf-8") as handle:
            return yaml.safe_load(handle.read())

    def raw(self, name):
        with open(os.path.join(self.into, name), "rb") as handle:
            return handle.read()

    def snapshot(self):
        return {n: self.raw(n) for n in sorted(os.listdir(self.into))}

    def run_cli(self, *extra):
        proc = subprocess.run(
            [sys.executable, MERGE, self.fresh, "--into", self.into, *extra],
            capture_output=True, text=True, encoding="utf-8",
        )
        return proc.returncode, proc.stdout, proc.stderr

    def report(self, out):
        lines = out.strip().splitlines()
        self.assertEqual(lines[0], "```beter-catalog-merge")
        self.assertEqual(lines[-1], "```")
        return yaml.safe_load("\n".join(lines[1:-1]))

    def merged(self, *extra):
        rc, out, err = self.run_cli(*extra)
        self.assertEqual(rc, 0, out + err)
        return self.report(out)

    def refused(self, *needles, extra=()):
        before = self.snapshot()
        rc, out, _ = self.run_cli(*extra)
        self.assertEqual(rc, 1, out)
        self.assertNotIn("beter-catalog-merge", out)
        for needle in needles:
            self.assertIn(needle, out)
        self.assertEqual(self.snapshot(), before)
        return out

    # -- the 2026-10-07 shape

    def test_regressed_index_keeps_every_committed_discipline(self):
        self.scenario("regressed_index")
        report = self.merged()
        doc = self.read("discipline-index.yaml")
        self.assertEqual([d["sport"] for d in doc["disciplines"]], SPORTS)
        self.assertEqual(str(doc["snapshot_date"]), "2026-10-07")
        self.assertEqual(report["files"]["discipline-index.yaml"]["absent_from_docs"], 11)
        self.assertEqual(len(report["absent_from_docs"]), 11)
        self.assertEqual(report["absent_from_docs"][0]["key"], {"sport": 1})
        self.assertEqual(report["added"], [])
        self.assertTrue(report["written"])
        self.assertEqual(report["scalars"], [{
            "file": "discipline-index.yaml", "path": "snapshot_date",
            "from": "2026-10-01", "to": "2026-10-07"}])

    # -- entries

    def test_added_codes_are_appended_at_the_end(self):
        self.scenario("added_renamed_changed")
        report = self.merged()
        codes = [e["code"] for e in self.read("sport-6-efootball.yaml")["trading"]["result_types"]]
        self.assertEqual(codes, [1, 43])
        self.assertEqual(report["added"], [{
            "file": "sport-6-efootball.yaml", "path": "trading.result_types",
            "key": {"code": 43}, "name": "Corner"}])
        self.assertTrue(report["written"])
        doc = self.read("sport-6-efootball.yaml")
        self.assertEqual(list(doc), ["version", "sport", "name", "slug", "snapshot_date",
                                     "trading", "incidents", "unresolved"])
        self.assertIn(b"snapshot_date: 2026-10-01\n", self.raw("sport-6-efootball.yaml"))

    def test_rename_is_applied_and_reported(self):
        self.scenario("added_renamed_changed")
        report = self.merged()
        self.assertIn({"file": "sport-6-efootball.yaml", "path": "trading.market_types",
                       "key": {"code": 3}, "from": "Total", "to": "Total goals"}, report["renamed"])
        names = [e["name"] for e in self.read("sport-6-efootball.yaml")["trading"]["market_types"]]
        self.assertEqual(names, ["Match result", "Total goals"])

    def test_other_field_change_is_reported_and_not_applied(self):
        self.write(self.into, "sport-6-efootball.yaml", SPORT_6)
        self.write(self.fresh, "sport-6-efootball.yaml",
                   SPORT_6.replace("{band: below_1000, code: 1}", "{band: below_1000, code: 2}"))
        report = self.merged()
        self.assertEqual(len(report["changed"]), 1)
        self.assertEqual(report["changed"][0]["path"], "incidents.types")
        self.assertEqual(report["changed"][0]["fields"], ["source"])
        self.assertEqual(report["renamed"], [])
        incident = self.read("sport-6-efootball.yaml")["incidents"]["types"][0]
        self.assertEqual(incident["source"]["code"], 1)
        self.assertFalse(report["written"])

    def test_name_plus_field_change_applies_the_name_only(self):
        self.scenario("added_renamed_changed")
        report = self.merged()
        self.assertIn({"file": "sport-6-efootball.yaml", "path": "incidents.types",
                       "key": {"code": 4}, "from": "Goal", "to": "Goal scored"}, report["renamed"])
        self.assertEqual(report["changed"], [{
            "file": "sport-6-efootball.yaml", "path": "incidents.types", "key": {"code": 4},
            "name": "Goal scored", "fields": ["source"]}])
        incident = self.read("sport-6-efootball.yaml")["incidents"]["types"][0]
        self.assertEqual(incident["name"], "Goal scored")
        self.assertEqual(incident["source"]["code"], 1)

    def test_documented_markets_are_keyed_by_the_tuple(self):
        self.write(self.into, "sport-6-efootball.yaml", SPORT_6)
        fresh = SPORT_6.replace(
            '    - {marketType: 1, resultType: 1, interval: 1, subInterval: 2, name: "Result, half"}\n',
            '    - {marketType: 1, resultType: 1, interval: 1, subInterval: 2, name: "Result, half"}\n'
            '    - {marketType: 1, resultType: 1, interval: 2, name: "Result, extra time"}\n')
        self.write(self.fresh, "sport-6-efootball.yaml", fresh)
        report = self.merged()
        self.assertEqual(report["added"], [{
            "file": "sport-6-efootball.yaml", "path": "trading.documented_markets",
            "key": {"marketType": 1, "resultType": 1, "interval": 2},
            "name": "Result, extra time"}])
        rows = self.read("sport-6-efootball.yaml")["trading"]["documented_markets"]
        self.assertEqual(len(rows), 3)

    def test_resolved_unresolved_entry_leaves_unresolved(self):
        self.scenario("resolved")
        report = self.merged()
        self.assertEqual(report["resolved"], [{
            "file": "sport-6-efootball.yaml", "path": "unresolved",
            "key": {"field": "incident.type", "code": 77}}])
        self.assertEqual(report["absent_from_docs"], [])
        doc = self.read("sport-6-efootball.yaml")
        self.assertEqual(doc["unresolved"], [])
        self.assertEqual([t["code"] for t in doc["incidents"]["types"]], [4, 77])
        rc, out, _ = self.run_cli()
        self.assertEqual(self.report(out)["resolved"], [])

    def test_field_forms_that_resolve_and_forms_that_stay(self):
        for field, resolves in ([(f, True) for f in RESOLVING_FIELDS]
                                + [(f, False) for f in STAYING_FIELDS]):
            with self.subTest(field=field):
                committed = ALL_LISTS.replace(
                    "unresolved: []", "unresolved:\n  - {field: %s, code: 9}" % field)
                self.write(self.into, "sport-6-x.yaml", committed)
                self.write(self.fresh, "sport-6-x.yaml", ALL_LISTS)
                report = self.merged("--dry-run")
                self.assertEqual(len(report["resolved"]), 1 if resolves else 0, report)
                self.assertEqual(len(report["absent_from_docs"]), 0 if resolves else 1, report)

    def test_nested_documented_markets_are_keyed_by_the_tuple(self):
        self.scenario("nested_markets")
        report = self.merged()
        self.assertEqual(report["added"], [{
            "file": "sport-6-efootball.yaml", "path": "trading.documented_markets.match",
            "key": {"marketType": 2, "resultType": 43, "interval": 1, "subInterval": 1},
            "name": "Corners, half"}])

    def test_unresolved_entry_stays_when_its_code_is_in_another_list(self):
        self.write(self.into, "sport-6-efootball.yaml", SPORT_6)
        self.write(self.fresh, "sport-6-efootball.yaml", SPORT_6.replace(
            '[{code: 1, name: "Goal"}]', '[{code: 1, name: "Goal"}, {code: 77, name: "Other"}]'))
        report = self.merged()
        self.assertEqual(report["resolved"], [])
        self.assertEqual(len(self.read("sport-6-efootball.yaml")["unresolved"]), 1)

    # -- files

    def test_new_discipline_file_is_added_whole(self):
        self.write(self.into, "sport-6-efootball.yaml", SPORT_6)
        self.write(self.fresh, "sport-6-efootball.yaml", SPORT_6)
        basketball = SPORT_6.replace("sport: 6", "sport: 11").replace("efootball", "basketball")
        self.write(self.fresh, "sport-11-basketball.yaml", basketball)
        report = self.merged()
        self.assertEqual(report["files_added"], ["sport-11-basketball.yaml"])
        self.assertEqual(report["files"]["sport-11-basketball.yaml"]["added"], 7)
        self.assertEqual(report["added"], [])
        self.assertEqual(self.read("sport-11-basketball.yaml"), yaml.safe_load(basketball))

    def test_committed_file_not_in_staging_is_kept(self):
        self.write(self.into, "sport-6-efootball.yaml", SPORT_6)
        self.write(self.fresh, "discipline-index.yaml", index_doc([6]))
        report = self.merged()
        self.assertEqual(report["files_not_in_staging"], ["sport-6-efootball.yaml"])
        self.assertEqual(self.read("sport-6-efootball.yaml"), yaml.safe_load(SPORT_6))

    # -- meta.yaml

    def test_partial_meta_keeps_committed_pages_and_takes_later_dates(self):
        self.scenario("partial_meta")
        report = self.merged()
        meta = self.read("meta.yaml")
        pages = meta["source"]["pages"]
        self.assertEqual([p["path"] for p in pages],
                         ["feed/trading-feed/meta-data", "feed/incident-feed/incidents"])
        self.assertEqual([p["sha256"] for p in pages], ["aaaa", "cccc"])
        self.assertEqual(meta["source"]["base"], "https://docs.example.invalid/public/")
        self.assertEqual(str(meta["snapshot_date"]), "2026-10-08")
        self.assertEqual(str(meta["changelog_seen"]), "2026-09-30")
        self.assertEqual(meta["gaps"], ["sport 6 scoreboard stages not published",
                                        "sport 2 incident params not published"])
        self.assertIn(b"fetched_at: 2026-10-08T09:00:00Z", self.raw("meta.yaml"))
        self.assertEqual(report["files"]["meta.yaml"]["added"], 0)
        self.assertEqual(report["files"]["meta.yaml"]["absent_from_docs"], 0)

    def test_later_changelog_seen_stays_without_refresh(self):
        self.write(self.into, "meta.yaml", META)
        self.write(self.fresh, "meta.yaml", META_FULL)
        report = self.merged()
        meta = self.read("meta.yaml")
        self.assertEqual(str(meta["changelog_seen"]), "2026-09-30")
        self.assertEqual(str(meta["snapshot_date"]), "2026-10-08")
        self.assertNotIn("changelog_seen", [s["path"] for s in report["scalars"]])

    def test_refresh_moves_changelog_seen_to_the_later_date(self):
        extra = self.scenario("full_meta")
        report = self.merged(*extra)
        meta = self.read("meta.yaml")
        self.assertEqual(str(meta["changelog_seen"]), "2026-10-07")
        self.assertEqual(str(meta["snapshot_date"]), "2026-10-08")
        self.assertEqual([p["sha256"] for p in meta["source"]["pages"]], ["dddd", "bbbb"])
        self.assertIn({"file": "meta.yaml", "path": "changelog_seen",
                       "from": "2026-09-30", "to": "2026-10-07"}, report["scalars"])

    def test_empty_changelog_seen_keeps_the_committed_value(self):
        self.write(self.into, "meta.yaml", META)
        self.write(self.fresh, "meta.yaml", META_FULL.replace(
            "changelog_seen: 2026-10-07", "changelog_seen:"))
        self.merged()
        self.assertEqual(str(self.read("meta.yaml")["changelog_seen"]), "2026-09-30")

    def test_changelog_seen_later_than_snapshot_date_exits_one(self):
        self.write(self.into, "meta.yaml", META)
        self.write(self.fresh, "meta.yaml", META_FULL.replace(
            "snapshot_date: 2026-10-08", "snapshot_date: 2026-10-02"))
        self.refused("meta.yaml: changelog_seen:", "later than the merged snapshot_date",
                     extra=("--refresh",))

    def test_older_meta_dates_do_not_move_back(self):
        self.write(self.into, "meta.yaml", META_PARTIAL)
        self.write(self.fresh, "meta.yaml", META)
        report = self.merged("--refresh")
        self.assertEqual(report["scalars"], [])
        meta = self.read("meta.yaml")
        self.assertEqual(str(meta["snapshot_date"]), "2026-10-08")
        self.assertEqual(str(meta["changelog_seen"]), "2026-10-07")
        self.assertEqual(len(meta["source"]["pages"]), 2)

    def test_empty_meta_exits_one(self):
        self.scenario("empty_meta")
        self.refused("meta.yaml: $:", "empty")

    # -- whole runs

    def test_merging_twice_reports_and_writes_nothing(self):
        for name, text in (("meta.yaml", META), ("discipline-index.yaml", index_doc(SPORTS)),
                           ("sport-6-efootball.yaml", SPORT_6)):
            self.write(self.fresh, name, text)
        os.rmdir(self.into)
        first = self.merged()
        self.assertTrue(first["written"])
        self.assertEqual(sorted(first["files_added"]), sorted(os.listdir(self.fresh)))
        before = self.snapshot()
        second = self.merged()
        self.assertFalse(second["written"])
        self.assertEqual(second["files"], {})
        for section in ("files_added", "files_not_in_staging", "absent_from_docs", "added",
                        "renamed", "changed", "resolved", "scalars"):
            self.assertEqual(second[section], [], section)
        self.assertEqual(self.snapshot(), before)

    def test_dry_run_writes_nothing(self):
        self.write(self.into, "sport-6-efootball.yaml", SPORT_6)
        self.write(self.fresh, "sport-6-efootball.yaml",
                   SPORT_6.replace('name: "Total"', 'name: "Total goals"'))
        self.write(self.fresh, "sport-11-basketball.yaml", SPORT_6.replace("sport: 6", "sport: 11"))
        before = self.snapshot()
        report = self.merged("--dry-run")
        self.assertFalse(report["written"])
        self.assertEqual(len(report["renamed"]), 1)
        self.assertEqual(self.snapshot(), before)

    # -- refusals

    def test_list_without_identity_field_exits_one(self):
        self.write(self.into, "sport-6-efootball.yaml", SPORT_6)
        self.write(self.fresh, "sport-6-efootball.yaml", SPORT_6.replace(
            '[{code: 1, name: "Goal"}]', '[{id: 1, name: "Goal"}]'))
        self.refused("sport-6-efootball.yaml: trading.result_types[0]:", "code")

    def test_duplicate_identity_exits_one(self):
        self.write(self.into, "sport-6-efootball.yaml", SPORT_6)
        self.write(self.fresh, "sport-6-efootball.yaml", SPORT_6.replace(
            '[{code: 1, name: "Goal"}]', '[{code: 1, name: "Goal"}, {code: 1, name: "Again"}]'))
        self.refused("trading.result_types[1]:", "share the identity")

    def test_mapping_where_a_list_is_expected_exits_one(self):
        self.write(self.into, "sport-6-efootball.yaml", SPORT_6)
        self.write(self.fresh, "sport-6-efootball.yaml", SPORT_6.replace(
            '[{code: 1, name: "Goal"}]', '{code: 1, name: "Goal"}'))
        self.refused("trading.result_types:", "list")

    def test_list_where_a_mapping_is_expected_exits_one(self):
        self.write(self.into, "sport-6-efootball.yaml", SPORT_6)
        self.write(self.fresh, "sport-6-efootball.yaml", SPORT_6.replace(
            "incidents:\n  types:\n", "incidents:\n  - types:\n").replace(
            "    - code: 4\n      name: \"Goal\"\n      source: {band: below_1000, code: 1}\n",
            "    - {code: 4, name: \"Goal\"}\n"))
        self.refused("incidents:", "mapping")

    def test_unparseable_file_exits_one(self):
        self.write(self.into, "sport-6-efootball.yaml", SPORT_6)
        self.write(self.fresh, "sport-6-efootball.yaml", "trading: [unclosed\n")
        self.refused("cannot parse")

    def test_code_type_mismatch_exits_one(self):
        self.scenario("type_mismatch")
        self.refused("trading.market_types[1]:", "differs in type")

    def test_missing_source_directory_exits_three(self):
        proc = subprocess.run(
            [sys.executable, MERGE, os.path.join(self.dir.name, "absent"), "--into", self.into],
            capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(proc.returncode, 3)
        self.assertIn("no such directory", proc.stdout)


class MergeCatalogUsageTest(unittest.TestCase):
    def test_no_arguments_prints_usage(self):
        proc = subprocess.run([sys.executable, MERGE], capture_output=True, text=True,
                              encoding="utf-8")
        self.assertEqual(proc.returncode, 3)
        self.assertIn("usage:", proc.stdout)

    def test_missing_yaml_prints_missing_line_and_exits_two(self):
        module = load_module()
        buf = io.StringIO()
        with mock.patch.dict(sys.modules, {"yaml": None}), contextlib.redirect_stdout(buf):
            rc = module.main(["fresh", "--into", "catalog"])
        self.assertEqual(rc, 2)
        self.assertTrue(buf.getvalue().startswith("MISSING: install pyyaml"))
        self.assertIn("merge-catalog.mjs", buf.getvalue())


def node_skip_reason():
    if shutil.which("node") is None:
        return "node is not on PATH"
    with tempfile.TemporaryDirectory() as tmp:
        proc = subprocess.run(["node", MERGE_MJS, tmp, "--into", tmp], cwd=tmp,
                              capture_output=True, text=True, encoding="utf-8")
    if proc.returncode == 2 and proc.stdout.startswith("MISSING"):
        return "js-yaml is not resolvable from the current directory, bin/ or NODE_PATH"
    return None


@unittest.skipUnless(HAVE_DEPS, "pyyaml not installed")
class MergeCatalogParityTest(unittest.TestCase):
    """merge-catalog.mjs prints the same report and exits the same on every scenario."""

    @classmethod
    def setUpClass(cls):
        reason = node_skip_reason()
        if reason:
            raise unittest.SkipTest(reason)
        cls.module = load_module()

    def run_tool(self, command, committed, fresh, extra):
        with tempfile.TemporaryDirectory() as tmp:
            write_tree(os.path.join(tmp, "staging"), fresh)
            if committed:
                write_tree(os.path.join(tmp, "catalog"), committed)
            runs = []
            for _ in range(2):
                proc = subprocess.run(command + ["staging", "--into", "catalog"] + extra,
                                      cwd=tmp, capture_output=True, text=True, encoding="utf-8")
                runs.append((proc.returncode, proc.stdout.replace("\r\n", "\n"),
                             self.parsed(os.path.join(tmp, "catalog"))))
            return runs

    def parsed(self, directory):
        if not os.path.isdir(directory):
            return {}
        loader = self.module._loader(yaml)
        out = {}
        for name in sorted(os.listdir(directory)):
            with open(os.path.join(directory, name), encoding="utf-8") as handle:
                out[name] = yaml.load(handle.read(), Loader=loader)
        return out

    def test_reports_match(self):
        for name, (committed, fresh, extra) in SCENARIOS.items():
            with self.subTest(scenario=name):
                py = self.run_tool([sys.executable, MERGE], committed, fresh, extra)
                js = self.run_tool(["node", MERGE_MJS], committed, fresh, extra)
                self.assertEqual(js, py)


if __name__ == "__main__":
    unittest.main()
