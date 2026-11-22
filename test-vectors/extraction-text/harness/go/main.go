// Cross-check oracle for the draft text profile, built from Go's own Unicode
// 17.0.0 data: the standard unicode package (classes) and golang.org/x/text
// v0.39.0 norm and cases (17.0.0 tables under the go1.27 build tag).
//
// Protocol: one request per stdin line, "<mode> <hex UTF-8>"; one hex reply
// per line. Mode "classes" (no argument) prints one class letter per scalar
// value (X for surrogates). It deliberately does not use the profile's
// derived table.
package main

import (
	"bufio"
	"encoding/hex"
	"fmt"
	"os"
	"strings"
	"unicode"
	"unicode/utf8"

	"golang.org/x/text/cases"
	"golang.org/x/text/unicode/norm"
)

func isDI(r rune) bool {
	// DerivedCoreProperties.txt header: Other_DICP + Cf + Variation_Selector
	// - White_Space - FFF9..FFFB - 13430..13440 - Prepended_Concatenation_Mark.
	in := unicode.Is(unicode.Other_Default_Ignorable_Code_Point, r) || unicode.Is(unicode.Cf, r) ||
		unicode.Is(unicode.Variation_Selector, r)
	if !in || unicode.Is(unicode.White_Space, r) || (r >= 0xFFF9 && r <= 0xFFFB) ||
		(r >= 0x13430 && r <= 0x13440) || unicode.Is(unicode.Prepended_Concatenation_Mark, r) {
		return false
	}
	return true
}

func class(r rune) byte {
	switch {
	case isDI(r):
		return 'I'
	case unicode.Is(unicode.Ideographic, r):
		return 'C'
	case unicode.IsLetter(r) || unicode.IsMark(r) || unicode.IsNumber(r):
		return 'W'
	}
	return 'S'
}

var folder = cases.Fold()

// foldString: repeat NFKC, full case folding and deletion of
// Default_Ignorable code points until stable, then NFC. This is the UCD's
// prose description of NFKC_Casefold, implemented with library code rather
// than the profile's NFD + per-code-point NFKC_CF mapping.
func foldString(s string) string {
	for i := 0; i < 8; i++ {
		t := norm.NFKC.String(s)
		t = folder.String(t)
		t = strings.Map(func(r rune) rune {
			if isDI(r) {
				return -1
			}
			return r
		}, t)
		if t == s {
			break
		}
		s = t
	}
	return norm.NFC.String(s)
}

// tokenFold applies the profile's separator filter after the fold.
func tokenFold(s string) string {
	f := foldString(s)
	f = strings.Map(func(r rune) rune {
		if c := class(r); c == 'W' || c == 'C' {
			return r
		}
		return -1
	}, f)
	return norm.NFC.String(f)
}

// tokens: the profile's plain token rule, written independently.
func tokens(s string) string {
	var out []string
	b := []byte(s)
	i := 0
	for i < len(b) {
		r, n := utf8.DecodeRune(b[i:])
		c := class(r)
		if c == 'S' || c == 'I' {
			i += n
			continue
		}
		start := i
		end := i + n
		if c == 'W' {
			j := end
			for j < len(b) {
				r2, n2 := utf8.DecodeRune(b[j:])
				c2 := class(r2)
				if c2 == 'I' {
					j += n2
					continue
				}
				if c2 == 'W' {
					j += n2
					end = j
					continue
				}
				break
			}
		}
		text := string(b[start:end])
		out = append(out, fmt.Sprintf("%d-%d:%s", start, end, hex.EncodeToString([]byte(tokenFold(text)))))
		i = end
	}
	return strings.Join(out, ",")
}

func main() {
	w := bufio.NewWriterSize(os.Stdout, 1<<20)
	defer w.Flush()
	if len(os.Args) > 1 && os.Args[1] == "classes" {
		for r := rune(0); r <= 0x10FFFF; r++ {
			if r >= 0xD800 && r <= 0xDFFF {
				w.WriteByte('X')
				continue
			}
			w.WriteByte(class(r))
		}
		w.WriteByte('\n')
		return
	}
	if len(os.Args) > 1 && os.Args[1] == "versions" {
		fmt.Fprintf(w, "unicode=%s norm=%s cases=%s\n", unicode.Version, norm.Version, cases.UnicodeVersion)
		return
	}
	sc := bufio.NewScanner(os.Stdin)
	sc.Buffer(make([]byte, 1<<20), 1<<26)
	for sc.Scan() {
		mode, arg, _ := strings.Cut(sc.Text(), " ")
		raw, err := hex.DecodeString(arg)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(2)
		}
		s := string(raw)
		var res string
		switch mode {
		case "fold":
			res = hex.EncodeToString([]byte(foldString(s)))
		case "tokenfold":
			res = hex.EncodeToString([]byte(tokenFold(s)))
		case "tokens":
			res = tokens(s)
		case "nfc":
			res = hex.EncodeToString([]byte(norm.NFC.String(s)))
		case "nfd":
			res = hex.EncodeToString([]byte(norm.NFD.String(s)))
		default:
			fmt.Fprintln(os.Stderr, "unknown mode", mode)
			os.Exit(2)
		}
		w.WriteString(res)
		w.WriteByte('\n')
	}
}
