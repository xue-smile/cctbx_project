// $Id$
/* Copyright (c) 2001 The Regents of the University of California through
   E.O. Lawrence Berkeley National Laboratory, subject to approval by the
   U.S. Department of Energy. See files COPYRIGHT.txt and
   cctbx/LICENSE.txt for further details.

   Revision history:
     2001 May 31: merged from CVS branch sgtbx_type (R.W. Grosse-Kunstleve)
     Apr 2001: SourceForge release (R.W. Grosse-Kunstleve)
 */

#include <ctype.h> // cannot use cctype b/o non-conforming compilers
#include <cctbx/eltbx/basic.h>

namespace cctbx { namespace eltbx {

  std::string StripLabel(const std::string& Label, bool Exact)
  {
    std::string result;
    std::string::const_iterator l;
    for (l = Label.begin(); l != Label.end(); l++) {
      if (!isspace(*l)) break;
    }
    char digit = '\0';
    for (; l != Label.end(); l++) {
      if (isspace(*l)) {
        break;
      }
      if (isdigit(*l)) {
        if (digit != '\0') break;
        digit = *l;
      }
      else if (*l == '+' || *l == '-') {
        if (digit == '\0')
            digit = '1';
        result += digit;
        result += *l++;
        break;
      }
      else if (digit != '\0') {
        break;
      }
      else {
        result += toupper(*l);
      }
    }
    if (Exact && l != Label.end() && !isspace(*l)) {
      return "";
    }
    return result;
  }

  int MatchLabels(const std::string& WorkLabel, const char* TabLabel)
  {
    int i;
    for (i = 0; i < WorkLabel.size() && TabLabel[i]; i++)
      if (WorkLabel[i] != toupper(TabLabel[i])) break;
    if (i == WorkLabel.size() && TabLabel[i] == '\0') return -i;
    if (i == 1 && isalpha(TabLabel[1])) return 0;
    return i;
  }

}} // namespace cctbx::eltbx
