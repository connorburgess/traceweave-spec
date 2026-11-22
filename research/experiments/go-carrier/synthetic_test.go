// This is a synthetic experiment harness, not an embedder for supplied programs.
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
	"regexp"
	"strconv"
	"strings"
	"testing"
	"time"
)

// The input boundary is exactly one fixed-name in-memory source file, no other
// package files or build inputs. This function is not a package loader.
type specimen struct {
	fs     *token.FileSet
	file   *ast.File
	fn     *ast.FuncDecl
	info   *types.Info
	decls  []*ast.AssignStmt // source order
	roles  []*types.Var      // return order, independent of spelling and source order
	values []int64           // return order
}

var localName = regexp.MustCompile(`^[a-z][a-z0-9]*$`)
var decimal = regexp.MustCompile(`^(0|[1-9][0-9]*)$`)

func inspectSynthetic(src []byte) (*specimen, error) {
	fs := token.NewFileSet()
	f, err := parser.ParseFile(fs, "fixture.go", src, parser.ParseComments|parser.AllErrors)
	if err != nil {
		return nil, fmt.Errorf("parse: %w", err)
	}
	// No headers/directives, imports, aliases, other declarations or external files.
	if len(f.Comments) != 0 || f.Name.Name != "main" || len(f.Imports) != 0 || len(f.Decls) != 1 {
		return nil, fmt.Errorf("file_boundary")
	}
	fn, ok := f.Decls[0].(*ast.FuncDecl)
	if !ok || fn.Name.Name != "sample" || fn.Recv != nil || fn.Type.TypeParams != nil || fn.Body == nil || len(fn.Type.Params.List) != 0 || fn.Type.Results == nil || len(fn.Type.Results.List) != 1 {
		return nil, fmt.Errorf("function_shape")
	}
	result := fn.Type.Results.List[0]
	if len(result.Names) != 0 {
		return nil, fmt.Errorf("named_result")
	}
	at, ok := result.Type.(*ast.ArrayType)
	if !ok {
		return nil, fmt.Errorf("result_array")
	}
	elt, ok := at.Elt.(*ast.Ident)
	if !ok || elt.Name != "int" {
		return nil, fmt.Errorf("result_int")
	}
	length, ok := at.Len.(*ast.BasicLit)
	if !ok || length.Kind != token.INT || !decimal.MatchString(length.Value) {
		return nil, fmt.Errorf("array_length")
	}
	n, err := strconv.Atoi(length.Value)
	if err != nil || n < 0 || n > 4 {
		return nil, fmt.Errorf("binding_count")
	}
	if len(fn.Body.List) != n+1 {
		return nil, fmt.Errorf("body_shape")
	}
	info := &types.Info{Defs: map[*ast.Ident]types.Object{}, Uses: map[*ast.Ident]types.Object{}, Scopes: map[ast.Node]*types.Scope{}, Types: map[ast.Expr]types.TypeAndValue{}}
	conf := types.Config{GoVersion: "go1.27"}
	if _, err := conf.Check("synthetic", fs, []*ast.File{f}, info); err != nil {
		return nil, fmt.Errorf("typecheck: %w", err)
	}
	s := &specimen{fs: fs, file: f, fn: fn, info: info}
	values := map[*types.Var]int64{}
	for _, stmt := range fn.Body.List[:n] {
		a, ok := stmt.(*ast.AssignStmt)
		if !ok || a.Tok != token.DEFINE || len(a.Lhs) != 1 || len(a.Rhs) != 1 {
			return nil, fmt.Errorf("literal_binding")
		}
		id, ok := a.Lhs[0].(*ast.Ident)
		if !ok || !localName.MatchString(id.Name) || id.IsExported() {
			return nil, fmt.Errorf("local_name")
		}
		obj, ok := info.Defs[id].(*types.Var)
		if !ok || obj.Type() != types.Typ[types.Int] {
			return nil, fmt.Errorf("local_object")
		}
		lit, ok := a.Rhs[0].(*ast.BasicLit)
		if !ok || lit.Kind != token.INT || !decimal.MatchString(lit.Value) {
			return nil, fmt.Errorf("literal_rhs")
		}
		value, err := strconv.ParseInt(lit.Value, 10, 32)
		if err != nil || value < 0 {
			return nil, fmt.Errorf("literal_range")
		}
		values[obj] = value
		s.decls = append(s.decls, a)
	}
	ret, ok := fn.Body.List[n].(*ast.ReturnStmt)
	if !ok || len(ret.Results) != 1 {
		return nil, fmt.Errorf("return_shape")
	}
	cl, ok := ret.Results[0].(*ast.CompositeLit)
	if !ok || len(cl.Elts) != n {
		return nil, fmt.Errorf("return_literal")
	}
	// go/types ensures the returned array type equals the signature; constrain its
	// spelling as well so parentheses, aliases and inferred lengths stay excluded.
	rt, ok := cl.Type.(*ast.ArrayType)
	if !ok {
		return nil, fmt.Errorf("return_array")
	}
	rl, ok := rt.Len.(*ast.BasicLit)
	if !ok || rl.Kind != token.INT || rl.Value != length.Value {
		return nil, fmt.Errorf("return_length")
	}
	re, ok := rt.Elt.(*ast.Ident)
	if !ok || re.Name != "int" {
		return nil, fmt.Errorf("return_int")
	}
	seen := map[*types.Var]bool{}
	for _, expr := range cl.Elts {
		id, ok := expr.(*ast.Ident)
		if !ok {
			return nil, fmt.Errorf("return_role")
		}
		obj, ok := info.Uses[id].(*types.Var)
		value, exists := values[obj]
		if !ok || !exists || seen[obj] {
			return nil, fmt.Errorf("return_bijection")
		}
		seen[obj] = true
		s.roles = append(s.roles, obj)
		s.values = append(s.values, value)
	}
	return s, nil
}

func codeName(role, alternative int) string {
	return "role" + string(rune('a'+role)) + string(rune('a'+alternative))
}

func checkCodebook(s *specimen) error {
	for role, target := range s.roles {
		for alt := 0; alt < 2; alt++ {
			name := codeName(role, alt)
			if token.Lookup(name).IsKeyword() || types.Universe.Lookup(name) != nil {
				return fmt.Errorf("codebook_reserved")
			}
			collision := false
			ast.Inspect(s.file, func(node ast.Node) bool {
				id, ok := node.(*ast.Ident)
				if ok && id.Name == name && s.info.ObjectOf(id) != target {
					collision = true
				}
				return true
			})
			if collision {
				return fmt.Errorf("codebook_collision_role_%d", role)
			}
		}
	}
	return nil
}

// Lexicographic permutations of return-role indices; this is raw state mapping,
// not identity, authentication, framing, redundancy or a keyed detector.
func roleOrders(n int) [][]int {
	var out [][]int
	var visit func([]int, []bool)
	visit = func(prefix []int, used []bool) {
		if len(prefix) == n {
			out = append(out, append([]int{}, prefix...))
			return
		}
		for i := 0; i < n; i++ {
			if !used[i] {
				used[i] = true
				visit(append(prefix, i), used)
				used[i] = false
			}
		}
	}
	visit(nil, make([]bool, n))
	return out
}
func rawStates(family string, n int) int {
	if family == "order" {
		return len(roleOrders(n))
	}
	return 1 << n
}
func fixedBits(states int) int {
	bits := 0
	for states > 1 {
		states /= 2
		bits++
	}
	return bits
}

func render(s *specimen) ([]byte, error) {
	var out bytes.Buffer
	if err := format.Node(&out, s.fs, s.file); err != nil {
		return nil, err
	}
	return out.Bytes(), nil
}

type outcome struct {
	source         []byte
	status, reason string
}

func embedSynthetic(src []byte, family string, state int) outcome {
	refuse := func(reason string) outcome { return outcome{append([]byte{}, src...), "refused", reason} }
	s, err := inspectSynthetic(src)
	if err != nil {
		return refuse(err.Error())
	}
	if family != "order" && family != "names" {
		return refuse("unknown_family")
	}
	if family == "names" {
		if err := checkCodebook(s); err != nil {
			return refuse(err.Error())
		}
	}
	count := rawStates(family, len(s.roles))
	if state < 0 || state >= count {
		return refuse("state_out_of_range")
	}
	if count == 1 {
		return refuse("zero_capacity")
	}
	current, err := extractSynthetic(src, src, family)
	if err == nil && current == state {
		return outcome{append([]byte{}, src...), "already_matching", ""}
	}
	if family == "order" {
		byRole := map[*types.Var]*ast.AssignStmt{}
		for _, a := range s.decls {
			byRole[s.info.Defs[a.Lhs[0].(*ast.Ident)].(*types.Var)] = a
		}
		for i, role := range roleOrders(len(s.roles))[state] {
			s.fn.Body.List[i] = byRole[s.roles[role]]
		}
	} else {
		replacements := map[types.Object]string{}
		// role 0 is the least significant mixed-radix digit, radix 2.
		for role, obj := range s.roles {
			replacements[obj] = codeName(role, (state>>role)&1)
		}
		ast.Inspect(s.file, func(node ast.Node) bool {
			if id, ok := node.(*ast.Ident); ok {
				if name, yes := replacements[s.info.ObjectOf(id)]; yes {
					id.Name = name
				}
			}
			return true
		})
	}
	out, err := render(s)
	if err != nil {
		return refuse("render_failure")
	}
	// Fresh type check verifies the graph modulo the role bijection, through the
	// narrow grammar plus unchanged role values. No cross-check pointer equality.
	after, err := inspectSynthetic(out)
	if err != nil || !reflect.DeepEqual(after.values, s.values) {
		return refuse("postcheck_failure")
	}
	got, err := extractSynthetic(src, out, family)
	if err != nil || got != state {
		return refuse("recovery_failure")
	}
	if bytes.Equal(src, out) {
		return refuse("unexpected_no_change")
	}
	return outcome{out, "changed", ""}
}

func extractSynthetic(reference, candidate []byte, family string) (int, error) {
	ref, err := inspectSynthetic(reference)
	if err != nil {
		return 0, fmt.Errorf("reference: %w", err)
	}
	got, err := inspectSynthetic(candidate)
	if err != nil {
		return 0, fmt.Errorf("candidate: %w", err)
	}
	if !reflect.DeepEqual(ref.values, got.values) {
		return 0, fmt.Errorf("reference_mismatch")
	}
	if family == "order" {
		indices := map[types.Object]int{}
		for i, obj := range got.roles {
			indices[obj] = i
		}
		order := []int{}
		for _, a := range got.decls {
			order = append(order, indices[got.info.Defs[a.Lhs[0].(*ast.Ident)]])
		}
		for rank, p := range roleOrders(len(got.roles)) {
			if reflect.DeepEqual(p, order) {
				return rank, nil
			}
		}
		return 0, fmt.Errorf("order_unavailable")
	}
	if family != "names" {
		return 0, fmt.Errorf("unknown_family")
	}
	if err := checkCodebook(ref); err != nil {
		return 0, err
	}
	if err := checkCodebook(got); err != nil {
		return 0, err
	}
	state := 0
	for role, obj := range got.roles {
		switch obj.Name() {
		case codeName(role, 0):
		case codeName(role, 1):
			state |= 1 << role
		default:
			return 0, fmt.Errorf("name_outside_codebook")
		}
	}
	return state, nil
}

func fixture(n int) []byte {
	var b strings.Builder
	b.WriteString("package main\nfunc sample() [" + strconv.Itoa(n) + "]int {\n")
	for role := 0; role < n; role++ {
		fmt.Fprintf(&b, "%s := %d\n", codeName(role, 0), role+1)
	}
	fmt.Fprintf(&b, "return [%d]int{", n)
	for role := 0; role < n; role++ {
		if role > 0 {
			b.WriteString(",")
		}
		b.WriteString(codeName(role, 0))
	}
	b.WriteString("}\n}\n")
	out, err := format.Source([]byte(b.String()))
	if err != nil {
		panic(err)
	}
	return out
}

// The canonicalizer rewrites actual AST nodes and emits complete source.
// It has no dependency on the requested/embedded state.
func canonicalize(src []byte, family string) ([]byte, error) {
	s, err := inspectSynthetic(src)
	if err != nil {
		return nil, err
	}
	if family == "order" {
		byRole := map[*types.Var]*ast.AssignStmt{}
		for _, a := range s.decls {
			byRole[s.info.Defs[a.Lhs[0].(*ast.Ident)].(*types.Var)] = a
		}
		for i, obj := range s.roles {
			s.fn.Body.List[i] = byRole[obj]
		}
	} else if family == "names" {
		if err := checkCodebook(s); err != nil {
			return nil, err
		}
		replacements := map[types.Object]string{}
		for role, obj := range s.roles {
			replacements[obj] = codeName(role, 0)
		}
		ast.Inspect(s.file, func(node ast.Node) bool {
			if id, ok := node.(*ast.Ident); ok {
				if name, yes := replacements[s.info.ObjectOf(id)]; yes {
					id.Name = name
				}
			}
			return true
		})
	} else {
		return nil, fmt.Errorf("unknown_family")
	}
	return render(s)
}

func directReturn(src []byte) ([]byte, error) {
	s, err := inspectSynthetic(src)
	if err != nil {
		return nil, err
	}
	ret := s.fn.Body.List[len(s.roles)].(*ast.ReturnStmt)
	cl := ret.Results[0].(*ast.CompositeLit)
	for i, v := range s.values {
		cl.Elts[i] = &ast.BasicLit{Kind: token.INT, Value: strconv.FormatInt(v, 10)}
	}
	s.fn.Body.List = []ast.Stmt{ret}
	return render(s)
}

type totals struct{ requests, changed, matching, refused, recovered, formatted, canonicalValid, canonicalErased, canonicalMatching, directValid, directErased int }

func TestSyntheticCarrierRoundTrips(t *testing.T) {
	started := time.Now()
	metrics := map[string]*totals{"order": {}, "names": {}}
	var program strings.Builder
	program.WriteString("package main\n")
	var calls strings.Builder
	compiled := 0
	addBehavior := func(src []byte, n int) {
		name := fmt.Sprintf("check%d", compiled)
		compiled++
		text := strings.TrimPrefix(string(src), "package main\n")
		text = strings.Replace(text, "func sample()", "func "+name+"()", 1)
		program.WriteString(text)
		fmt.Fprintf(&calls, "if %s() != [%d]int{", name, n)
		for role := 0; role < n; role++ {
			if role > 0 {
				calls.WriteString(",")
			}
			fmt.Fprintf(&calls, "%d", role+1)
		}
		calls.WriteString("} { panic(\"behavior mismatch\") }\n")
	}
	for _, family := range []string{"order", "names"} {
		m := metrics[family]
		for n := 0; n <= 4; n++ {
			ref := fixture(n)
			states := rawStates(family, n)
			t.Logf("capacity family=%s n=%d states=%d fixed_bits=%d identity_capacity=unavailable", family, n, states, fixedBits(states))
			observed := map[string]bool{}
			for state := 0; state < states; state++ {
				m.requests++
				out := embedSynthetic(ref, family, state)
				if states == 1 {
					if out.status != "refused" || out.reason != "zero_capacity" || !bytes.Equal(out.source, ref) {
						t.Fatalf("zero capacity: %+v", out)
					}
					m.refused++
					continue
				}
				switch out.status {
				case "changed":
					m.changed++
				case "already_matching":
					m.matching++
				default:
					t.Fatalf("%s n=%d state=%d: %+v", family, n, state, out)
				}
				observed[string(out.source)] = true
				got, err := extractSynthetic(ref, out.source, family)
				if err != nil || got != state {
					t.Fatalf("raw roundtrip got=%d err=%v", got, err)
				}
				m.recovered++
				again := embedSynthetic(out.source, family, state)
				if again.status != "already_matching" || !bytes.Equal(again.source, out.source) {
					t.Fatal("idempotence failed")
				}
				addBehavior(out.source, n)
				// Run the actual pinned-toolchain formatter, including its simplifier.
				command := exec.Command("gofmt", "-s")
				command.Stdin = bytes.NewReader(out.source)
				formatted, err := command.Output()
				if err != nil {
					t.Fatal(err)
				}
				got, err = extractSynthetic(ref, formatted, family)
				if err != nil || got != state {
					t.Fatalf("formatter recovery: %d %v", got, err)
				}
				m.formatted++
				addBehavior(formatted, n)
				canonical, err := canonicalize(out.source, family)
				if err != nil {
					t.Fatal(err)
				}
				got, err = extractSynthetic(ref, canonical, family)
				if err != nil || got != 0 {
					t.Fatalf("canonical recovery: %d %v", got, err)
				}
				if state == 0 {
					if !bytes.Equal(canonical, out.source) {
						t.Fatal("canonical state changed")
					}
					m.canonicalMatching++
				} else {
					if bytes.Equal(canonical, out.source) {
						t.Fatal("canonicalizer did not edit source")
					}
					m.canonicalErased++
				}
				m.canonicalValid++
				addBehavior(canonical, n)
				direct, err := directReturn(out.source)
				if err != nil {
					t.Fatal(err)
				}
				if _, err = extractSynthetic(ref, direct, family); err == nil {
					t.Fatal("direct return retained carrier grammar")
				}
				m.directValid++
				m.directErased++
				addBehavior(direct, n)
			}
			if states > 1 && len(observed) != states {
				t.Fatalf("mapping not injective: %s n=%d", family, n)
			}
		}
	}
	program.WriteString("func main(){\n")
	program.WriteString(calls.String())
	program.WriteString("}\n")
	// Compile/check the complete generated package before running all behaviors.
	fs := token.NewFileSet()
	f, err := parser.ParseFile(fs, "main.go", program.String(), 0)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := (&types.Config{GoVersion: "go1.27"}).Check("behavior", fs, []*ast.File{f}, nil); err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(t.TempDir(), "main.go")
	if err := os.WriteFile(path, []byte(program.String()), 0600); err != nil {
		t.Fatal(err)
	}
	runStarted := time.Now()
	output, err := exec.Command("go", "run", path).CombinedOutput()
	if err != nil {
		t.Fatalf("behavior run: %v\n%s", err, output)
	}
	for _, family := range []string{"order", "names"} {
		t.Logf("metrics family=%s %+v", family, *metrics[family])
	}
	t.Logf("compiled_behavior_checks=%d source_bytes=%d compile_run_elapsed=%s total_elapsed=%s", compiled, program.Len(), time.Since(runStarted), time.Since(started))
}

func TestSyntheticRefusalsAndControls(t *testing.T) {
	base := string(fixture(2))
	fixtures := []struct{ name, src string }{
		{"malformed", "package main\nfunc"},
		{"too_many_bindings", string(fixture(5))},
		{"tag", "//go:build linux\n\n" + base},
		{"cgo", strings.Replace(base, "package main", "package main\nimport \"C\"", 1)},
		{"embed", strings.Replace(base, "package main", "package main\nimport _ \"embed\"\n//go:embed asset\nvar asset string", 1)},
		{"compiler_directive", strings.Replace(base, "func sample", "//go:noinline\nfunc sample", 1)},
		{"body_comment", strings.Replace(base, "roleaa := 1", "// binding\nroleaa := 1", 1)},
		{"exported_local", strings.ReplaceAll(base, "roleaa", "Roleaa")},
		{"parameter", strings.Replace(base, "sample()", "sample(input int)", 1)},
		{"named_result", strings.Replace(base, "[2]int {", "(result [2]int) {", 1)},
		{"generic", strings.Replace(base, "sample()", "sample[T any]()", 1)},
		{"method", strings.Replace(base, "func sample()", "type receiver int\nfunc (r receiver) sample()", 1)},
		{"shadow", strings.Replace(base, "roleaa := 1", "roleaa := 1\n{ roleaa := 2; _ = roleaa }", 1)},
		{"mixed_short", strings.Replace(base, "roleba := 2", "roleaa, roleba := 1, 2", 1)},
		{"side_effect", strings.Replace(base, "roleaa := 1", "roleaa := func() int { println(\"effect\"); return 1 }()", 1)},
		{"alias_type", strings.Replace(base, "package main", "package main\ntype integer = int", 1)},
		{"mutable_alias", strings.Replace(base, "roleaa := 1", "values := []int{1}; alias := values; roleaa := alias[0]", 1)},
		{"closure", strings.Replace(base, "roleaa := 1", "roleaa := func() int { return 1 }()", 1)},
		{"goroutine_capture", strings.Replace(base, "roleaa := 1", "roleaa := 1; go func(){ _ = roleaa }()", 1)},
		{"field", strings.Replace(base, "roleaa := 1", "roleaa := struct{ Value int }{1}.Value", 1)},
		{"negative", strings.Replace(base, "roleaa := 1", "roleaa := -1", 1)},
		{"overflow", strings.Replace(base, "roleaa := 1", "roleaa := 2147483648", 1)},
		{"hex", strings.Replace(base, "roleaa := 1", "roleaa := 0x1", 1)},
		{"duplicate_return", strings.Replace(base, "roleaa, roleba", "roleaa, roleaa", 1)},
	}
	attempts := 0
	for _, f := range fixtures {
		for _, family := range []string{"order", "names"} {
			t.Run(f.name+"/"+family, func(t *testing.T) {
				original := []byte(f.src)
				out := embedSynthetic(original, family, 0)
				if out.status != "refused" || !bytes.Equal(out.source, original) {
					t.Fatalf("expected unchanged refusal: %+v", out)
				}
				repeat := embedSynthetic(original, family, 0)
				if repeat.reason != out.reason || !bytes.Equal(repeat.source, out.source) {
					t.Fatal("nondeterministic refusal")
				}
			})
			attempts++
		}
	}
	// A spelling reserved for role zero is already bound to role one. The source
	// satisfies the order grammar; the identifier family's entire codebook refuses.
	collision := []byte(strings.ReplaceAll(base, "roleba", "roleab"))
	if _, err := inspectSynthetic(collision); err != nil {
		t.Fatal(err)
	}
	for state := 0; state < 4; state++ {
		out := embedSynthetic(collision, "names", state)
		if out.status != "refused" || !strings.HasPrefix(out.reason, "codebook_collision") || !bytes.Equal(out.source, collision) {
			t.Fatalf("collision: %+v", out)
		}
	}
	if out := embedSynthetic(collision, "order", 1); out.status != "changed" {
		t.Fatalf("collision unnecessarily disallowed order: %+v", out)
	}
	for _, family := range []string{"order", "names"} {
		for _, state := range []int{-1, rawStates(family, 2)} {
			out := embedSynthetic([]byte(base), family, state)
			if out.status != "refused" || out.reason != "state_out_of_range" || string(out.source) != base {
				t.Fatal("range refusal")
			}
		}
		// Unmarked canonical source decodes: raw symbols cannot certify insertion.
		got, err := extractSynthetic([]byte(base), []byte(base), family)
		if err != nil || got != 0 {
			t.Fatalf("unmarked control: %d %v", got, err)
		}
		// Independently spelled same-task code is compatible with the reference's
		// structural anchor. Order decodes, names abstain outside the codebook.
		independent := []byte(strings.ReplaceAll(strings.ReplaceAll(base, "roleaa", "left"), "roleba", "right"))
		got, err = extractSynthetic([]byte(base), independent, family)
		if family == "order" && (err != nil || got != 0) {
			t.Fatal("independent order control")
		}
		if family == "names" && err == nil {
			t.Fatal("outside codebook accepted")
		}
		if family == "names" {
			out := embedSynthetic(independent, family, 3)
			state, err := extractSynthetic(independent, out.source, family)
			if out.status != "changed" || err != nil || state != 3 {
				t.Fatalf("scope-resolved rename from outside codebook: status=%s state=%d err=%v", out.status, state, err)
			}
		}
		wrong := []byte(strings.Replace(base, "roleaa := 1", "roleaa := 3", 1))
		if _, err := extractSynthetic(wrong, []byte(base), family); err == nil {
			t.Fatal("wrong reference accepted")
		}
	}
	t.Logf("grammar_refusal_inputs=%d requests=%d unchanged=%d; names_collision_requests=4 unchanged=4; out_of_range_requests=4 unchanged=4; identity_wrong_key_false_alerts=unavailable", len(fixtures), attempts, attempts)
}
