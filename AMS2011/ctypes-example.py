from ctypes import cdll, Structure, POINTER, c_float, c_double, c_int

class RadarStatus(Structure):
    _fields_ = [('time',c_double),
                ('az_pointing',c_float),
                ('cos_az',c_float),
                ('sin_az',c_float),
                ('el_pointing',c_float),
                ('cos_el',c_float),
                ('sin_el',c_float),
                ('cur_az_ind',c_int),
                ('cur_el_ind',c_int)]
from ctypes import cdll
_rslib = cdll.LoadLibrary('_librs.so')

radar_scan = _rslib.RS_radar_scan
radar_scan.argtypes = [POINTER(RadarStatus)]
radar_scan.restype = c_int
