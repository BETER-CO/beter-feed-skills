#!/usr/bin/env node
// merge-catalog.mjs - merge a fresh catalog extraction into the committed catalog.
//
// Usage:
//   node merge-catalog.mjs <fresh extraction dir> --into <committed catalog dir> [--dry-run] [--refresh]
//
// Same behaviour, report and exit status as merge-catalog.py, whose header
// states the merge rules. In short: every list is a union keyed by the
// entry's identity (`sport` in discipline-index.yaml, the marketType,
// resultType, interval[, subInterval] tuple in documented_markets,
// (field, code) in unresolved, `code` elsewhere); committed entries are kept;
// a changed name follows the fresh extraction (renamed) and every other
// differing field keeps its committed value (changed); new entries are
// appended (added); committed entries the extraction lacks are kept
// (absent_from_docs); an unresolved entry the same fresh file now resolves
// leaves unresolved (resolved); new files are added whole; meta.yaml unions
// source.pages by path, keeps the later snapshot_date, moves changelog_seen to
// the later date only under --refresh, and unions gaps and absences; every other scalar follows the fresh file
// (scalars). No committed entry is ever deleted. --dry-run writes nothing.
//
// Exit status:
//   0  merged, or the dry run computed the merge (the block says which)
//   1  a file cannot be merged (listed, nothing written)
//   2  cannot run here: js-yaml is not resolvable (a one-line MISSING message
//      says what to do instead)
//   3  could not run at all: usage error, no such directory, a file that
//      cannot be read, or a catalog directory that cannot be written
//
// YAML: js-yaml (CORE_SCHEMA) reads YAML 1.2 and merge-catalog.py's PyYAML
// reads YAML 1.1, as with validate.mjs and validate.py.
//
// js-yaml is looked up from the current directory, then from the directory of
// this script, then through NODE_PATH. Nothing is installed.

import { readFileSync, writeFileSync, existsSync, statSync, readdirSync, mkdirSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";

const REPORT_FIELDS = ["added", "renamed", "changed", "absent_from_docs", "resolved", "scalars"];
const SECTIONS = ["absent_from_docs", "added", "renamed", "changed", "resolved", "scalars"];
const META_FILE = "meta.yaml";
const INDEX_FILE = "discipline-index.yaml";
const META_UNION_KEYS = ["gaps", "absences"];
const META_LATER_KEYS = ["snapshot_date", "changelog_seen"];
const MARKET_KEY = ["marketType", "resultType", "interval"];
const MARKET_OPTIONAL = ["subInterval"];
const MISSING = Symbol("missing");
const PLAIN_FIELDS = ["file", "path"];

class MergeError extends Error {}
class ReadError extends Error {}

function missingLine() {
  return "MISSING: install js-yaml, or use merge-catalog.py";
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

const has = (obj, key) => Object.prototype.hasOwnProperty.call(obj, key);
const isMap = (v) => v !== null && typeof v === "object" && !Array.isArray(v);
const clone = (v) => (v === undefined ? v : structuredClone(v));

function deepEqual(a, b) {
  if (a === b) return true;
  if (Array.isArray(a) || Array.isArray(b)) {
    if (!Array.isArray(a) || !Array.isArray(b) || a.length !== b.length) return false;
    return a.every((v, i) => deepEqual(v, b[i]));
  }
  if (isMap(a) && isMap(b)) {
    const ka = Object.keys(a);
    if (ka.length !== Object.keys(b).length) return false;
    return ka.every((k) => has(b, k) && deepEqual(a[k], b[k]));
  }
  return false;
}

// ---------------------------------------------------------------- report text

const PLAIN = /^[A-Za-z_][A-Za-z0-9_.\-]*$/;
const PLAIN_PATH = /^[A-Za-z0-9_.][A-Za-z0-9_./\-]*(:\/[A-Za-z0-9_./\-]*)?$/;

function scalarText(v) {
  if (v === null || v === undefined) return "null";
  if (v === true) return "true";
  if (v === false) return "false";
  if (typeof v === "number") return String(v);
  return JSON.stringify(String(v));
}

function keyText(k) {
  k = String(k);
  return PLAIN.test(k) ? k : JSON.stringify(k);
}

function pathText(p) {
  p = p.replace(/\\/g, "/");
  return PLAIN_PATH.test(p) ? p : JSON.stringify(p);
}

function flow(v) {
  if (isMap(v)) {
    return (
      "{" +
      Object.entries(v)
        .map(([k, x]) => `${keyText(k)}: ${PLAIN_FIELDS.includes(k) && typeof x === "string" ? keyText(x) : flow(x)}`)
        .join(", ") +
      "}"
    );
  }
  if (Array.isArray(v)) return "[" + v.map(flow).join(", ") + "]";
  return scalarText(v);
}

function renderReport(into, written, report) {
  const lines = ["```beter-catalog-merge", "version: 1", `into: ${pathText(into)}`, `written: ${written}`];
  const names = Object.keys(report.files).sort();
  if (names.length) {
    lines.push("files:");
    for (const name of names) {
      const counts = report.files[name];
      const ordered = Object.fromEntries(REPORT_FIELDS.map((f) => [f, counts[f]]));
      lines.push(`  ${keyText(name)}: ${flow(ordered)}`);
    }
  } else {
    lines.push("files: {}");
  }
  for (const section of ["files_added", "files_not_in_staging"]) {
    const items = report[section];
    lines.push(items.length ? `${section}:` : `${section}: []`);
    for (const item of items) lines.push(`  - ${keyText(item)}`);
  }
  for (const section of SECTIONS) {
    const items = report[section];
    if (!items.length) {
      lines.push(`${section}: []`);
      continue;
    }
    lines.push(`${section}:`);
    for (const item of items) lines.push(`  - ${flow(item)}`);
  }
  lines.push("```");
  return lines.join("\n");
}

// ---------------------------------------------------------------- merging

function dotted(p) {
  let out = "";
  for (const part of p) {
    if (typeof part === "number") out += `[${part}]`;
    else out += (out ? "." : "") + String(part);
  }
  return out || "$";
}

const isContainer = (v) => isMap(v) || Array.isArray(v);

const snake = (segment) => segment.replace(/(?<=[a-z0-9])([A-Z])/g, "_$1").toLowerCase();
const plural = (word) => (word.endsWith("s") ? word : word + "s");

// Every [path segments, list] reachable through mappings, not through list entries.
function listsIn(doc, p = []) {
  const found = [];
  if (isMap(doc)) {
    for (const [k, v] of Object.entries(doc)) {
      if (Array.isArray(v)) found.push([[...p, String(k)], v]);
      else if (isMap(v)) found.push(...listsIn(v, [...p, String(k)]));
    }
  }
  return found;
}

function namesList(field, where) {
  const segments = field.split(".").map(snake);
  if (segments.length > where.length) return false;
  const tail = where.slice(where.length - segments.length);
  return segments.every((want, i) => tail[i] === want || tail[i] === plural(want));
}

function isResolved(freshRoot, field, code) {
  if (typeof field !== "string" || !field) return false;
  const hits = listsIn(freshRoot)
    .filter(([where]) => namesList(field, where))
    .map(([, items]) => items);
  if (hits.length !== 1) return false;
  return hits[0].some((e) => isMap(e) && has(e, "code") && deepEqual(e.code, code));
}

function kind(v) {
  if (v === null || v === undefined) return "null";
  if (typeof v === "boolean") return "bool";
  if (typeof v === "number") return "number";
  if (typeof v === "string") return "string";
  return "other";
}

class Merger {
  constructor(fname, report, itemise = true, freshRoot = null) {
    this.fname = fname;
    this.report = report;
    this.itemise = itemise;
    this.freshRoot = freshRoot;
    this.counts = Object.fromEntries(REPORT_FIELDS.map((f) => [f, 0]));
  }

  note(field, item) {
    this.counts[field] += 1;
    if (this.itemise) this.report[field].push(item);
  }

  fail(p, message) {
    throw new MergeError(`${this.fname}: ${dotted(p)}: ${message}`);
  }

  mismatch(p, committed, fresh) {
    const what = (v) => (isMap(v) ? "mapping" : Array.isArray(v) ? "list" : "scalar");
    this.fail(p, `a ${what(committed)} in the committed file and a ${what(fresh)} in the fresh one`);
  }

  identityFields(p) {
    const last = [...p].reverse().find((x) => typeof x !== "number");
    if (this.fname === INDEX_FILE) return [["sport"], []];
    if (p.includes("documented_markets")) return [MARKET_KEY, MARKET_OPTIONAL];
    if (last === "unresolved") return [["field", "code"], []];
    return [["code"], []];
  }

  // [exact token, type-blind token, key] for one list entry.
  identity(entry, p, index) {
    const [required, optional] = this.identityFields(p);
    if (!isMap(entry)) {
      this.fail([...p, index], `list entry is not a mapping, so it has no ${required.join(", ")} to merge on`);
    }
    const absent = required.filter((f) => !has(entry, f));
    if (absent.length) this.fail([...p, index], `list entry carries no ${absent.join(", ")}, so it cannot be merged`);
    const key = {};
    for (const f of required) key[f] = entry[f];
    for (const f of optional) if (has(entry, f)) key[f] = entry[f];
    const names = Object.keys(key).sort();
    const texts = names.map((k) => [k, key[k], scalarText(key[k]).replace(/^"+|"+$/g, "")]);
    const exact = JSON.stringify(texts.map(([k, v, t]) => [k, kind(v), t]));
    const blind = JSON.stringify(texts.map(([k, , t]) => [k, t]));
    return [exact, blind, key];
  }

  keyed(items, p) {
    const out = new Map();
    items.forEach((entry, i) => {
      const [exact, blind, key] = this.identity(entry, p, i);
      if (out.has(exact)) this.fail([...p, i], `two entries share the identity ${flow(key)}`);
      out.set(exact, { blind, key, entry, index: i });
    });
    return out;
  }

  item(p, key, entry) {
    const item = { file: this.fname, path: dotted(p), key };
    if (isMap(entry) && has(entry, "name")) item.name = entry.name;
    return item;
  }

  dropResolved(committed, fresh, p) {
    const kept = [];
    committed.forEach((entry, i) => {
      const [, , key] = this.identity(entry, p, i);
      if (isResolved(this.freshRoot, entry.field, entry.code)) this.note("resolved", this.item(p, key, entry));
      else kept.push(entry);
    });
    fresh.forEach((entry, i) => this.identity(entry, p, i));
    return [kept, fresh.filter((e) => !isResolved(this.freshRoot, e.field, e.code))];
  }

  mergeList(committed, fresh, p) {
    const last = [...p].reverse().find((x) => typeof x !== "number");
    if (last === "unresolved" && this.fname !== INDEX_FILE && this.freshRoot !== null) {
      [committed, fresh] = this.dropResolved(committed, fresh, p);
    }
    const ckeys = this.keyed(committed, p);
    const fkeys = this.keyed(fresh, p);
    const cblind = new Map([...ckeys.values()].map((v) => [v.blind, v.key]));
    for (const [exact, v] of fkeys) {
      if (!ckeys.has(exact) && cblind.has(v.blind)) {
        this.fail([...p, v.index], `identity ${flow(v.key)} differs in type from the committed ${flow(cblind.get(v.blind))}`);
      }
    }
    const out = [];
    for (const [exact, { key, entry }] of ckeys) {
      if (!fkeys.has(exact)) {
        out.push(clone(entry));
        this.note("absent_from_docs", this.item(p, key, entry));
        continue;
      }
      const next = fkeys.get(exact).entry;
      if (deepEqual(next, entry)) {
        out.push(clone(entry));
        continue;
      }
      const kept = clone(entry);
      const fields = Object.keys(entry).filter((k) => !has(next, k) || !deepEqual(next[k], entry[k]));
      fields.push(...Object.keys(next).filter((k) => !has(entry, k)));
      const at = fields.indexOf("name");
      if (at >= 0 && has(entry, "name") && has(next, "name")) {
        kept.name = clone(next.name);
        fields.splice(at, 1);
        this.note("renamed", { file: this.fname, path: dotted(p), key, from: entry.name, to: next.name });
      }
      if (fields.length) {
        const item = this.item(p, key, kept);
        item.fields = fields;
        this.note("changed", item);
      }
      out.push(kept);
    }
    for (const [exact, { key, entry }] of fkeys) {
      if (!ckeys.has(exact)) {
        out.push(clone(entry));
        this.note("added", this.item(p, key, entry));
      }
    }
    return out;
  }

  mergeValue(committed, fresh, p) {
    if (fresh === null && isContainer(committed)) fresh = MISSING;
    if (committed === null && isContainer(fresh)) committed = MISSING;
    const probe = fresh === MISSING ? committed : fresh;
    if (isMap(probe)) {
      const c = committed === MISSING ? {} : committed;
      const f = fresh === MISSING ? {} : fresh;
      if (!isMap(c) || !isMap(f)) this.mismatch(p, c, f);
      return this.mergeMapping(c, f, p);
    }
    if (Array.isArray(probe)) {
      const c = committed === MISSING ? [] : committed;
      const f = fresh === MISSING ? [] : fresh;
      if (!Array.isArray(c) || !Array.isArray(f)) this.mismatch(p, c, f);
      return this.mergeList(c, f, p);
    }
    if (isContainer(committed) && fresh !== MISSING) this.mismatch(p, committed, fresh);
    if (fresh === MISSING) return clone(committed);
    if (committed !== MISSING && !deepEqual(committed, fresh)) {
      this.note("scalars", { file: this.fname, path: dotted(p), from: committed, to: fresh });
    }
    return clone(fresh);
  }

  mergeMapping(committed, fresh, p) {
    const out = {};
    for (const [k, v] of Object.entries(committed)) {
      out[k] = this.mergeValue(v, has(fresh, k) ? fresh[k] : MISSING, [...p, k]);
    }
    for (const [k, v] of Object.entries(fresh)) {
      if (!has(committed, k)) out[k] = this.mergeValue(MISSING, v, [...p, k]);
    }
    return out;
  }
}

function mergePages(committed, fresh, merger) {
  const p = ["source", "pages"];
  const lists = [committed, fresh].map((doc) => {
    doc = doc === null || doc === undefined || doc === MISSING ? [] : doc;
    if (!Array.isArray(doc)) merger.fail(p, "expected a list of page records");
    const seen = new Map();
    doc.forEach((page, i) => {
      if (!isMap(page) || !has(page, "path")) merger.fail([...p, i], "page record carries no path, so it cannot be merged");
      if (seen.has(page.path)) merger.fail([...p, i], `two page records share the path ${scalarText(page.path)}`);
      seen.set(page.path, page);
    });
    return [doc, seen];
  });
  const [[c, cseen], [f, fseen]] = lists;
  return [
    ...c.map((page) => clone(fseen.has(page.path) ? fseen.get(page.path) : page)),
    ...f.filter((page) => !cseen.has(page.path)).map(clone),
  ];
}

function mergeMeta(committed, fresh, merger, refresh = false) {
  if (!isMap(fresh) || !Object.keys(fresh).length) {
    throw new MergeError(`${META_FILE}: $: the staging meta.yaml is empty or not a mapping`);
  }
  if (committed === MISSING) committed = {};
  if (!isMap(committed)) throw new MergeError(`${META_FILE}: $: the committed meta.yaml is not a mapping`);
  const out = clone(committed);
  for (const [key, value] of Object.entries(fresh)) {
    let old = has(committed, key) ? committed[key] : MISSING;
    if (META_LATER_KEYS.includes(key) && value === null && old !== MISSING) continue;
    if (key === "changelog_seen" && !refresh && old !== MISSING && old !== null) continue;
    if (META_UNION_KEYS.includes(key)) {
      const [c, f] = [old, value].map((side) => {
        side = side === MISSING || side === null ? [] : side;
        if (!Array.isArray(side) || !side.every((s) => typeof s === "string")) merger.fail([key], "expected a list of strings");
        return side;
      });
      out[key] = [...c, ...f.filter((s) => !c.includes(s))];
    } else if (META_LATER_KEYS.includes(key) && old !== MISSING && old !== null && value !== null) {
      const later = String(value) > String(old) ? value : old;
      out[key] = merger.mergeValue(old, later, [key]);
    } else if (key === "source") {
      old = old === MISSING || old === null ? {} : old;
      if (!isMap(old) || !isMap(value)) merger.fail([key], "a mapping in one file and not in the other");
      const source = clone(old);
      for (const [skey, svalue] of Object.entries(value)) {
        if (skey === "pages") source.pages = mergePages(old.pages, svalue, merger);
        else source[skey] = merger.mergeValue(has(old, skey) ? old[skey] : MISSING, svalue, ["source", skey]);
      }
      out[key] = source;
    } else {
      out[key] = merger.mergeValue(old, value, [key]);
    }
  }
  const seen = out.changelog_seen ?? null;
  const taken = out.snapshot_date ?? null;
  if (seen !== null && taken !== null && String(seen) > String(taken)) {
    merger.fail(["changelog_seen"], `the merged changelog_seen ${seen} is later than the merged snapshot_date ${taken}`);
  }
  return out;
}

function mergeFile(fname, committed, fresh, report, itemise = true, refresh = false) {
  const merger = new Merger(fname, report, itemise, fresh);
  let merged;
  if (fname === META_FILE) {
    merged = mergeMeta(committed, fresh, merger, refresh);
  } else {
    if (!isMap(fresh) || !(committed === MISSING || isMap(committed))) {
      throw new MergeError(`${fname}: $: the top level is not a mapping`);
    }
    merged = merger.mergeMapping(committed === MISSING ? {} : committed, fresh, []);
  }
  return [merged, merger.counts];
}

// ---------------------------------------------------------------- files

function isDir(p) {
  try {
    return statSync(p).isDirectory();
  } catch {
    return false;
  }
}

function yamlFiles(dir) {
  return readdirSync(dir)
    .filter((n) => n.toLowerCase().endsWith(".yaml") && statSync(path.join(dir, n)).isFile())
    .sort();
}

function readText(p) {
  try {
    return readFileSync(p, "utf-8").replace(/^﻿/, "");
  } catch (e) {
    throw new ReadError(`ERROR: cannot read ${p}: ${String(e.message ?? e).replace(/\s*\n\s*/g, " ")}`);
  }
}

function parse(yaml, p, text, fname) {
  try {
    // CORE_SCHEMA leaves 2026-01-01 style scalars as strings, like JSON.
    return yaml.load(text, { schema: yaml.CORE_SCHEMA }) ?? null;
  } catch (e) {
    throw new MergeError(`${fname}: $: cannot parse ${p}: ${String(e.message ?? e).replace(/\s*\n\s*/g, " ")}`);
  }
}

function parseArgs(argv) {
  let source = null;
  let into = null;
  let dryRun = false;
  let refresh = false;
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--into") {
      if (i + 1 >= argv.length) return null;
      into = argv[++i];
    } else if (a.startsWith("--into=")) {
      into = a.slice("--into=".length);
    } else if (a === "--dry-run") {
      dryRun = true;
    } else if (a === "--refresh") {
      refresh = true;
    } else if (a === "-h" || a === "--help" || a.startsWith("--")) {
      return null;
    } else if (source === null) {
      source = a;
    } else {
      return null;
    }
  }
  if (source === null || !into) return null;
  return { source, into, dryRun, refresh };
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args === null) {
    console.log("usage: merge-catalog.mjs <fresh extraction dir> --into <committed catalog dir> [--dry-run] [--refresh]");
    return 3;
  }
  const { source, into, dryRun, refresh } = args;

  const yaml = tryRequire("js-yaml");
  if (yaml === null) {
    console.log(missingLine());
    return 2;
  }

  if (!isDir(source)) {
    console.log(`ERROR: no such directory: ${source}`);
    return 3;
  }
  if (existsSync(into) && !isDir(into)) {
    console.log(`ERROR: ${into} is not a directory. Pass --into DIR with the committed catalog directory.`);
    return 3;
  }
  const freshNames = yamlFiles(source);
  if (!freshNames.length) {
    console.log(`ERROR: no catalog files (*.yaml) in ${source}`);
    return 3;
  }
  const committedNames = isDir(into) ? yamlFiles(into) : [];

  const report = {
    files: {},
    files_added: [],
    files_not_in_staging: [],
    ...Object.fromEntries(SECTIONS.map((section) => [section, []])),
  };
  const writes = [];
  const errors = [];
  try {
    for (const fname of freshNames) {
      const freshPath = path.join(source, fname);
      const freshText = readText(freshPath);
      let merged, counts, changed, newline;
      try {
        const fresh = parse(yaml, freshPath, freshText, fname);
        if (committedNames.includes(fname)) {
          const intoPath = path.join(into, fname);
          const committedText = readText(intoPath);
          const committed = parse(yaml, intoPath, committedText, fname);
          [merged, counts] = mergeFile(fname, committed, fresh, report, true, refresh);
          changed = !deepEqual(merged, committed);
          newline = committedText.includes("\r\n") ? "\r\n" : "\n";
        } else {
          [merged, counts] = mergeFile(fname, MISSING, fresh, report, false, refresh);
          report.files_added.push(fname);
          changed = true;
          newline = freshText.includes("\r\n") ? "\r\n" : "\n";
        }
      } catch (e) {
        if (!(e instanceof MergeError)) throw e;
        errors.push(e.message);
        continue;
      }
      if (changed || Object.values(counts).some((n) => n)) report.files[fname] = counts;
      if (changed) writes.push([fname, merged, newline]);
    }
  } catch (e) {
    if (!(e instanceof ReadError)) throw e;
    console.log(e.message);
    return 3;
  }
  if (errors.length) {
    for (const line of errors) console.log(line);
    console.error(`${errors.length} file(s) cannot be merged; nothing written`);
    return 1;
  }
  report.files_not_in_staging = committedNames.filter((n) => !freshNames.includes(n));

  let written = false;
  if (writes.length && !dryRun) {
    try {
      mkdirSync(into, { recursive: true });
    } catch (e) {
      console.log(`ERROR: cannot create ${into}: ${e.message ?? e}. Pass --into DIR with a directory you can write to.`);
      return 3;
    }
    for (const [fname, merged, newline] of writes) {
      const p = path.join(into, fname);
      let text = yaml.dump(merged, { schema: yaml.CORE_SCHEMA, sortKeys: false, noRefs: true });
      if (newline === "\r\n") text = text.replace(/\n/g, "\r\n");
      try {
        writeFileSync(p, text, "utf-8");
      } catch (e) {
        console.log(`ERROR: cannot write ${p}: ${e.message ?? e}. Pass --into DIR with a directory you can write to.`);
        return 3;
      }
      written = true;
    }
  }

  console.log(renderReport(into, written, report));
  return 0;
}

process.exitCode = main();
