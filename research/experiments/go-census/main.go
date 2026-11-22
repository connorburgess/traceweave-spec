// Source-only census. This original scanner never imports, builds, or executes
// inspected packages. AST patterns are observations, not transformation safety.
package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"io/fs"
	"os"
	"path/filepath"
	"regexp"
	"runtime"
	"sort"
	"strconv"
	"strings"
	"unicode/utf8"
)

const ruleVersion = "go-census-v1"

var decimal = regexp.MustCompile(`^(0|[1-9][0-9]*)$`)
var localName = regexp.MustCompile(`^[a-z][a-z0-9]*$`)

type span struct{ Start, End int }
type function struct {
	Name        string
	Span        span
	ShapeReason string
	Gates       []string
}
type run struct {
	Span           span
	Length         int
	Block          span
	NonASCIIprefix bool
}
type fileRecord struct {
	Path, Class, SHA256 string
	Bytes               int
	Parsed              bool
	Error               string `json:",omitempty"`
	Flags               []string
	Functions           []function
	AnonymousFunctions  int
	Runs                []run
}
type classCounts struct {
	Files, Bytes, Parsed, ParserFailures, Unreadable, Functions, AnonymousFunctions int
	ExactEligible, ShapeMatches, PotentialRuns, PotentialBindings                   int
	SingletonRuns, RunsAtLeastTwo                                                   int
	ShapeRefusals, GateFailures, RunLengths, Flags                                  map[string]int
}
type fileCounts struct {
	Path, Class                                                  string
	Bytes, Functions, ExactEligible, ShapeMatches, PotentialRuns int
	Parsed                                                       bool
}
type report struct {
	Rules, ScannerSHA256, GoVersion   string
	GoFiles, GoBytes, SkippedSymlinks int
	FilesystemErrors                  []string
	Classes                           map[string]*classCounts
	Files                             []fileCounts
}
type details struct {
	Rules, ScannerSHA256              string
	Files                             []fileRecord
	SkippedSymlinks, FilesystemErrors []string
}

func digest(b []byte) string { h := sha256.Sum256(b); return hex.EncodeToString(h[:]) }
func newCounts() *classCounts {
	return &classCounts{ShapeRefusals: map[string]int{}, GateFailures: map[string]int{}, RunLengths: map[string]int{}, Flags: map[string]int{}}
}
func offset(fs *token.FileSet, p token.Pos) int { return fs.PositionFor(p, false).Offset }
func bounds(fs *token.FileSet, n ast.Node) span {
	return span{offset(fs, n.Pos()), offset(fs, n.End())}
}
func literalBinding(stmt ast.Stmt) bool {
	a, ok := stmt.(*ast.AssignStmt)
	if !ok || a.Tok != token.DEFINE || len(a.Lhs) != 1 || len(a.Rhs) != 1 {
		return false
	}
	id, ok := a.Lhs[0].(*ast.Ident)
	if !ok || !localName.MatchString(id.Name) {
		return false
	}
	lit, ok := a.Rhs[0].(*ast.BasicLit)
	if !ok || lit.Kind != token.INT || !decimal.MatchString(lit.Value) {
		return false
	}
	_, err := strconv.ParseInt(lit.Value, 10, 32)
	return err == nil
}
func arrayLength(expr ast.Expr) (int, bool) {
	a, ok := expr.(*ast.ArrayType)
	if !ok {
		return 0, false
	}
	id, ok := a.Elt.(*ast.Ident)
	if !ok || id.Name != "int" {
		return 0, false
	}
	lit, ok := a.Len.(*ast.BasicLit)
	if !ok || !decimal.MatchString(lit.Value) {
		return 0, false
	}
	n, err := strconv.Atoi(lit.Value)
	return n, err == nil && n >= 0 && n <= 4
}

// Shape-only: intentionally ignores fixed sample/package names to measure
// substantive syntax scarcity separately. Never substitutes for go/types,
// complete-package/source/build checks or reviewed carrier acceptance.
func shapeReason(fn *ast.FuncDecl) string {
	if fn.Recv != nil || fn.Type.TypeParams != nil || fn.Type.Params == nil || len(fn.Type.Params.List) != 0 || fn.Type.Results == nil || len(fn.Type.Results.List) != 1 || len(fn.Type.Results.List[0].Names) != 0 {
		return "signature"
	}
	n, ok := arrayLength(fn.Type.Results.List[0].Type)
	if !ok {
		return "result_shape"
	}
	if fn.Body == nil || len(fn.Body.List) != n+1 {
		return "body_shape"
	}
	seen := map[string]bool{}
	for _, stmt := range fn.Body.List[:n] {
		if !literalBinding(stmt) {
			return "binding_shape"
		}
		name := stmt.(*ast.AssignStmt).Lhs[0].(*ast.Ident).Name
		if seen[name] {
			return "binding_redeclaration"
		}
		seen[name] = true
	}
	ret, ok := fn.Body.List[n].(*ast.ReturnStmt)
	if !ok || len(ret.Results) != 1 {
		return "return_shape"
	}
	cl, ok := ret.Results[0].(*ast.CompositeLit)
	if !ok || len(cl.Elts) != n {
		return "return_shape"
	}
	m, ok := arrayLength(cl.Type)
	if !ok || n != m {
		return "return_shape"
	}
	for _, expr := range cl.Elts {
		id, ok := expr.(*ast.Ident)
		if !ok || !seen[id.Name] {
			return "return_bijection"
		}
		delete(seen, id.Name)
	}
	return "shape_match_only"
}
func classify(path string, generated bool) string {
	for _, component := range strings.Split(filepath.ToSlash(path), "/") {
		switch component {
		case "vendor", "third_party", "third-party", "external":
			return "dependency"
		case "testdata":
			return "testdata"
		}
	}
	if generated {
		return "generated"
	}
	if strings.HasSuffix(path, "_test.go") {
		return "test"
	}
	return "primary"
}
func scanFile(path string, src []byte) fileRecord {
	r := fileRecord{Path: filepath.ToSlash(path), Bytes: len(src), SHA256: digest(src), Flags: []string{}, Functions: []function{}, Runs: []run{}}
	fs := token.NewFileSet()
	f, err := parser.ParseFile(fs, path, src, parser.ParseComments|parser.AllErrors)
	r.Class = classify(path, false)
	if err != nil {
		r.Error = err.Error()
		return r
	}
	r.Parsed = true
	r.Class = classify(path, ast.IsGenerated(f))
	flags := map[string]bool{}
	for _, g := range f.Comments {
		for _, c := range g.List {
			text := c.Text
			if strings.Contains(text, "go:build") || strings.HasPrefix(text, "// +build") {
				flags["build_constraints"] = true
			}
			if strings.Contains(text, "go:embed") {
				flags["embed_directive"] = true
			}
			if strings.Contains(text, "go:") || strings.HasPrefix(text, "//line ") {
				flags["go_or_line_directive"] = true
			}
		}
	}
	for _, imp := range f.Imports {
		p, _ := strconv.Unquote(imp.Path.Value)
		if p == "C" {
			flags["cgo"] = true
		}
		if p == "unsafe" {
			flags["unsafe"] = true
		}
	}
	base := filepath.Base(path)
	// Conservative suffix flag: any extra underscore segment is unsupported as a
	// filename configuration in this census, not an inferred OS/arch selection.
	if strings.Contains(strings.TrimSuffix(strings.TrimSuffix(base, ".go"), "_test"), "_") {
		flags["filename_configuration_unresolved"] = true
	}
	for flag := range flags {
		r.Flags = append(r.Flags, flag)
	}
	sort.Strings(r.Flags)
	for _, decl := range f.Decls {
		fn, ok := decl.(*ast.FuncDecl)
		if !ok {
			continue
		}
		reason := shapeReason(fn)
		gates := []string{"source_build_scope_type_preconditions_unestablished"}
		if fn.Name.Name != "sample" {
			gates = append(gates, "fixed_function_name")
		}
		if f.Name.Name != "main" {
			gates = append(gates, "fixed_package_name")
		}
		if len(f.Imports) != 0 || len(f.Comments) != 0 || len(f.Decls) != 1 {
			gates = append(gates, "single_comment_free_import_free_file")
		}
		if reason != "shape_match_only" {
			gates = append(gates, "substantive_shape")
		}
		r.Functions = append(r.Functions, function{fn.Name.Name, bounds(fs, fn), reason, gates})
	}
	ast.Inspect(f, func(node ast.Node) bool {
		if _, ok := node.(*ast.FuncLit); ok {
			r.AnonymousFunctions++
		}
		block, ok := node.(*ast.BlockStmt)
		if !ok {
			return true
		}
		for i := 0; i < len(block.List); {
			if !literalBinding(block.List[i]) {
				i++
				continue
			}
			start := i
			for i < len(block.List) && literalBinding(block.List[i]) {
				i++
			}
			a, b := block.List[start], block.List[i-1]
			s := span{offset(fs, a.Pos()), offset(fs, b.End())}
			r.Runs = append(r.Runs, run{s, i - start, bounds(fs, block), utf8.RuneCount(src[:s.Start]) != s.Start})
		}
		return true
	})
	return r
}
func scan(root, hash string) (report, details, error) {
	sum := report{Rules: ruleVersion, ScannerSHA256: hash, Classes: map[string]*classCounts{}, Files: []fileCounts{}, FilesystemErrors: []string{}}
	raw := details{Rules: ruleVersion, ScannerSHA256: hash, Files: []fileRecord{}, SkippedSymlinks: []string{}, FilesystemErrors: []string{}}
	info, err := os.Lstat(root)
	if err != nil {
		return sum, raw, err
	}
	if info.Mode()&os.ModeSymlink != 0 || !info.IsDir() {
		return sum, raw, fmt.Errorf("root must be a real directory")
	}
	err = filepath.WalkDir(root, func(path string, d fs.DirEntry, walkErr error) error {
		rel, _ := filepath.Rel(root, path)
		rel = filepath.ToSlash(rel)
		if walkErr != nil {
			raw.FilesystemErrors = append(raw.FilesystemErrors, rel+": "+walkErr.Error())
			return nil
		}
		if d.IsDir() {
			if d.Name() == ".git" {
				return filepath.SkipDir
			}
			return nil
		}
		if d.Type()&os.ModeSymlink != 0 {
			raw.SkippedSymlinks = append(raw.SkippedSymlinks, rel)
			return nil
		}
		if !strings.HasSuffix(d.Name(), ".go") {
			return nil
		}
		sum.GoFiles++
		src, readErr := os.ReadFile(path)
		if readErr != nil {
			raw.Files = append(raw.Files, fileRecord{Path: rel, Class: classify(rel, false), Error: "unreadable: " + readErr.Error()})
			return nil
		}
		r := scanFile(rel, src)
		raw.Files = append(raw.Files, r)
		sum.GoBytes += r.Bytes
		return nil
	})
	if err != nil {
		return sum, raw, err
	}
	for _, r := range raw.Files {
		c := sum.Classes[r.Class]
		if c == nil {
			c = newCounts()
			sum.Classes[r.Class] = c
		}
		c.Files++
		c.Bytes += r.Bytes
		if r.Parsed {
			c.Parsed++
		} else if strings.HasPrefix(r.Error, "unreadable:") {
			c.Unreadable++
		} else {
			c.ParserFailures++
		}
		c.Functions += len(r.Functions)
		c.AnonymousFunctions += r.AnonymousFunctions
		c.PotentialRuns += len(r.Runs)
		shape := 0
		for _, fn := range r.Functions {
			if fn.ShapeReason == "shape_match_only" {
				c.ShapeMatches++
				shape++
			} else {
				c.ShapeRefusals[fn.ShapeReason]++
			}
			for _, gate := range fn.Gates {
				c.GateFailures[gate]++
			}
		}
		for _, run := range r.Runs {
			c.PotentialBindings += run.Length
			c.RunLengths[strconv.Itoa(run.Length)]++
			if run.Length == 1 {
				c.SingletonRuns++
			} else {
				c.RunsAtLeastTwo++
			}
		}
		for _, flag := range r.Flags {
			c.Flags[flag]++
		}
		sum.Files = append(sum.Files, fileCounts{r.Path, r.Class, r.Bytes, len(r.Functions), 0, shape, len(r.Runs), r.Parsed})
	}
	sum.SkippedSymlinks = len(raw.SkippedSymlinks)
	sum.FilesystemErrors = raw.FilesystemErrors
	return sum, raw, nil
}
func writeJSON(path string, value any) error {
	b, err := json.MarshalIndent(value, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(b, '\n'), 0600)
}
func main() {
	root := flag.String("root", "", "pinned source directory, read-only")
	summary := flag.String("summary", "", "aggregate JSON path")
	detail := flag.String("details", "", "ignored local detailed JSON path")
	scanner := flag.String("scanner", "main.go", "scanner source path for hash")
	flag.Parse()
	if *root == "" || *summary == "" || *detail == "" {
		fmt.Fprintln(os.Stderr, "root, summary and details are required")
		os.Exit(2)
	}
	source, err := os.ReadFile(*scanner)
	if err != nil {
		panic(err)
	}
	sum, raw, err := scan(*root, digest(source))
	if err != nil {
		panic(err)
	}
	sum.GoVersion = runtime.Version()
	if err = writeJSON(*summary, sum); err != nil {
		panic(err)
	}
	if err = writeJSON(*detail, raw); err != nil {
		panic(err)
	}
	fmt.Printf("rules=%s scanner_sha256=%s files=%d bytes=%d classes=%d filesystem_errors=%d\n", ruleVersion, sum.ScannerSHA256, sum.GoFiles, sum.GoBytes, len(sum.Classes), len(sum.FilesystemErrors))
}
