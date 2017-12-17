#!/bin/bash -xe

PACKAGES=(build-essential \
        cmake \
        git \
        wget \
        unzip \
        yasm \
        ffmpeg \
        pkg-config \
        libswscale-dev \
        libjpeg-dev \
        libpng-dev \
        libtiff-dev \
        libjasper-dev \
        libpq-dev \
        libavformat-dev \
        libavcodec-dev \
        libavdevice-dev \
        libavfilter-dev \
        libavformat-dev \
        libavresample-dev \
        libavutil-dev \
        libswscale-dev \
        libavc1394-dev \
	libavl-dev)

function compile_tbb() {
  pushd /tmp
  wget https://github.com/01org/tbb/archive/2018_U2.tar.gz -O - | tar xvzf - 
  cd tbb-2018_U2/
  make tbb CXXFLAGS="-DTBB_USE_GCC_BUILTINS=1 -D__TBB_64BIT_ATOMICS=0" 
  pushd build/linux_armv7_gcc_cc6.3.0_libc2.24_kernel4.9.59_release/
  source tbbvars.sh
  popd
  popd
  rm -rf tbb-2018_U2/
}

ARCH=$(uname -m)
[[ $ARCH = "armv7l" ]] && compile_tbb || PACKAGES+=(libtbb2 libtbb-dev)

echo 'deb http://ftp.uk.debian.org/debian jessie-backports main' >> /etc/apt/sources.list

apt-get update && \
  apt-get install -y \
    ${PACKAGES[@]} && \
  rm -rf /var/lib/apt/lists/*
