// $Id$
/* Copyright (c) 2001 The Regents of the University of California through
   E.O. Lawrence Berkeley National Laboratory, subject to approval by the
   U.S. Department of Energy. See files COPYRIGHT.txt and
   cctbx/LICENSE.txt for further details.

   Revision history:
     Apr 2001: SourceForge release (R.W. Grosse-Kunstleve)
 */

#ifndef CCTBX_ELTBX_WAVELENGTHS_H
#define CCTBX_ELTBX_WAVELENGTHS_H

#include <string>
#include <cctbx/constants.h>

namespace cctbx { namespace eltbx {

  namespace detail {
    struct RawWaveLength {
      const char* Label;
      float       lambda;
    };
  }

  //! Characteristic wavelengths of commonly used x-ray tube target materials.
  class WaveLength {
    public:
      //! Default constructor. Calling certain methods may cause crashes!
      WaveLength() : m_RawEntry(0) {}
      //! Get i'th entry in the internal table.
      /*! Can be used to iterate over all entries.
       */
      explicit
      WaveLength(int i);
      //! Lookup characteristic wavelength for given label.
      /*! The lookup is not case-sensitive.
       */
      WaveLength(const std::string& Label);
      //! Return label.
      const char* Label() const { return m_RawEntry->Label; }
      //! Return wavelength (Angstrom).
      float operator()() const { return m_RawEntry->lambda; }
      //! Return energy (keV).
      float Energy() const {
        if (m_RawEntry->lambda == 0.) return 0.;
        return cctbx::constants::factor_keV_Angstrom / m_RawEntry->lambda;
      }
    private:
      const detail::RawWaveLength* m_RawEntry;
  };

}} // cctbx::eltbx

#endif // CCTBX_ELTBX_WAVELENGTHS_H
