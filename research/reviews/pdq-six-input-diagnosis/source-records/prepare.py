from pathlib import Path
import shutil,hashlib,json,difflib
r=Path(__file__).resolve().parent
src=r/'baseline-run-root/source'; dst=r/'instrumented-source';shutil.copytree(src,dst)
helper='''
#include <fstream>
#include <cstdlib>
#include <string>
static void trace(const std::string& name, const float* a, size_t n) {
 const char* d=std::getenv("PDQ_TRACE"); if(!d) std::abort();
 std::ofstream out(std::string(d)+"/"+name+".f32",std::ios::binary);
 out.write(reinterpret_cast<const char*>(a),n*sizeof(float)); if(!out) std::abort();
}
'''
p=dst/'pdq/cpp/hashing/pdqhashing.cpp';s=p.read_text();s=helper+s
s=s.replace('  const auto& D = dct_matrix_64;','  const auto& D = dct_matrix_64;\n  trace("D", D.data(), 1024);\n  trace("A", &A[0][0], 4096);')
s=s.replace('      T[i][j] = sumk;\n    }\n  }','      T[i][j] = sumk;\n    }\n  }\n  trace("T", &T[0][0], 1024);')
s=s.replace('  float dct_median = torben(&dctOutput16x16[0][0], 16 * 16);','  float dct_median = torben(&dctOutput16x16[0][0], 16 * 16);\n  static int variant=0;\n  trace("B-"+std::to_string(variant), &dctOutput16x16[0][0], 256);\n  trace("median-"+std::to_string(variant++), &dct_median, 1);')
p.write_text(s)
p=dst/'pdq/cpp/downscaling/downscaling.cpp';s=helper+p.read_text();s=s.replace('    boxAlongColsFloat(buffer2, buffer1, numRows, numCols, windowSizeAlongCols);','    trace("rows-"+std::to_string(i), buffer2, numRows*numCols);\n    boxAlongColsFloat(buffer2, buffer1, numRows, numCols, windowSizeAlongCols);\n    trace("cols-"+std::to_string(i), buffer1, numRows*numCols);');p.write_text(s)
patch=''.join(''.join(difflib.unified_diff((src/p.relative_to(dst)).read_text().splitlines(True),p.read_text().splitlines(True),fromfile='baseline/'+str(p.relative_to(dst)),tofile='instrumented/'+str(p.relative_to(dst)))) for p in dst.rglob('*.cpp') if p.read_bytes()!=(src/p.relative_to(dst)).read_bytes())
(r/'instrumentation.patch').write_text(patch)
files=[r/'prepare.py',r/'instrumentation.patch',*dst.rglob('*')]
(r/'prebuild-identities.json').write_text(json.dumps({str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()},indent=2)+'\n')
