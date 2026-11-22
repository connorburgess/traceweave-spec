#!/usr/bin/env node
// Cross-check the draft ts-tokens / tsx-tokens vectors against the TypeScript
// 6.0.3 parser and scanner (project-local node_modules, pinned by package-lock.json).
//
//   cd research/drafts/extraction-vectors-typescript/harness
//   npm ci --ignore-scripts      # once; installs typescript@6.0.3 locally
//   node crosscheck.js [--json OUT]
//
// The oracle is TypeScript's parser (createSourceFile), not the bare scanner:
// regex/division, template continuation and JSX all need the parser's context.
// Leaf tokens of the syntax tree are compared with the vector tokens by coarse
// class and byte span. Declared adjustments (each counted in the output):
//   gt-merge     TS keeps '>' '>' separate where the profile has one '>>'
//                (type-argument closers); accepted when the TS tokens are
//                contiguous and cover exactly the profile token.
//   jsx-trim     TS JsxText includes surrounding white space; it is trimmed
//                with the profile's trivia set before comparison, and
//                white-space-only JsxText is dropped.
//   word         keyword vs ident is the profile's textual rule (§4.1); TS has
//                keyword kinds for contextual words, so both compare as 'word'.
// Inputs TS reports parse diagnostics for are compared against the raw scanner
// instead (no regex/template/JSX rescans) and are listed separately.
"use strict";
const fs = require("fs");
const path = require("path");
const ts = require(path.join(__dirname, "node_modules", "typescript"));

const DIR = path.join(__dirname, "..");
const FILES = [["ts.json", ts.ScriptKind.TS, "x.ts"], ["tsx.json", ts.ScriptKind.TSX, "x.tsx"],
  ["limits-ts.json", ts.ScriptKind.TS, "x.ts"]];
const PRE_LEX = new Set(["input-too-large", "invalid-utf8", "bom", "nul"]);

// ---------------------------------------------------------------- profile Unicode data
const TABLES = JSON.parse(fs.readFileSync(path.join(DIR, "..", "extraction-vectors", "unicode-17.0.0-tables.json")));
const ID_START_EXTRA = new Set([0x037A, 0x0E33, 0x0EB3, 0x309B, 0x309C, 0xFC5E, 0xFC5F, 0xFC60, 0xFC61, 0xFC62,
  0xFC63, 0xFDFA, 0xFDFB, 0xFE70, 0xFE72, 0xFE74, 0xFE76, 0xFE78, 0xFE7A, 0xFE7C, 0xFE7E, 0xFF9E, 0xFF9F]);
const ID_CONTINUE_EXTRA = new Set([0x037A, 0x309B, 0x309C, 0xFC5E, 0xFC5F, 0xFC60, 0xFC61, 0xFC62, 0xFC63, 0xFDFA,
  0xFDFB, 0xFE70, 0xFE72, 0xFE74, 0xFE76, 0xFE78, 0xFE7A, 0xFE7C, 0xFE7E]);
function inRanges(r, cp) {
  let lo = 0, hi = r.length - 1;
  while (lo <= hi) {
    const m = (lo + hi) >> 1;
    if (cp < r[m][0]) hi = m - 1; else if (cp > r[m][1]) lo = m + 1; else return true;
  }
  return false;
}
const idStart = cp => cp === 0x24 || cp === 0x5F || inRanges(TABLES.properties.xid_start, cp) || ID_START_EXTRA.has(cp);
const idPart = cp => cp === 0x24 || cp === 0x200C || cp === 0x200D || inRanges(TABLES.properties.xid_continue, cp)
  || ID_CONTINUE_EXTRA.has(cp);
const ZS = new Set([0x20, 0xA0, 0x1680, 0x2000, 0x2001, 0x2002, 0x2003, 0x2004, 0x2005, 0x2006, 0x2007, 0x2008, 0x2009,
  0x200A, 0x202F, 0x205F, 0x3000]);
const isWs = cp => cp === 9 || cp === 0xB || cp === 0xC || cp === 0xFEFF || ZS.has(cp);
const isLt = cp => cp === 0xA || cp === 0xD || cp === 0x2028 || cp === 0x2029;
const TRIVIA = s => { const cp = s.codePointAt(0); return isWs(cp) || isLt(cp); };

// ---------------------------------------------------------------- helpers
function byteMap(text) { // UTF-16 index -> UTF-8 byte offset
  const m = new Array(text.length + 1);
  let b = 0;
  for (let i = 0; i < text.length; i++) {
    m[i] = b;
    const c = text.charCodeAt(i);
    if (c < 0x80) b += 1; else if (c < 0x800) b += 2;
    else if (c >= 0xD800 && c <= 0xDBFF) { m[i + 1] = b; b += 4; i++; } else b += 3;
  }
  m[text.length] = b;
  return m;
}
const K = ts.SyntaxKind;
function coarse(kind, parent) {
  if (kind === K.Identifier || (kind >= K.FirstKeyword && kind <= K.LastKeyword)) return "word";
  if (kind === K.PrivateIdentifier) return "privatename";
  if (kind === K.NumericLiteral) return "number";
  if (kind === K.BigIntLiteral) return "bigint";
  if (kind === K.StringLiteral) return parent && parent.kind === K.JsxAttribute ? "jsx-string" : "string";
  if (kind === K.NoSubstitutionTemplateLiteral) return "template";
  if (kind === K.TemplateHead) return "template-head";
  if (kind === K.TemplateMiddle) return "template-middle";
  if (kind === K.TemplateTail) return "template-tail";
  if (kind === K.RegularExpressionLiteral) return "regex";
  if (kind === K.JsxText || kind === K.JsxTextAllWhiteSpaces) return "jsx-text";
  if (kind >= K.FirstPunctuation && kind <= K.LastPunctuation) return "punct";
  return "other:" + K[kind];
}
const ours = c => (c === "keyword" || c === "ident") ? "word" : c;

function parserTokens(sf, text) {
  const out = [];
  (function walk(node, parent) {
    if (node.kind >= K.FirstJSDocNode && node.kind <= K.LastJSDocNode) return;
    const kids = node.getChildren(sf);
    if (kids.length === 0 && node.kind !== K.SyntaxList) {
      if (node.kind === K.EndOfFileToken || node.kind === K.OmittedExpression) return; // zero-width nodes
      let a = node.getStart(sf), b = node.getEnd();
      if (node.kind === K.JsxText || node.kind === K.JsxTextAllWhiteSpaces) {
        a = node.pos;
        while (a < b && TRIVIA(text[a])) a++;
        while (b > a && TRIVIA(text[b - 1])) b--;
        if (a === b) return;
      }
      out.push([coarse(node.kind, parent), a, b]);
      return;
    }
    for (const k of kids) walk(k, node.kind === K.SyntaxList ? parent : node);
  })(sf, null);
  return out;
}

function scannerTokens(text, variant) {
  const out = [];
  const s = ts.createScanner(ts.ScriptTarget.Latest, true, variant, text);
  for (;;) {
    const k = s.scan();
    if (k === K.EndOfFileToken) break;
    out.push([coarse(k, null), s.getTokenStart(), s.getTokenEnd()]);
  }
  return out;
}

function compare(mine, theirs, adj) {
  let i = 0, j = 0;
  while (i < mine.length && j < theirs.length) {
    const [c, a, b] = mine[i], [tc, ta, tb] = theirs[j];
    if (c === tc && a === ta && b === tb) { i++; j++; continue; }
    if (c === "punct" && tc === "punct" && a === ta && tb < b) { // gt-merge
      let k = j, end = tb;
      while (end < b && k + 1 < theirs.length && theirs[k + 1][0] === "punct" && theirs[k + 1][1] === end) {
        k++; end = theirs[k][2];
      }
      if (end === b) { adj["gt-merge"] = (adj["gt-merge"] || 0) + 1; i++; j = k + 1; continue; }
    }
    return `token ${i}: profile ${JSON.stringify(mine[i])}, TypeScript ${JSON.stringify(theirs[j])}`;
  }
  if (i !== mine.length || j !== theirs.length) {
    return `length: profile ${mine.length - i} extra, TypeScript ${theirs.length - j} extra` +
      (j < theirs.length ? ` (next TS ${JSON.stringify(theirs[j])})` : ` (next profile ${JSON.stringify(mine[i])})`);
  }
  return null;
}

// ---------------------------------------------------------------- vectors
const report = { typescript: ts.version, vectors: [], tables: {} };
const tally = { ok_agree: 0, ok_agree_raw: 0, ok_diverge: 0, err_same_offset: 0, err_other_offset: 0,
  err_ts_accepts: 0, prelex_not_compared: 0, documented_divergence: 0 };
// Vectors tagged "departure" pin a deliberate divergence (profile §9); they must diverge.
const isDeparture = v => (v.tags || []).includes("departure");
const adj = {};
for (const [file, kind, name] of FILES) {
  const doc = JSON.parse(fs.readFileSync(path.join(DIR, file), "utf8"));
  const variant = kind === ts.ScriptKind.TSX ? ts.LanguageVariant.JSX : ts.LanguageVariant.Standard;
  for (const v of doc.vectors) {
    const r = v.result;
    const rec = { id: v.id, file };
    if (v.inputText === null || (r.status === "error" && PRE_LEX.has(r.error.code))) {
      rec.outcome = "pre-lexing error (shared §3 rule); not compared";
      if (r.status === "error" && r.error.code === "bom") {
        const sf = ts.createSourceFile(name, v.inputText, ts.ScriptTarget.Latest, true, kind);
        rec.note = `TypeScript parse diagnostics: ${sf.parseDiagnostics.length} (TS skips a BOM; OD-1 rejects it)`;
      }
      if (r.status === "error" && r.error.code === "nul") {
        const sf = ts.createSourceFile(name, v.inputText, ts.ScriptTarget.Latest, true, kind);
        rec.note = `TypeScript parse diagnostics: ${sf.parseDiagnostics.length} (TS accepts NUL in a string; shared rule rejects it)`;
      }
      tally.prelex_not_compared++;
      report.vectors.push(rec);
      continue;
    }
    const text = v.inputText;
    const bm = byteMap(text);
    const sf = ts.createSourceFile(name, text, ts.ScriptTarget.Latest, true, kind);
    const diags = sf.parseDiagnostics.map(d => ({ code: d.code, offset: bm[d.start],
      message: ts.flattenDiagnosticMessageText(d.messageText, " ") }));
    if (r.status === "error") {
      if (diags.length === 0 && isDeparture(v)) { rec.outcome = "documented divergence: profile rejects, TypeScript parses"; tally.documented_divergence++; }
      else if (diags.length === 0) { rec.outcome = "DIVERGE: profile rejects, TypeScript parses without diagnostics"; tally.err_ts_accepts++; }
      else if (diags.some(d => d.offset === r.error.offset)) { rec.outcome = "agree: both reject, a TS diagnostic at the same offset"; tally.err_same_offset++; }
      else { rec.outcome = "agree on rejection, offsets differ"; tally.err_other_offset++; }
      rec.profile = `${r.error.code}@${r.error.offset}`;
      rec.typescript = diags.slice(0, 3);
      report.vectors.push(rec);
      continue;
    }
    const mine = r.tokens.map(t => [ours(t.class), t.span[0], t.span[1]]);
    const toBytes = list => list.map(([c, a, b]) => [c, bm[a], bm[b]]);
    const local = {};
    if (diags.length === 0) {
      const d = compare(mine, toBytes(parserTokens(sf, text)), local);
      rec.oracle = "parser";
      if (d && isDeparture(v)) { rec.outcome = "documented divergence: " + d; tally.documented_divergence++; }
      else if (d) { rec.outcome = "DIVERGE: " + d; tally.ok_diverge++; }
      else if (isDeparture(v)) { rec.outcome = "UNEXPECTED agreement on a departure vector"; tally.ok_diverge++; }
      else { rec.outcome = "agree"; tally.ok_agree++; }
    } else {
      const d = compare(mine, toBytes(scannerTokens(text, variant)), local);
      rec.oracle = "raw scanner (TS parse diagnostics: " + diags.map(x => `${x.code}@${x.offset}`).join(", ") + ")";
      rec.typescript = diags.slice(0, 3);
      if (d) { rec.outcome = "DIVERGE: " + d; tally.ok_diverge++; } else { rec.outcome = "agree"; tally.ok_agree_raw++; }
    }
    for (const [k, n] of Object.entries(local)) { adj[k] = (adj[k] || 0) + n; rec.adjustments = local; }
    report.vectors.push(rec);
  }
}

// ---------------------------------------------------------------- corpus (--corpus)
// Every lib/*.d.ts and lib/*.js file (both ts-tokens; .js maps to ts-tokens in stage 1) shipped in the pinned typescript package, lexed by ../tslex.py via
// lex_json.py with no size limit, compared with the TypeScript parser's tokens.
// .d.ts files are outside the profile's input scope (§2); they are used here only
// as lexer test material.
if (process.argv.includes("--corpus")) {
  const { spawnSync } = require("child_process");
  const lib = path.join(__dirname, "node_modules", "typescript", "lib");
  const groups = [["ts-tokens", ts.ScriptKind.TS, fs.readdirSync(lib).filter(f => f.endsWith(".d.ts"))],
    ["ts-tokens", ts.ScriptKind.JS, fs.readdirSync(lib).filter(f => f.endsWith(".js"))]];
  const corpus = { files: 0, bytes: 0, tokens: 0, agree: 0, diverge: [], tsDiagnostics: [] };
  for (const [profile, kind, names] of groups) {
    const res = spawnSync("python3", ["-I", path.join(__dirname, "lex_json.py"), profile,
      ...names.map(n => path.join(lib, n))], { maxBuffer: 1 << 30, encoding: "utf8" });
    if (res.status !== 0) throw new Error(res.stderr);
    for (const line of res.stdout.trim().split("\n")) {
      const got = JSON.parse(line);
      const text = fs.readFileSync(got.file, "utf8");
      const name = path.basename(got.file);
      const sf = ts.createSourceFile(name, text, ts.ScriptTarget.Latest, true, kind);
      const bm = byteMap(text);
      corpus.files++; corpus.bytes += Buffer.byteLength(text);
      if (sf.parseDiagnostics.length) { corpus.tsDiagnostics.push(name); continue; }
      if (got.error) { corpus.diverge.push(`${name}: profile ${got.error.join("@")}, TypeScript parses`); continue; }
      const mine = got.tokens.map(([c, a, b]) => [ours(c), a, b]);
      const theirs = parserTokens(sf, text).map(([c, a, b]) => [c, bm[a], bm[b]]);
      const d = compare(mine, theirs, adj);
      corpus.tokens += mine.length;
      if (d) corpus.diverge.push(`${name}: ${d}`); else corpus.agree++;
    }
  }
  report.corpus = corpus;
  console.log(`corpus: ${corpus.files} files, ${corpus.bytes} bytes, ${corpus.tokens} profile tokens; agree ${corpus.agree}, diverge ${corpus.diverge.length}, TS diagnostics ${corpus.tsDiagnostics.length}`);
  for (const d of corpus.diverge) console.log("  DIVERGE " + d);
}

// ---------------------------------------------------------------- divergence probes (--probes)
// Each probe states the expected outcome: "agree", or the profile decision that makes
// it diverge. Any outcome other than the expected one is printed as UNEXPECTED.
const PROBES = [
  ["ts-tokens", "if (x) {}\n/re/.test(s);\n", "diverge:TSOD-3 '}' is always followed by division"],
  ["ts-tokens", "function f() {}\n/re/.test(s);\n", "diverge:TSOD-3 function-declaration '}' is followed by division"],
  ["ts-tokens", "class C {}\n/re/.test(s);\n", "diverge:TSOD-3 class-declaration '}' is followed by division"],
  ["ts-tokens", "x = await / 2;\n", "diverge:TSOD-3 'await' is always a keyword (script-code identifier misread)"],
  ["ts-tokens", "x = (a) => {}\n/re/.test(s);\n", "agree"],
  ["ts-tokens", "a\n++/re/.lastIndex;\n", "agree"],
  ["ts-tokens", "b\n!/x/.test(s);\n", "agree"],
  ["ts-tokens", "x = {} / 2;\ny = class {} / 2;\n", "agree"],
  ["ts-tokens", "s = 'a\rb';\n", "agree"],
  ["ts-tokens", "x = 0_1;\n", "agree"],
  ["ts-tokens", "o = 08.1_1;\n", "diverge:D-4 NonOctalDecimal literal is lexically valid (TS: strict-mode diagnostic)"],
  ["ts-tokens", "const a = <div>hi</div>;\n", "agree"],
  ["tsx-tokens", "const z = <div>a</div> / 2;\n", "agree"],
  ["tsx-tokens", "const a = <a <b/> />;\n", "agree"],
  ["tsx-tokens", "class A { m() { return new <T>(x: T) => x; } }\n", "agree"],
  ["tsx-tokens", "interface I { new <T>(x: T): T }\n", "diverge:TSOD-8 construct signature in tsx"],
  ["tsx-tokens", "type U = A | (<T>() => T);\n", "diverge:TSOD-8 generic function type after '(' in tsx"],
  ["tsx-tokens", "f<(<T>(x: T) => T)>(g);\n", "diverge:TSOD-8 generic function type in a type argument in tsx"],
  ["ts-tokens", "for (const m of /a/g.exec(s)) {}\n", "diverge:TSOD-3 contextual 'of' is an ident"],
  ["tsx-tokens", "type F = <T>(x: T) => T;\n", "diverge:TSOD-5 generic function type after '=' in tsx"],
  ["tsx-tokens", "interface I { <T>(x: T): T }\n", "diverge:TSOD-5 generic call signature in tsx"],
  ["tsx-tokens", "let f: <T>() => void;\n", "diverge:TSOD-5 generic function type after ':' in tsx"],
  // TS checks regex pattern and flags in the checker, not the parser: lexically both accept.
  ["ts-tokens", "x = /(/;\n", "agree"],
  ["ts-tokens", "x = /a/gg;\n", "agree"],
  ["ts-tokens", "x = `\\x`;\n", "diverge:§4.7 untagged template escapes are not checked"],
  ["ts-tokens", "x = '\\01';\n", "diverge:§4.6 legacy octal escapes are lexically valid"],
  ["ts-tokens", "x = 010;\n", "diverge:§4.5 legacy octal literals are lexically valid"],
  ["ts-tokens", "<<<<<<< HEAD\nx;\n=======\ny;\n>>>>>>> b\n", "diverge:§4.3 merge-conflict markers are not trivia"],
  ["ts-tokens", "a\u0085;\n", "diverge:§3.1 U+0085 is not white space"],
  ["ts-tokens", "a\u200b;\n", "diverge:§3.1 U+200B is not white space"],
  ["ts-tokens", "a\u088f;\n", "diverge:§3.2 Unicode 17 identifier characters (TS tables are older)"],
  ["ts-tokens", "\ufeffx;\n", "diverge:OD-1 shared BOM rule"],
  ["ts-tokens", "x = {} / 1;\n", "agree"],
  ["ts-tokens", "x = ++/re/.lastIndex;\n", "agree"],
  ["ts-tokens", "x = a\n/hi/g.exec(c);\n", "agree"],
  ["ts-tokens", "function* g() { yield /re/; }\n", "agree"],
  ["ts-tokens", "x = y as any / 2;\n", "agree"],
  ["ts-tokens", "switch (x) { case /x/: break; }\n", "agree"],
  ["ts-tokens", "do /x/.exec(s); while (0);\n", "agree"],
  ["ts-tokens", "for (;;) /x/.exec(s);\n", "agree"],
  ["ts-tokens", "class A { #a = 1; m() { return this.#a / 2; } }\n", "agree"],
  ["ts-tokens", "x = a ? /b/ : c;\n", "agree"],
  ["ts-tokens", "async function f() { await /x/; }\n", "agree"],
  ["ts-tokens", "let v = <const>['a'];\n", "agree"],
  ["ts-tokens", "x = a!.b! / c;\n", "agree"],
  ["tsx-tokens", "const f = <T = string,>(x: T) => x;\n", "agree"],
  ["tsx-tokens", "const f = <T extends unknown>(x: T) => x;\n", "agree"],
  ["tsx-tokens", "const a = <A {...p} key={1} />;\n", "agree"],
  ["tsx-tokens", "const a = <a>&nbsp;x &amp; y</a>;\n", "agree"],
  ["tsx-tokens", "const a = <a>{}</a>;\n", "agree"],
  ["tsx-tokens", "const a = <a>{cond ? <b/> : null}{list.map(i => <i key={i}>{i}</i>)}</a>;\n", "agree"],
  ["tsx-tokens", "f(<a/>, <b></b>);\n", "agree"],
  ["tsx-tokens", "const a = <svg:rect xlink:href=\"#x\" />;\n", "agree"],
  ["tsx-tokens", "if (a < b) c = d > e;\n", "agree"],
  ["tsx-tokens", "const x = y as Array<Map<K, V>>;\n", "agree"],
];
if (process.argv.includes("--probes")) {
  const { spawnSync } = require("child_process");
  const os = require("os");
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "tw-ts-probes-"));
  const files = PROBES.map(([p, src], i) => { const f = path.join(dir, `p${i}`); fs.writeFileSync(f, src); return f; });
  const lexed = {};
  for (const prof of ["ts-tokens", "tsx-tokens"]) {
    const idx = PROBES.map((p, i) => [p, i]).filter(([p]) => p[0] === prof).map(([, i]) => i);
    const res = spawnSync("python3", ["-I", path.join(__dirname, "lex_json.py"), prof, ...idx.map(i => files[i])],
      { encoding: "utf8" });
    if (res.status !== 0) throw new Error(res.stderr);
    res.stdout.trim().split("\n").forEach((line, n) => { lexed[idx[n]] = JSON.parse(line); });
  }
  const probes = { agreeAsExpected: 0, divergeAsExpected: 0, unexpected: 0, rows: [] };
  PROBES.forEach(([prof, src, expect], i) => {
    const kind = prof === "tsx-tokens" ? ts.ScriptKind.TSX : ts.ScriptKind.TS;
    const sf = ts.createSourceFile(prof === "tsx-tokens" ? "p.tsx" : "p.ts", src, ts.ScriptTarget.Latest, true, kind);
    const bm = byteMap(src);
    const got = lexed[i];
    let outcome;
    if (got.error && sf.parseDiagnostics.length === 0) outcome = `profile ${got.error.join("@")}, TypeScript parses`;
    else if (got.error) outcome = "agree";
    else if (sf.parseDiagnostics.length) outcome = `profile accepts, TypeScript diagnostic ${sf.parseDiagnostics[0].code}@${bm[sf.parseDiagnostics[0].start]}`;
    else outcome = compare(got.tokens.map(([c, a, b]) => [ours(c), a, b]),
      parserTokens(sf, src).map(([c, a, b]) => [c, bm[a], bm[b]]), {}) || "agree";
    const ok = expect === "agree" ? outcome === "agree" : outcome !== "agree";
    if (!ok) probes.unexpected++; else if (expect === "agree") probes.agreeAsExpected++; else probes.divergeAsExpected++;
    probes.rows.push({ profile: prof, input: src, expect, outcome, asExpected: ok });
    if (!ok || expect !== "agree") console.log(`  ${ok ? "" : "UNEXPECTED "}probe ${JSON.stringify(src)} [${prof}] expect ${expect}: ${outcome}`);
  });
  report.probes = probes;
  console.log(`probes: ${PROBES.length}; agree as expected ${probes.agreeAsExpected}, diverge as documented ${probes.divergeAsExpected}, unexpected ${probes.unexpected}`);
}

// ---------------------------------------------------------------- Unicode tables
const diff = { start: [], part: [], whitespace: [], lineTerminator: [] };
for (let cp = 0; cp <= 0x10FFFF; cp++) {
  if (cp >= 0xD800 && cp <= 0xDFFF) continue;
  if (ts.isIdentifierStart(cp, ts.ScriptTarget.Latest) !== idStart(cp)) diff.start.push(cp);
  if (ts.isIdentifierPart(cp, ts.ScriptTarget.Latest) !== idPart(cp)) diff.part.push(cp);
  if (ts.isWhiteSpaceSingleLine(cp) !== isWs(cp)) diff.whitespace.push(cp);
  if (ts.isLineBreak(cp) !== isLt(cp)) diff.lineTerminator.push(cp);
}
const hex = cp => "U+" + cp.toString(16).toUpperCase().padStart(4, "0");
for (const [k, list] of Object.entries(diff)) {
  report.tables[k] = { count: list.length,
    profileOnly: list.filter(cp => (k === "start" ? idStart : k === "part" ? idPart : k === "whitespace" ? isWs : isLt)(cp)).length,
    sample: list.slice(0, 12).map(hex) };
}
report.tally = tally;
report.adjustments = adj;

const out = process.argv.indexOf("--json");
if (out > 0) fs.writeFileSync(process.argv[out + 1], JSON.stringify(report, null, 1) + "\n");
console.log(`TypeScript ${ts.version}`);
for (const r of report.vectors) {
  if (r.outcome !== "agree" || r.oracle !== "parser") console.log(`  ${r.id}: ${r.outcome}${r.oracle && r.oracle !== "parser" ? " [" + r.oracle + "]" : ""}${r.profile ? " profile " + r.profile + "; TS " + (r.typescript || []).map(d => d.code + "@" + d.offset).join(",") : ""}${r.note ? " — " + r.note : ""}`);
}
console.log("tally", JSON.stringify(tally));
console.log("adjustments", JSON.stringify(adj));
for (const [k, t] of Object.entries(report.tables)) console.log(`table ${k}: ${t.count} code points differ (${t.profileOnly} profile-only); first ${t.sample.join(" ")}`);
