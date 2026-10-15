#!/usr/bin/env python3
"""fetch-docs.py — fetch BETER docs pages and extract plain text from <main>.

Usage:
  fetch-docs.py [--out DIR] [--base URL] [--raw] [--section TEXT]
                [--grep REGEX [--context N]] PAGE [PAGE ...]

Options may come before, between or after the pages.

PAGE is a docs path such as "feed/trading-feed/meta-data" (no leading slash,
no ".html"; the routing table in the feed-docs skill lists them). A full
docs URL or a path with a leading slash or a ".html" suffix is accepted and
reduced to the bare path. Default --base is "https://docs.beter.co/public/".
Default --out is ".beter-fetch" relative to the current directory, created if
missing.

For each page this prints one line to stdout:
  <page>\t<http status>\t<bytes written>\t<sha256 of the text>\t<output file>
A non-200 status prints only "<page>\t<http status>" and writes no file for
that page, and says why on stderr (a 404 names the routing table). The process
exits 1 if any page failed.

--raw additionally keeps the fetched HTML beside the text, as "<name>.html".

Slices. The full text is always written to the output file; these two options
also print part of it on stdout, straight after that page's status line, so a
caller can read a slice instead of a whole page. Matching is case-insensitive.

  --section TEXT   print every section whose heading (h1-h6) contains TEXT: the
                   heading line through the line before the next heading of the
                   same or a higher level, preceded by a "[lines A-B of FILE]"
                   line. Sections nested in a printed section are not repeated.
  --grep REGEX     print the lines matching REGEX as "L<n>: <line>", where n is
                   the line number in the output file, with --context N lines
                   either side as "L<n>- <line>" (default 0) and "--" between
                   groups. With --section, only inside the matched sections.
                   REGEX is kept to the syntax Python's re and JavaScript's
                   RegExp share.

A slice that matches nothing prints a note on stderr (for --section, the
headings the page does have) and makes the process exit 1.

Exit status: 0 all pages fetched (and any slice matched), 1 a page failed or a
slice matched nothing, 2 bad usage (no page, unknown or invalid option), 3 the
--out directory cannot be created or written.

Text-extraction rules (kept byte-for-byte identical between this script and
fetch-docs.mjs — change both together):

  1. Locate the first <main>...</main> element in the page. If there is none,
     fall back to <body>...</body> (and say so on stderr). If there is
     neither, use the whole document (and say so on stderr).
  2. Walk that element. Skip the contents of <script>, <style>, <noscript>
     entirely.
  3. These tags force a line break, both where they open and where they
     close (void elements br/hr only break once, where they open): p, div,
     section, article, header, footer, h1-h6, li, ul, ol, table, tr, br, hr,
     pre, blockquote, dl, dt, dd, form, fieldset, figure, figcaption, main,
     nav, aside, address, details, summary.
  4. Each <td>/<th> is preceded by " | ", so a table row collects onto one
     line as " | "-separated columns; the separator left in front of a
     row's first cell is stripped back off during cleanup.
  5. HTML entities (a fixed named-entity table plus numeric &#NN;/&#xNN;
     references) are decoded to characters as they are collected. Any other
     text is kept as-is (already UTF-8 once decoded from the response body).
  6. The collected text is split on the forced line breaks from step 3.
     Each resulting line has its leading/trailing whitespace stripped, a
     leading "| " left by step 4 removed, and any remaining run of 2+ spaces
     collapsed to one. Runs of more than one consecutive blank line are
     collapsed to a single blank line, and leading/trailing blank lines are
     dropped.
  7. The result is written as UTF-8, one line per block/row.

The position and level of every h1-h6 line is noted while walking (for
--section); it never changes the text.
"""

import argparse
import hashlib
import os
import re
import sys
import http.client
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

BLOCK_TAGS = {
    "p", "div", "section", "article", "header", "footer",
    "h1", "h2", "h3", "h4", "h5", "h6", "li", "ul", "ol",
    "table", "tr", "br", "hr", "pre", "blockquote",
    "dl", "dt", "dd", "form", "fieldset", "figure", "figcaption",
    "main", "nav", "aside", "address", "details", "summary",
}
CELL_TAGS = {"td", "th"}
SKIP_TAGS = {"script", "style", "noscript"}
HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

# Private-use marks the extractor drops in front of a heading's text and
# render_document() strips again, recording the heading level on that line.
_MARK_OPEN = ""
_MARK_CLOSE = ""
_MARK_RE = re.compile(_MARK_OPEN + r"([1-6])" + _MARK_CLOSE)

ENTITY_MAP = {
    "amp": "&", "lt": "<", "gt": ">", "quot": '"', "apos": "'",
    "nbsp": " ", "mdash": "—", "ndash": "–", "hellip": "…",
    "lsquo": "‘", "rsquo": "’", "ldquo": "“", "rdquo": "”",
    "copy": "©", "reg": "®", "trade": "™",
}

_WS_RE = re.compile(r"[ \t\r\n\f]+")
_MULTI_SPACE_RE = re.compile(r" {2,}")
_MAIN_RE = re.compile(r"<main[\s>]", re.IGNORECASE)
_BODY_RE = re.compile(r"<body[\s>]", re.IGNORECASE)


def decode_charref(number):
    number = number.strip()
    try:
        if number[:1] in ("x", "X"):
            code = int(number[1:], 16)
        else:
            code = int(number, 10)
        return chr(code)
    except (ValueError, OverflowError):
        return ""


class Extractor(HTMLParser):
    """Extracts text from the first <main> (or <body>, or whole document)."""

    def __init__(self, target):
        super().__init__(convert_charrefs=False)
        self.target = target  # "main", "body", or None
        self.in_target = target is None
        self.target_depth = 0
        self.skip_depth = 0
        self.done = False
        self.parts = []

    def _emit(self, text):
        if not self.in_target or self.done or self.skip_depth:
            return
        collapsed = _WS_RE.sub(" ", text)
        if collapsed:
            self.parts.append(collapsed)

    def _start_common(self, tag):
        if not self.in_target or self.done:
            return
        if tag in SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag in CELL_TAGS:
            self.parts.append(" | ")
        if tag in BLOCK_TAGS:
            self.parts.append("\n")
        if tag in HEADING_TAGS:
            self.parts.append(_MARK_OPEN + tag[1] + _MARK_CLOSE)

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if self.target is not None and not self.in_target:
            if tag == self.target:
                self.in_target = True
                self.target_depth = 1
            return
        if self.target is not None and self.in_target and tag == self.target:
            self.target_depth += 1
        self._start_common(tag)

    def handle_startendtag(self, tag, attrs):
        tag = tag.lower()
        if self.target is not None and not self.in_target:
            return
        self._start_common(tag)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if self.target is not None and not self.in_target:
            return
        if self.done:
            return
        if tag in SKIP_TAGS:
            if self.skip_depth:
                self.skip_depth -= 1
        elif not self.skip_depth and tag in BLOCK_TAGS:
            self.parts.append("\n")
        if self.target is not None and tag == self.target:
            self.target_depth -= 1
            if self.target_depth <= 0:
                self.done = True
                self.in_target = False

    def handle_data(self, data):
        self._emit(data)

    def handle_entityref(self, name):
        self._emit(ENTITY_MAP.get(name, "&" + name + ";"))

    def handle_charref(self, name):
        self._emit(decode_charref(name))

    def get_text(self):
        return "".join(self.parts)


def render_document(raw_text):
    """Clean the collected text; returns (text, headings).

    headings is a list of (zero-based line index in text, level 1-6, heading
    text) in document order.
    """
    lines = raw_text.split("\n")
    cleaned = []
    levels = []
    blank_run = 0
    for raw_line in lines:
        level = 0
        found = _MARK_RE.search(raw_line)
        if found:
            level = int(found.group(1))
            raw_line = _MARK_RE.sub("", raw_line)
        line = raw_line.strip()
        if line.startswith("| "):
            line = line[2:]
        elif line == "|":
            line = ""
        line = _MULTI_SPACE_RE.sub(" ", line)
        if line == "":
            blank_run += 1
            if blank_run > 1:
                continue
        else:
            blank_run = 0
        cleaned.append(line)
        levels.append(level if line else 0)
    while cleaned and cleaned[0] == "":
        cleaned.pop(0)
        levels.pop(0)
    while cleaned and cleaned[-1] == "":
        cleaned.pop()
        levels.pop()
    headings = [(i, lv, cleaned[i]) for i, lv in enumerate(levels) if lv]
    return "\n".join(cleaned) + ("\n" if cleaned else ""), headings


def extract_text(html_text, page):
    if _MAIN_RE.search(html_text):
        target = "main"
    elif _BODY_RE.search(html_text):
        target = "body"
        print(f"no <main> element on {page}; falling back to <body>", file=sys.stderr)
    else:
        target = None
        print(f"no <main> or <body> element on {page}; using the whole document", file=sys.stderr)
    extractor = Extractor(target)
    extractor.feed(html_text)
    extractor.close()
    return render_document(extractor.get_text())


def normalize_page(page):
    """Reduce a page argument to the bare docs path."""
    path = page.strip()
    # Git Bash rewrites an argument with a leading slash into a path under the
    # Git install directory (the drive, the install path, "Git", then "feed/x").
    path = re.sub(r"^[A-Za-z]:[\\/](?:[^\\/]+[\\/])*?Git[\\/]", "", path)
    path = re.sub(r"^[a-zA-Z][a-zA-Z0-9+.-]*://[^/]+/?", "", path)
    path = re.split(r"[?#]", path, maxsplit=1)[0].strip("/")
    if path.startswith("public/"):
        path = path[len("public/"):]
    if path.endswith(".html"):
        path = path[: -len(".html")]
    return path


def fetch(url):
    """Returns (status, body, reason); status 0 means no HTTP response."""
    req = urllib.request.Request(url, headers={"User-Agent": "beter-feed-skills-fetch/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read(), ""
    except urllib.error.HTTPError as e:
        return e.code, b"", e.reason if isinstance(e.reason, str) else ""
    except (urllib.error.URLError, http.client.HTTPException, OSError, ValueError) as e:
        reason = getattr(e, "reason", None) or e
        return 0, b"", str(reason)


def explain_failure(page, url, status, reason):
    if status == 0:
        return (f"{page}: no HTTP response from {url} ({reason or 'unknown error'}). "
                "The helper needs outbound HTTPS to docs.beter.co.")
    if status == 404:
        return (f"{page}: HTTP 404 from {url}. Page paths come from the routing table "
                "in the feed-docs skill (SKILL.md, and references/doc-map.md for the "
                "complete list): bare paths such as feed/trading-feed/meta-data, no host, "
                "no leading slash, no .html, no .md or .txt suffix.")
    return f"{page}: HTTP {status} from {url}."


def choose_sections(lines, headings, needle):
    """Line ranges (start, end) of the sections whose heading contains needle."""
    needle = needle.lower()
    ranges = []
    for k, (index, level, text) in enumerate(headings):
        if needle not in text.lower():
            continue
        if ranges and index < ranges[-1][1]:
            continue  # nested in a section already chosen
        end = len(lines)
        for later_index, later_level, _ in headings[k + 1:]:
            if later_level <= level:
                end = later_index
                break
        while end > index + 1 and lines[end - 1] == "":
            end -= 1
        ranges.append((index, end))
    return ranges


def emit_slice(page, text, headings, out_path, section, pattern, context):
    """Print the requested slice of a page; returns False when nothing matched."""
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    domain = [(0, len(lines))]
    if section is not None:
        domain = choose_sections(lines, headings, section)
        if not domain:
            shown = "; ".join(f"h{lv} {t}" for _, lv, t in headings[:40])
            more = f" (+{len(headings) - 40} more)" if len(headings) > 40 else ""
            print(f'{page}: no heading containing "{section}". Headings: '
                  f'{shown or "none"}{more}', file=sys.stderr)
            return False
    if pattern is None:
        for n, (start, end) in enumerate(domain):
            if n:
                print()
            print(f"[lines {start + 1}-{end} of {out_path}]")
            print("\n".join(lines[start:end]))
        return True

    matched = False
    first_group = True
    for start, end in domain:
        hits = {i for i in range(start, end) if pattern.search(lines[i])}
        if not hits:
            continue
        matched = True
        shown = set()
        for i in hits:
            shown.update(range(max(start, i - context), min(end, i + context + 1)))
        previous = None
        for i in sorted(shown):
            if previous is not None and i != previous + 1:
                print("--")
            elif previous is None and not first_group:
                print("--")
            print(f"L{i + 1}{':' if i in hits else '-'} {lines[i]}")
            previous = i
        first_group = False
    if not matched:
        print(f"{page}: no line matches {pattern.pattern!r}"
              f"{' inside the chosen sections' if section is not None else ''}",
              file=sys.stderr)
    return matched


def main():
    # A Windows console codepage (cp1251, cp1252, ...) cannot encode every
    # character a page name or a slice may carry; never die printing.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(
        prog="fetch-docs.py",
        description="Fetch BETER docs pages and extract the text of <main> as plain text.",
    )
    parser.add_argument("pages", metavar="PAGE", nargs="+",
                         help='docs path, e.g. "feed/trading-feed/meta-data"')
    parser.add_argument("--section", metavar="TEXT", default=None,
                         help="also print the sections whose heading contains TEXT")
    parser.add_argument("--grep", metavar="REGEX", default=None,
                         help="also print the lines matching REGEX, with line numbers")
    parser.add_argument("--context", metavar="N", type=int, default=0,
                         help="lines of context around each --grep match (default 0)")
    parser.add_argument("--out", default=".beter-fetch",
                         help="output directory (default: .beter-fetch)")
    parser.add_argument("--base", default="https://docs.beter.co/public/",
                         help="base URL (default: https://docs.beter.co/public/)")
    parser.add_argument("--raw", action="store_true",
                         help="also keep the fetched HTML beside the text, as <name>.html")
    # parse_intermixed_args: options may follow or sit between the pages.
    args = parser.parse_intermixed_args()

    pattern = None
    if args.context < 0:
        parser.error("--context must be 0 or more")
    if args.context and args.grep is None:
        parser.error("--context needs --grep")
    if args.grep is not None:
        try:
            pattern = re.compile(args.grep, re.IGNORECASE)
        except re.error as e:
            parser.error(f"--grep is not a valid regular expression: {e}")

    base = args.base if args.base.endswith("/") else args.base + "/"
    try:
        os.makedirs(args.out, exist_ok=True)
    except OSError as e:
        print(f"cannot create output directory {args.out!r}: {e.strerror or e}. "
              "Pass --out DIR with a directory you can write to.", file=sys.stderr)
        sys.exit(3)

    failed = False
    for page in args.pages:
        page_path = normalize_page(page)
        url = base + urllib.parse.quote(page_path, safe="/%-._~")
        status, raw, reason = fetch(url)
        if status != 200:
            print(f"{page}\t{status}")
            print(explain_failure(page, url, status, reason), file=sys.stderr)
            failed = True
            continue

        html_text = raw.decode("utf-8", errors="replace")
        text, headings = extract_text(html_text, page)
        out_bytes = text.encode("utf-8")

        filename = page_path.replace("/", "__") + ".txt"
        out_path = os.path.join(args.out, filename)
        try:
            with open(out_path, "wb") as f:
                f.write(out_bytes)

            if args.raw:
                raw_path = os.path.join(args.out, page_path.replace("/", "__") + ".html")
                with open(raw_path, "wb") as f:
                    f.write(raw)
        except OSError as e:
            print(f"{page}\tcannot write {args.out!r}: {e.strerror or e}. "
                  "Pass --out DIR with a directory you can write to.", file=sys.stderr)
            sys.exit(3)

        digest = hashlib.sha256(out_bytes).hexdigest()
        print(f"{page}\t{status}\t{len(out_bytes)}\t{digest}\t{out_path}")

        if args.section is not None or pattern is not None:
            if not emit_slice(page, text, headings, out_path, args.section, pattern, args.context):
                failed = True

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
