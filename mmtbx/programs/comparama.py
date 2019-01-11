# -*- coding: utf-8 -*-
from __future__ import division, print_function

from libtbx.program_template import ProgramTemplate

from mmtbx.validation import comparama
from mmtbx.validation.ramalyze import res_type_labels

from matplotlib.backends.backend_pdf import PdfPages

# =============================================================================

class Program(ProgramTemplate):

  description = '''
phenix.comparama: tool for compare Ramachandran plots, e.g. before-after
  refinement.

Usage examples:
  phenix.comparama model1.pdb model2.pdb
  phenix.comparama model1.cif model2.cif
  '''

  datatypes = ['model', 'phil']

  master_phil_str = """\
    include scope mmtbx.validation.comparama.master_phil_str
    output
    {
      individual_residues = True
        .type = bool
      sorted_individual_residues = False
        .type = bool
      counts = True
        .type = bool
      prefix = kleywegt
        .type = str
      plots = False
        .type = bool
        .help = output Kleywegt plots - arrows on Rama plot showing where \
          residues moved.
      pdf = True
        .type = bool
        .help = save the same plots as one pdf file
    }
"""

  # ---------------------------------------------------------------------------
  def validate(self):
    print('Validating inputs', file=self.logger)
    self.data_manager.has_models(expected_n=2, exact_count=True, raise_sorry=True)
    model_1, model_2 = self._get_models()
    assert model_1.get_hierarchy().is_similar_hierarchy(model_2.get_hierarchy())
    for m in [model_1, model_2]:
      assert m.get_hierarchy().models_size() == 1

  # ---------------------------------------------------------------------------
  def run(self):
    # I'm guessing self.data_manager, self.params and self.logger
    # are already defined here...
    # print('Using model: %s' % self.data_manager.get_default_model_name(), file=self.logger)

    # this must be mmtbx.model.manager?
    model_1, model_2 = self._get_models()

    self.rama_comp = comparama.rcompare(
        model1 = model_1,
        model2 = model_2,
        params = self.params.comparama,
        log = self.logger)

    # outputting results
    results = self.rama_comp.get_results()
    res_columns = zip(*results)
    if self.params.output.individual_residues:
      for r in results:
        self.show_single_result(r)
      print("="*80, file=self.logger)
    if self.params.output.sorted_individual_residues:
      sorted_res = sorted(results, key=lambda tup: tup[1])
      for r in sorted_res:
        self.show_single_result(r)
      print("="*80, file=self.logger)

    nr = self.rama_comp.get_number_results()
    print ("mean: %.3f std: %.3f" % (nr.mean_diff, nr.std_diff), file=self.logger)
    print("Sum of rama scores: \t\t\t %.3f -> %.3f" % (nr.sum_1, nr.sum_2) , file=self.logger)
    print("Sum of rama scores/n_residues:\t\t %.4f -> %.4f (%d residues)" % \
        (nr.sum_1/nr.n_res, nr.sum_2/nr.n_res, nr.n_res), file=self.logger)
    print("Sum of rama scores scaled:\t\t %.3f -> %.3f" % \
        (nr.scaled_sum_1, nr.scaled_sum_2) , file=self.logger)
    print("Sum of rama scores/n_residues scaled:\t %.4f -> %.4f (%d residues)" % \
        (nr.scaled_sum_1/nr.n_res, nr.scaled_sum_2/nr.n_res, nr.n_res), file=self.logger)

    if self.params.output.counts:
      for k, v in nr.counts.iteritems():
        print("%-20s: %d" % (k,v), file=self.logger)

    base_fname = "%s--%s" % (self.data_manager.get_model_names()[0].split('.')[0],
        self.data_manager.get_model_names()[1].split('.')[0])

    if self.params.output.plots:
      for pos, plot in self.rama_comp.get_plots().iteritems():
        file_label = res_type_labels[pos].replace("/", "_")
        plot_file_name = "%s_%s_%s_plot.png" % (
            base_fname, self.params.output.prefix, file_label)
        print("saving: '%s'" % plot_file_name)
        plot.save_image(plot_file_name, dpi=300)

    if self.params.output.pdf:
      pdf_fname = "%s_%s.pdf" % (base_fname, self.params.output.prefix)
      pdfp = PdfPages(pdf_fname)
      for pos, plot in self.rama_comp.get_plots().iteritems():
        pdfp.savefig(plot.figure)
      print("saving: '%s'" % pdf_fname)
      pdfp.close()

  def show_single_result(self, r):
    print("%s %.2f, (%.1f:%.1f), (%.1f:%.1f), %s, Score: %.4f -> %.4f" % \
        (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[8], r[9]),
        file=self.logger)

  # ---------------------------------------------------------------------------
  def get_results(self):
    return self.rama_comp.get_results()

  def _get_models(self):
    m_names = self.data_manager.get_model_names()
    model_1 = self.data_manager.get_model(filename=m_names[0])
    model_2 = self.data_manager.get_model(filename=m_names[1])
    return model_1, model_2
