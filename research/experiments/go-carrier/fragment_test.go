// Synthetic fragment/alignment experiments. Parsing/extraction never executes input.
package carrier

import (
	"bytes"
	"fmt"
	"go/ast"
	"go/format"
	"go/parser"
	"go/token"
	"go/types"
	"os"
	"os/exec"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
	"time"
	"unicode/utf8"
)

type byteSpan struct{ Start, End int } // UTF-8 byte offsets, half-open, original source.
type localSymbol struct {
	Span        byteSpan
	Role, Value int
}
type localRecovery struct {
	Status                       string
	Span                         byteSpan
	State                        int // meaningful only when Status == "recovered"
	Symbols                      []localSymbol
	Anchors                      []byteSpan
	Examined, Supported, Skipped int
}
type functionAnchor struct {
	fn         *ast.FuncDecl
	normalized []byte
	spec       *specimen
	span       byteSpan
}

// The host envelope permits only import-free, comment/directive-free function
// bodies in a single main-package file. Ordinary comments outside functions are
// allowed for offset tests. No package loading, wrappers for excerpts, or execution.
func recoverInSyntheticHost(reference, candidate []byte, family string) localRecovery {
	fail := func(status string) localRecovery { return localRecovery{Status: status, State: -1} }
	if family != "order" && family != "names" {
		return fail("unknown_family")
	}
	ref, err := inspectSynthetic(reference)
	if err != nil {
		return fail("invalid_reference")
	}
	fs := token.NewFileSet()
	f, err := parser.ParseFile(fs, "host.go", candidate, parser.ParseComments|parser.AllErrors)
	if err != nil {
		return fail("host_parse_error")
	}
	if f.Name.Name != "main" || len(f.Imports) != 0 {
		return fail("host_boundary")
	}
	for _, c := range f.Comments {
		// CommentGroup.Text omits directive comments; inspect raw tokens.
		for _, comment := range c.List {
			if strings.Contains(comment.Text, "go:") || strings.Contains(comment.Text, "+build") || strings.HasPrefix(comment.Text, "//line ") {
				return fail("host_directive")
			}
		}
	}
	for _, d := range f.Decls {
		if _, ok := d.(*ast.FuncDecl); !ok {
			return fail("host_boundary")
		}
	}
	info := &types.Info{Defs: map[*ast.Ident]types.Object{}, Uses: map[*ast.Ident]types.Object{}}
	if _, err := (&types.Config{GoVersion: "go1.27"}).Check("synthetic-host", fs, []*ast.File{f}, info); err != nil {
		return fail("host_type_error")
	}
	result := fail("no_anchor")
	var matching []functionAnchor
	for _, d := range f.Decls {
		fn := d.(*ast.FuncDecl)
		result.Examined++
		bodyComment := false
		for _, c := range f.Comments {
			if fn.Pos() <= c.Pos() && c.End() <= fn.End() {
				bodyComment = true
			}
		}
		if bodyComment {
			result.Skipped++
			continue
		}
		// This wrapper is only a grammar validator; all reported coordinates and
		// symbol object checks below use the original AST and full-host type checker.
		copyFn := *fn
		copyFn.Name = ast.NewIdent("sample")
		var b bytes.Buffer
		if err := format.Node(&b, fs, &copyFn); err != nil {
			result.Skipped++
			continue
		}
		normalized := append([]byte("package main\n"), b.Bytes()...)
		s, err := inspectSynthetic(normalized)
		if err != nil {
			result.Skipped++
			continue
		}
		result.Supported++
		if !reflect.DeepEqual(ref.values, s.values) {
			continue
		}
		span := byteSpan{fs.PositionFor(fn.Pos(), false).Offset, fs.PositionFor(fn.End(), false).Offset}
		matching = append(matching, functionAnchor{fn, normalized, s, span})
		result.Anchors = append(result.Anchors, span)
	}
	// Ambiguity is resolved before decoding. Never pick the first, or the one
	// whose spelling happens to be decodable under the requested family.
	if len(matching) > 1 {
		result.Status = "ambiguous_anchor"
		return result
	}
	if len(matching) == 0 {
		return result
	}
	anchor := matching[0]
	result.Span = anchor.span
	if rawStates(family, len(ref.roles)) == 1 {
		result.Status = "zero_capacity"
		return result
	}
	// Preserve full-host codebook collision checks: normalization must not hide
	// function/package identifiers or identifiers in unrelated functions.
	if family == "names" {
		for role, local := range anchor.spec.roles {
			var target types.Object
			for id, obj := range info.Defs {
				if _, ok := obj.(*types.Var); ok && id.Pos() >= anchor.fn.Pos() && id.End() <= anchor.fn.End() && id.Name == local.Name() {
					target = obj
				}
			}
			if target == nil {
				result.Status = "host_binding_error"
				return result
			}
			collision := false
			ast.Inspect(f, func(node ast.Node) bool {
				id, ok := node.(*ast.Ident)
				if ok && (id.Name == codeName(role, 0) || id.Name == codeName(role, 1)) && info.ObjectOf(id) != target {
					collision = true
				}
				return true
			})
			if collision {
				result.Status = "host_codebook_collision"
				return result
			}
		}
	}
	state, err := extractSynthetic(reference, anchor.normalized, family)
	if err != nil {
		result.Status = "raw_unavailable"
		return result
	}
	result.Status = "recovered"
	result.State = state
	// Each symbol points to the original local definition identifier. For order,
	// Value is its source-order index, not an independently encoded bit. For names,
	// Value is the role's radix-two digit. Function-level State remains the unit.
	originalRoles := map[types.Object]int{}
	ret := anchor.fn.Body.List[len(ref.roles)].(*ast.ReturnStmt)
	for role, expr := range ret.Results[0].(*ast.CompositeLit).Elts {
		originalRoles[info.Uses[expr.(*ast.Ident)]] = role
	}
	for position, stmt := range anchor.fn.Body.List[:len(ref.roles)] {
		id := stmt.(*ast.AssignStmt).Lhs[0].(*ast.Ident)
		role, ok := originalRoles[info.Defs[id]]
		if !ok {
			return fail("host_binding_error")
		}
		value := position
		if family == "names" {
			value = (state >> role) & 1
		}
		result.Symbols = append(result.Symbols, localSymbol{byteSpan{fs.PositionFor(id.Pos(), false).Offset, fs.PositionFor(id.End(), false).Offset}, role, value})
	}
	return result
}

func namedFunction(t *testing.T, source []byte, name string) string {
	t.Helper()
	s, err := inspectSynthetic(source)
	if err != nil {
		t.Fatal(err)
	}
	s.fn.Name = ast.NewIdent(name)
	var b bytes.Buffer
	if err := format.Node(&b, s.fs, s.fn); err != nil {
		t.Fatal(err)
	}
	return b.String()
}
func syntheticHost(functions ...string) []byte {
	return []byte("package main\n" + strings.Join(functions, "\n") + "\n")
}
func changeRoleValues(t *testing.T, source []byte, add int64) []byte {
	t.Helper()
	s, err := inspectSynthetic(source)
	if err != nil {
		t.Fatal(err)
	}
	for _, stmt := range s.decls {
		lit := stmt.Rhs[0].(*ast.BasicLit)
		var value int64
		fmt.Sscan(lit.Value, &value)
		lit.Value = fmt.Sprint(value + add)
	}
	out, err := render(s)
	if err != nil {
		t.Fatal(err)
	}
	return out
}

type behaviorTarget struct {
	name   string
	values []int
}
type hostCase struct {
	name    string
	source  []byte
	want    string
	state   int
	targets []behaviorTarget // Only generated fixtures with known expected values.
}

func TestSyntheticFragmentsAndTransplants(t *testing.T) {
	start := time.Now()
	var combined strings.Builder
	combined.WriteString("package main\n")
	var calls strings.Builder
	queries, recovered, abstained, compiledHosts, compiledReturns, symbolCount := 0, 0, 0, 0, 0, 0
	for _, family := range []string{"order", "names"} {
		ref := fixture(3)
		state := rawStates(family, 3) - 1
		marked := embedSynthetic(ref, family, state)
		if marked.status != "changed" {
			t.Fatal("expected nonzero donor")
		}
		copied := namedFunction(t, marked.source, "carried")
		helper := "func unrelated() int { return 99 }"
		whole := syntheticHost(helper, copied)
		// An independent construction uses its own locals, then receives only the
		// donor's raw rank/digits through the public mapping, not donor AST nodes.
		independent := []byte(strings.NewReplacer("roleaa", "left", "roleba", "middle", "roleca", "right").Replace(string(ref)))
		signal := embedSynthetic(independent, family, state)
		if signal.status != "changed" {
			t.Fatal("signal transfer failed")
		}
		otherReference := changeRoleValues(t, independent, 10)
		otherSignal := embedSynthetic(otherReference, family, state)
		if otherSignal.status != "changed" {
			t.Fatal("changed-context signal transfer failed")
		}
		small := embedSynthetic(fixture(2), family, rawStates(family, 2)-1)
		if small.status != "changed" {
			t.Fatal("short run generation")
		}
		// Delete one actual declaration, leaving an unresolved return role. Parsing
		// can succeed but host type checking must fail; no candidate is executed.
		donor, err := inspectSynthetic(marked.source)
		if err != nil {
			t.Fatal(err)
		}
		donor.fn.Body.List = donor.fn.Body.List[1:]
		incomplete, err := render(donor)
		if err != nil {
			t.Fatal(err)
		}
		rawStart := bytes.Index(marked.source, []byte("{")) + 1
		rawEnd := bytes.LastIndex(marked.source, []byte("return"))
		excerpt := marked.source[rawStart:rawEnd]
		independentWant := "recovered"
		if family == "names" {
			independentWant = "raw_unavailable"
		}
		collisionWant := "recovered"
		if family == "names" {
			collisionWant = "host_codebook_collision"
		}
		cases := []hostCase{
			{"whole_function", whole, "recovered", state, []behaviorTarget{{"carried", []int{1, 2, 3}}}},
			{"unicode_relocation", []byte("package main\n// prefix: ไทย café 🧵\n" + helper + "\n" + namedFunction(t, marked.source, "moved") + "\n"), "recovered", state, []behaviorTarget{{"moved", []int{1, 2, 3}}}},
			{"changed_host_context", syntheticHost("func unrelated() int { return 12345 }", copied), "recovered", state, []behaviorTarget{{"carried", []int{1, 2, 3}}}},
			{"missing_binding", incomplete, "host_type_error", -1, nil},
			{"statement_excerpt", excerpt, "host_parse_error", -1, nil},
			{"shortened_run", syntheticHost(namedFunction(t, small.source, "short")), "no_anchor", -1, []behaviorTarget{{"short", []int{1, 2}}}},
			{"duplicate_anchor", syntheticHost(namedFunction(t, marked.source, "first"), namedFunction(t, independent, "second")), "ambiguous_anchor", -1, []behaviorTarget{{"first", []int{1, 2, 3}}, {"second", []int{1, 2, 3}}}},
			{"changed_literal_context", syntheticHost(namedFunction(t, changeRoleValues(t, marked.source, 10), "changed")), "no_anchor", -1, []behaviorTarget{{"changed", []int{11, 12, 13}}}},
			{"independent_same_task", syntheticHost(namedFunction(t, independent, "independent")), independentWant, 0, []behaviorTarget{{"independent", []int{1, 2, 3}}}},
			{"signal_only_same_context", syntheticHost(helper, namedFunction(t, signal.source, "recipient")), "recovered", state, []behaviorTarget{{"recipient", []int{1, 2, 3}}}},
			{"signal_only_other_context", syntheticHost(namedFunction(t, otherSignal.source, "recipient")), "no_anchor", -1, []behaviorTarget{{"recipient", []int{11, 12, 13}}}},
			{"host_codebook_collision", syntheticHost("func roleab() int { return 99 }", copied), collisionWant, state, []behaviorTarget{{"carried", []int{1, 2, 3}}}},
		}
		for _, c := range cases {
			t.Run(family+"/"+c.name, func(t *testing.T) {
				queries++
				before := append([]byte{}, c.source...)
				got := recoverInSyntheticHost(ref, c.source, family)
				if got.Status != c.want {
					t.Fatalf("want %s got %+v", c.want, got)
				}
				if !bytes.Equal(before, c.source) {
					t.Fatal("extractor mutated input")
				}
				if got.Status == "recovered" {
					recovered++
					if got.State != c.state || len(got.Symbols) != 3 {
						t.Fatalf("wrong raw result %+v", got)
					}
					// Ground truth is an exact source substring; verify original UTF-8 byte
					// coordinates rather than offsets in normalized/wrapper source.
					start := bytes.Index(c.source, []byte("func "+c.targets[0].name+"("))
					end := bytes.Index(c.source[start:], []byte("\n}")) + start + 2
					if got.Span != (byteSpan{start, end}) {
						t.Fatalf("span want=[%d,%d) got=%+v", start, end, got.Span)
					}
					for position, symbol := range got.Symbols {
						if symbol.Span.Start < start || symbol.Span.End > end || !localName.Match(c.source[symbol.Span.Start:symbol.Span.End]) {
							t.Fatalf("bad symbol span %+v", symbol)
						}
						if !strings.HasPrefix(strings.TrimSpace(string(c.source[symbol.Span.End:])), fmt.Sprintf(":= %d", symbol.Role+1)) {
							t.Fatalf("symbol does not point to expected role's definition: %+v", symbol)
						}
						if family == "order" && (symbol.Role != roleOrders(3)[c.state][position] || symbol.Value != position) {
							t.Fatalf("wrong localized order symbol: %+v", symbol)
						}
						if family == "names" && (symbol.Value != (c.state>>symbol.Role)&1 || string(c.source[symbol.Span.Start:symbol.Span.End]) != codeName(symbol.Role, symbol.Value)) {
							t.Fatalf("wrong localized name digit: %+v", symbol)
						}
						symbolCount++
					}
					if c.name == "unicode_relocation" && utf8.RuneCount(c.source[:start]) == start {
						t.Fatal("non-ASCII prefix control ineffective")
					}
				} else {
					abstained++
					if got.State != -1 || len(got.Symbols) != 0 {
						t.Fatal("abstention leaked selected raw state")
					}
				}
				if c.name == "duplicate_anchor" {
					if len(got.Anchors) != 2 {
						t.Fatalf("missing duplicate intervals %+v", got)
					}
					for _, span := range got.Anchors {
						if !bytes.HasPrefix(c.source[span.Start:span.End], []byte("func ")) {
							t.Fatal("bad ambiguous span")
						}
					}
				}
				t.Logf("outcome=%s raw_state=%d span=%+v anchors=%v symbols=%v examined=%d supported=%d skipped=%d", got.Status, got.State, got.Span, got.Anchors, got.Symbols, got.Examined, got.Supported, got.Skipped)
			})
			if len(c.targets) == 0 {
				continue
			}
			// Compile only the hard-coded/generated test cases, never an extractor input
			// supplied by a caller. Include every declaration from each trusted host.
			fs := token.NewFileSet()
			f, err := parser.ParseFile(fs, "trusted.go", c.source, 0)
			if err != nil {
				t.Fatal(err)
			}
			rename := map[string]string{}
			prefix := fmt.Sprintf("host%d", compiledHosts)
			for _, d := range f.Decls {
				fn := d.(*ast.FuncDecl)
				rename[fn.Name.Name] = prefix + fn.Name.Name
				fn.Name = ast.NewIdent(rename[fn.Name.Name])
			}
			for _, d := range f.Decls {
				var b bytes.Buffer
				if err := format.Node(&b, fs, d); err != nil {
					t.Fatal(err)
				}
				combined.Write(b.Bytes())
				combined.WriteString("\n")
			}
			for _, target := range c.targets {
				fmt.Fprintf(&calls, "if %s() != [%d]int{", rename[target.name], len(target.values))
				for i, v := range target.values {
					if i > 0 {
						calls.WriteString(",")
					}
					fmt.Fprint(&calls, v)
				}
				calls.WriteString("} { panic(\"trusted host output mismatch\") }\n")
				compiledReturns++
			}
			compiledHosts++
		}
		// A changed-context signal also decodes against its own matching reference:
		// the old reference abstention is an alignment rule, not transplant security.
		got := recoverInSyntheticHost(otherReference, syntheticHost(namedFunction(t, otherSignal.source, "recipient")), family)
		if got.Status != "recovered" || got.State != state {
			t.Fatalf("own-reference signal result %+v", got)
		}
		t.Logf("own_reference_signal family=%s state=%d span=%+v symbols=%v", family, got.State, got.Span, got.Symbols)
	}
	combined.WriteString("func main(){\n")
	combined.WriteString(calls.String())
	combined.WriteString("}\n")
	path := filepath.Join(t.TempDir(), "main.go")
	if err := os.WriteFile(path, []byte(combined.String()), 0600); err != nil {
		t.Fatal(err)
	}
	output, err := exec.Command("go", "run", path).CombinedOutput()
	if err != nil {
		t.Fatalf("trusted aggregate compile/run: %v\n%s", err, output)
	}
	t.Logf("main_queries=%d recovered=%d abstained=%d localized_definition_symbols=%d own_reference_controls=2 compiled_trusted_hosts=%d compiled_return_checks=%d aggregate_bytes=%d elapsed=%s", queries, recovered, abstained, symbolCount, compiledHosts, compiledReturns, combined.Len(), time.Since(start))
}

func TestSyntheticHostAlignmentGuards(t *testing.T) {
	ref := fixture(3)
	cases := []struct {
		name         string
		source       []byte
		family, want string
	}{
		{"unknown_family", ref, "other", "unknown_family"},
		{"directive", []byte("//go:build linux\n\n" + string(ref)), "order", "host_directive"},
		{"compiler_directive", []byte(strings.Replace(string(ref), "func sample", "//go:noinline\nfunc sample", 1)), "order", "host_directive"},
		{"line_directive", []byte("//line another.go:99\n" + string(ref)), "order", "host_directive"},
		{"import_boundary", []byte(strings.Replace(string(ref), "package main", "package main\nimport _ \"unsafe\"", 1)), "order", "host_boundary"},
		{"package_declaration", []byte(strings.Replace(string(ref), "package main", "package main\nvar extra = 1", 1)), "order", "host_boundary"},
		{"body_comment", []byte(strings.Replace(string(ref), "roleaa := 1", "// body\nroleaa := 1", 1)), "order", "no_anchor"},
		{"zero_order", fixture(1), "order", "zero_capacity"},
		{"zero_names", fixture(0), "names", "zero_capacity"},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			reference := ref
			if strings.HasPrefix(c.name, "zero_") {
				reference = c.source
			}
			got := recoverInSyntheticHost(reference, c.source, c.family)
			if got.Status != c.want || got.State != -1 || len(got.Symbols) != 0 {
				t.Fatalf("guard %+v", got)
			}
		})
	}
	// Reverse duplicate order: neither list order nor codebook decodability can
	// disambiguate two structurally matching complete functions.
	independent := []byte(strings.NewReplacer("roleaa", "left", "roleba", "middle", "roleca", "right").Replace(string(ref)))
	for _, family := range []string{"order", "names"} {
		host := syntheticHost(namedFunction(t, independent, "first"), namedFunction(t, ref, "second"))
		got := recoverInSyntheticHost(ref, host, family)
		if got.Status != "ambiguous_anchor" || len(got.Anchors) != 2 || got.State != -1 {
			t.Fatalf("reversed duplicates %+v", got)
		}
	}
	if got := recoverInSyntheticHost([]byte("invalid"), ref, "order"); got.Status != "invalid_reference" || got.State != -1 || len(got.Symbols) != 0 {
		t.Fatalf("invalid reference guard: %+v", got)
	}
	t.Log("guard_queries=12 abstentions=12 (9 boundary/zero-capacity plus 2 reversed duplicate anchors and 1 invalid reference)")
}
