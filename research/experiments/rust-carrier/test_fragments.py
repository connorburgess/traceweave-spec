"""Regression tests for closed-host alignment, ambiguity and original byte spans."""
import unittest
from unittest.mock import patch

import experiment as carrier
import fragment_experiment as fragment


class FragmentTests(unittest.TestCase):
    def setUp(self):
        self.reference = carrier.fixture(4)
        self.marked = carrier.embed(self.reference, 'spelling', 5)[0]

    def test_original_utf8_function_and_literal_coordinates(self):
        source = fragment.host([('copied', self.marked)])
        result = fragment.align(self.reference, source, 'spelling')
        self.assertEqual(result['state'], 5)
        begin, end = result['function_span_bytes']
        self.assertEqual(source.encode()[begin:end].decode(), self.marked.rstrip())
        self.assertEqual(begin, len(source[:source.index('fn specimen')].encode()))
        self.assertNotEqual(begin, source.index('fn specimen'))
        expected = [('a', '1_2u32', 1), ('b', '23u32', 0), ('c', '3_4u32', 1), ('d', '45u32', 0)]
        for symbol, (name, text, bit) in zip(result['symbols'], expected):
            start, finish = symbol['span_bytes']
            self.assertEqual((symbol['name'], source.encode()[start:finish].decode(), symbol['raw']), (name, text, bit))

    def test_order_span_is_original_declaration_run(self):
        marked = carrier.embed(self.reference, 'order', 23)[0]
        source = fragment.host([('copied', marked)])
        result = fragment.align(self.reference, source, 'order')
        begin, end = result['symbols'][0]['span_bytes']
        self.assertEqual(source.encode()[begin:end].decode(), 'let d: u32 = 45u32; let c: u32 = 34u32; let b: u32 = 23u32; let a: u32 = 12u32;')

    def test_duplicate_and_conflicting_anchors_abstain_before_context_selection(self):
        for second in (self.marked, self.reference):
            result = fragment.align(self.reference, fragment.host([('origin', self.marked), ('other', second)]), 'spelling', 'origin')
            self.assertEqual(result['matching_anchors'], 2)
            self.assertEqual(result['reason'], 'ambiguous_reference_anchors')
            self.assertEqual(result['symbols'], [])

    def test_changed_context_open_recovers_strict_abstains(self):
        source = fragment.host([('moved', self.marked)])
        self.assertEqual(fragment.align(self.reference, source, 'spelling')['state'], 5)
        result = fragment.align(self.reference, source, 'spelling', 'origin')
        self.assertEqual((result['state'], result['reason']), (None, 'context_mismatch'))
        self.assertEqual(result['symbols'], [])

    def test_same_context_signal_only_transfer_decodes_without_authentication(self):
        for family, state in [('order', 23), ('spelling', 5)]:
            donor = carrier.embed(self.reference, family, state)[0]
            independent = fragment.independent_source(family, donor)
            self.assertNotEqual(independent, donor)
            result = fragment.align(self.reference, fragment.host([('origin', independent)]), family, 'origin')
            self.assertEqual(result['state'], state)

    def test_independent_same_task_natural_state_is_not_identity(self):
        source = fragment.host([('origin', fragment.independent_source('spelling'))])
        self.assertEqual(fragment.align(self.reference, source, 'spelling', 'origin')['state'], 0)

    def test_transferred_signal_with_changed_values_fails_reference_anchor(self):
        for family, state in [('order', 23), ('spelling', 5)]:
            donor = carrier.embed(self.reference, family, state)[0]
            source = fragment.host([('origin', fragment.independent_source(family, donor, changed_values=True))])
            result = fragment.align(self.reference, source, family, 'origin')
            self.assertEqual(result['reason'], 'no_complete_reference_anchor')
            self.assertEqual(result['symbols'], [])

    def test_incomplete_run_never_becomes_full_reference_rank(self):
        source = fragment.host([('partial', carrier.fixture(3))])
        result = fragment.align(self.reference, source, 'order')
        self.assertEqual(result['reason'], 'no_complete_reference_anchor')
        self.assertEqual(result['symbols'], [])

    def test_partial_copy_preserves_surviving_donor_symbols_but_abstains(self):
        _, cases = fragment.make_cases()
        for family, state in [('order', 23), ('spelling', 15)]:
            case = next(c for c in cases if c['family'] == family and c['donor_state'] == state and c['category'] == 'incomplete_run')
            bindings, _ = carrier.parse(fragment.host_nodes(case['candidate'])[0]['source'], carrier.BOUNDARY)
            if family == 'order':
                self.assertEqual([n for n, _, _ in bindings], ['c', 'b', 'a'])
            else:
                self.assertTrue(all('_' in t for _, _, t in bindings))
            self.assertEqual(fragment.align(self.reference, case['candidate'], family)['symbols'], [])

    def test_direct_return_same_task_has_no_carrier(self):
        source = fragment.host([('origin', 'fn specimen() -> [u32; 4] { [12u32,23u32,34u32,45u32] }')])
        self.assertEqual(fragment.align(self.reference, source, 'spelling')['reason'], 'no_complete_reference_anchor')

    def test_cut_excerpt_and_malformed_lists_abstain(self):
        bad_sources = [self.marked[self.marked.index('let '):],
                       *(fragment.host([('origin', self.reference.replace('[a, b, c, d]', text))])
                         for text in ('[a,,b,c,d]', '[,a,b,c,d]', '[abcd]'))]
        for source in bad_sources:
            with self.subTest(source=source):
                self.assertEqual(fragment.align(self.reference, source, 'spelling')['status'], 'abstain')

    def test_unexpected_spelling_erases_rather_than_zero(self):
        source = fragment.host([('origin', self.reference.replace('12u32', '1__2u32'))])
        result = fragment.align(self.reference, source, 'spelling')
        self.assertEqual((result['state'], result['reason']), (None, 'unexpected spelling'))

    def test_return_sequence_and_value_are_reference_anchor_components(self):
        for changed in (self.reference.replace('12u32', '13u32'), self.reference.replace('[a, b, c, d]', '[b, a, c, d]')):
            result = fragment.align(self.reference, fragment.host([('origin', changed)]), 'spelling')
            self.assertEqual(result['reason'], 'no_complete_reference_anchor')

    def test_observer_syntax_anywhere_invalidates_entire_closed_host(self):
        source = fragment.host([('origin', self.marked)])
        for extra in ('include!("anything.rs");', 'macro_rules! reader { () => {} }', '#[observer] mod elsewhere {}', '// arbitrary comment'):
            result = fragment.align(self.reference, source+extra, 'spelling')
            self.assertEqual(result['status'], 'abstain')
            self.assertEqual(result['symbols'], [])

    def test_unknown_family_and_changed_boundary_refused(self):
        source = fragment.host([('origin', self.marked)])
        self.assertEqual(fragment.align(self.reference, source, 'unknown')['reason'], 'unknown carrier family')
        self.assertEqual(fragment.align(self.reference, source, 'spelling', boundary=carrier.BOUNDARY | {'source_observers': True})['reason'], 'unsupported build/source boundary')

    def test_duplicate_module_and_non_ascii_outside_fixed_banner_refused(self):
        sources = [fragment.host([('origin', self.marked), ('origin', self.marked)]),
                   fragment.host([('origin', self.marked)])+'\u00a0']
        for source in sources:
            self.assertEqual(fragment.align(self.reference, source, 'spelling')['status'], 'abstain')

    def test_reserved_and_nonallowlisted_module_names_refused(self):
        for name in ('mod', 'fn', 'self', 'arbitrary'):
            source = fragment.host([(name, self.marked)])
            self.assertEqual(fragment.align(self.reference, source, 'spelling')['status'], 'abstain')

    def test_invalid_direct_return_decimal_forms_refused(self):
        for literal in ('012u32', '4294967296u32', '1__2u32', '12u32u32'):
            text = f'fn specimen() -> [u32; 4] {{ [{literal},23u32,34u32,45u32] }}'
            self.assertEqual(fragment.align(self.reference, fragment.host([('origin', text)]), 'spelling')['status'], 'abstain')

    def test_alignment_never_invokes_compiler_or_subprocess(self):
        with patch.object(carrier, 'run', side_effect=AssertionError('alignment executed a command')):
            result = fragment.align(self.reference, fragment.host([('origin', self.marked)]), 'spelling')
            self.assertEqual(result['state'], 5)

    def test_compilation_oracle_does_not_follow_changed_candidate_values(self):
        _, cases = fragment.make_cases()
        case = next(c for c in cases if c['family'] == 'order' and c['donor_state'] == 0 and c['category'] == 'whole_copy')
        corrupted = dict(case, candidate=case['candidate'].replace('12u32', '13u32'))
        with patch.object(carrier, 'run') as command:
            with self.assertRaises(AssertionError):
                fragment.compile_generated_cases([corrupted])
            command.assert_not_called()

    def test_matrix_results_are_deterministic_and_cover_expected_outcomes(self):
        reference, cases = fragment.make_cases()
        self.assertEqual(len(cases), 72)
        for case in cases:
            result = fragment.align(reference, case['candidate'], case['family'], case['expected_context'])
            self.assertEqual(result, fragment.align(reference, case['candidate'], case['family'], case['expected_context']))
            self.assertEqual((result['state'], result['reason']), (case['expected_state'], case['expected_reason']))


if __name__ == '__main__':
    unittest.main()
