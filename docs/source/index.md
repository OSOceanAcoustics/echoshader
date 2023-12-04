# Welcome to echoshader

Open source Python package for building interactive ocean sonar data visualizations on the HoloViz suite of libraries.

## What are ocean sonar systems?

Ocean sonar systems, such as echosounders, are the [workhorse to study life in the ocean](https://storymaps.arcgis.com/stories/e245977def474bdba60952f30576908f). They provide continuous observations of fish and zooplankton by transmitting sounds and analyzing the echoes bounced off these animals, just like how medical ultrasound images the interior of human body. In recent years these systems are widely deployed on ships, autonomous vehicles, or moorings, bringing in a lot of data that allow scientists to study the change of the marine ecosystem.

## What is echoshader?

Echoshader aims to enhance the capability to interactively visualize large volumes of ocean sonar data to accelerate the data exploration and discovery process. The project will go hand-in-hand with ongoing development of the [echopype](https://echopype.readthedocs.io/en/stable/) package that handles the standardization, pre-processing, and organization of these data.

By providing an accessible and customizable platform for echo data visualization, the project can accelerate advancements in oceanographic research for the benefit of conservation and sustainable resource management like fishery.

## Installation

Echoshader relies on several crucial packages which will need to be installed first (best in a separate environment)

```bash
mamba create -n echoshader -c pyviz -c conda-forge echopype hvplot geoviews pyvista ipykernel
```

We recommend use [mamba](https://mamba.readthedocs.io/en/latest/user_guide/mamba.html) to manage conda's environments, which is a re-implementation of conda offering additional benefits.

Note: Users may already have `echopype` installed, but it should be at a version greater than or equal to `0.7.1`.

To link this environment with a Jupyter kernel:

```bash
conda activate echoshader
python -m ipykernel install --user --name echoshader --display-name "echoshader"
```

The latest branch can be installed via the following:

```bash
pip install git+https://github.com/OSOceanAcoustics/echoshader.git
```

## Creating 'dev' Environment

This section is intended for those who are actively developing this package.

To run in development mode, fork and clone the repository at [Echoshader](https://github.com/OSOceanAcoustics/echoshader):

```bash
mamba create -c conda-forge -n echoshader-dev --yes python=3.10 --file requirements.txt --file requirements-dev.txt
pip install -e
```
