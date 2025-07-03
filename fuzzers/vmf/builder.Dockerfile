ARG parent_image
FROM $parent_image as deps

RUN  apt-get update \
     && DEBIAN_FRONTEND="noninteractive" apt-get install -y --no-install-recommends --fix-missing \
       ca-certificates \
       curl \
       gdb \
       git \
       gnupg \
       lsb-core \
       lsb-release \
       zip

RUN lsb_release -a | grep -q "18.04" && ( \
      echo "deb http://apt.llvm.org/bionic/ llvm-toolchain-bionic-12 main" >> /etc/apt/sources.list && \
      curl -L https://apt.llvm.org/llvm-snapshot.gpg.key | apt-key add - \
    ) || \
    (lsb_release -a | grep -q "20.04") || \
    (lsb_release -a | grep -q "22.04") || (echo "Ubuntu 18.04, 20.04, or 22.04 required!!!" >&2; exit 1)

RUN  apt-get update \
     && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends --fix-missing \
       graphviz \
       doxygen \
       libcurl4-openssl-dev \
       python3-dev \
       python3-pip \
       python3-setuptools \
       build-essential \
       cmake

# ENV  LLVM_CONFIG=llvm-config-12
# RUN set -ex \
#     && cd `$LLVM_CONFIG --bindir` \
#     && for f in *; do rm -f /usr/bin/$f; ln -s ../lib/llvm-12/bin/$f /usr/bin/$f; done \
#     && set +ex

#RUN set -ex \
#    && apt-get update && apt-get install -y gcc-9-plugin-dev --fix-missing \
#    && set +ex

FROM deps AS aflpp

RUN apt-get update && \
    apt-get install -y \
        build-essential \
        python3-dev \
        python3-setuptools \
        automake \
        cmake \
        git \
        flex \
        bison \
        libglib2.0-dev \
        libpixman-1-dev \
        cargo \
        libgtk-3-dev \
        # for QEMU mode
        ninja-build \
        gcc-$(gcc --version|head -n1|sed 's/\..*//'|sed 's/.* //')-plugin-dev \
        libstdc++-$(gcc --version|head -n1|sed 's/\..*//'|sed 's/.* //')-dev --fix-missing

# Clone and build AFL++
RUN set -ex \
  && git clone -b dev https://github.com/AFLplusplus/AFLplusplus.git /AFLplusplus \
  && cd /AFLplusplus \
  && git checkout 56d5aa3101945e81519a3fac8783d0d8fad82779 \
  && unset CFLAGS CXXFLAGS \
  && export CC=clang AFL_NO_X86=1 \
  && PYTHON_INCLUDE=/ make -j \
  && cp utils/aflpp_driver/libAFLDriver.a / \
  && set +ex

FROM aflpp AS vmf

# Clone, build, install VMF
RUN set -ex \
    && git clone --depth 1 https://github.com/draperlaboratory/vadermodularfuzzer.git /vmf \
    && cd /vmf \
    && mkdir -p build \
    && cd build \
    && cmake .. \
    && make -j \
    && make install \
    && set +ex
