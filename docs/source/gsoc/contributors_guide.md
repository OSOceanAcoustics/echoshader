# GSoC Contributor's Guide

```{attention}
This program has ended for this year. Come back next year if you'd like to participate. In the meantime checkout this year's [contribution](2022/index.md).
```

The Echoshader team aims to recruit talented [Google Summer of Code (GSoC)](https://summerofcode.withgoogle.com/)
participants to help us create the capability to interactively visualize large volumes of cloud-based ocean sonar data
to accelerate the data exploration and discovery process. This project will go hand-in-hand with ongoing development of
the [echopype](https://github.com/OSOceanAcoustics/echopype) package that handles the standardization, pre-processing,
and organization of these data. We aim for creating ocean sonar data visualization functionalities based on the
[HoloViz](https://holoviz.org/) suite of Python tools, and developing widgets that can be flexibly combined in
[Panel](https://panel.holoviz.org/) dashboards or used in Jupyter notebooks for interactive data visualization.

## Getting Started

The sonar data we will be working with can come from several different instruments and are stored in different binary
formats specific to these instruments. This binary data is difficult to work with directly and does not allow for
efficient processing. We use [echopype](https://github.com/OSOceanAcoustics/echopype) to convert the raw data into a
more user friendly structure following an interoperable netCDF data model, and serialize the data into
[netCDF](https://www.unidata.ucar.edu/software/netcdf/) or [Zarr](https://zarr.readthedocs.io/en/stable/) formats.
This standardized raw data is then calibrated to arrive at the datasets you will be working with, also in netCDF or
Zarr formats.

Before diving into the project, we suggest that you review the items below.
We also provide some additional helpful resources and initial steps to get you started.

### Storage format

We use two formats to store the data:

* [netCDF files](https://www.unidata.ucar.edu/software/netcdf/) - the current defacto file for working with
multidimensional, array-oriented scientific data from climate and oceanographic research. Although it is not necessary
to understand the netCDF library in its entirety, Unidata (the netCDF maintainer) does provide a well documented
[netCDF python interface](https://unidata.github.io/netcdf4-python/). This documentation describes useful aspects of
how netCDF defines common terms such as groups, dimensions, variables, and attributes.

* [Zarr](https://zarr.readthedocs.io/en/stable/) - a format for the storage of chunked, compressed,
arrays. Zarr has similar characteristics to netCDF, but has the added benefit of being a cloud-native data format. For
this reason, Zarr is ideal for storing large data sets in the cloud. Zarr provides a great overview of its
[storage specifications](https://zarr.readthedocs.io/en/stable/spec/v2.html#hierarchies) that may be useful to read.

### Data Structures

netCDF and Zarr formats can be easily read with the [xarray](https://xarray.pydata.org/en/stable/index.html) library in
Python. Additionally, xarray enables efficient computation of our data, which is labelled and multi-dimensional.
A fantastic [xarray tutorial](https://xarray-contrib.github.io/xarray-tutorial/) has been put
together that describes the fundamentals of xarray. Be sure to become familiar with both DataArrays and Datasets as they
are heavily used.

### Ocean Sonar Data: What are in the Datasets?

For this project, you will be initially working with the output of the
[compute_Sv](https://echopype.readthedocs.io/en/stable/api/echopype.calibrate.compute_Sv.html#echopype.calibrate.compute_Sv)
function. This is a function in echopype that computes the volume backscattering strength (Sv) from the raw data. Sv is
basically how strong the echo return is from a volume of water. This function returns an xarray Dataset that has several
variables that are necessary for the visualization of ocean sonar data.

The Dataset has the dimensions and coordinates:

* `frequency` - sonar transducer frequency, with units Hz
* `ping_time` - timestamp of each ping
* `range_bin` - sample index along a range

The data variables of the Dataset are listed below, where items in parenthesis are the dimensions of the data variables:

* Key data variables you will be working with:
  * `Sv` (frequency, ping_time, range_bin) - volume backscattering strength measured from the echo
  * `range` (frequency, ping_time, range_bin) - the measured range of an echo in meters
* Other variables included in this dataset. These are included so that the exact parameters used in the calibration
(from raw to Sv) are recorded:
  * `temperature` - the temperature measurement of the water collected by the echosounder, with unit degree Celsius
  * `salinity` - the salinity measurement of the water collected by the echosounder, with unit part per thousand (PSU)
  * `pressure` - the pressure measurement of the water collected by the echosounder, with unit dbars
  * `sound_speed` (frequency, ping_time) - sound speed (in units m/s) for the provided temperature, salinity, and pressure
  * `sound_absorption` (frequency, ping_time) - sea water absorption (in units dB/m) for each frequency and ping time, this
    value is based on the temperature, salinity, pressure, and sound_speed
  * `sa_correction` (frequency) - the sa correction for each frequency
  * `gain_correction` - (frequency) - the gain correction for each frequency
  * `equivalent_beam_angle` (frequency) - the beam angle for each frequency

### Visualizing Ocean Sonar Data

Using the above Dataset we can visualize the strength of the echoes (often called the echogram) by plotting `Sv` along
`ping_time` and `range_bin` (here, an inverse water depth measure) axes, where the water surface is near the top of the
image (the bright red line):

![echogram example 1](img/echogram_example.png)

By compiling several of these echograms and processing the data further, one can visualize the data over several hours.
This can yield visualizations such as the image below, which shows the daily vertical migration of zooplankton in the
water column -- including the impact of a solar eclipse on this migration!

![echogram example 2](img/bokeh_plot.png)

### Additional Resources

Some useful resources for getting started with the proposed visualization tools:

* Getting started with [HoloViz](https://nbviewer.org/github/philippjfr/pydata-2021/blob/master/PyData_2021.ipynb)
* Useful resources and example dashboards in [Panel](https://awesome-panel.org/)

### Initial Steps to Become Familiar with the Data and Visualizations

1. Read the example files provided in TBD using xarray
2. Construct a widget that displays the `Sv` variable with ping_time as the x coordinate and range_bin as the y
coordinate
3. Improve the widget by allowing the user to change the frequency and the colormap
4. Explore the desired types of visualization -- these are issues labeled with `gsoc 2022 wanted`
5. Become familiar with the notebook examples provided in TBD.

## Brainstorm with us

In the [Issues](https://github.com/OSOceanAcoustics/echoshader/issues) section of this repository, we list some
visualization ideas from mentors. We encourage you as a GSoC participant to propose your own original project ideas by
[creating a new issue](https://github.com/OSOceanAcoustics/echoshader/issues/new?assignees=&labels=gsoc+ideas+2022&template=gsoc-ideas.md&title=) in this repo.

Please [sign up as a GSoC participant](https://summerofcode.withgoogle.com/get-started/). Once the official application
opens, please submit your proposals based on the [Echoshader GSoC Proposal](proposal-template.md) template.

## Questions?

For project-related question, feel free to [raise an issue](https://github.com/OSOceanAcoustics/echoshader/issues/new?assignees=&labels=gsoc+questions+2022&template=gsoc-questions.md&title=).

Having more questions about being a GSoC mentor or participant? Check out the [GSoC mentor & participant guides](https://google.github.io/gsocguides/).

## The Mentor Team
<!-- Open Source Ocean Acoustics started back in 2018 from [OceanHackWeek](https://oceanhackweek.github.io/). It is
meant as a home for open source tools and resources in ocean acoustics.  --> The GSoC 2022 mentor team consists of
members: Brandon Reyes ([@b-reyes](https://github.com/b-reyes)),  Emilio Mayorga ([@emiliom](https://github.com/emiliom)),
Wu-Jung Lee ([@leewujung](https://github.com/leewujung)), Don Setiawan ([@lsetiawan](https://github.com/lsetiawan)),
Valentina Staneva ([@valentina-s](https://github.com/valentina-s)) of the [Echospace](https://uw-echospace.github.io/)
group at the University of Washington in Seattle. We are a diverse group of researchers whose work centers around
extracting knowledge from large volumes of ocean acoustic data, which contain rich information about animals ranging
from zooplankton, fish, to marine mammals. Integrating physics-based models and data-driven methods, our current work
focuses on mining water column sonar data and spans a broad spectrum from developing computational methods, building
open source software and cloud applications, to joint analysis of acoustic observations and ocean environmental variables.
