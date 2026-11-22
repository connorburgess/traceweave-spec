// Command crosscheck-go is the Go oracle for the draft extraction vectors.
//
// With no argument it lexes standard input with go/scanner (mode 0, comments
// skipped) and prints one line per token and per error. Literal and message
// bytes are base64-encoded so that no quoting form needs to be parsed back. With the argument
// "tables" it prints the Unicode version and the Go identifier tables
// (unicode.IsLetter plus '_', and unicode.Nd) as JSON ranges.
// Standard library only; it reads only standard input.
package main

import (
	"encoding/base64"
	"encoding/json"
	"fmt"
	"go/scanner"
	"go/token"
	"io"
	"os"
	"unicode"
)

func ranges(pred func(rune) bool) [][2]int {
	var out [][2]int
	for r := rune(0); r <= unicode.MaxRune; r++ {
		if r >= 0xD800 && r <= 0xDFFF {
			continue
		}
		if !pred(r) {
			continue
		}
		if n := len(out); n > 0 && out[n-1][1] == int(r)-1 {
			out[n-1][1] = int(r)
		} else {
			out = append(out, [2]int{int(r), int(r)})
		}
	}
	return out
}

func main() {
	if len(os.Args) == 2 && os.Args[1] == "tables" {
		enc := json.NewEncoder(os.Stdout)
		_ = enc.Encode(map[string]any{
			"unicodeVersion": unicode.Version,
			"go_letter":      ranges(func(r rune) bool { return r == '_' || unicode.IsLetter(r) }),
			"go_digit":       ranges(func(r rune) bool { return unicode.Is(unicode.Nd, r) }),
		})
		return
	}
	src, err := io.ReadAll(os.Stdin)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	fset := token.NewFileSet()
	f := fset.AddFile("input.go", -1, len(src))
	var errs scanner.ErrorList
	var s scanner.Scanner
	s.Init(f, src, func(pos token.Position, msg string) { errs.Add(pos, msg) }, 0)
	for {
		pos, tok, lit := s.Scan()
		if tok == token.EOF {
			break
		}
		fmt.Printf("T\t%d\t%s\t%s\n", f.Offset(pos), tok.String(), base64.StdEncoding.EncodeToString([]byte(lit)))
	}
	for _, e := range errs {
		fmt.Printf("ERR\t%d\t%s\n", e.Pos.Offset, base64.StdEncoding.EncodeToString([]byte(e.Msg)))
	}
	fmt.Println("END")
}
