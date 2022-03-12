# GSoC Contributor's Guide

The Echoshader team aims to recruit talented [Google Summer of Code (GSoC)](https://summerofcode.withgoogle.com/) participants to help us create the capability to interactively visualize large volumes of cloud-based ocean sonar data to accelerate the data exploration and discovery process. This project will go hand-in-hand with ongoing development of the [echopype](https://github.com/OSOceanAcoustics/echopype) package that handles the standardization, pre-processing, and organization of these data. We aim for creating ocean sonar data visualization functionalities based on the [HoloViz](https://holoviz.org/) suite of Python tools, and developing widgets that can be flexibly combined in [Panel](https://panel.holoviz.org/) dashboards or used in Jupyter notebooks for interactive data visualization.


## Getting Started

As this project is an ongoing development of echopype, there are a couple of preliminary items you should become familiar
with before diving in. We outline these items below as well as provide some additional helpful resources. 

### Storage format

In echopype, we utilize two methods for storing results: 

* netcdf files - the current defacto file for working with array-oriented scientific data from climate research.
Although it is not necessary to understand the netCDF library in its entirety, Unidata does provide a well documented 
[netcdf](https://unidata.github.io/netcdf4-python/) python interface. This documentation describes useful aspects of 
how netcdf defines common terms such as groups, dimensions, variables, and attributes.  

* [Zarr](https://zarr.readthedocs.io/en/stable/) - a format for the storage of chunked, compressed, N-dimensional 
arrays. Zarr has similar characteristics to netcdf, but has the added benefit of being able to be both read and wrote to
concurrently from multiple threads or processes. Zarr provides a great overview of its [storage specifications](https://zarr.readthedocs.io/en/stable/spec/v2.html#hierarchies)
that may be useful to read.    

### Data Structures

echopype was written to utilize as much functionality of [xarray](https://xarray.pydata.org/en/stable/index.html) 
as possible. This is very beneficial as xarray is a library that can naturally work with our data, which is labelled 
and multi-dimensional. A fantastic [xarray tutorial](https://xarray-contrib.github.io/xarray-tutorial/) has been put 
together that describes the fundamentals of xarray. Be sure to become familiar with both DataArrays and Datasets as they
are heavily used.     

### Ocean Sonar Data

For this project, you will be initially working with the output of the [compute_Sv](https://echopype.readthedocs.io/en/stable/api/echopype.calibrate.compute_Sv.html#echopype.calibrate.compute_Sv) 
function. This is a function in echopype that computes the volume backscattering strength (Sv) of the provided EchoData
object. This function returns an xarray Dataset that has several variables that are necessary for the visualization 
of ocean sonar data. The Dataset has the dimensions and coordinates: 

* frequency - transducer frequency used for the experiment, with units Hz

* ping_time - timestamp of each ping

* range_bin - sample index along a range

The data variables of the Dataset are as follows, where items in parenthesis are the dimensions of the data variables: 

* Sv (frequency, ping_time, range_bin) - volume backscattering strength measured from the echo

* range (frequency, ping_time, range_bin) - the measured range of an echo in meters 

* temperature - the temperature measurement of the water collected by the echosounder, with unit degree Celsius

* salinity - the salinity measurement of the water collected by the echosounder, with unit part per thousand (PSU)

* pressure - the pressure measurement of the water collected by the echosounder, with unit dbars

* sound_speed (frequency, ping_time) - sound speed (in units m/s) for the provided temperature, salinity, and pressure 

* sound_absorption (frequency, ping_time) - sea water absorption (in units dB/m) for each frequency and ping time, this 
value is based on the temperature, salinity, pressure, and sound_speed

* sa_correction (frequency) - the sa correction for each frequency

* gain_correction - (frequency) - the gain correction for each frequency

* equivalent_beam_angle (frequency) - the beam angle for each frequency

### Additional Resources

Some useful resources for getting started with the proposed visualization tools: 

* Getting started with [HoloViz](https://nbviewer.org/github/philippjfr/pydata-2021/blob/master/PyData_2021.ipynb)

* Useful resources and example dashboards in [Panel](https://awesome-panel.org/)


## Brainstorm with us!

In the [Issues](https://github.com/OSOceanAcoustics/echoshader/issues) section of this repository, we list some visualization ideas from mentors. We encourage you as a GSoC participant to propose your own original ideas as new issues.

Feel free to propose project ideas by [raising an issue](https://github.com/OSOceanAcoustics/echoshader/issues/new?assignees=&labels=gsoc+ideas+2022&template=gsoc-ideas.md&title=) in this repo.

Please [sign up as a GSoC participant](https://summerofcode.withgoogle.com/get-started/). Once the official application opens, please submit your proposals based on the [Echoshader GSoC Proposal](proposal-template.md) template.


### Questions?

For project-related question, feel free to [raise an issue](https://github.com/OSOceanAcoustics/echoshader/issues/new?assignees=&labels=gsoc+questions+2022&template=gsoc-questions.md&title=). 

Having more questions about being a GSoC mentor or participant? Check out the [GSoC mentor & participant guides](https://google.github.io/gsocguides/).


## The Mentor Team
<!-- Open Source Ocean Acoustics started back in 2018 from [OceanHackWeek](https://oceanhackweek.github.io/). It is meant as a home for open source tools and resources in ocean acoustics.  -->
The GSoC 2022 mentor team consists of members: Brandon Reyes ([@b-reyes](https://github.com/b-reyes)),  Emilio Mayorga ([@emiliom](https://github.com/emiliom)), Wu-Jung Lee ([@leewujung](https://github.com/leewujung)), Don Setiawan ([@lsetiawan](https://github.com/lsetiawan)), Valentina Staneva ([@valentina-s](https://github.com/valentina-s)) of the [Echospace](https://uw-echospace.github.io/) group at the University of Washington in Seattle. We are a diverse group of researchers whose work centers around extracting knowledge from large volumes of ocean acoustic data, which contain rich information about animals ranging from zooplankton, fish, to marine mammals. Integrating physics-based models and data-driven methods, our current work focuses on mining water column sonar data and spans a broad spectrum from developing computational methods, building open source software and cloud applications, to joint analysis of acoustic observations and ocean environmental variables.
