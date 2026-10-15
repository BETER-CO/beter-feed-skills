#!/usr/bin/env python3
"""validate.py - validate a beter-feed YAML or JSON file against its schema.

Usage:
  validate.py <file.yaml|json> [--schema <name>]

The schemas live in ../skills/feed-integration/schemas/ next to this
plugin's skill. --schema takes a short name (mapping-spec, bindings, scaffold),
the full file name, or a path to a schema file. Without --schema the schema is
picked from the shape of the document:

  top-level "bindings"                          -> bindings
  top-level "rows", "key_shape" or "feed"       -> scaffold
  top-level "channel", "catalog" or "policy"    -> mapping-spec

Output: one line per error, "<json path>: <message>", on stdout.

Exit status:
  0  the document is valid
  1  the document has errors (listed)
  2  cannot run here: PyYAML or jsonschema is not importable (a one-line
     MISSING message says what to do instead)
  3  could not check at all: usage error, no such file or unreadable file,
     no schema could be chosen, or the document's top-level keys match more
     than one schema (pass --schema)

validate.mjs behaves the same with plain node.

YAML dialect: PyYAML reads YAML 1.1 and validate.mjs's js-yaml reads YAML 1.2,
so an unquoted `on: yes` differs. Write keys and booleans in the schema's
quoted or lowercase true/false form; the two helpers then agree on every
document this skill writes.
"""

import json
import os
import sys

SCHEMA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    os.pardir, "skills", "feed-integration", "schemas",
)

SCHEMA_NAMES = {
    "mapping-spec": "beter-mapping-spec.schema.json",
    "bindings": "beter-bindings.schema.json",
    "scaffold": "beter-scaffold.schema.json",
}


def missing_line(schema_file):
    return (
        "MISSING: install pyyaml jsonschema, or use validate.mjs, "
        "or check against schemas/%s by hand" % schema_file
    )


def resolve_schema_name(name):
    """Return (schema file path, schema file name) for a --schema value."""
    if name in SCHEMA_NAMES:
        fname = SCHEMA_NAMES[name]
    else:
        fname = name
        if fname.startswith("beter-") and not fname.endswith(".json"):
            fname = fname + ".schema.json"
        short = fname[len("beter-"):] if fname.startswith("beter-") else fname
        short = short[: -len(".schema.json")] if short.endswith(".schema.json") else short
        if short in SCHEMA_NAMES:
            fname = SCHEMA_NAMES[short]
    for candidate in (os.path.join(SCHEMA_DIR, fname), name):
        if os.path.isfile(candidate):
            return candidate, os.path.basename(candidate)
    return None, fname


def matching_schemas(doc):
    """Names of every schema whose top-level shape the document matches."""
    if not isinstance(doc, dict):
        return []
    found = []
    if "bindings" in doc:
        found.append("bindings")
    if any(k in doc for k in ("rows", "key_shape", "feed")):
        found.append("scaffold")
    if any(k in doc for k in ("channel", "catalog", "policy")):
        found.append("mapping-spec")
    return found


def json_path(error):
    out = "$"
    for part in error.absolute_path:
        if isinstance(part, int):
            out += "[%d]" % part
        else:
            out += "." + str(part)
    return out


def describe(error):
    message = error.message
    if len(message) > 300:
        message = message[:297] + "..."
    if error.validator in ("oneOf", "anyOf") and error.context:
        from jsonschema.exceptions import best_match
        inner = best_match(error.context)
        if inner is not None:
            where = json_path(inner)
            text = inner.message if len(inner.message) <= 200 else inner.message[:197] + "..."
            message += " (closest branch: %s: %s)" % (where, text)
    return message.replace("\n", " ")


def load_document(path, yaml_module):
    with open(path, "r", encoding="utf-8-sig") as handle:
        text = handle.read()
    if path.lower().endswith(".json"):
        return json.loads(text)
    return yaml_module.load(text, Loader=_string_dates_loader(yaml_module))


def _string_dates_loader(yaml_module):
    """SafeLoader that leaves 2026-01-01 style scalars as strings, like JSON."""
    ts = "tag:yaml.org,2002:timestamp"

    class Loader(yaml_module.SafeLoader):
        pass

    Loader.yaml_implicit_resolvers = {
        first: [(tag, rx) for tag, rx in resolvers if tag != ts]
        for first, resolvers in yaml_module.SafeLoader.yaml_implicit_resolvers.items()
    }
    return Loader


def parse_args(argv):
    path = None
    schema = None
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--schema":
            i += 1
            if i >= len(argv):
                return None, None
            schema = argv[i]
        elif arg.startswith("--schema="):
            schema = arg[len("--schema="):]
        elif arg in ("-h", "--help"):
            return None, None
        elif path is None:
            path = arg
        else:
            return None, None
        i += 1
    if path is None:
        return None, None
    return path, schema


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    path, schema_arg = parse_args(argv)
    if path is None:
        print("usage: validate.py <file.yaml|json> [--schema mapping-spec|bindings|scaffold]")
        return 3

    default_schema = SCHEMA_NAMES.get(schema_arg or "", None) or "beter-mapping-spec.schema.json"
    try:
        import yaml
        import jsonschema
        from jsonschema import validators
    except ImportError:
        print(missing_line(default_schema if schema_arg else "<name>.schema.json"))
        return 2

    if not os.path.isfile(path):
        print("ERROR: no such file: %s" % path)
        return 3
    try:
        doc = load_document(path, yaml)
    except OSError as exc:
        print("ERROR: cannot read %s: %s" % (path, str(exc).replace("\n", " ")))
        return 3
    except (ValueError, yaml.YAMLError) as exc:
        detail = str(exc).replace("\n", " ")
        print("$: cannot parse %s: %s" % (path, detail))
        return 1

    name = schema_arg
    if name is None:
        matches = matching_schemas(doc)
        if len(matches) > 1:
            print(
                "ERROR: ambiguous document, matches %s; pass --schema <name>"
                % ", ".join(matches)
            )
            return 3
        if not matches:
            print(
                "ERROR: cannot pick a schema from the top-level keys; "
                "pass --schema mapping-spec|bindings|scaffold"
            )
            return 3
        name = matches[0]
    schema_path, schema_file = resolve_schema_name(name)
    if schema_path is None:
        print("ERROR: unknown schema %r; known: %s" % (name, ", ".join(sorted(SCHEMA_NAMES))))
        return 3

    with open(schema_path, "r", encoding="utf-8-sig") as handle:
        schema = json.load(handle)
    cls = validators.validator_for(schema, default=jsonschema.Draft202012Validator)
    validator = cls(schema)
    errors = sorted(
        validator.iter_errors(doc),
        key=lambda e: ([str(p) for p in e.absolute_path], e.message),
    )
    for error in errors:
        print("%s: %s" % (json_path(error), describe(error)))
    if errors:
        print("%d error(s) against %s" % (len(errors), schema_file), file=sys.stderr)
        return 1
    print("OK: %s is valid against %s" % (path, schema_file), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
