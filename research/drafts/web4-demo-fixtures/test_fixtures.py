import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import check

class FixtureTests(unittest.TestCase):
    def test_committed(self):
        self.assertEqual(check.check(),3)

    def test_corruptions(self):
        mutations=[('recipes.json',lambda d:d['cases'].pop()),
                   ('recipes.json',lambda d:d['cases'].append(copy.deepcopy(d['cases'][0]))),
                   ('recipes.json',lambda d:d['cases'][0].update(sampleSha256='0'*64)),
                   ('expected.json',lambda d:d['cases'][1]['modes']['normalized']['outcome'].update({'class':'no-match'})),
                   ('expected.json',lambda d:d['cases'][2]['modes']['exact']['outcome'].update({'class':'no-match'})),
                   ('config/comparison-config.json',lambda d:d.update(minRegionDistinctHashes=99)),
                   ('evidence/run.json',lambda d:d['cli']['rust']['version'].update(stamp='unstamped')),
                   ('evidence/run.json',lambda d:d['commands'][0].update(exit=1)),
                   ('evidence/run.json',lambda d:d['cases'][0]['artifacts']['go'].update({'body.json':'0'*64})),
                   ('evidence/run.json',lambda d:d['commands'].pop())]
        for name,mutate in mutations:
            with self.subTest(file=name),tempfile.TemporaryDirectory() as tmp:
                target=Path(tmp)/'package';shutil.copytree(HERE,target,ignore=shutil.ignore_patterns('__pycache__'))
                p=target/name;d=json.loads(p.read_bytes());mutate(d);p.write_text(json.dumps(d))
                with self.assertRaises(ValueError):check.check(target)

    def assert_run_rejected(self, mutate, message):
        # Both entry points must reject the same corrupted retained run without
        # executing a CLI. The other package evidence stays byte-identical.
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'package'
            shutil.copytree(HERE,target,ignore=shutil.ignore_patterns('__pycache__'))
            p=target/'evidence/run.json';data=json.loads(p.read_bytes())
            mutate(data);p.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,message):check.check(target)
            with self.assertRaisesRegex(ValueError,message):check.verify_replay(target/'evidence')

    def test_static_replay_acceptance(self):
        check.verify_replay(HERE/'evidence')

    def test_cli_metadata_gaps(self):
        mutations=[('missing identities',lambda d:d.pop('cli')),
                   ('empty identities',lambda d:d.update(cli={})),
                   ('missing Go',lambda d:d['cli'].pop('go')),
                   ('missing Rust',lambda d:d['cli'].pop('rust')),
                   ('extra identity',lambda d:d['cli'].update(other=copy.deepcopy(d['cli']['go']))),
                   ('missing version',lambda d:d['cli']['rust'].pop('version')),
                   ('missing binary digest',lambda d:d['cli']['go'].pop('sha256')),
                   ('wrong digest',lambda d:d['cli']['rust'].update(sha256='0'*64)),
                   ('missing stamp',lambda d:d['cli']['rust']['version'].pop('stamp')),
                   ('wrong stamp',lambda d:d['cli']['go']['version'].update(stamp='unstamped')),
                   ('wrong name',lambda d:d['cli']['go']['version']['implementation'].update(name='traceweave')),
                   ('wrong commit',lambda d:d['cli']['rust']['version']['implementation'].update(commit='0'*40)),
                   ('wrong spec',lambda d:d['cli']['go']['version'].update(specCommit='0'*40))]
        for label,mutate in mutations:
            with self.subTest(corruption=label):self.assert_run_rejected(mutate,'CLI|binary')

    def test_command_coverage_gaps(self):
        def duplicate_all(d):
            d['commands']=[copy.deepcopy(d['commands'][0]) for _ in range(160)]
        def substitute_one(d):d['commands'][5]=copy.deepcopy(d['commands'][0])
        def swap(d):d['commands'][0],d['commands'][1]=d['commands'][1],d['commands'][0]
        def substitute_case(d):d['commands'][40:60]=copy.deepcopy(d['commands'][0:20])
        mutations=[('review duplicated 160 records',duplicate_all),
                   ('one duplicate, count unchanged',substitute_one),
                   ('reordered operations',swap),
                   ('substitute case block, count unchanged',substitute_case),
                   ('missing command list',lambda d:d.pop('commands')),
                   ('missing command',lambda d:d['commands'].pop()),
                   ('wrong native CLI',lambda d:d['commands'][10].update(cli='rust')),
                   ('missing stdout flag',lambda d:d['commands'][2]['argv'].__delitem__(slice(-2,None))),
                   ('wrong Go stdin',lambda d:d['commands'][10].update(stdinSha256='0'*64)),
                   ('wrong extract output',lambda d:d['commands'][0].update(stdoutSha256='0'*64)),
                   ('wrong catalogue output',lambda d:d['commands'][2].update(stdoutSha256='0'*64)),
                   ('wrong body output',lambda d:d['commands'][8].update(stdoutSha256='0'*64)),
                   ('missing output digest',lambda d:d['commands'][1].pop('stdoutSha256')),
                   ('malformed stderr digest',lambda d:d['commands'][1].update(stderrSha256='invalid')),
                   ('unsuccessful validation',lambda d:d['commands'][1].update(exit=1))]
        for label,mutate in mutations:
            with self.subTest(corruption=label):self.assert_run_rejected(mutate,'command')

if __name__=='__main__':unittest.main()
