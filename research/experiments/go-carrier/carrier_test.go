// Synthetic feasibility checks only; not an embedder or a safety analyzer.
package carrier

import (
	"fmt"
	"go/ast"
	"go/format"
	"go/parser"
	"go/token"
	"os"
	"os/exec"
	"path/filepath"
	"reflect"
	"sort"
	"strings"
	"testing"
)

func permutations(xs []string) [][]string {
	if len(xs) == 0 {
		return [][]string{{}}
	}
	var out [][]string
	for i, x := range xs {
		rest := append([]string{}, xs[:i]...)
		rest = append(rest, xs[i+1:]...)
		for _, tail := range permutations(rest) {
			out = append(out, append([]string{x}, tail...))
		}
	}
	return out
}

func declarationOrder(t *testing.T, src []byte) []string {
	t.Helper()
	f, err := parser.ParseFile(token.NewFileSet(), "fixture.go", src, 0)
	if err != nil {
		t.Fatal(err)
	}
	fn := f.Decls[0].(*ast.FuncDecl)
	var names []string
	for _, s := range fn.Body.List {
		if a, ok := s.(*ast.AssignStmt); ok {
			names = append(names, a.Lhs[0].(*ast.Ident).Name)
		}
	}
	return names
}

func TestAllLiteralPermutations(t *testing.T) {
	// The fixture contains only fresh local int bindings and a fixed return.
	// No calls, aliases, shared state, tracing guarantees, or input programs.
	names := []string{"a", "b", "c", "d"}
	orders := permutations(names)
	if len(orders) != 24 {
		t.Fatal(len(orders))
	}
	var program strings.Builder
	program.WriteString("package main\nimport \"fmt\"\n")
	canonical := map[string]bool{}
	for i, order := range orders {
		var body strings.Builder
		fmt.Fprintf(&body, "func f%d() [4]int {\n", i)
		for _, name := range order {
			fmt.Fprintf(&body, "%s := %d\n", name, int(name[0]-'a')+1)
		}
		body.WriteString("return [4]int{a,b,c,d}\n}\n")
		formatted, err := format.Source([]byte("package main\n" + body.String()))
		if err != nil {
			t.Fatal(err)
		}
		if got := declarationOrder(t, formatted); !reflect.DeepEqual(got, order) {
			t.Fatalf("formatter changed order: %v", got)
		}
		// A simple canonicalization attack: sort this proven-restricted fixture's
		// declarations by name. All 24 different orders become the same order.
		sorted := append([]string{}, declarationOrder(t, formatted)...)
		sort.Strings(sorted)
		canonical[strings.Join(sorted, ",")] = true
		program.WriteString(body.String())
	}
	program.WriteString("func main(){\n")
	for i := range orders {
		fmt.Fprintf(&program, "fmt.Println(f%d())\n", i)
	}
	program.WriteString("}\n")
	path := filepath.Join(t.TempDir(), "main.go")
	if err := os.WriteFile(path, []byte(program.String()), 0600); err != nil {
		t.Fatal(err)
	}
	// Execute only the synthetic source constructed above, never supplied files.
	out, err := exec.Command("go", "run", path).CombinedOutput()
	if err != nil {
		t.Fatalf("%v: %s", err, out)
	}
	if string(out) != strings.Repeat("[1 2 3 4]\n", 24) {
		t.Fatalf("different results: %s", out)
	}
	if len(canonical) != 1 {
		t.Fatalf("unexpected canonical states: %d", len(canonical))
	}
	t.Log("24/24 literal orders retain output; 24/24 retain order through go/format; canonical sorting collapses 24 orders to 1")
}

func TestDistinctBindingsDoNotProveIndependence(t *testing.T) {
	observe := func(reverse bool) string {
		var events []string
		first := func() int { events = append(events, "first"); return 1 }
		second := func() int { events = append(events, "second"); return 2 }
		if reverse {
			b := second()
			a := first()
			_, _ = a, b
		} else {
			a := first()
			b := second()
			_, _ = a, b
		}
		return strings.Join(events, ",")
	}
	if observe(false) == observe(true) {
		t.Fatal("counterexample did not change effect order")
	}
	t.Log("different local destinations do not make calls safe to reorder")
}
