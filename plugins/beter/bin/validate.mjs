#!/usr/bin/env node
// validate.mjs - validate a beter-feed YAML or JSON file against its schema.
//
// Usage:
//   node validate.mjs <file.yaml|json> [--schema <name>]
//
// Same behaviour as validate.py. The schemas live in
// ../skills/feed-integration/schemas/. --schema takes a short name
// (mapping-spec, bindings, scaffold), the full file name, or a path to a
// schema file. Without --schema the schema is picked from the top-level shape:
//
//   "bindings"                          -> bindings
//   "rows", "key_shape" or "feed"       -> scaffold
//   "channel", "catalog" or "policy"    -> mapping-spec
//
// Output: one line per error, "<json path>: <message>", on stdout.
//
// Exit status:
//   0  the document is valid
//   1  the document has errors (listed)
//   2  cannot run here: ajv (v8) or js-yaml is not resolvable (a one-line
//      MISSING message says what to do instead)
//   3  could not check at all: usage error, no such file or unreadable file,
//      no schema could be chosen, or the document's top-level keys match more
//      than one schema (pass --schema)
//
// YAML dialect: js-yaml (CORE_SCHEMA) reads YAML 1.2 and validate.py's PyYAML
// reads YAML 1.1, so an unquoted `on: yes` differs. Write keys and booleans in
// the schema's quoted or lowercase true/false form; the two helpers then agree
// on every document this skill writes.
//
// ajv and js-yaml are looked up from the current directory, then from the
// directory of this script, then through NODE_PATH. Nothing is installed.

import { readFileSync, existsSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SCHEMA_DIR = path.join(HERE, "..", "skills", "feed-integration", "schemas");

const SCHEMA_NAMES = {
  "mapping-spec": "beter-mapping-spec.schema.json",
  bindings: "beter-bindings.schema.json",
  scaffold: "beter-scaffold.schema.json",
};

function missingLine(schemaFile) {
  return (
    "MISSING: install ajv js-yaml, or use validate.py, " +
    `or check against schemas/${schemaFile} by hand`
  );
}

function tryRequire(id) {
  const bases = [path.join(process.cwd(), "noop.js"), import.meta.url];
  for (const base of bases) {
    try {
      return createRequire(base)(id);
    } catch {
      // try the next base
    }
  }
  return null;
}

function resolveSchema(name) {
  let fname = name;
  if (Object.prototype.hasOwnProperty.call(SCHEMA_NAMES, name)) {
    fname = SCHEMA_NAMES[name];
  } else {
    let short = name.replace(/\.schema\.json$/, "").replace(/^beter-/, "");
    if (Object.prototype.hasOwnProperty.call(SCHEMA_NAMES, short)) fname = SCHEMA_NAMES[short];
  }
  for (const candidate of [path.join(SCHEMA_DIR, fname), name]) {
    if (existsSync(candidate)) return { file: candidate, name: path.basename(candidate) };
  }
  return { file: null, name: fname };
}

// Names of every schema whose top-level shape the document matches.
function matchingSchemas(doc) {
  if (doc === null || typeof doc !== "object" || Array.isArray(doc)) return [];
  const found = [];
  if ("bindings" in doc) found.push("bindings");
  if (["rows", "key_shape", "feed"].some((k) => k in doc)) found.push("scaffold");
  if (["channel", "catalog", "policy"].some((k) => k in doc)) found.push("mapping-spec");
  return found;
}

function parseArgs(argv) {
  let file = null;
  let schema = null;
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--schema") {
      if (i + 1 >= argv.length) return null;
      schema = argv[++i];
    } else if (a.startsWith("--schema=")) {
      schema = a.slice("--schema=".length);
    } else if (a === "-h" || a === "--help") {
      return null;
    } else if (file === null) {
      file = a;
    } else {
      return null;
    }
  }
  return file === null ? null : { file, schema };
}

// "/markets/3/rule" -> "$.markets[3].rule"
function jsonPath(instancePath) {
  let out = "$";
  for (const raw of instancePath.split("/").slice(1)) {
    const part = raw.replace(/~1/g, "/").replace(/~0/g, "~");
    out += /^\d+$/.test(part) ? `[${part}]` : `.${part}`;
  }
  return out;
}

function describe(err) {
  let message = err.message ?? "invalid";
  const p = err.params ?? {};
  if (err.keyword === "additionalProperties" && p.additionalProperty !== undefined) {
    message = `Additional properties are not allowed (${JSON.stringify(p.additionalProperty)} was unexpected)`;
  } else if (err.keyword === "required" && p.missingProperty !== undefined) {
    message = `${JSON.stringify(p.missingProperty)} is a required property`;
  } else if (err.keyword === "enum" && Array.isArray(p.allowedValues)) {
    message = `must be one of ${JSON.stringify(p.allowedValues)}`;
  } else if (err.keyword === "const" && "allowedValue" in p) {
    message = `must equal ${JSON.stringify(p.allowedValue)}`;
  }
  message = message.replace(/\s*\n\s*/g, " ");
  return message.length > 300 ? message.slice(0, 297) + "..." : message;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args === null) {
    console.log("usage: validate.mjs <file.yaml|json> [--schema mapping-spec|bindings|scaffold]");
    return 3;
  }

  const defaultSchema =
    (args.schema && SCHEMA_NAMES[args.schema]) || (args.schema ? args.schema : "<name>.schema.json");
  const ajvModule = tryRequire("ajv/dist/2020");
  const needsYaml = !args.file.toLowerCase().endsWith(".json");
  const yaml = needsYaml ? tryRequire("js-yaml") : null;
  if (ajvModule === null || (needsYaml && yaml === null)) {
    console.log(missingLine(defaultSchema));
    return 2;
  }
  const Ajv = ajvModule.default ?? ajvModule;

  if (!existsSync(args.file)) {
    console.log(`ERROR: no such file: ${args.file}`);
    return 3;
  }
  let text;
  try {
    text = readFileSync(args.file, "utf-8").replace(/^\uFEFF/, "");
  } catch (e) {
    console.log(`ERROR: cannot read ${args.file}: ${String(e.message ?? e).replace(/\s*\n\s*/g, " ")}`);
    return 3;
  }
  let doc;
  try {
    // CORE_SCHEMA leaves 2026-01-01 style scalars as strings, like JSON.
    doc = needsYaml ? yaml.load(text, { schema: yaml.CORE_SCHEMA }) : JSON.parse(text);
  } catch (e) {
    console.log(`$: cannot parse ${args.file}: ${String(e.message ?? e).replace(/\s*\n\s*/g, " ")}`);
    return 1;
  }

  let name = args.schema;
  if (name === null) {
    const matches = matchingSchemas(doc);
    if (matches.length > 1) {
      console.log(`ERROR: ambiguous document, matches ${matches.join(", ")}; pass --schema <name>`);
      return 3;
    }
    if (matches.length === 0) {
      console.log(
        "ERROR: cannot pick a schema from the top-level keys; pass --schema mapping-spec|bindings|scaffold"
      );
      return 3;
    }
    name = matches[0];
  }
  const resolved = resolveSchema(name);
  if (resolved.file === null) {
    console.log(`ERROR: unknown schema '${name}'; known: ${Object.keys(SCHEMA_NAMES).sort().join(", ")}`);
    return 3;
  }
  const schema = JSON.parse(readFileSync(resolved.file, "utf-8").replace(/^\uFEFF/, ""));

  const ajv = new Ajv({ allErrors: true, strict: false });
  const validate = ajv.compile(schema);
  if (validate(doc)) {
    console.error(`OK: ${args.file} is valid against ${resolved.name}`);
    return 0;
  }
  const lines = (validate.errors ?? [])
    // "if" is bookkeeping for if/then/else; the "then" errors carry the point.
    .filter((e) => e.keyword !== "if")
    .map((e) => `${jsonPath(e.instancePath)}: ${describe(e)}`);
  for (const line of [...new Set(lines)].sort()) console.log(line);
  console.error(`${new Set(lines).size} error(s) against ${resolved.name}`);
  return 1;
}

process.exitCode = main();
