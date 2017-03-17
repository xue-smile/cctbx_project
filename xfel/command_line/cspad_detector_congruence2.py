#!/usr/bin/env python
# -*- mode: python; coding: utf-8; indent-tabs-mode: nil; python-indent: 2 -*-
#
# detector_congruence.py
#
#  Copyright (C) 2016 Lawrence Berkeley National Laboratory (LBNL)
#
#  Author: Aaron Brewster
#
#  This code is distributed under the X license, a copy of which is
#  included in the root directory of this package.
#
# LIBTBX_SET_DISPATCHER_NAME cspad.detector_congruence2
#
from __future__ import division
from dials.array_family import flex
from scitbx.matrix import col
from matplotlib import pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.colors import Normalize
from matplotlib import cm
import numpy as np
from libtbx.phil import parse
import libtbx.load_env
import math

help_message = '''

This program is used to calculate statisical measurements of consistency
between two detectors.

Example:

  %s experiment1.json experiment2.json reflections1.pickle reflections2.pickle
''' % libtbx.env.dispatcher_name

# Create the phil parameters
phil_scope = parse('''
tag = None
  .type = str
  .help = Used in the plot titles
hierarchy_level=0
  .type=int
  .help=Provide congruence statistics for detector modules at the given hierarchy level.
colormap=RdYlGn_r
  .type=str
  .help=matplotlib color map. See e.g.: \
        http://matplotlib.org/examples/color/colormaps_reference.html
show_plots=False
  .type=bool
  .help=Whether to show congruence plots
draw_normal_arrows=False
  .type=bool
  .help=Whether to draw the XY components of each panel group's normal vector. Useful \
        for visualizing tilt.
''')

def iterate_detector_at_level(item, depth = 0, level = 0):
  """
  Iterate through all panel groups or panels of a detector object at a given
  hierarchy level
  @param item panel group or panel. Use detector.hierarchy().
  @param depth current dept for recursion. Should be 0 for initial call.
  @param level iterate groups at this level
  @return next panel or panel group object
  """
  if level == depth:
    yield item
  else:
    for child in item:
      for subitem in iterate_detector_at_level(child, depth+1, level):
        yield subitem

def iterate_panels(panelgroup):
  """
  Find and iterate all panels in the given panel group, regardless of the hierarchly level
  of this panelgroup
  @param panelgroup the panel group of interest
  @return the next panel
  """
  if panelgroup.is_group():
    for child in panelgroup:
      for subitem in iterate_panels(child):
        yield subitem
  else:
    yield panelgroup

def id_from_name(detector, name):
  """ Jiffy function to get the id of a panel using its name
  @param detector detector object
  @param name panel name
  @return index of panel in detector
  """
  return [p.get_name() for p in detector].index(name)

def get_center(pg):
  """ Find the center of a panel group pg, projected on its fast/slow plane """
  if pg.is_group():
    # find the average center of all this group's children
    children_center = col((0,0,0))
    count = 0
    for p in iterate_panels(pg):
      children_center += get_center(p)
      count += 1
    children_center /= count

    # project the children center onto the plane of the panel group
    pgf = col(pg.get_fast_axis())
    pgs = col(pg.get_slow_axis())
    pgn = col(pg.get_normal())
    pgo = col(pg.get_origin())

    return (pgf.dot(children_center) * pgf) + (pgs.dot(children_center) * pgs) + (pgn.dot(pgo) * pgn)
  else:
    s = pg.get_image_size()
    return col(pg.get_pixel_lab_coord((s[0]/2, s[1]/2)))

def get_bounds(root, pg):
  """ Find the max extent of the panel group pg, projected onto the fast/slow plane of root """
  def panel_bounds(root, panel):
    size = panel.get_image_size()
    p0 = col(panel.get_pixel_lab_coord((0,0)))
    p1 = col(panel.get_pixel_lab_coord((size[0]-1,0)))
    p2 = col(panel.get_pixel_lab_coord((size[0]-1,size[1]-1)))
    p3 = col(panel.get_pixel_lab_coord((0,size[1]-1)))

    rn = col(root.get_normal())
    rf = col(root.get_fast_axis())
    rs = col(root.get_slow_axis())

    return [col((p.dot(rf), + p.dot(rs),0)) for p in [p0, p1, p2, p3]]

  if pg.is_group():
    minx = miny = float('inf')
    maxx = maxy = float('-inf')
    for panel in iterate_panels(pg):
      bounds = panel_bounds(root, panel)
      for v in bounds:
        if v[0] < minx:
          minx = v[0]
        if v[0] > maxx:
          maxx = v[0]
        if v[1] < miny:
          miny = v[1]
        if v[1] > maxy:
          maxy = v[1]
    return [col((minx, miny, 0)),
            col((maxx, miny, 0)),
            col((maxx, maxy, 0)),
            col((minx, maxy, 0))]

  else:
    return panel_bounds(root, pg)


class Script(object):
  ''' Class to parse the command line options. '''

  def __init__(self):
    ''' Set the expected options. '''
    from dials.util.options import OptionParser
    import libtbx.load_env

    # Create the option parser
    usage = "usage: %s experiment1.json experiment2.json reflections1.pickle reflections2.pickle" % libtbx.env.dispatcher_name
    self.parser = OptionParser(
      usage=usage,
      sort_options=True,
      phil=phil_scope,
      read_experiments=True,
      read_datablocks=True,
      read_reflections=True,
      epilog=help_message)

  def run(self):
    ''' Parse the options. '''
    from dials.util.options import flatten_experiments, flatten_datablocks, flatten_reflections
    # Parse the command line arguments
    params, options = self.parser.parse_args(show_diff_phil=True)
    self.params = params
    experiments = flatten_experiments(params.input.experiments)
    datablocks = flatten_datablocks(params.input.datablock)
    reflections = flatten_reflections(params.input.reflections)

    # Find all detector objects
    detectors = []
    detectors.extend(experiments.detectors())
    dbs = []
    for datablock in datablocks:
      dbs.extend(datablock.unique_detectors())
    detectors.extend(dbs)

    # Verify inputs
    if len(detectors) != 2:
      print "Please provide two experiments and or datablocks for comparison"
      return

    # These lines exercise the iterate_detector_at_level and iterate_panels functions
    # for a detector with 4 hierarchy levels
    """
    print "Testing iterate_detector_at_level"
    for level in xrange(4):
      print "iterating at level", level
      for panelg in iterate_detector_at_level(detectors[0].hierarchy(), 0, level):
        print panelg.get_name()

    print "Testing iterate_panels"
    for level in xrange(4):
      print "iterating at level", level
      for panelg in iterate_detector_at_level(detectors[0].hierarchy(), 0, level):
        for panel in iterate_panels(panelg):
          print panel.get_name()
    """
    tmp = []
    for refls in reflections:
      print "N reflections total:", len(refls)
      refls = refls.select(refls.get_flags(refls.flags.used_in_refinement))
      print "N reflections used in refinement", len(refls)
      print "Reporting only on those reflections used in refinement"

      refls['difference_vector_norms'] = (refls['xyzcal.mm']-refls['xyzobs.mm.value']).norms()
      tmp.append(refls)
    reflections = tmp

    s0 = col(flex.vec3_double([col(b.get_s0()) for b in experiments.beams()]).mean())

    # Compute a set of radial and transverse displacements for each reflection
    print "Setting up stats..."
    tmp_refls = []
    for refls, expts in zip(reflections, [wrapper.data for wrapper in params.input.experiments]):
      tmp = flex.reflection_table()
      assert len(expts.detectors()) == 1
      dect = expts.detectors()[0]
      # Need to construct a variety of vectors
      for panel_id, panel in enumerate(dect):
        panel_refls = refls.select(refls['panel'] == panel_id)
        bcl = flex.vec3_double()
        # Compute the beam center in lab space (a vector pointing from the origin to where the beam would intersect
        # the panel, if it did intersect the panel)
        for expt_id in set(panel_refls['id']):
          beam = expts[expt_id].beam
          s0_ = beam.get_s0()
          expt_refls = panel_refls.select(panel_refls['id'] == expt_id)
          beam_centre = panel.get_beam_centre_lab(s0_)
          bcl.extend(flex.vec3_double(len(expt_refls), beam_centre))
        panel_refls['beam_centre_lab'] = bcl

        # Compute obs in lab space
        x, y, _ = panel_refls['xyzobs.mm.value'].parts()
        c = flex.vec2_double(x, y)
        panel_refls['obs_lab_coords'] = panel.get_lab_coord(c)
        # Compute deltaXY in panel space. This vector is relative to the panel origin
        x, y, _ = (panel_refls['xyzcal.mm'] - panel_refls['xyzobs.mm.value']).parts()
        # Convert deltaXY to lab space, subtracting off of the panel origin
        panel_refls['delta_lab_coords'] = panel.get_lab_coord(flex.vec2_double(x,y)) - panel.get_origin()
        tmp.extend(panel_refls)
      refls = tmp
      # The radial vector points from the center of the reflection to the beam center
      radial_vectors = (refls['obs_lab_coords'] - refls['beam_centre_lab']).each_normalize()
      # The transverse vector is orthogonal to the radial vector and the beam vector
      transverse_vectors = radial_vectors.cross(refls['beam_centre_lab']).each_normalize()
      # Compute the raidal and transverse components of each deltaXY
      refls['radial_displacements']     = refls['delta_lab_coords'].dot(radial_vectors)
      refls['transverse_displacements'] = refls['delta_lab_coords'].dot(transverse_vectors)

      tmp_refls.append(refls)
    reflections = tmp_refls

    refl_counts = {}
    rmsds_table_data = []
    pg_bc_dists = flex.double()
    root1 = detectors[0].hierarchy()
    root2 = detectors[1].hierarchy()

    for pg_id, (pg1, pg2) in enumerate(zip(iterate_detector_at_level(root1, 0, params.hierarchy_level),
                                           iterate_detector_at_level(root2, 0, params.hierarchy_level))):
      """ First compute statistics for detector congruence """
      # Count up the number of reflections in this panel group pair for use as a weighting scheme
      total_refls = 0
      pg1_refls = 0
      pg2_refls = 0
      for p1, p2 in zip(iterate_panels(pg1), iterate_panels(pg2)):
        r1 = len(reflections[0].select(reflections[0]['panel'] == id_from_name(detectors[0], p1.get_name())))
        r2 = len(reflections[1].select(reflections[1]['panel'] == id_from_name(detectors[1], p2.get_name())))
        total_refls += r1 + r2
        pg1_refls += r1
        pg2_refls += r2
      if pg1_refls == 0 and pg2_refls == 0:
        print "No reflections on panel group", pg_id
        continue

      assert pg1.get_name() == pg2.get_name()
      refl_counts[pg1.get_name()] = total_refls

      row = ["%d"%pg_id]
      for pg, refls, det in zip([pg1, pg2], reflections, detectors):
        pg_refls = flex.reflection_table()
        for p in iterate_panels(pg):
          pg_refls.extend(refls.select(refls['panel'] == id_from_name(det, p.get_name())))
        if len(pg_refls) == 0:
          rmsd = r_rmsd = t_rmsd = 0
        else:
          rmsd = math.sqrt(flex.sum_sq(pg_refls['difference_vector_norms'])/len(pg_refls))*1000
          r_rmsd = math.sqrt(flex.sum_sq(pg_refls['radial_displacements'])/len(pg_refls))*1000
          t_rmsd = math.sqrt(flex.sum_sq(pg_refls['transverse_displacements'])/len(pg_refls))*1000

        row.extend(["%6.1f"%rmsd, "%6.1f"%r_rmsd, "%6.1f"%t_rmsd, "%8d"%len(pg_refls)])
      rmsds_table_data.append(row)

      dists = flex.double()
      for pg, r in zip([pg1, pg2], [root1, root2]):
        bc = col(pg.get_beam_centre_lab(s0))
        ori = get_center(pg)

        dists.append((ori-bc).length())

      pg_weights = flex.double([pg1_refls, pg2_refls])
      if 0 in pg_weights:
        dist_m = dist_s = 0
      else:
        stats = flex.mean_and_variance(dists, pg_weights)
        dist_m = stats.mean()
        dist_s = stats.gsl_stats_wsd()

      pg_bc_dists.append(dist_m)


    table_d = {d:row for d, row in zip(pg_bc_dists, rmsds_table_data)}
    table_header = ["PanelG"]
    table_header2 = ["Id"]
    table_header3 = [""]
    for i in xrange(len(detectors)):
      table_header.extend(["D%d"%i]*4)
      table_header2.extend(["RMSD", "rRMSD", "tRMSD", "N refls"])
      table_header3.extend(["(microns)"]*3)
      table_header3.append("")
    rmsds_table_data = [table_header, table_header2, table_header3]
    rmsds_table_data.extend([table_d[key] for key in sorted(table_d)])

    row = ["Overall"]
    for refls in reflections:
      row.append("%6.1f"%(math.sqrt(flex.sum_sq(refls['difference_vector_norms'])/len(refls))*1000))
      row.append("%6.1f"%(math.sqrt(flex.sum_sq(refls['radial_displacements'])/len(refls))*1000))
      row.append("%6.1f"%(math.sqrt(flex.sum_sq(refls['transverse_displacements'])/len(refls))*1000))
      row.append("%8d"%len(refls))
    rmsds_table_data.append(row)

    from libtbx import table_utils
    print "RMSDs by detector number"
    print table_utils.format(rmsds_table_data,has_header=3,justify='center',delim=" ")
    print "PanelG Id: panel group id or panel id, depending on hierarchy_level"
    print "RMSD: root mean squared deviation between observed and predicted spot locations"
    print "rRMSD: RMSD of radial components of the observed-predicted vectors"
    print "tRMSD: RMSD of transverse components of the observed-predicted vectors"
    print "N refls: number of reflections"

    if params.tag is None:
      tag = ""
    else:
      tag = "%s "%params.tag

    if params.show_plots:
      # Plot the results
      self.detector_plot_dict(detectors[0], refl_counts, u"%sN reflections"%tag, u"%6d", show=False)

  def detector_plot_dict(self, detector, data, title, units_str, show=True, reverse_colormap=False):
    """
    Use matplotlib to plot a detector, color coding panels according to data
    @param detector detector reference detector object
    @param data python dictionary of panel names as keys and numbers as values
    @param title title string for plot
    @param units_str string with a formatting statment for units on each panel
    """
    # initialize the color map
    values = flex.double(data.values())
    norm = Normalize(vmin=flex.min(values), vmax=flex.max(values))
    if reverse_colormap:
      cmap = plt.cm.get_cmap(self.params.colormap + "_r")
    else:
      cmap = plt.cm.get_cmap(self.params.colormap)
    sm = cm.ScalarMappable(norm=norm, cmap=cmap)
    if len(values) == 0:
      print "no values"
      return
    elif len(values) == 1:
      sm.set_array(np.arange(values[0], values[0], 1)) # needed for colorbar
    else:
      sm.set_array(np.arange(flex.min(values), flex.max(values), (flex.max(values)-flex.min(values))/20)) # needed for colorbar

    fig = plt.figure()
    ax = fig.add_subplot(111, aspect='equal')
    max_dim = 0
    root = detector.hierarchy()
    rf = col(root.get_fast_axis())
    rs = col(root.get_slow_axis())
    for pg_id, pg in enumerate(iterate_detector_at_level(root, 0, self.params.hierarchy_level)):
      if pg.get_name() not in data:
        continue
      # get panel coordinates
      p0, p1, p2, p3 = get_bounds(root, pg)

      v1 = p1-p0
      v2 = p3-p0
      vcen = ((v2/2) + (v1/2)) + p0

      # add the panel to the plot
      ax.add_patch(Polygon((p0[0:2],p1[0:2],p2[0:2],p3[0:2]), closed=True, color=sm.to_rgba(data[pg.get_name()]), fill=True))
      ax.annotate("%d %s"%(pg_id, units_str%data[pg.get_name()]), vcen[0:2], ha='center')

      if self.params.draw_normal_arrows:
        pgn = col(pg.get_normal())
        v = col((rf.dot(pgn), rs.dot(pgn), 0))
        v *= 10000
        ax.arrow(vcen[0], vcen[1], v[0], v[1], head_width=5.0, head_length=10.0, fc='k', ec='k')

      # find the plot maximum dimensions
      for p in [p0, p1, p2, p3]:
        for c in p[0:2]:
          if abs(c) > max_dim:
            max_dim = abs(c)

    # plot the results
    ax.set_xlim((-max_dim,max_dim))
    ax.set_ylim((-max_dim,max_dim))
    ax.set_xlabel("mm")
    ax.set_ylabel("mm")
    fig.colorbar(sm)
    plt.title(title)
    if show:
      plt.show()

if __name__ == '__main__':
  from dials.util import halraiser
  try:
    script = Script()
    script.run()
  except Exception as e:
    halraiser(e)