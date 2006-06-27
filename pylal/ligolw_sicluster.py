# $Id$
#
# Copyright (C) 2006  Duncan A. Brown
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

#
# =============================================================================
#
#                                   Preamble
#
# =============================================================================
#

import sys

from glue import segments
from glue.ligolw import lsctables
from pylal import llwapp
from pylal.date import LIGOTimeGPS
from pylal import SnglInspiralUtils

__author__ = "Duncan Brown <dbrown@ligo.caltech.edu>"
__version__ = "$Revision$"[11:-2]
__date__ = "$Date$"[7:-2]


#
# =============================================================================
#
#                                 Preparation
#
# =============================================================================
#

def get_tables(doc):
  searchsummtable = llwapp.get_table(
    doc, lsctables.SearchSummaryTable.tableName)
  snglinspiraltable = llwapp.get_table(
    doc, lsctables.SnglInspiralTable.tableName)
  return searchsummtable.get_inlist().extent(), \
    searchsummtable.get_outlist().extent(), snglinspiraltable


#
# =============================================================================
#
#                           Add Process Information
#
# =============================================================================
#

def append_process(doc, **kwargs):
  process = llwapp.append_process(
    doc, program = "ligolw_sicluster", version = __version__, 
    cvs_repository = "lscsoft", cvs_entry_time = __date__, 
    comment = kwargs["comment"])

  llwapp.append_process_params(doc, process, 
    [("--cluster-window", "lstring", kwargs["cluster_window"])])
  if kwargs["snr_threshold"] > 0:
    llwapp.append_process_params(doc, process, 
      [("--snr-threshold", "lstring", kwargs["snr_threshold"])])
  if kwargs["sort_descending_snr"]:
    llwapp.append_process_params(doc, process, 
      [("--sort-descending-snr", "lstring", " ")])
  if kwargs["sort_ascending_snr"]:
    llwapp.append_process_params(doc, process, 
      [("--sort-ascending-snr", "lstring", " ")])

  return process


#
# =============================================================================
#
#                             Clustering Algorithm
#
# =============================================================================
#

def SnglInspiralCluster(a, b):
  """
  Replace a with a cluster constructed from a and b. 
  """
  if b.snr >= a.snr:
    return b
  else:
    return a


def ClusterSnglInspiralTable(triggers, testfunc, clusterfunc, 
  twindow, bailoutfunc = None):
  """
  Cluster the triggers in the list.  testfunc should accept a pair of
  triggers, and return 0 if they should be clustered.  clusterfunc
  should accept a pair of triggers, and replace the contents of the
  first with a cluster constructed from the two.  If bailoutfunc is
  provided, the triggers will be sorted using testfunc as a
  comparison operator, and then only pairs of triggers for which
  bailoutfunc returns 0 will be considered for clustering.
  """
  while True:
    did_cluster = False

    if bailoutfunc:
      triggers.sort(testfunc)

    i = 0
    while i < len(triggers):
      j = i + 1
      while j < len(triggers):
        if not testfunc(triggers[i], triggers[j],twindow):
          triggers[i] = clusterfunc(triggers[i], triggers[j])
          del triggers[j]
          did_cluster = True
        else:
          if bailoutfunc:
            if bailoutfunc(triggers[i], triggers[j]):
              break
          j += 1
      i += 1

    if not did_cluster:
      return


#
# =============================================================================
#
#                                 Library API
#
# =============================================================================
#

def ligolw_sicluster(doc, **kwargs):
  # Extract segments and tables
  inseg, outseg, snglinspiraltable = get_tables(doc)

  # Add process information
  process = append_process(doc, **kwargs)

  # Delete all triggers below threshold
  if kwargs["snr_threshold"] > 0:
    if kwargs["verbose"]:
      print >>sys.stderr, "discarding triggers with snr < %f..." % \
        kwargs["snr_threshold"]
      for trigger in snglinspiraltable.rows:
        if trigger.snr < kwargs["snr_threshold"]:
          del trigger

  # Cluster
  if kwargs["verbose"]:
    print >>sys.stderr, "clustering..."
  ClusterSnglInspiralTable(snglinspiraltable.rows, 
    kwargs["testfunc"], kwargs["clusterfunc"],
    LIGOTimeGPS(kwargs["cluster_window"]), kwargs["bailoutfunc"])

  # Sort by signal-to-noise ratio
  if kwargs["sort_ascending_snr"] or kwargs["sort_descending_snr"]:
    if kwargs["verbose"]:
      print >>sys.stderr, "sorting by snr..."
    snglinspiraltable.rows.sort(SnglInspiralUtils.CompareSnglInspiralBySnr)
    if kwargs["sort_descending_snr"]:
      snglinspiraltable.rows.reverse()

  # Add search summary information
  llwapp.append_search_summary(doc, process, inseg = inseg, outseg = outseg, 
    nevents = len(snglinspiraltable))
  llwapp.set_process_end_time(process)

  return doc
