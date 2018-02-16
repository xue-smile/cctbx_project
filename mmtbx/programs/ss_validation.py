# -*- coding: utf-8 -*-
from __future__ import division, print_function

import os

from libtbx import group_args
from libtbx.program_template import ProgramTemplate

from mmtbx.secondary_structure import ss_validation

# =============================================================================

class Program(ProgramTemplate):

  description = '''
phenix.secondary_structure_validation: tool for validation of secondary
  structure annotations.

Usage examples:
  phenix.secondary_structure_validation model.pdb
  phenix.secondary_structure_validation model.cif
  phenix.secondary_structure_validation model.pdb nproc=7
  '''

  datatypes = ['model', 'phil']

  master_phil_str = '''
ss_validation {
  nproc = 1
    .type = int
  bad_hbond_cutoff = 3.5
    .type = float
  mediocre_hbond_cutoff = 3.0
    .type = float
  filter_annotation = False
    .type = bool
    .help = Output filtered annotations
}
'''

  # ---------------------------------------------------------------------------
  def validate(self):
    print('Validating inputs', file=self.logger)
    self.data_manager.has_models(raise_sorry=True)

  # ---------------------------------------------------------------------------
  def run(self):
    # I'm guessing self.data_manager, self.params and self.logger
    # are already defined here...
    print('Using model: %s' % self.data_manager.get_default_model_name())
    # print(dir(self.params))

    # this must be mmtbx.model.manager?
    model = self.data_manager.get_model()

    self.results = ss_validation.run(pdb_inp=model.get_model_input(),
        pdb_hierarchy=model.get_hierarchy(),
        cs=model.crystal_symmetry(),
        params = self.params.ss_validation,
        out = self.logger)


  # ---------------------------------------------------------------------------
  def get_results(self):
    return self.results

# =============================================================================
# end