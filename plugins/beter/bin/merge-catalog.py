#!/usr/bin/env python3
"""merge-catalog.py - merge a fresh catalog extraction into the committed catalog.

Usage:
  merge-catalog.py <fresh extraction dir> --into <committed catalog dir> [--dry-run] [--refresh]

The fresh extraction directory is the staging directory the documentation was
extracted into: *.yaml files named and shaped as in beter-feed/catalog/
(meta.yaml, discipline-index.yaml, shared-codes.yaml, sport-<id>-<slug>.yaml),
per references/catalog/02-snapshot.md. The committed catalog directory is
beter-feed/catalog/; it is created when it does not exist, so the first
extraction is the same command.

The merge is additive. No committed entry is ever deleted:

  - Every list is a union keyed by the entry's identity: `sport` in
    discipline-index.yaml, (marketType, resultType, interval[, subInterval])
    in documented_markets, (field, code) in unresolved, and `code` in every
    other list. A list entry without its identity fields, two entries with
    one identity, or one identity whose values differ in type between the
    two files (code 1 against code "1") stops the merge.
  - An entry in both: the committed entry is kept, except that a changed
    `name` follows the fresh extraction (renamed). Every other differing
    field keeps its committed value and is reported (changed, with fields).
  - An entry only in the fresh extraction is appended to its list (added).
  - An entry only in the committed catalog is kept (absent_from_docs).
  - An unresolved entry whose code the same fresh file now carries in the
    list its `field` names leaves unresolved (resolved). Each segment of the
    field is snake-cased and matches the list path segment at the same place
    from the end when it equals the segment or its plural: incident.type
    names incidents.types, marketType names trading.market_types,
    trading.interval names trading.intervals. A field that matches no list,
    or more than one, leaves the entry where it is.
  - A file only in the fresh extraction is added whole (files_added); its
    entries are counted, not listed. A committed file the extraction lacks is
    kept untouched (files_not_in_staging).
  - meta.yaml is merged: source.pages is a union keyed by `path` in which the
    fresh record wins for a path it carries; snapshot_date takes the later
    date; changelog_seen takes the later date only under --refresh, which a
    changelog refresh passes, and otherwise keeps its committed value; gaps
    and absences are unioned by exact string; a
    value the fresh meta.yaml lacks, or leaves null, keeps its committed
    value. An empty or non-mapping fresh meta.yaml, or a merged
    changelog_seen later than the merged snapshot_date, stops the merge.
  - Every other scalar follows the fresh file; each one that moves is
    reported under scalars with its old and new value.

A file is rewritten only when its merged content differs from what is
committed, so merging the same extraction twice writes nothing the second
time. --dry-run writes nothing at all. Either way one fenced
beter-catalog-merge block is printed on stdout.

Exit status:
  0  merged, or the dry run computed the merge (the block says which)
  1  a file cannot be merged: it does not parse, a list entry carries no
     identity field, two entries share one identity, an identity differs in
     type, the two files hold different kinds of value at the same path, the
     fresh meta.yaml is empty, or the merged changelog_seen is later than the
     merged snapshot_date (listed, nothing written)
  2  cannot run here: PyYAML is not importable (a one-line MISSING message
     says what to do instead)
  3  could not run at all: usage error, no such directory, a file that
     cannot be read, or a catalog directory that cannot be written

merge-catalog.mjs behaves the same with plain node.
"""

import copy
import json
import os
import re
import sys

REPORT_FIELDS = ("added", "renamed", "changed", "absent_from_docs", "resolved", "scalars")
SECTIONS = ("absent_from_docs", "added", "renamed", "changed", "resolved", "scalars")
META_FILE = "meta.yaml"
INDEX_FILE = "discipline-index.yaml"
META_UNION_KEYS = ("gaps", "absences")
META_LATER_KEYS = ("snapshot_date", "changelog_seen")
MARKET_KEY = ("marketType", "resultType", "interval")
MARKET_OPTIONAL = ("subInterval",)
MISSING = object()


class MergeError(Exception):
    """A file that cannot be merged; the message names the file and path."""


def missing_line():
    return "MISSING: install pyyaml, or use merge-catalog.mjs"


def _loader(yaml_module):
    """SafeLoader that leaves 2026-01-01 style scalars as strings, like JSON."""
    ts = "tag:yaml.org,2002:timestamp"

    class Loader(yaml_module.SafeLoader):
        pass

    Loader.yaml_implicit_resolvers = {
        first: [(tag, rx) for tag, rx in resolvers if tag != ts]
        for first, resolvers in yaml_module.SafeLoader.yaml_implicit_resolvers.items()
    }
    return Loader


def _dumper(yaml_module):
    """SafeDumper that writes date-like strings plain and never emits aliases."""
    ts = "tag:yaml.org,2002:timestamp"

    class Dumper(yaml_module.SafeDumper):
        def ignore_aliases(self, data):
            return True

    Dumper.yaml_implicit_resolvers = {
        first: [(tag, rx) for tag, rx in resolvers if tag != ts]
        for first, resolvers in yaml_module.SafeDumper.yaml_implicit_resolvers.items()
    }
    return Dumper


def dump(yaml_module, data):
    # yaml.safe_dump(..., sort_keys=False, allow_unicode=True), with dates kept as written.
    return yaml_module.dump(
        data, Dumper=_dumper(yaml_module), sort_keys=False, allow_unicode=True,
        default_flow_style=False,
    )


# ---------------------------------------------------------------- report text

_PLAIN = re.compile(r"^[A-Za-z_][A-Za-z0-9_.\-]*$")
_PLAIN_PATH = re.compile(r"^[A-Za-z0-9_.][A-Za-z0-9_./\-]*(:/[A-Za-z0-9_./\-]*)?$")
PLAIN_FIELDS = ("file", "path")


def scalar_text(value):
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)):
        return repr(value)
    return json.dumps(str(value), ensure_ascii=False)


def flow(value):
    if isinstance(value, dict):
        return "{" + ", ".join(
            "%s: %s" % (key_text(k), key_text(v) if k in PLAIN_FIELDS and isinstance(v, str)
                        else flow(v))
            for k, v in value.items()) + "}"
    if isinstance(value, list):
        return "[" + ", ".join(flow(v) for v in value) + "]"
    return scalar_text(value)


def key_text(key):
    key = str(key)
    return key if _PLAIN.match(key) else json.dumps(key, ensure_ascii=False)


def path_text(path):
    path = path.replace("\\", "/")
    return path if _PLAIN_PATH.match(path) else json.dumps(path, ensure_ascii=False)


def render_report(into, written, report):
    lines = ["```beter-catalog-merge", "version: 1",
             "into: %s" % path_text(into),
             "written: %s" % ("true" if written else "false")]
    if report["files"]:
        lines.append("files:")
        for name in sorted(report["files"]):
            counts = report["files"][name]
            lines.append("  %s: %s" % (key_text(name), flow({f: counts[f] for f in REPORT_FIELDS})))
    else:
        lines.append("files: {}")
    for section in ("files_added", "files_not_in_staging"):
        items = report[section]
        lines.append("%s:" % section if items else "%s: []" % section)
        for item in items:
            lines.append("  - %s" % key_text(item))
    for section in SECTIONS:
        items = report[section]
        if not items:
            lines.append("%s: []" % section)
            continue
        lines.append("%s:" % section)
        for item in items:
            lines.append("  - %s" % flow(item))
    lines.append("```")
    return "\n".join(lines)


# ---------------------------------------------------------------- merging

def dotted(path):
    out = ""
    for part in path:
        if isinstance(part, int):
            out += "[%d]" % part
        else:
            out += ("." if out else "") + str(part)
    return out or "$"


def is_container(value):
    return isinstance(value, (dict, list))


def same(a, b):
    """Equality that tells 1, 1.0, True and "1" apart, as the Node twin does."""
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return kind(a) == kind(b) and a == b


def snake(segment):
    return re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", segment).lower()


def plural(word):
    return word if word.endswith("s") else word + "s"


def lists_in(doc, path=()):
    """Every (path segments, list) reachable through mappings, not through list entries."""
    found = []
    if isinstance(doc, dict):
        for key, value in doc.items():
            if isinstance(value, list):
                found.append((tuple(path) + (str(key),), value))
            elif isinstance(value, dict):
                found.extend(lists_in(value, tuple(path) + (str(key),)))
    return found


def names_list(field, where):
    segments = [snake(s) for s in field.split(".")]
    if len(segments) > len(where):
        return False
    tail = where[len(where) - len(segments):]
    return all(have in (want, plural(want)) for want, have in zip(segments, tail))


def is_resolved(fresh_root, field, code):
    if not isinstance(field, str) or not field:
        return False
    hits = [items for where, items in lists_in(fresh_root) if names_list(field, where)]
    if len(hits) != 1:
        return False
    return any(isinstance(e, dict) and "code" in e and same(e["code"], code) for e in hits[0])


def kind(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    return "other"


def token(pairs):
    return json.dumps([[k, kind(v), text] for k, v, text in pairs])


class Merger:
    def __init__(self, fname, report, itemise=True, fresh_root=None):
        self.fname = fname
        self.report = report
        self.itemise = itemise
        self.fresh_root = fresh_root
        self.counts = {f: 0 for f in REPORT_FIELDS}

    def note(self, field, item):
        self.counts[field] += 1
        if self.itemise:
            self.report[field].append(item)

    def fail(self, path, message):
        raise MergeError("%s: %s: %s" % (self.fname, dotted(path), message))

    def mismatch(self, path, committed, fresh):
        def what(value):
            return "mapping" if isinstance(value, dict) else "list" if isinstance(value, list) else "scalar"
        self.fail(path, "a %s in the committed file and a %s in the fresh one"
                  % (what(committed), what(fresh)))

    def identity_fields(self, path):
        last = next((p for p in reversed(path) if not isinstance(p, int)), None)
        if self.fname == INDEX_FILE:
            return ("sport",), ()
        if "documented_markets" in path:
            return MARKET_KEY, MARKET_OPTIONAL
        if last == "unresolved":
            return ("field", "code"), ()
        return ("code",), ()

    def identity(self, entry, path, index):
        """(exact token, type-blind token, key) for one list entry."""
        required, optional = self.identity_fields(path)
        if not isinstance(entry, dict):
            self.fail(path + [index], "list entry is not a mapping, so it has no %s to merge on"
                      % ", ".join(required))
        absent = [f for f in required if f not in entry]
        if absent:
            self.fail(path + [index], "list entry carries no %s, so it cannot be merged"
                      % ", ".join(absent))
        key = {f: entry[f] for f in required}
        key.update({f: entry[f] for f in optional if f in entry})
        names = sorted(key)
        texts = [(k, key[k], scalar_text(key[k]).strip('"')) for k in names]
        exact = token(texts)
        blind = json.dumps([[k, text] for k, _, text in texts])
        return exact, blind, key

    def keyed(self, items, path):
        out = {}
        for i, entry in enumerate(items):
            exact, blind, key = self.identity(entry, path, i)
            if exact in out:
                self.fail(path + [i], "two entries share the identity %s" % flow(key))
            out[exact] = (blind, key, entry, i)
        return out

    def item(self, path, key, entry):
        item = {"file": self.fname, "path": dotted(path), "key": key}
        if isinstance(entry, dict) and "name" in entry:
            item["name"] = entry["name"]
        return item

    def drop_resolved(self, committed, fresh, path):
        kept = []
        for i, entry in enumerate(committed):
            _, _, key = self.identity(entry, path, i)
            if is_resolved(self.fresh_root, entry["field"], entry["code"]):
                self.note("resolved", self.item(path, key, entry))
            else:
                kept.append(entry)
        for i, entry in enumerate(fresh):
            self.identity(entry, path, i)
        fresh = [e for e in fresh if not is_resolved(self.fresh_root, e["field"], e["code"])]
        return kept, fresh

    def merge_list(self, committed, fresh, path):
        last = next((p for p in reversed(path) if not isinstance(p, int)), None)
        if last == "unresolved" and self.fname != INDEX_FILE and self.fresh_root is not None:
            committed, fresh = self.drop_resolved(committed, fresh, path)
        ckeys = self.keyed(committed, path)
        fkeys = self.keyed(fresh, path)
        cblind = {blind: key for blind, key, _, _ in ckeys.values()}
        for exact, (blind, key, _, i) in fkeys.items():
            if exact not in ckeys and blind in cblind:
                self.fail(path + [i], "identity %s differs in type from the committed %s"
                          % (flow(key), flow(cblind[blind])))
        out = []
        for exact, (_, key, entry, _) in ckeys.items():
            if exact not in fkeys:
                out.append(copy.deepcopy(entry))
                self.note("absent_from_docs", self.item(path, key, entry))
                continue
            new = fkeys[exact][2]
            if same(new, entry):
                out.append(copy.deepcopy(entry))
                continue
            kept = copy.deepcopy(entry)
            fields = [k for k in entry if k not in new or not same(new[k], entry[k])]
            fields += [k for k in new if k not in entry]
            if "name" in fields and "name" in entry and "name" in new:
                kept["name"] = copy.deepcopy(new["name"])
                fields.remove("name")
                self.note("renamed", {"file": self.fname, "path": dotted(path), "key": key,
                                      "from": entry["name"], "to": new["name"]})
            if fields:
                item = self.item(path, key, kept)
                item["fields"] = fields
                self.note("changed", item)
            out.append(kept)
        for exact, (_, key, entry, _) in fkeys.items():
            if exact not in ckeys:
                out.append(copy.deepcopy(entry))
                self.note("added", self.item(path, key, entry))
        return out

    def merge_value(self, committed, fresh, path):
        if fresh is None and is_container(committed):
            fresh = MISSING
        if committed is None and is_container(fresh):
            committed = MISSING
        container = committed if fresh is MISSING else fresh
        if isinstance(container, dict):
            c = {} if committed is MISSING else committed
            f = {} if fresh is MISSING else fresh
            if not isinstance(c, dict) or not isinstance(f, dict):
                self.mismatch(path, c, f)
            return self.merge_mapping(c, f, path)
        if isinstance(container, list):
            c = [] if committed is MISSING else committed
            f = [] if fresh is MISSING else fresh
            if not isinstance(c, list) or not isinstance(f, list):
                self.mismatch(path, c, f)
            return self.merge_list(c, f, path)
        if is_container(committed) and fresh is not MISSING:
            self.mismatch(path, committed, fresh)
        if fresh is MISSING:
            return copy.deepcopy(committed)
        if committed is not MISSING and not same(committed, fresh):
            self.note("scalars", {"file": self.fname, "path": dotted(path),
                                  "from": committed, "to": fresh})
        return copy.deepcopy(fresh)

    def merge_mapping(self, committed, fresh, path):
        out = {}
        for key, value in committed.items():
            out[key] = self.merge_value(value, fresh.get(key, MISSING), path + [key])
        for key, value in fresh.items():
            if key not in committed:
                out[key] = self.merge_value(MISSING, value, path + [key])
        return out


def merge_pages(committed, fresh, merger):
    path = ["source", "pages"]
    lists = []
    for doc in (committed, fresh):
        doc = [] if doc is None or doc is MISSING else doc
        if not isinstance(doc, list):
            merger.fail(path, "expected a list of page records")
        seen = {}
        for i, page in enumerate(doc):
            if not isinstance(page, dict) or "path" not in page:
                merger.fail(path + [i], "page record carries no path, so it cannot be merged")
            if page["path"] in seen:
                merger.fail(path + [i], "two page records share the path %s"
                            % scalar_text(page["path"]))
            seen[page["path"]] = page
        lists.append((doc, seen))
    (c, cseen), (f, fseen) = lists
    out = [copy.deepcopy(fseen.get(p["path"], p)) for p in c]
    out += [copy.deepcopy(p) for p in f if p["path"] not in cseen]
    return out


def merge_meta(committed, fresh, merger, refresh=False):
    if not isinstance(fresh, dict) or not fresh:
        raise MergeError("%s: $: the staging meta.yaml is empty or not a mapping" % META_FILE)
    if committed is MISSING:
        committed = {}
    if not isinstance(committed, dict):
        raise MergeError("%s: $: the committed meta.yaml is not a mapping" % META_FILE)
    out = copy.deepcopy(committed)
    for key, value in fresh.items():
        old = committed.get(key, MISSING)
        if key in META_LATER_KEYS and value is None and old is not MISSING:
            continue
        if key == "changelog_seen" and not refresh and old is not MISSING and old is not None:
            continue
        if key in META_UNION_KEYS:
            lists = []
            for side in (old, value):
                side = [] if side is MISSING or side is None else side
                if not isinstance(side, list) or not all(isinstance(v, str) for v in side):
                    merger.fail([key], "expected a list of strings")
                lists.append(side)
            c, f = lists
            out[key] = list(c) + [s for s in f if s not in c]
        elif key in META_LATER_KEYS and old is not MISSING and old is not None and value is not None:
            later = value if str(value) > str(old) else old
            out[key] = merger.merge_value(old, later, [key])
        elif key == "source":
            old = {} if old is MISSING or old is None else old
            if not isinstance(old, dict) or not isinstance(value, dict):
                merger.fail([key], "a mapping in one file and not in the other")
            source = copy.deepcopy(old)
            for skey, svalue in value.items():
                if skey == "pages":
                    source["pages"] = merge_pages(old.get("pages"), svalue, merger)
                else:
                    source[skey] = merger.merge_value(old.get(skey, MISSING), svalue,
                                                      ["source", skey])
            out[key] = source
        else:
            out[key] = merger.merge_value(old, value, [key])
    seen, taken = out.get("changelog_seen"), out.get("snapshot_date")
    if seen is not None and taken is not None and str(seen) > str(taken):
        merger.fail(["changelog_seen"], "the merged changelog_seen %s is later than the merged "
                    "snapshot_date %s" % (seen, taken))
    return out


def merge_file(fname, committed, fresh, report, itemise=True, refresh=False):
    merger = Merger(fname, report, itemise, fresh_root=fresh)
    if fname == META_FILE:
        merged = merge_meta(committed, fresh, merger, refresh)
    else:
        if not isinstance(fresh, dict) or not (committed is MISSING or isinstance(committed, dict)):
            raise MergeError("%s: $: the top level is not a mapping" % fname)
        merged = merger.merge_mapping({} if committed is MISSING else committed, fresh, [])
    return merged, merger.counts


# ---------------------------------------------------------------- files

def yaml_files(directory):
    return sorted(n for n in os.listdir(directory)
                  if n.lower().endswith(".yaml") and os.path.isfile(os.path.join(directory, n)))


class ReadError(Exception):
    pass


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as handle:
            return handle.read()
    except OSError as exc:
        raise ReadError("ERROR: cannot read %s: %s" % (path, str(exc).replace("\n", " ")))


def parse(yaml_module, path, text, fname):
    try:
        return yaml_module.load(text, Loader=_loader(yaml_module))
    except yaml_module.YAMLError as exc:
        raise MergeError("%s: $: cannot parse %s: %s"
                         % (fname, path, str(exc).replace("\n", " ")))


def parse_args(argv):
    source = None
    into = None
    dry_run = False
    refresh = False
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--into":
            i += 1
            if i >= len(argv):
                return None
            into = argv[i]
        elif arg.startswith("--into="):
            into = arg[len("--into="):]
        elif arg == "--dry-run":
            dry_run = True
        elif arg == "--refresh":
            refresh = True
        elif arg in ("-h", "--help") or arg.startswith("--"):
            return None
        elif source is None:
            source = arg
        else:
            return None
        i += 1
    if source is None or not into:
        return None
    return source, into, dry_run, refresh


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    args = parse_args(argv)
    if args is None:
        print("usage: merge-catalog.py <fresh extraction dir> --into <committed catalog dir> "
              "[--dry-run] [--refresh]")
        return 3
    source, into, dry_run, refresh = args

    try:
        import yaml
    except ImportError:
        print(missing_line())
        return 2

    if not os.path.isdir(source):
        print("ERROR: no such directory: %s" % source)
        return 3
    if os.path.exists(into) and not os.path.isdir(into):
        print("ERROR: %s is not a directory. Pass --into DIR with the committed catalog directory."
              % into)
        return 3
    fresh_names = yaml_files(source)
    if not fresh_names:
        print("ERROR: no catalog files (*.yaml) in %s" % source)
        return 3
    committed_names = yaml_files(into) if os.path.isdir(into) else []

    report = {"files": {}, "files_added": [], "files_not_in_staging": []}
    report.update({section: [] for section in SECTIONS})
    writes = []
    errors = []
    try:
        for fname in fresh_names:
            fresh_path = os.path.join(source, fname)
            fresh_text = read_text(fresh_path)
            try:
                fresh = parse(yaml, fresh_path, fresh_text, fname)
                if fname in committed_names:
                    into_path = os.path.join(into, fname)
                    committed_text = read_text(into_path)
                    committed = parse(yaml, into_path, committed_text, fname)
                    merged, counts = merge_file(fname, committed, fresh, report, refresh=refresh)
                    changed = not same(merged, committed)
                    newline = "\r\n" if "\r\n" in committed_text else "\n"
                else:
                    merged, counts = merge_file(fname, MISSING, fresh, report, itemise=False,
                                                refresh=refresh)
                    report["files_added"].append(fname)
                    changed = True
                    newline = "\r\n" if "\r\n" in fresh_text else "\n"
            except MergeError as exc:
                errors.append(str(exc))
                continue
            if changed or any(counts.values()):
                report["files"][fname] = counts
            if changed:
                writes.append((fname, merged, newline))
    except ReadError as exc:
        print(str(exc))
        return 3
    if errors:
        for line in errors:
            print(line)
        print("%d file(s) cannot be merged; nothing written" % len(errors), file=sys.stderr)
        return 1
    report["files_not_in_staging"] = [n for n in committed_names if n not in fresh_names]

    written = False
    if writes and not dry_run:
        try:
            os.makedirs(into, exist_ok=True)
        except OSError as exc:
            print("ERROR: cannot create %s: %s. Pass --into DIR with a directory you can write to."
                  % (into, exc.strerror or exc))
            return 3
        for fname, merged, newline in writes:
            path = os.path.join(into, fname)
            text = dump(yaml, merged)
            try:
                with open(path, "w", encoding="utf-8", newline=newline) as handle:
                    handle.write(text)
            except OSError as exc:
                print("ERROR: cannot write %s: %s. Pass --into DIR with a directory you can write to."
                      % (path, exc.strerror or exc))
                return 3
            written = True

    print(render_report(into, written, report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
