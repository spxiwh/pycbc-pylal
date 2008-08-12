#!/usr/bin/env python
#
# Copyright (C) 2008  Nickolas Fotopoulos
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
"""
This module is intended to store generic, reusable, sub-classable plot classes
to minimize formulaic copying and pasting.
"""

__author__ = "Nickolas Fotopoulos <nvf@gravity.phys.uwm.edu>"
__version__ = "$Revision$"[11:-2]
__date__ = "$Date$"


itertools = __import__("itertools")  # absolute import of system-wide itertools

import numpy
import pylab

from glue import iterutils

from pylal import viz

# general defaults
pylab.rc("lines", markersize=12)
pylab.rc("text", usetex=True)

##############################################################################
# abstract classes

class BasicPlot(object):
    """
    A very default meta-class to almost any plot you might want to make.
    It provides basic initialization, a savefig method, and a close method.
    It is up to developers to subclass BasicPlot and fill in the add_content()
    and finalize() methods.
    """
    def __init__(self, xlabel="", ylabel="", title=""):
        """
        Basic plot initialization.  A subclass can override __init__ and call
        this one (plotutils.BasicPlot.__init__(self, *args, **kwargs)) and
        then initialize variables to hold data to plot and labels.
        """
        self.fig = pylab.figure()
        self.ax = self.fig.add_subplot(111)

        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.set_title(title)

        self.ax.grid(True)

    def add_content(self, data, label="_nolabel_"):
        """
        Stub.  Replace with a method that appends values or lists of values
        to self.data_sets and appends labels to self.data_labels.  Feel free
        to accept complicated inputs, but try to store only the raw numbers
        that will enter the plot.
        """
        raise NotImplemented

    def finalize(self):
        """
        Stub.  Replace with a function that creates and makes your plot
        pretty.  Do not do I/O here.
        """
        raise NotImplemented

    def savefig(self, *args, **kwargs):
        self.fig.savefig(*args, **kwargs)

    def close(self):
        """
        Close the plot and release its memory.
        """
        pylab.close(self.fig)

    def add_legend_if_labels_exist(self, *args, **kwargs):
        """
        Create a legend if there are any non-trivial labels.
        """
        for label in self.data_labels:
            if not (label is None or label.startswith("_")):
                self.ax.legend(*args, **kwargs)
                return


##############################################################################
# utility functions

def default_colors():
    return itertools.cycle(('b', 'g', 'r', 'c', 'm', 'y', 'k'))

def default_symbols():
    return itertools.cycle(('x', '^', 'D', 'H', 'o', '1', '+'))

def determine_common_bin_limits(data_sets, default_min=0, default_max=0):
    """
    Given a some nested sequences (e.g. list of lists), determine the largest
    and smallest values over the data sets and determine a common binning.
    """
    max_stat = max(list(iterutils.flatten(data_sets)) + [-numpy.inf])
    min_stat = min(list(iterutils.flatten(data_sets)) + [numpy.inf])
    if numpy.isinf(-max_stat):
        max_stat = default_max
    if numpy.isinf(min_stat):
        min_stat = default_min
    return min_stat, max_stat


##############################################################################
# generic, but usable classes

class SimplePlot(BasicPlot):
    """
    Exactly what you get by calling pylab.plot(), but with the handy extras
    of the BasicPlot class.
    """
    def __init__(self, *args, **kwargs):
        BasicPlot.__init__(self, *args, **kwargs)
        self.x_data_sets = []
        self.y_data_sets = []
        self.data_labels = []

    def add_content(self, x_data, y_data, label="_nolegend_"):
        self.x_data_sets.append(x_data)
        self.y_data_sets.append(y_data)
        self.data_labels.append(label)

    def finalize(self):
        # make plot
        colors = default_colors()

        for x_vals, y_vals, color, label in \
            itertools.izip(self.x_data_sets, self.y_data_sets, colors,
                           self.data_labels):
            self.ax.plot(x_vals, y_vals, color=color, label=label)

        # add legend if there are any non-trivial labels
        self.add_legend_if_labels_exist()

        # decrement reference counts
        del self.x_data_sets
        del self.y_data_sets
        del self.data_labels

class BarPlot(BasicPlot):
    """
    A simple vertical bar plot.  Bars are centered on the x values and have
    height equal to the y values.
    """
    def __init__(self, *args, **kwargs):
        BasicPlot.__init__(self, *args, **kwargs)
        self.x_data_sets = []
        self.y_data_sets = []
        self.data_labels = []

    def add_content(self, x_data, y_data, label="_nolabel_"):
        self.x_data_sets.append(x_data)
        self.y_data_sets.append(y_data)
        self.data_labels.append(label)

    def finalize(self, orientation="vertical"):
        # make plot
        colors = default_colors()

        for x_vals, y_vals, color, label in \
            itertools.izip(self.x_data_sets, self.y_data_sets, colors,
                           self.data_labels):
            self.ax.bar(x_vals, y_vals, color=color, label=label,
                        align="center", linewidth=0, orientation=orientation)

        # add legend if there are any non-trivial labels
        self.add_legend_if_labels_exist()

        # decrement reference counts
        del self.x_data_sets
        del self.y_data_sets
        del self.data_labels

class VerticalBarHistogram(BasicPlot):
    """
    Histogram data sets with a common binning, then make a vertical bar plot.
    """
    def __init__(self, *args, **kwargs):
        BasicPlot.__init__(self, *args, **kwargs)
        self.data_sets = []
        self.data_labels = []

    def add_content(self, data, label="_nolabel_"):
        self.data_sets.append(data)
        self.data_labels.append(label)

    def finalize(self, num_bins=20):
        # determine binning
        min_stat, max_stat = determine_common_bin_limits(self.data_sets)
        bins = numpy.linspace(min_stat, max_stat, num_bins)

        # determine bar width; gets silly for more than a few data sets
        width = (1 - 0.1 * len(self.data_sets)) * max_stat / num_bins

        # make plot
        colors = default_colors()
        count = itertools.count()
        for i, data_set, color, label in \
            itertools.izip(count, self.data_sets, colors, self.labels):
            # make histogram
            y, x = numpy.histogram(stats, bins=bins)

            # stagger bins for pure aesthetics
            x += 0.1 * i * max_stat / num_bins

            # plot
            self.ax.bar(x, y, color, label=label, width=width, alpha=0.6,
                        align="center")

        # add legend if there are any non-trivial labels
        self.add_legend_if_labels_exist()

        # decrement reference counts
        del self.data_sets
        del self.data_labels

class NumberVsBinBarPlot(BasicPlot):
    """
    Make a bar plot in which the width and placement of the bars are set
    by the given bins.
    """
    def __init__(self, *args, **kwargs):
        BasicPlot.__init__(self, *args, **kwargs)
        self.bin_sets = []
        self.value_sets = []
        self.data_labels = []

    def add_content(self, bins, values, label="_nolabel_"):
        if len(bins) != len(values):
            raise ValueError, "length of bins and values do not match"
        self.bin_sets.append(bins)
        self.value_sets.append(values)
        self.data_labels.append(label)

    def finalize(self, orientation="vertical"):
        colors = default_colors()
        for bins, values, color, label in itertools.izip(self.bin_sets,
            self.value_sets, colors, self.data_labels):
            x_vals = bins.centres()
            widths = bins.upper() - bins.lower()

            if orientation == "vertical":
                self.ax.bar(x_vals, values, width=widths, color=color,
                    label=label, align="center", linewidth=0)
            elif orientation == "horizontal":
                self.ax.barh(x_vals, values, height=widths, color=color,
                    label=label, align="center", linewidth=0)
            else:
                raise ValueError, orientation + " must be 'vertical' " \
                    "or 'horizontal'"

        pylab.axis('tight')

        # add legend if there are any non-trivial labels
        self.add_legend_if_labels_exist()

        # decrement reference counts
        del self.bin_sets
        del self.value_sets
        del self.data_labels

class CumulativeHistogramPlot(BasicPlot):
    """
    Cumulative histogram of foreground that also has a shaded region,
    determined by the mean and standard deviation of the background
    population coincidence statistics.
    """
    def __init__(self, *args, **kwargs):
        BasicPlot.__init__(self, *args, **kwargs)
        self.fg_data_sets = []
        self.fg_labels = []
        self.bg_data_sets = []
        self.bg_label = "_nolegend_"

    def add_content(self, fg_data_set, label="_nolegend_"):
        self.fg_data_sets.append(fg_data_set)
        self.fg_labels.append(label)

    def add_background(self, bg_data_sets, label="_nolegend_"):
        self.bg_data_sets.extend(bg_data_sets)
        self.bg_label = label

    def finalize(self, num_bins=20, normalization=1):
        epsilon = 1e-8

        # determine binning
        min_stat, max_stat = determine_common_bin_limits(\
            self.fg_data_sets + self.bg_data_sets)
        bins = numpy.linspace(min_stat, max_stat, num_bins)
        dx = bins[1] - bins[0]

        # plot foreground
        colors = default_colors()
        symbols = default_symbols()
        for data_set, color, symbol, label in \
            itertools.izip(self.fg_data_sets, colors, symbols,
            self.fg_labels):
            # make histogram
            y, x = numpy.histogram(data_set, bins=bins)
            y = y[::-1].cumsum()[::-1]

            # plot
            y = numpy.array(y, dtype=numpy.float32)
            y[y <= epsilon] = epsilon
            self.ax.plot(x + dx/2, y*normalization, symbol + color, label=label)

        # shade background region
        if len(self.bg_data_sets) > 0:
            # histogram each background instance separately and take stats
            hist_sum = numpy.zeros(len(bins), dtype=float)
            sq_hist_sum = numpy.zeros(len(bins), dtype=float)
            for instance in self.bg_data_sets:
                # make histogram
                y, x = numpy.histogram(instance, bins=bins)
                y = y[::-1].cumsum()[::-1]
                hist_sum += y
                sq_hist_sum += y*y
          
            # get statistics
            N = len(self.bg_data_sets)
            means = hist_sum / N
            stds = numpy.sqrt((sq_hist_sum - hist_sum*means) / (N - 1))
          
            # plot mean
            means[means <= epsilon] = epsilon
            self.ax.plot(x + dx/2, means*normalization, 'r+',
                label=r"$\mu_\mathrm{%s}$" % self.bg_label)

            # shade in the area
            upper = means + stds
            lower = means - stds
            lower[lower <= epsilon] = epsilon
            tmp_x, tmp_y = viz.makesteps(bins, upper, lower)
            self.ax.fill(tmp_x, tmp_y*normalization, facecolor='y', alpha=0.3,
                label=r"$\sigma_\mathrm{%s}$" % self.bg_label)

        # make semilogy plot
        self.ax.set_yscale("log")

        # adjust plot range
        self.ax.set_xlim((0.9 * min_stat, 1.1 * max_stat))
        possible_ymins = [0.6]
        if len(self.bg_data_sets) > 0:
            possible_ymins.append(0.6 / N)
        else:
            possible_ymins.append(0.6 * normalization)
        self.ax.set_ylim(min(possible_ymins))

        # add legend if there are any non-trivial labels
        self.data_labels = self.fg_labels + [self.bg_label]
        self.add_legend_if_labels_exist()

        # decrement reference counts
        del self.fg_data_sets
        del self.bg_data_sets
        del self.fg_labels
        del self.bg_label
        del self.data_labels


class ImagePlot(BasicPlot):
    """
    The equivalent of pylab.imshow(), but with the BasicPlot niceties and
    some defaults that are more in tune with what a scientist wants --
    origin="lower", requiring x and y bins so that we can label axes
    correctly, and a colorbar.
    """
    def __init__(self, *args, **kwargs):
        BasicPlot.__init__(self, *args, **kwargs)
        self.image = None

    def add_content(self, image, x_bins, y_bins):
        """
        Add a given image to this plot.

        @param image: two-dimensional numpy array to plot
        @param x_bins: pylal.rate.Bins instance describing the x binning
        @param y_bins: pylal.rate.Bins instance describing the y binning
        """
        if self.image is not None:
            raise ValueError, "can only plot one image"
        if image.ndim != 2:
            raise ValueError, "require 2-D array"
        self.image = image
        self.x_bins = x_bins
        self.y_bins = y_bins

    def finalize(self, colormap=None, colorbar=True):
        if self.image is None:
            raise ValueError, "nothing to finalize"

        extent = [self.x_bins.lower()[0], self.x_bins.upper()[-1],
                  self.y_bins.lower()[0], self.y_bins.upper()[-1]]

        im = self.ax.imshow(self.image, origin="lower", extent=extent,
                            cmap=colormap, interpolation="nearest")

        pylab.axis('tight')

        if colorbar:
            self.fig.colorbar(im)

class FillPlot(BasicPlot):
    """
    Given a list of vertices (passed by x-coords and y-coords), fill the
    regions (by default with successively darker gray shades).
    """
    def __init__(self, *args, **kwargs):
        BasicPlot.__init__(self, *args, **kwargs)
        self.x_coord_sets = []
        self.y_coord_sets = []
        self.data_labels = []
        self.shades = []

    def add_content(self, x_coords, y_coords, label="_nolabel_", shade=None):
        if len(x_coords) != len(y_coords):
            raise ValueError, "x and y coords have different length"
        if iterutils.any(s is None for s in self.shades) and shade is not None \
        or iterutils.any(s is not None for s in self.shades) and shade is None:
            raise ValueError, "cannot mix explicit and automatic shading"

        self.x_coord_sets.append(x_coords)
        self.y_coord_sets.append(y_coords)
        self.data_labels.append(label)
        self.shades.append(shade)

    def finalize(self):
        # fill in default shades if necessary
        if iterutils.any(s is None for s in self.shades):
            n = len(self.shades)
            grays = numpy.linspace(0, 1, n, endpoint=False)[::-1]
            self.shades = numpy.vstack((grays, grays, grays)).T

        # plot
        for x, y, s, l in zip(self.x_coord_sets, self.y_coord_sets,
                              self.shades, self.data_labels):
            self.ax.fill(x, y, facecolor=s, label=l)

        # add legend if there are any non-trivial labels
        self.add_legend_if_labels_exist()

class SixStripSeriesPlot(BasicPlot):
    """
    Given a time- or frequency-series, plot it across six horizontal axes,
    stacked on top of one another.  This is good for representing a
    high-resolution one-dimensional data set.  To support missing data,
    we require x and y coordinates for each data set.
    """
    def __init__(self, xlabel="", ylabel="", title=""):
        self.fig = pylab.figure(figsize=(5.54, 7.5))
        self.title = title

        # do not want to create axes yet
        self.xlabel = xlabel
        self.ylabel = ylabel

        self.x_coord_sets = []
        self.y_coord_sets = []
        self.data_labels = []
        self.formats = []

    def add_content(self, x_coords, y_coords, label="_nolabel_", format=None):
        if len(x_coords) != len(y_coords):
            raise ValueError, "x and y coords have different length"
        if iterutils.any(c is None for c in self.formats) and format is not None \
        or iterutils.any(c is not None for c in self.formats) and format is None:
            raise ValueError, "cannot mix explicit and automatic formating"

        self.x_coord_sets.append(x_coords)
        self.y_coord_sets.append(y_coords)
        self.data_labels.append(label)
        self.formats.append(format)

    def finalize(self, yscale="linear"):

        min_x, max_x = determine_common_bin_limits(self.x_coord_sets)

        numaxes = 6  # This is hardcoded below.  Change at your own risk.
        ticks_per_axis = 6 # Hardcoded, but you can change it if it looks bad.
        fperaxis = (max_x - min_x) / numaxes
        freq_boundaries = numpy.linspace(min_x, max_x, numaxes + 1)
        freq_ranges = zip(freq_boundaries[:-1], freq_boundaries[1:])

        # attempt to put ticks at every multiple of 10 unless there are too few
        # or too many
        tickspacing = int(numpy.ceil(fperaxis / ticks_per_axis / 10)) * 10
        if abs(fperaxis / tickspacing - ticks_per_axis) > 2:
            tickspacing = int(numpy.ceil(fperaxis / ticks_per_axis))

        # iterate over axes
        for j, freq_range in enumerate(freq_ranges):
            # create one of the 6 axes
            ax = self.fig.add_axes([.12, .84-.155*j, .86, 0.124])

            # Since default_colors() returns an infinite iterator, we need to
            # initialize it again and again.
            if iterutils.any(c is None for c in self.formats):
                formats = default_colors()
            else:
                formats = self.formats

            for x_coords, y_coords, label, format in zip(self.x_coord_sets,
                self.y_coord_sets, self.data_labels, formats):
                # just look at the region relevant to our axis
                ind = (x_coords >= freq_range[0]) & (x_coords < freq_range[1])
                x = x_coords[ind]
                y = y_coords[ind]

                # add data to axes
                ax.plot(x, y, format, label=label, markersize=1)

                # fix the limits and ticks
                ax.set_xlim(freq_range)

                mintick = int(numpy.ceil(freq_range[0] / tickspacing)) \
                    * tickspacing
                maxtick = int(numpy.floor(freq_range[1] / tickspacing)) \
                    * tickspacing
                ax.set_xticks(xrange(mintick, maxtick+1, tickspacing))

                ax.set_ylabel(self.ylabel)
                ax.set_yscale(yscale)
                ax.grid(True)

        # label bottom row
        ax.set_xlabel(self.xlabel)

        # title top row
        self.fig.axes[0].set_title(self.title)

        # apply common y limits
        y_lims = [ax.get_ylim() for ax in self.fig.axes]
        new_y_lims = determine_common_bin_limits(y_lims)
        for ax in self.fig.axes:
            ax.set_ylim(new_y_lims)

