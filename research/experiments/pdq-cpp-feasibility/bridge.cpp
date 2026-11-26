// Local raw-luma bridge; upstream PDQ core is compiled unchanged.
#include <pdq/cpp/hashing/pdqhashing.h>
#include <cfenv>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <vector>
using namespace facebook::pdq::hashing;
uint32_t read32(std::ifstream& in) {
  unsigned char b[4];
  if (!in.read(reinterpret_cast<char*>(b),4)) throw std::runtime_error("truncated input");
  return uint32_t(b[0]) | (uint32_t(b[1])<<8) | (uint32_t(b[2])<<16) | (uint32_t(b[3])<<24);
}
int main(int argc,char** argv) {
  static_assert(sizeof(float)==4 && std::numeric_limits<float>::is_iec559 && std::numeric_limits<float>::digits==24,"binary32 required");
  if (argc!=2) return 2;
  try {
    if (std::fesetround(FE_TONEAREST)!=0) throw std::runtime_error("rounding setup failed");
    std::ifstream in(argv[1],std::ios::binary);
    char magic[8];
    if (!in.read(magic,8) || std::memcmp(magic,"TWLUMA1\0",8)) throw std::runtime_error("bad header");
    int cols=read32(in),rows=read32(in);
    if (rows<32 || cols<32 || rows>128 || cols>128) throw std::runtime_error("outside declared smoke dimensions");
    std::vector<float> a(rows*cols),b(rows*cols);
    for(float& v:a) {
      uint32_t bits=read32(in); std::memcpy(&v,&bits,4);
      if (!std::isfinite(v) || v<0 || v>255 || v!=std::floor(v)) throw std::runtime_error("integer luma required");
    }
    if (in.peek()!=std::char_traits<char>::eof()) throw std::runtime_error("trailing bytes");
    float b64[64][64],b16x64[16][64],b16[16][16],aux[16][16];
    Hash256 hashes[8];int quality=-1;
    bool ok=pdqDihedralHash256esFromFloatLuma(a.data(),b.data(),rows,cols,b64,b16x64,b16,aux,
      &hashes[0],&hashes[1],&hashes[2],&hashes[3],&hashes[4],&hashes[5],&hashes[6],&hashes[7],quality);
    if(!ok) throw std::runtime_error("core refused input");
    const char* names[]={"orig","rot90","rot180","rot270","flipx","flipy","flipp","flipm"};
    std::cout<<"{\"quality\":"<<quality<<",\"hashes\":{";
    for(int j=0;j<8;j++) {
      if(j)std::cout<<",";
      std::cout<<"\""<<names[j]<<"\":\"";
      for(int i=15;i>=0;i--)std::cout<<std::hex<<std::setfill('0')<<std::setw(4)<<hashes[j].w[i];
      std::cout<<"\"";
    }
    std::cout<<"},\"floatDigits\":"<<std::dec<<std::numeric_limits<float>::digits
             <<",\"doubleDigits\":"<<std::numeric_limits<double>::digits<<",\"roundNearest\":"
             <<(std::fegetround()==FE_TONEAREST?"true":"false")<<"}\n";
  } catch(const std::exception& e) {std::cerr<<e.what()<<"\n";return 2;}
}
