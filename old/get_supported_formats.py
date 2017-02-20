import ioctl.linux
import struct
import fcntl

dev = open('/dev/video0')
fd = dev.fileno()

"""
type v4l2_fmtdesc struct {
    index       uint32
    _type       uint32
    flags       uint32
    description [32]uint8
    pixelformat uint32
    reserved    [4]uint32
}

type v4l2_frmsizeenum struct {
    index        uint32
    pixel_format uint32 // corresponds to VIDIOC_ENUM_FMT 
    _type        uint32
    union        [24]uint8
    reserved     [2]uint32
}

"""
# c code for this:
# _IOWR('V',  2, struct v4l2_fmtdesc)
v4l2_fmtdesc_fmt = 'IIIBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBIIIII'
v4l2_fmtdesc = struct.calcsize(v4l2_fmtdesc_fmt)

VIDIOC_ENUM_FMT = ioctl.linux.IOWR('V', 2, v4l2_fmtdesc)
V4L2_BUF_TYPE_VIDEO_CAPTURE = 1

v4l2_frmsizeenum_fmt = 'IIIBBBBBBBBBBBBBBBBBBBBBBBBII'
v4l2_frmsizeenum = struct.calcsize(v4l2_frmsizeenum_fmt)
VIDIOC_ENUM_FRAMESIZES = ioctl.linux.IOWR('V', 74, v4l2_frmsizeenum)


### both supported formats -- iterate over first value until exception to get all of them:
fcntl.ioctl(fd, VIDIOC_ENUM_FMT, struct.pack(v4l2_fmtdesc_fmt, 0, 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0))
fcntl.ioctl(fd, VIDIOC_ENUM_FMT, struct.pack(v4l2_fmtdesc_fmt, 1, 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0))

## resolutions:
i=0
resolutions = []
while True:
  try:
    res = fcntl.ioctl(fd, VIDIOC_ENUM_FRAMESIZES, struct.pack(v4l2_frmsizeenum_fmt,i,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0))
    resolutions.append(res)
    i += 1
  except Exception as e:
    print('e: %s' % e)
    break

"""
_IOC = lambda d,t,nr,size: (d << _IOC_DIRSHIFT) | (ord(t) << _IOC_TYPESHIFT) | \
     (nr << _IOC_NRSHIFT) | (size << _IOC_SIZESHIFT)
_IOWR = lambda t,nr,size: _IOC(_IOC_READ | _IOC_WRITE, t, nr, size)
VIDIOC_ENUM_FMT = _IOWR('V', 2, v4l2_fmtdesc)
"""

