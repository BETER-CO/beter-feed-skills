#!/usr/bin/env node
// fetch-docs.mjs — fetch BETER docs pages and extract plain text from <main>.
//
// Usage:
//   node fetch-docs.mjs [--out DIR] [--base URL] [--raw] [--section TEXT]
//                       [--grep REGEX [--context N]] PAGE [PAGE ...]
//
// Options may come before, between or after the pages.
//
// PAGE is a docs path such as "feed/trading-feed/meta-data" (no leading
// slash, no ".html"; the routing table in the feed-docs skill lists
// them). A full docs URL or a path with a leading slash or a ".html" suffix
// is accepted and reduced to the bare path. Default --base is
// "https://docs.beter.co/public/". Default --out is ".beter-fetch" relative
// to the current directory, created if missing.
//
// For each page this prints one line to stdout:
//   <page>\t<http status>\t<bytes written>\t<sha256 of the text>\t<output file>
// A non-200 status prints only "<page>\t<http status>" and writes no file
// for that page, and says why on stderr (a 404 names the routing table). The
// process exits 1 if any page failed.
//
// --raw additionally keeps the fetched HTML beside the text, as "<name>.html".
//
// Slices. The full text is always written to the output file; these two
// options also print part of it on stdout, straight after that page's status
// line, so a caller can read a slice instead of a whole page. Matching is
// case-insensitive.
//
//   --section TEXT   print every section whose heading (h1-h6) contains TEXT:
//                    the heading line through the line before the next heading
//                    of the same or a higher level, preceded by a
//                    "[lines A-B of FILE]" line. Sections nested in a printed
//                    section are not repeated.
//   --grep REGEX     print the lines matching REGEX as "L<n>: <line>", where n
//                    is the line number in the output file, with --context N
//                    lines either side as "L<n>- <line>" (default 0) and "--"
//                    between groups. With --section, only inside the matched
//                    sections. REGEX is kept to the syntax Python's re and
//                    JavaScript's RegExp share.
//
// A slice that matches nothing prints a note on stderr (for --section, the
// headings the page does have) and makes the process exit 1.
//
// Exit status: 0 all pages fetched (and any slice matched), 1 a page failed
// or a slice matched nothing, 2 bad usage (no page, unknown or invalid
// option), 3 the --out directory cannot be created or written.
//
// Text-extraction rules (kept byte-for-byte identical between this script
// and fetch-docs.py — change both together):
//
//   1. Locate the first <main>...</main> element in the page. If there is
//      none, fall back to <body>...</body> (and say so on stderr). If there
//      is neither, use the whole document (and say so on stderr).
//   2. Walk that element. Skip the contents of <script>, <style>,
//      <noscript> entirely.
//   3. These tags force a line break, both where they open and where they
//      close (void elements br/hr only break once, where they open): p,
//      div, section, article, header, footer, h1-h6, li, ul, ol, table, tr,
//      br, hr, pre, blockquote, dl, dt, dd, form, fieldset, figure,
//      figcaption, main, nav, aside, address, details, summary.
//   4. Each <td>/<th> is preceded by " | ", so a table row collects onto
//      one line as " | "-separated columns; the separator left in front of
//      a row's first cell is stripped back off during cleanup.
//   5. HTML entities (a fixed named-entity table plus numeric &#NN;/&#xNN;
//      references) are decoded to characters as they are collected. Any
//      other text is kept as-is (already UTF-8 once decoded from the
//      response body).
//   6. The collected text is split on the forced line breaks from step 3.
//      Each resulting line has its leading/trailing whitespace stripped, a
//      leading "| " left by step 4 removed, and any remaining run of 2+
//      spaces collapsed to one. Runs of more than one consecutive blank
//      line are collapsed to a single blank line, and leading/trailing
//      blank lines are dropped.
//   7. The result is written as UTF-8, one line per block/row.
//
// The position and level of every h1-h6 line is noted while walking (for
// --section); it never changes the text.

import { writeFile, mkdir } from "node:fs/promises";
import { createHash } from "node:crypto";
import path from "node:path";

const BLOCK_TAGS = new Set([
  "p", "div", "section", "article", "header", "footer",
  "h1", "h2", "h3", "h4", "h5", "h6", "li", "ul", "ol",
  "table", "tr", "br", "hr", "pre", "blockquote",
  "dl", "dt", "dd", "form", "fieldset", "figure", "figcaption",
  "main", "nav", "aside", "address", "details", "summary",
]);
const CELL_TAGS = new Set(["td", "th"]);
const SKIP_TAGS = new Set(["script", "style", "noscript"]);
const HEADING_TAGS = new Set(["h1", "h2", "h3", "h4", "h5", "h6"]);

// Private-use marks the extractor drops in front of a heading's text and
// renderDocument() strips again, recording the heading level on that line.
const MARK_OPEN = "";
const MARK_CLOSE = "";
const MARK_RE = new RegExp(MARK_OPEN + "([1-6])" + MARK_CLOSE);
const MARK_ALL_RE = new RegExp(MARK_OPEN + "[1-6]" + MARK_CLOSE, "g");

const ENTITY_MAP = {
  amp: "&", lt: "<", gt: ">", quot: '"', apos: "'",
  nbsp: " ", mdash: "—", ndash: "–", hellip: "…",
  lsquo: "‘", rsquo: "’", ldquo: "“", rdquo: "”",
  copy: "©", reg: "®", trade: "™",
};

const WS_RE = /[ \t\r\n\f]+/g;
const MULTI_SPACE_RE = / {2,}/g;
const MAIN_RE = /<main[\s>]/i;
const BODY_RE = /<body[\s>]/i;
const ENTITY_RE = /&(#x[0-9a-fA-F]+|#[0-9]+|[a-zA-Z][a-zA-Z0-9]*);/g;
// Comments/doctype (skipped whole), end tags, and start tags (attrs ignored,
// trailing group catches a self-closing "/").
const TAG_RE = /<!--[\s\S]*?-->|<!DOCTYPE[^>]*>|<\/([a-zA-Z][a-zA-Z0-9:-]*)\s*>|<([a-zA-Z][a-zA-Z0-9:-]*)((?:\s+(?:"[^"]*"|'[^']*'|[^<>])*)?)(\/?)>/g;

function decodeEntities(text) {
  return text.replace(ENTITY_RE, (whole, body) => {
    if (body[0] === "#") {
      const isHex = body[1] === "x" || body[1] === "X";
      const num = isHex ? body.slice(2) : body.slice(1);
      const code = parseInt(num, isHex ? 16 : 10);
      if (Number.isNaN(code)) return "";
      try {
        return String.fromCodePoint(code);
      } catch {
        return "";
      }
    }
    return Object.prototype.hasOwnProperty.call(ENTITY_MAP, body) ? ENTITY_MAP[body] : whole;
  });
}

class Extractor {
  constructor(target) {
    this.target = target; // "main" | "body" | null
    this.inTarget = target === null;
    this.targetDepth = 0;
    this.skipDepth = 0;
    this.done = false;
    this.parts = [];
  }

  _startCommon(tag) {
    if (!this.inTarget || this.done) return;
    if (SKIP_TAGS.has(tag)) {
      this.skipDepth += 1;
      return;
    }
    if (this.skipDepth) return;
    if (CELL_TAGS.has(tag)) this.parts.push(" | ");
    if (BLOCK_TAGS.has(tag)) this.parts.push("\n");
    if (HEADING_TAGS.has(tag)) this.parts.push(MARK_OPEN + tag[1] + MARK_CLOSE);
  }

  handleStartTag(tag) {
    if (this.target !== null && !this.inTarget) {
      if (tag === this.target) {
        this.inTarget = true;
        this.targetDepth = 1;
      }
      return;
    }
    if (this.target !== null && this.inTarget && tag === this.target) {
      this.targetDepth += 1;
    }
    this._startCommon(tag);
  }

  handleStartEndTag(tag) {
    if (this.target !== null && !this.inTarget) return;
    this._startCommon(tag);
  }

  handleEndTag(tag) {
    if (this.target !== null && !this.inTarget) return;
    if (this.done) return;
    if (SKIP_TAGS.has(tag)) {
      if (this.skipDepth) this.skipDepth -= 1;
    } else if (!this.skipDepth && BLOCK_TAGS.has(tag)) {
      this.parts.push("\n");
    }
    if (this.target !== null && tag === this.target) {
      this.targetDepth -= 1;
      if (this.targetDepth <= 0) {
        this.done = true;
        this.inTarget = false;
      }
    }
  }

  handleData(raw) {
    if (!this.inTarget || this.done || this.skipDepth) return;
    const decoded = decodeEntities(raw);
    const collapsed = decoded.replace(WS_RE, " ");
    if (collapsed) this.parts.push(collapsed);
  }

  getText() {
    return this.parts.join("");
  }
}

// Cleans the collected text; returns { text, headings } where headings is a
// list of { index (zero-based line in text), level (1-6), text } in order.
function renderDocument(rawText) {
  const lines = rawText.split("\n");
  const cleaned = [];
  const levels = [];
  let blankRun = 0;
  for (const originalLine of lines) {
    let rawLine = originalLine;
    let level = 0;
    const found = MARK_RE.exec(rawLine);
    if (found) {
      level = Number(found[1]);
      rawLine = rawLine.replace(MARK_ALL_RE, "");
    }
    let line = rawLine.trim();
    if (line.startsWith("| ")) {
      line = line.slice(2);
    } else if (line === "|") {
      line = "";
    }
    line = line.replace(MULTI_SPACE_RE, " ");
    if (line === "") {
      blankRun += 1;
      if (blankRun > 1) continue;
    } else {
      blankRun = 0;
    }
    cleaned.push(line);
    levels.push(line ? level : 0);
  }
  while (cleaned.length && cleaned[0] === "") {
    cleaned.shift();
    levels.shift();
  }
  while (cleaned.length && cleaned[cleaned.length - 1] === "") {
    cleaned.pop();
    levels.pop();
  }
  const headings = [];
  levels.forEach((level, index) => {
    if (level) headings.push({ index, level, text: cleaned[index] });
  });
  return { text: cleaned.join("\n") + (cleaned.length ? "\n" : ""), headings };
}

function extractText(htmlText, page) {
  let target;
  if (MAIN_RE.test(htmlText)) {
    target = "main";
  } else if (BODY_RE.test(htmlText)) {
    target = "body";
    process.stderr.write(`no <main> element on ${page}; falling back to <body>\n`);
  } else {
    target = null;
    process.stderr.write(`no <main> or <body> element on ${page}; using the whole document\n`);
  }

  const extractor = new Extractor(target);
  TAG_RE.lastIndex = 0;
  let lastIndex = 0;
  let m;
  while ((m = TAG_RE.exec(htmlText)) !== null) {
    if (m.index > lastIndex) {
      extractor.handleData(htmlText.slice(lastIndex, m.index));
    }
    lastIndex = TAG_RE.lastIndex;
    const endTag = m[1];
    const startTag = m[2];
    const selfClose = m[4] === "/";
    if (endTag) {
      extractor.handleEndTag(endTag.toLowerCase());
    } else if (startTag) {
      const tag = startTag.toLowerCase();
      if (selfClose) {
        extractor.handleStartEndTag(tag);
      } else {
        extractor.handleStartTag(tag);
      }
    }
    // else: a comment or doctype — skipped entirely.
  }
  if (lastIndex < htmlText.length) {
    extractor.handleData(htmlText.slice(lastIndex));
  }

  return renderDocument(extractor.getText());
}

// Reduces a page argument to the bare docs path.
function normalizePage(page) {
  let p = page.trim();
  // Git Bash rewrites an argument with a leading slash into a path under the
  // Git install directory (the drive, the install path, "Git", then "feed/x").
  p = p.replace(/^[A-Za-z]:[\\/](?:[^\\/]+[\\/])*?Git[\\/]/, "");
  p = p.replace(/^[a-zA-Z][a-zA-Z0-9+.-]*:\/\/[^/]+\/?/, "");
  p = p.split(/[?#]/, 1)[0].replace(/^\/+|\/+$/g, "");
  if (p.startsWith("public/")) p = p.slice("public/".length);
  if (p.endsWith(".html")) p = p.slice(0, -".html".length);
  return p;
}

// status 0 means no HTTP response; reason then says why.
async function fetchPage(url) {
  try {
    const res = await fetch(url, {
      headers: { "User-Agent": "beter-feed-skills-fetch/1.0" },
      redirect: "follow",
      signal: AbortSignal.timeout(30000),
    });
    const buf = Buffer.from(await res.arrayBuffer());
    return { status: res.status, raw: buf, reason: "" };
  } catch (e) {
    const cause = e && e.cause ? e.cause.code || e.cause.message : "";
    return { status: 0, raw: Buffer.alloc(0), reason: String(cause || (e && e.message) || e) };
  }
}

function explainFailure(page, url, status, reason) {
  if (status === 0) {
    return (
      `${page}: no HTTP response from ${url} (${reason || "unknown error"}). ` +
      "The helper needs outbound HTTPS to docs.beter.co."
    );
  }
  if (status === 404) {
    return (
      `${page}: HTTP 404 from ${url}. Page paths come from the routing table ` +
      "in the feed-docs skill (SKILL.md, and references/doc-map.md for the " +
      "complete list): bare paths such as feed/trading-feed/meta-data, no host, " +
      "no leading slash, no .html, no .md or .txt suffix."
    );
  }
  return `${page}: HTTP ${status} from ${url}.`;
}

// Line ranges [start, end) of the sections whose heading contains needle.
function chooseSections(lines, headings, needle) {
  const lowered = needle.toLowerCase();
  const ranges = [];
  headings.forEach((h, k) => {
    if (!h.text.toLowerCase().includes(lowered)) return;
    if (ranges.length && h.index < ranges[ranges.length - 1][1]) return; // nested
    let end = lines.length;
    for (const later of headings.slice(k + 1)) {
      if (later.level <= h.level) {
        end = later.index;
        break;
      }
    }
    while (end > h.index + 1 && lines[end - 1] === "") end -= 1;
    ranges.push([h.index, end]);
  });
  return ranges;
}

// Prints the requested slice of a page; returns false when nothing matched.
function emitSlice(page, text, headings, outPath, section, pattern, context) {
  const out = [];
  const lines = text.split("\n");
  if (lines.length && lines[lines.length - 1] === "") lines.pop();
  let domain = [[0, lines.length]];
  if (section !== null) {
    domain = chooseSections(lines, headings, section);
    if (domain.length === 0) {
      const shown = headings.slice(0, 40).map((h) => `h${h.level} ${h.text}`).join("; ");
      const more = headings.length > 40 ? ` (+${headings.length - 40} more)` : "";
      process.stderr.write(
        `${page}: no heading containing "${section}". Headings: ${shown || "none"}${more}\n`
      );
      return false;
    }
  }
  if (pattern === null) {
    domain.forEach(([start, end], n) => {
      if (n) out.push("");
      out.push(`[lines ${start + 1}-${end} of ${outPath}]`);
      out.push(lines.slice(start, end).join("\n"));
    });
    process.stdout.write(out.join("\n") + "\n");
    return true;
  }

  let matched = false;
  let firstGroup = true;
  for (const [start, end] of domain) {
    const hits = new Set();
    for (let i = start; i < end; i++) if (pattern.test(lines[i])) hits.add(i);
    if (hits.size === 0) continue;
    matched = true;
    const shown = new Set();
    for (const i of hits) {
      for (let j = Math.max(start, i - context); j < Math.min(end, i + context + 1); j++) shown.add(j);
    }
    let previous = null;
    for (const i of [...shown].sort((a, b) => a - b)) {
      if (previous !== null && i !== previous + 1) out.push("--");
      else if (previous === null && !firstGroup) out.push("--");
      out.push(`L${i + 1}${hits.has(i) ? ":" : "-"} ${lines[i]}`);
      previous = i;
    }
    firstGroup = false;
  }
  if (out.length) process.stdout.write(out.join("\n") + "\n");
  if (!matched) {
    process.stderr.write(
      `${page}: no line matches ${JSON.stringify(pattern.source)}` +
        `${section !== null ? " inside the chosen sections" : ""}\n`
    );
  }
  return matched;
}

const USAGE =
  "usage: fetch-docs.mjs [--out DIR] [--base URL] [--raw] [--section TEXT] " +
  "[--grep REGEX [--context N]] PAGE [PAGE ...]\n";

function parseArgs(argv) {
  const args = {
    out: ".beter-fetch",
    base: "https://docs.beter.co/public/",
    raw: false,
    section: null,
    grep: null,
    context: null,
    pages: [],
    error: null,
  };
  const valued = ["out", "base", "section", "grep", "context"];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--raw") {
      args.raw = true;
    } else if (a === "-h" || a === "--help") {
      args.help = true;
    } else if (a.startsWith("--")) {
      const eq = a.indexOf("=");
      const name = eq === -1 ? a.slice(2) : a.slice(2, eq);
      if (!valued.includes(name)) {
        args.error = `unknown option ${a}`;
        continue;
      }
      let value;
      if (eq !== -1) {
        value = a.slice(eq + 1);
      } else if (i + 1 < argv.length) {
        value = argv[++i];
      } else {
        args.error = `${a} needs a value`;
        continue;
      }
      args[name] = value;
    } else {
      args.pages.push(a);
    }
  }
  return args;
}

function fail(message, code) {
  process.stderr.write(message + "\n");
  process.exitCode = code;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));

  if (args.help) {
    process.stdout.write(USAGE);
    return;
  }
  if (args.error !== null || args.pages.length === 0) {
    process.stderr.write(USAGE);
    fail(args.error !== null ? `fetch-docs.mjs: error: ${args.error}` : "fetch-docs.mjs: error: no PAGE given", 2);
    return;
  }

  let context = 0;
  if (args.context !== null) {
    context = /^\d+$/.test(args.context) ? Number(args.context) : NaN;
    if (Number.isNaN(context)) return fail("fetch-docs.mjs: error: --context must be 0 or more", 2);
    if (args.grep === null) return fail("fetch-docs.mjs: error: --context needs --grep", 2);
  }
  let pattern = null;
  if (args.grep !== null) {
    try {
      pattern = new RegExp(args.grep, "i");
    } catch (e) {
      return fail(`fetch-docs.mjs: error: --grep is not a valid regular expression: ${e.message}`, 2);
    }
  }

  const base = args.base.endsWith("/") ? args.base : args.base + "/";
  try {
    await mkdir(args.out, { recursive: true });
  } catch (e) {
    return fail(
      `cannot create output directory '${args.out}': ${e.code || e.message}. ` +
        "Pass --out DIR with a directory you can write to.",
      3
    );
  }

  let failed = false;
  for (const page of args.pages) {
    const pagePath = normalizePage(page);
    const url = base + pagePath;
    const { status, raw, reason } = await fetchPage(url);

    if (status !== 200) {
      process.stdout.write(`${page}\t${status}\n`);
      process.stderr.write(explainFailure(page, url, status, reason) + "\n");
      failed = true;
      continue;
    }

    const htmlText = raw.toString("utf-8");
    const { text, headings } = extractText(htmlText, page);
    const outBytes = Buffer.from(text, "utf-8");

    const filename = pagePath.replace(/\//g, "__") + ".txt";
    const outPath = path.join(args.out, filename);
    try {
      await writeFile(outPath, outBytes);
      if (args.raw) {
        const rawPath = path.join(args.out, pagePath.replace(/\//g, "__") + ".html");
        await writeFile(rawPath, raw);
      }
    } catch (e) {
      return fail(
        `${page}\tcannot write '${args.out}': ${e.code || e.message}. ` +
          "Pass --out DIR with a directory you can write to.",
        3
      );
    }

    const digest = createHash("sha256").update(outBytes).digest("hex");
    process.stdout.write(`${page}\t${status}\t${outBytes.length}\t${digest}\t${outPath}\n`);

    if (args.section !== null || pattern !== null) {
      if (!emitSlice(page, text, headings, outPath, args.section, pattern, context)) failed = true;
    }
  }

  process.exitCode = failed ? 1 : 0;
}

main();
