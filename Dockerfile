FROM python:3.6
### https://github.com/janza/docker-python3-opencv/blob/opencv_contrib/Dockerfile

ENV APP_DIR /app

COPY install.sh $APP_DIR/

WORKDIR $APP_DIR

### install os packages:
RUN ./install.sh

WORKDIR /

RUN pip install --no-cache-dir numpy
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


COPY requirements.txt $APP_DIR/

WORKDIR $APP_DIR

RUN pip install --no-cache-dir -r requirements.txt

COPY . $APP_DIR/

CMD ["python3", "main.py" ]
