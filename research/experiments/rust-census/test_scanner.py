import unittest
import tempfile
from pathlib import Path
import scanner


class ScannerTests(unittest.TestCase):
    def test_opaque_comments_strings_and_nested_comments(self):
        text = '''// fn fake() 12u32\n/* fn fake /* fn inner */ 12u32 */
        const S: &str = r###"fn fake 12u32"###;
        const B: &[u8] = b"fn fake 12u32";
        const C: char = 'f'; fn real<'a>() { let a: u32 = 12u32; let b: u32 = 23u32; }
        '''
        result = scanner.inspect_file(text.encode())
        self.assertEqual(result['lexical_fn_tokens'], 1)
        self.assertEqual(result['potential_spelling_tokens'], 2)
        self.assertEqual(result['potential_adjacent_runs'], 1)
        self.assertEqual(result['exact_eligible'], 0)

    def test_unicode_offsets_are_original_bytes(self):
        source = '// café\nfn demo() { 12u32; }'
        result = scanner.inspect_file(source.encode())
        begin, end = result['local_offsets']['spelling'][0]
        self.assertEqual(source.encode()[begin:end], b'12u32')
        self.assertNotEqual(begin, source.index('12u32'))

    def test_fail_closed_lexical_failures(self):
        for text in ('/* unterminated', 'r#"unterminated', '"unterminated'):
            with self.assertRaises(ValueError):
                scanner.lex(text)

    def test_macro_fn_tokens_are_lexical_not_functions(self):
        result = scanner.inspect_file(b'macro_rules! make { () => { fn x() {} } }')
        self.assertEqual(result['lexical_fn_tokens'], 1)
        self.assertEqual(result['exact_eligible'], 0)

    def test_numeric_and_pattern_limits(self):
        for value in ('12', '12u64', '1__2u32', '4294967296u32', '012u32'):
            self.assertIsNone(scanner.canonical_u32(value))
        result = scanner.inspect_file(b'let a: u32 = 12u32; call(); let b: u32 = 23u32;')
        self.assertEqual(result['potential_literal_declarations'], 2)
        self.assertEqual(result['potential_adjacent_runs'], 0)

    def test_exact_shape_still_has_unknown_boundary(self):
        result = scanner.inspect_file(scanner.carrier.fixture(2).encode())
        self.assertEqual(result['exact_whole_file_grammar_shape'], 1)
        self.assertEqual(result['exact_eligible'], 0)
        self.assertEqual(result['exact_boundary'], 'not_established')

    def test_inline_test_markers_are_only_lexical_flags(self):
        result = scanner.inspect_file(b'#[cfg(test)] mod tests { #[test] fn demo() {} }')
        self.assertEqual(result['markers']['inline_test_marker_tokens'], 2)

    def test_inventory_path_traversal_and_ancestor_symlinks_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            # macOS /var may itself be a symlink; use a resolved trusted temp root.
            root = root.resolve()
            (root/'real').mkdir()
            (root/'linked').symlink_to(root/'real', target_is_directory=True)
            for path in ('../outside.rs', '/outside.rs', 'src/../outside.rs', 'src//x.rs', './x.rs', 'linked/x.rs'):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    scanner.safe_path(root, path)


if __name__ == '__main__':
    unittest.main()
