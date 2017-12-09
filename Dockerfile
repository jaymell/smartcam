FROM python:3.6
### https://github.com/janza/docker-python3-opencv/blob/opencv_contrib/Dockerfile
RUN echo 'deb http://ftp.uk.debian.org/debian jessie-backports main' >> /etc/apt/sources.list
RUN apt-get update && \
        apt-get install -y \
        build-essential \
        cmake \
        git \
        wget \
        unzip \
        yasm \
        ffmpeg \
        pkg-config \
        libswscale-dev \
        libtbb2 \
        libtbb-dev \
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
        libavl-dev

RUN pip install numpy
WORKDIR /
RUN wget https://github.com/opencv/opencv_contrib/archive/3.3.0.zip \
&& unzip 3.3.0.zip \
&& rm 3.3.0.zip
RUN wget https://github.com/opencv/opencv/archive/3.3.0.zip \
&& unzip 3.3.0.zip \
&& mkdir /opencv-3.3.0/cmake_binary \
&& cd /opencv-3.3.0/cmake_binary \
&& cmake -DBUILD_TIFF=ON \
  -DBUILD_opencv_java=OFF \
  -DOPENCV_EXTRA_MODULES_PATH=/opencv_contrib-3.3.0/modules \
  -DWITH_CUDA=OFF \
  -DENABLE_AVX=ON \
  -DWITH_OPENGL=ON \
  -DWITH_FFMPEG=ON \
  -DWITH_OPENCL=ON \
  -DWITH_IPP=ON \
  -DWITH_TBB=ON \
  -DWITH_EIGEN=ON \
  -DWITH_V4L=ON \
  -DBUILD_TESTS=OFF \
  -DBUILD_PERF_TESTS=OFF \
  -DCMAKE_BUILD_TYPE=RELEASE \
  -DCMAKE_INSTALL_PREFIX=$(python3.6 -c "import sys; print(sys.prefix)") \
  -DPYTHON_EXECUTABLE=$(which python3.6) \
  -DPYTHON_INCLUDE_DIR=$(python3.6 -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())") \
  -DPYTHON_PACKAGES_PATH=$(python3.6 -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())") .. \
&& make install \
&& rm /3.3.0.zip \
&& rm -r /opencv-3.3.0

ENV APP_DIR /app
WORKDIR $APP_DIR

COPY requirements.txt $APP_DIR/

RUN pip install -r requirements.txt

COPY . $APP_DIR/

CMD ["python3", "main.py" ]
