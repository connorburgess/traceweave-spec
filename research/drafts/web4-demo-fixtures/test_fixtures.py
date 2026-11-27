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

if __name__=='__main__':unittest.main()
