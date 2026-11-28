from pathlib import Path
import unittest,json,csv,os
import numpy as np
r=Path(__file__).resolve().parent
j=json.loads((r/'diagnosis.json').read_text());baseline=json.loads((r/'baseline-artifact/comparison.json').read_text())
def independent_hash(b,median,greater_equal=False):
 bits=b>=median if greater_equal else b>median
 return f'{sum(int(bit)<<k for k,bit in enumerate(bits.flat)):064x}'
def accept(b,median,expected):
 assert median==float(np.sort(b.flat)[127]),'median'
 assert independent_hash(b,median)==expected,'bits'
class TraceChecks(unittest.TestCase):
 def test_all_observed_variants_and_csv_accounting(self):
  count=0
  for case,base in zip(j['cases'],baseline['cases']):
   d=r/'traces'/case['id']
   with (d/'affected-bits.csv').open() as f:rows=list(csv.DictReader(f))
   self.assertEqual(len(rows),sum(v['differentBits'] for v in case['variants']))
   for k,v in enumerate(case['variants']):
    b=np.fromfile(d/f'B-{k}.f32',dtype='<f4').reshape(16,16);accept(b,v['cppMedian'],base['cpp']['hashes'][v['name']]);count+=1
    pb=np.fromfile(d/'py-B.f64',dtype='<f8').reshape(16,16)
    # Check CSV against exact recorded scalar margins and selected bit indices.
    entries=[row for row in rows if row['variant']==v['name']]
    self.assertEqual([int(row['bitIndex']) for row in entries],v['indices'])
    for row in entries:
     i,k2=int(row['row']),int(row['col']);self.assertEqual(float(row['cppCoefficient']),float(b[i,k2]));self.assertEqual(float(row['cppMargin']),float(b[i,k2])-v['cppMedian']);self.assertNotEqual(row['cppBit'],row['pythonBit'])
  self.assertEqual(count,48)
 def test_changed_observation_rejected(self):
  base=baseline['cases'][3];d=r/'traces'/base['id'];b=np.fromfile(d/'B-0.f32',dtype='<f4').reshape(16,16);m=j['cases'][3]['variants'][0]['cppMedian'];b.flat[0]=float(b.max())
  with self.assertRaises(AssertionError):accept(b,m,base['cpp']['hashes']['orig'])
 def test_wrong_variant_rejected(self):
  base=baseline['cases'][3];b=np.fromfile(r/'traces/asymmetric/B-1.f32',dtype='<f4').reshape(16,16);m=j['cases'][3]['variants'][1]['cppMedian']
  with self.assertRaises(AssertionError):accept(b,m,base['cpp']['hashes']['orig'])
 def test_tie_rule_negative(self):
  b=np.zeros((16,16));self.assertEqual(independent_hash(b,0),'0'*64);self.assertNotEqual(independent_hash(b,0,True),'0'*64)
 def test_baseline_and_probe_accounting(self):
  self.assertEqual(j['baseline']['cppHashesExact'],32);self.assertEqual(j['baseline']['cppQualityExact'],6)
  self.assertEqual([c['id'] for c in j['cases']],['black','constant127','low-contrast','asymmetric','wide','tall'])
  for c in j['cases']:
   self.assertTrue(c['instrumentationUnchanged']);self.assertEqual(c['probes']['cpp-D-f32']['cppExactVariants'],8)
   self.assertEqual(c['probes']['cpp-D-f32']['BvsCpp']['different'],0)
   for n in ['rows-0','cols-0','rows-1','cols-1','A']:self.assertEqual(c['stages'][n]['different'],0)
if __name__=='__main__':unittest.main(verbosity=2)
