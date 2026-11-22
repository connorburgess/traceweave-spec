//! Cross-check oracle for the draft text profile: unicode-normalization
//! 0.1.25 (Unicode 17.0.0) for NFC/NFD, and unicode-segmentation 1.13.3
//! (Unicode 17.0.0) for UAX #29 word boundaries, used only to show where the
//! profile's simpler token rule differs from UAX #29.
//! pulldown-cmark 0.13.5 (CommonMark 0.31.2) renders Markdown to its text
//! content, used only to show where the profile's Markdown masks differ
//! from a CommonMark parse (not an agreement check).
//! Protocol: "<mode> <hex UTF-8>" per stdin line, one reply per line.
use pulldown_cmark::{Event, Options, Parser, Tag, TagEnd};
use std::io::{self, BufRead, BufWriter, Write};
use unicode_normalization::UnicodeNormalization;
use unicode_segmentation::UnicodeSegmentation;

/// Text content of a CommonMark document: text, inline code and image alt
/// text; code blocks, HTML, metadata blocks and link destinations dropped.
fn md_text(s: &str) -> String {
    let mut out = String::new();
    let mut skip = 0usize;
    for ev in Parser::new_ext(s, Options::ENABLE_YAML_STYLE_METADATA_BLOCKS) {
        match ev {
            Event::Start(Tag::CodeBlock(_)) | Event::Start(Tag::MetadataBlock(_)) => skip += 1,
            Event::End(TagEnd::CodeBlock) | Event::End(TagEnd::MetadataBlock(_)) => skip -= 1,
            Event::Text(t) | Event::Code(t) if skip == 0 => out.push_str(&t),
            Event::SoftBreak | Event::HardBreak => out.push('\n'),
            Event::End(_) => out.push('\n'),
            _ => {}
        }
    }
    out
}

fn hexs(b: &[u8]) -> String {
    b.iter().map(|x| format!("{x:02x}")).collect()
}

fn unhex(s: &str) -> Vec<u8> {
    (0..s.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap())
        .collect()
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let out = io::stdout();
    let mut w = BufWriter::new(out.lock());
    if args.get(1).map(|s| s.as_str()) == Some("versions") {
        let (a, b, c) = unicode_normalization::UNICODE_VERSION;
        let (d, e, f) = unicode_segmentation::UNICODE_VERSION;
        writeln!(w, "unicode-normalization={a}.{b}.{c} unicode-segmentation={d}.{e}.{f} pulldown-cmark=0.13.5").unwrap();
        return;
    }
    for line in io::stdin().lock().lines() {
        let line = line.unwrap();
        let (mode, arg) = line.split_once(' ').unwrap_or((line.as_str(), ""));
        let s = String::from_utf8(unhex(arg)).unwrap();
        let res = match mode {
            "nfc" => hexs(s.nfc().collect::<String>().as_bytes()),
            "nfd" => hexs(s.nfd().collect::<String>().as_bytes()),
            "words" => s
                .unicode_word_indices()
                .map(|(i, t)| format!("{}-{}", i, i + t.len()))
                .collect::<Vec<_>>()
                .join(","),
            "mdtext" => hexs(md_text(&s).as_bytes()),
            _ => panic!("unknown mode {mode}"),
        };
        writeln!(w, "{res}").unwrap();
    }
}
