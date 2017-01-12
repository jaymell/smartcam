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
"""

# _IOWR('V',  2, struct v4l2_fmtdesc)

v4l2_fmtdesc = struct.calcsize('!III%sIIIII' % 'B'*32)

# golang returns this: 3225441794
# but following returns this: 3296744962
VIDIOC_ENUM_FMT = ioctl.linux.IOWR('V', 2, v4l2_fmtdesc)

my_str=""
fcntl.ioctl(fd, VIDIOC_ENUM_FMT, my_str)

