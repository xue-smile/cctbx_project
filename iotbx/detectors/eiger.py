from __future__ import division
from iotbx.detectors.detectorbase import DetectorImageBase

class EIGERImage(DetectorImageBase):
  def __init__(self,filename,index=0):
    DetectorImageBase.__init__(self,filename)
    self.vendortype = "EigerX"
    self.supports_multiple_images = True
    self.img_number = index # 0-indexed to clients, internally 1-indexed
    if self.img_number == None: self.img_number = 0
    self.vendor_specific_null_value = -1

  mandatory_keys = ['PIXEL_SIZE_UNITS', 'DISTANCE', 'WAVELENGTH', 'SIZE1',
    'SIZE2', 'TWOTHETA', 'DISTANCE_UNITS', 'OSC_RANGE',
    'BEAM_CENTER_X', 'BEAM_CENTER_Y',
    'CCD_IMAGE_SATURATION', 'OSC_START', 'PIXEL_SIZE']

  def readHeader(self,dxtbx_instance,maxlength=12288): # XXX change maxlength!!!
    if not self.parameters:

      self.parameters={'CCD_IMAGE_SATURATION':65535}
      D = dxtbx_instance.get_detector()
      self.parameters['PIXEL_SIZE'] = D[0].get_pixel_size()[0]
      self.parameters['PIXEL_SIZE_UNITS'] = "mm"
      self.parameters['DISTANCE'] = D[0].get_distance()
      self.parameters['DISTANCE_UNITS'] = "mm"
      self.parameters['SIZE1'] = D[0].get_image_size()[1]
      self.parameters['SIZE2'] = D[0].get_image_size()[0]
      B = dxtbx_instance.get_beam()
      beam_center = D[0].get_beam_centre_lab(B.get_s0())
      self.parameters['BEAM_CENTER_X'] = beam_center[1]
      self.parameters['BEAM_CENTER_Y'] = beam_center[0]
      self._image_count = dxtbx_instance.get_num_images()
      self.parameters['WAVELENGTH'] = B.get_wavelength()
      from scitbx.matrix import col
      detector_normal = D[0].get_normal()
      tt_angle_deg = col(detector_normal).angle(col((0.,0.,1.)),deg=True)
      assert tt_angle_deg < 0.01 # assert normal to within 0.01 degree
      self.parameters['TWOTHETA'] = 0.0

      S = dxtbx_instance.get_scan()
      osc_range = S.get_oscillation()[1]
      self.parameters['OSC_RANGE'] = osc_range
      self.parameters['OSC_START'] = S.get_oscillation()[0] + self.img_number*osc_range

      #these parameters have to be set here due to the call to image_coords_as_detector_cords below.  they are normally set later.
      if self.parameters.has_key("SIZE2"):
        self.image_size_fast = self.size2
      if self.parameters.has_key("SIZE1"):
        self.image_size_slow = self.size1
      if self.parameters.has_key("PIXEL_SIZE"):
        self.pixel_resolution = self.pixel_size

      if self.size1==4371 and self.size2==4150:
        self.vendortype="Eiger-16M"
      elif self.size1==3269 and self.size2==3110:
        self.vendortype="Eiger-9M"
      elif self.size1==2167 and self.size2==2070:
        self.vendortype="Eiger-4M"
      elif self.size1==1065 and self.size2==2030:
        self.vendortype="Eiger-1M"
      dxtbx_instance.vendortype = self.vendortype

  def read(self):
      image = self.get_raw_data_callback(self,self.img_number)
      self.bin_safe_set_data(image)

  def image_count(self):
    return self._image_count

  def integerdepth(self):
    return 2

  def dataoffset(self):
    return 0
