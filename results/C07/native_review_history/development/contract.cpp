#include <cstddef>
#include <cstdint>

// Only the existing real polynomial contraction; no likelihood or new model.
// Arrays are contiguous C-order. Caller validates dimensions and node indices.
extern "C" void contract_moments(
    std::size_t n, std::size_t kcount, std::size_t d,
    const std::int64_t* segment, const double* fraction,
    const double* pg, const double* pr, const double* pw,
    const double* meanbank, const double* covbank,
    double* mean, double* cov) {
  for (std::size_t i=0; i<n; ++i) {
    const double f=fraction[i];
    for (std::size_t k=0; k<kcount; ++k) {
      const auto ik=i*kcount+k;
      const double g=pg[ik];
      const double w[6]={g,g*f,g*f*f,g*f*f*f,pr[ik],pw[ik]};
      double* mu=mean+ik*d;
      double* sigma=cov+ik*d*d;
      for(std::size_t a=0;a<d;++a) mu[a]=0;
      for(std::size_t a=0;a<d*d;++a) sigma[a]=0;
      const double* mb=meanbank+(segment[i]*kcount+k)*6*d;
      for(std::size_t s=0;s<6;++s)
        for(std::size_t a=0;a<d;++a) mu[a]+=w[s]*mb[s*d+a];
      const double* cb=covbank+(segment[i]*kcount+k)*21*d*d;
      std::size_t pair=0;
      for(std::size_t s=0;s<6;++s) {
        for(std::size_t t=s;t<6;++t,++pair) {
          const double weight=w[s]*w[t];
          for(std::size_t a=0;a<d*d;++a)
            sigma[a]+=weight*cb[pair*d*d+a];
        }
      }
    }
  }
}
