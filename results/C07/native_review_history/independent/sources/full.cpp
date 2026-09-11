#include <cstddef>
#include <cstdint>
#include <cmath>
#include <complex>
using C=std::complex<double>;
extern "C" std::int64_t full_likelihood(
 std::size_t n,std::size_t nd,std::size_t K,std::size_t P,std::size_t D,
 const std::int64_t* seg,const double* frac,const std::int64_t* targets,
 const double* pg,const double* pr,const double* pw,
 const double* means,const double* covpacked,const C* gamma,
 const double* red2,const double* white2,const double* freqweights,
 const C* q,const double* y,const double* z,double* result){
 if(P>16||D>16||K>8)return -1;
 const std::size_t triangle=D*(D+1)/2;
 constexpr double pi=3.141592653589793238462643383279502884;
 for(std::size_t nrow=0;nrow<n;++nrow){
  auto model=targets[nrow]/nd,id=targets[nrow]%nd;
  const double f=frac[nrow];double answer=0;
  if(model==0){
   for(std::size_t k=0;k<K;++k){
    const auto nk=nrow*K+k;C L[16*16]={},v[16];
    auto offset=seg[nrow]*4*K*P*P+k*P*P;
    for(std::size_t a=0;a<P;++a){
     for(std::size_t b=0;b<=a;++b){
      auto ab=a*P+b;C g=gamma[offset+ab]+f*(gamma[offset+K*P*P+ab]+f*(gamma[offset+2*K*P*P+ab]+f*gamma[offset+3*K*P*P+ab]));
      C value=pg[nk]*g;
      if(a==b)value+=pr[nk]*red2[a]+pw[nk]*white2[a];
      for(std::size_t j=0;j<b;++j)value-=L[a*P+j]*std::conj(L[b*P+j]);
      if(a==b){if(!(value.real()>0)||!std::isfinite(value.real()))return nrow+1;L[ab]=std::sqrt(value.real());}
      else L[ab]=value/L[b*P+b].real();
     }
     C value=q[(id*K+k)*P+a];
     for(std::size_t j=0;j<a;++j)value-=L[a*P+j]*v[j];
     v[a]=value/L[a*P+a].real();
     answer-=std::norm(v[a])+2*std::log(L[a*P+a].real())+std::log(pi);
    }
   }
  }else{
   double mu[8*16]={},cv[8*136]={};
   bool compressed=(model==2||model==4);auto kind=(model>=3)?1:0;
   for(std::size_t k=0;k<K;++k){
    auto nk=nrow*K+k;double g=pg[nk],w[6]={g,g*f,g*f*f,g*f*f*f,pr[nk],pw[nk]};
    auto out=compressed?0:k;double wm=compressed?freqweights[k]:1.,wc=wm*wm;
    const auto offset=seg[nrow]*K+k;
    const double* mb=means+offset*6*D;const double* cb=covpacked+offset*21*triangle;
    for(std::size_t s=0;s<6;++s)
     for(std::size_t a=0;a<D;++a)mu[out*D+a]+=wm*w[s]*mb[s*D+a];
    std::size_t pair=0;
    for(std::size_t s=0;s<6;++s)
     for(std::size_t t=s;t<6;++t,++pair){
      double val=wc*w[s]*w[t];
      for(std::size_t a=0;a<triangle;++a)cv[out*triangle+a]+=val*cb[pair*triangle+a];
     }
   }
   for(std::size_t k=0;k<(compressed?1:K);++k){
    double L[16*16]={},v[16];std::size_t pair=0;
    for(std::size_t a=0;a<D;++a){
     for(std::size_t b=0;b<=a;++b,++pair){
      double value=cv[k*triangle+pair];
      for(std::size_t j=0;j<b;++j)value-=L[a*D+j]*L[b*D+j];
      if(a==b){if(!(value>0)||!std::isfinite(value))return nrow+1;L[a*D+b]=std::sqrt(value);}
      else L[a*D+b]=value/L[b*D+b];
     }
     double value=(compressed?z[(kind*nd+id)*D+a]:y[((kind*nd+id)*K+k)*D+a])-mu[k*D+a];
     for(std::size_t j=0;j<a;++j)value-=L[a*D+j]*v[j];
     v[a]=value/L[a*D+a];
     answer-=.5*(v[a]*v[a]+2*std::log(L[a*D+a])+std::log(2*pi));
    }
   }
  }
  result[nrow]=answer;
 }
 return 0;
}
