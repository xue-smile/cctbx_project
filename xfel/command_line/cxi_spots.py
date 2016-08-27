from __future__ import division
# LIBTBX_SET_DISPATCHER_NAME cxi.spots
# LIBTBX_PRE_DISPATCHER_INCLUDE_SH PHENIX_GUI_ENVIRONMENT=1
# LIBTBX_PRE_DISPATCHER_INCLUDE_SH export PHENIX_GUI_ENVIRONMENT
# LIBTBX_PRE_DISPATCHER_INCLUDE_SH export BOOST_ADAPTBX_FPE_DEFAULT=1

from xfel.cxi.display_spots import run_one
import sys,os

if (__name__ == "__main__"):
  files = [arg for arg in sys.argv[1:] if os.path.isfile(arg)]
  arguments = [arg for arg in sys.argv[1:] if not os.path.isfile(arg)]
  for file in files:
    run_one(file, *arguments, **({'display':True}))
