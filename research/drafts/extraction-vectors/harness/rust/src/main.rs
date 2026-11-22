//! Rust oracle for the draft extraction vectors.
//!
//! With no argument: lex standard input with proc-macro2's fallback lexer and
//! print one line per token (delimiters flattened) with byte ranges. With the
//! argument `tables`: print unicode-ident's Unicode version and XID tables as
//! JSON ranges. It reads only standard input.
use proc_macro2::{Delimiter, TokenStream, TokenTree};
use std::io::Read;

fn walk(ts: TokenStream, out: &mut Vec<String>) {
    for tt in ts {
        match tt {
            TokenTree::Group(g) => {
                let (o, c) = match g.delimiter() {
                    Delimiter::Parenthesis => ("(", ")"),
                    Delimiter::Bracket => ("[", "]"),
                    Delimiter::Brace => ("{", "}"),
                    Delimiter::None => ("<none>", "</none>"),
                };
                let r = g.span_open().byte_range();
                out.push(format!("D\t{}\t{}\t{}", o, r.start, r.end));
                walk(g.stream(), out);
                let r = g.span_close().byte_range();
                out.push(format!("D\t{}\t{}\t{}", c, r.start, r.end));
            }
            TokenTree::Ident(i) => {
                let r = i.span().byte_range();
                out.push(format!("I\t{}\t{}\t{}", i, r.start, r.end));
            }
            TokenTree::Punct(p) => {
                let r = p.span().byte_range();
                out.push(format!("P\t{}\t{}\t{}\t{:?}", p.as_char(), r.start, r.end, p.spacing()));
            }
            TokenTree::Literal(l) => {
                let r = l.span().byte_range();
                let hex: String = l.to_string().bytes().map(|b| format!("{:02x}", b)).collect();
                out.push(format!("L\t{}\t{}\t{}", hex, r.start, r.end));
            }
        }
    }
}

fn ranges(pred: fn(char) -> bool) -> String {
    let mut out: Vec<(u32, u32)> = Vec::new();
    for c in (0u32..=0x10FFFF).filter_map(char::from_u32) {
        if !pred(c) {
            continue;
        }
        let v = c as u32;
        match out.last_mut() {
            Some(last) if last.1 + 1 == v => last.1 = v,
            _ => out.push((v, v)),
        }
    }
    let items: Vec<String> = out.iter().map(|(a, b)| format!("[{},{}]", a, b)).collect();
    format!("[{}]", items.join(","))
}

fn main() {
    if std::env::args().nth(1).as_deref() == Some("tables") {
        let (a, b, c) = unicode_ident::UNICODE_VERSION;
        println!(
            "{{\"unicodeVersion\":\"{}.{}.{}\",\"xid_start\":{},\"xid_continue\":{}}}",
            a, b, c, ranges(unicode_ident::is_xid_start), ranges(unicode_ident::is_xid_continue)
        );
        return;
    }
    let mut b = Vec::new();
    std::io::stdin().read_to_end(&mut b).unwrap();
    let s = match String::from_utf8(b) {
        Ok(s) => s,
        Err(e) => {
            println!("ERR\tinvalid-utf8 {}", e.utf8_error().valid_up_to());
            return;
        }
    };
    match s.parse::<TokenStream>() {
        Ok(ts) => {
            let mut out = Vec::new();
            walk(ts, &mut out);
            for l in out {
                println!("{}", l);
            }
            println!("OK");
        }
        Err(e) => println!("ERR\t{}", e.span().byte_range().start),
    }
}
