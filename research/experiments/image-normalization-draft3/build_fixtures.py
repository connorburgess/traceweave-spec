"""Explicit fixture builder. Expected outputs come only from the mathematical oracle."""
import hashlib
import json
from pathlib import Path
import oracle

HERE = Path(__file__).resolve().parent


def flat(a):
    return bytes(v for row in a for v in row)


def make():
    cases = []
    shapes = [('black',32,32), ('white',32,32), ('swatches',32,32),
              ('identity',32,32), ('width-only',47,32), ('height-only',32,47),
              ('noninteger',37,41), ('order-equality',48,64),
              ('vertical-first',48,65), ('wide',65,48), ('edge',9,7),
              ('single-column',1,9), ('single-row',9,1), ('single-pixel',1,1)]
    for name, w, h in shapes:
        rgb = []
        for y in range(h):
            row = []
            for x in range(w):
                if name == 'black': p = (0,0,0)
                elif name == 'white': p = (255,255,255)
                elif name == 'swatches':
                    p = [(255,0,0),(0,255,0),(0,0,255),(1,0,0),(0,1,0),
                         (0,0,1),(128,128,128),(255,255,255)][x % 8]
                elif name == 'edge': p = (255,255,255) if x == 0 or y == 0 else (0,0,0)
                else:
                    p = ((17*x+31*y+7*x*y)%256, (73*x+11*y+3*x*y)%256,
                         (29*x+53*y+13*x*y)%256)
                row.append(p)
            rgb.append(row)
        grey = oracle.grey(rgb)
        out, first, order = oracle.resize(grey)
        raw = bytes(v for row in rgb for p in row for v in p)
        cases.append(dict(id=name,width=w,height=h,rgbHex=raw.hex(),greyHex=flat(grey).hex(),
                          order=order,firstHex=flat(first).hex(),outputHex=flat(out).hex()))
    sizes = sorted({n for c in cases for n in [c['width'],c['height']] if n!=32})
    tables = {str(n): oracle.weights(n) for n in sizes}
    return dict(fixtureVersion='image-normalization-draft3-fixtures-1',
                derivation='computed-mathematical-oracle-not-hand-derived',
                coefficientSha256=hashlib.sha256(json.dumps(tables,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
                cases=cases)


if __name__ == '__main__':
    (HERE/'fixtures.json').write_text(json.dumps(make(),indent=2)+'\n')
