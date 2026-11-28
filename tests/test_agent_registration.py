"""Bounded illustrative SK checker regressions; no protocol client or service runs."""
import ast
import copy
import importlib.util
import json
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'test-vectors/registration'
spec = importlib.util.spec_from_file_location('agent_registration_checker', FOLDER / 'check_registration.py')
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)


def fixture(name):
    return json.loads((FOLDER / 'fixtures' / (name + '.json')).read_text())


def checked(doc):
    return C.check_object(doc['fixture']['kind'], doc['object'], doc['fixture'])


class AgentRegistrationTests(unittest.TestCase):
    def test_valid_descriptions_and_digest_request(self):
        for name in ['a2a-card-local-registrar', 'a2a-card-hosted-witness', 'mcp-tool-register', 'a2a-request-witness']:
            with self.subTest(name=name):
                self.assertEqual(checked(fixture(name)), set())

    def test_each_complete_notice_in_each_description(self):
        for name, indices in [('a2a-card-local-registrar', [0, 1]),
                              ('a2a-card-hosted-witness', [0]), ('mcp-tool-register', [None])]:
            for index in indices:
                for sentence in [*C.REQUIRED_SENTENCES, C.AGENT_SENTENCE]:
                    doc = fixture(name)
                    desc = doc['object'] if index is None else doc['object']['skills'][index]
                    desc['description'] = desc['description'].replace(sentence, '')
                    with self.subTest(name=name, index=index, sentence=sentence):
                        self.assertEqual(checked(doc), {'notice-missing'})
                doc = fixture(name)
                desc = doc['object'] if index is None else doc['object']['skills'][index]
                desc['description'] = 42
                self.assertEqual(checked(doc), {'notice-missing'})

    def test_notice_elsewhere_or_incomplete_does_not_cover_missing_skill_text(self):
        doc = fixture('a2a-card-local-registrar')
        self.assertIn(C.AGENT_SENTENCE, doc['object']['description'])
        desc = doc['object']['skills'][1]
        desc['description'] = desc['description'].replace(C.AGENT_SENTENCE, C.AGENT_SENTENCE[:-1])
        self.assertEqual(checked(doc), {'notice-missing'})

    def request(self, parts):
        doc = fixture('a2a-request-witness')
        doc['object']['message']['parts'] = parts
        return doc

    def test_unsupported_content_alone_extra_and_permuted(self):
        data = fixture('a2a-request-witness')['object']['message']['parts'][0]
        for part in [{'text': 'source text'}, {'raw': 'c291cmNl'}, {'url': 'https://content.example.invalid/a'}]:
            for parts in [[part], [data, part], [part, data], [data, part, data]]:
                with self.subTest(parts=parts):
                    self.assertEqual(checked(self.request(parts)), {'content-on-wire'})

    def test_malformed_oneof_count_body_and_digest(self):
        data = fixture('a2a-request-witness')['object']['message']['parts'][0]
        for parts in [[], None, 'not-an-array', [None], [{}], [dict(data, text='two variants')],
                      [dict(data, unknown=True)], [data, data], [{'data': []}]]:
            with self.subTest(parts=parts):
                self.assertEqual(checked(self.request(parts)), {'a2a-shape'})
        for digest in ['0' * 63, '0' * 65, '0' * 64 + '\n', 10 ** 63, None]:
            doc = fixture('a2a-request-witness')
            doc['object']['message']['parts'][0]['data']['presented']['sha256'] = digest
            self.assertEqual(checked(doc), {'a2a-shape'})

    def test_deterministic_multi_fault_precedence(self):
        data = fixture('a2a-request-witness')['object']['message']['parts'][0]
        doc = self.request([data, {'text': 'unsupported'}])
        doc['object']['message']['role'] = 'ROLE_AGENT'
        self.assertEqual(checked(doc), {'a2a-shape'})
        for parts in [[dict(data, text='mixed'), {'raw': 'eA=='}],
                      [{'raw': 'eA=='}, dict(data, text='mixed')]]:
            self.assertEqual(checked(self.request(parts)), {'a2a-shape'})
        bad = copy.deepcopy(data)
        bad['data']['requestVersion'] = 'wrong'
        bad['data']['presented']['sha256'] = '0' * 64
        self.assertEqual(checked(self.request([bad, {'text': 'unsupported'}])), {'content-on-wire'})
        bad['data']['fingerprints'] = ['content-derived']
        self.assertEqual(checked(self.request([bad])), {'forbidden-field'})
        del bad['data']['fingerprints']
        self.assertEqual(checked(self.request([bad])), {'a2a-shape'})
        bad['data']['requestVersion'] = C.WITNESS_REQUEST_VERSION
        self.assertEqual(checked(self.request([bad])), {'evidence-wrong-target'})

    def test_version_drift_remains_explicit_and_generic_parts_unchanged(self):
        doc = fixture('a2a-request-witness')
        self.assertEqual(checked(doc), set())
        doc['object']['message']['parts'][0]['data']['requestVersion'] = 'traceweave-witness-request-draft-1'
        self.assertEqual(checked(doc), {'a2a-shape'})  # I4 pending normative choice, no silent version change.
        out = set()
        C.check_wire_parts([{'text': 'generic A2A text'}], out)
        self.assertEqual(out, set())

    def test_selected_pure_builders_reproduce_description_fixtures(self):
        tree = ast.parse((FOLDER / 'build_fixtures.py').read_text())
        selected = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef)
                                   and n.name in {'local_card', 'hosted_card', 'mcp_tool', 'write', 'build_agent_checker_negatives'}], type_ignores=[])
        ns = {'C': C, 'LIMIT': ' '.join([*C.REQUIRED_SENTENCES, C.AGENT_SENTENCE]),
              'EXT': {'uri': C.A2A_EXTENSION, 'description': 'Traceweave registration profile (proposed; not published).', 'required': True}}
        exec(compile(selected, 'pure illustrative description builders', 'exec'), ns)
        for name, fn in [('a2a-card-local-registrar', 'local_card'), ('a2a-card-hosted-witness', 'hosted_card'), ('mcp-tool-register', 'mcp_tool')]:
            self.assertEqual(fixture(name)['object'], ns[fn]())
        # Reproduce only the ten illustrative mutations in a tiny temporary tree,
        # never importing the builder module or rebuilding signed/frozen vectors.
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / 'fixtures').mkdir()
            for name in ['a2a-card-local-registrar', 'mcp-tool-register', 'a2a-request-witness']:
                (target / 'fixtures' / (name + '.json')).write_bytes((FOLDER / 'fixtures' / (name + '.json')).read_bytes())
            ns.update(HERE=target, json=json, copy=copy)
            ns['build_agent_checker_negatives']()
            negatives = list((target / 'negative').glob('*.json'))
            self.assertEqual(len(negatives), 10)
            for path in negatives:
                self.assertEqual(path.read_bytes(), (FOLDER / 'negative' / path.name).read_bytes())


if __name__ == '__main__':
    unittest.main(verbosity=2)
