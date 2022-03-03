[![Build Status](https://teamcity.seeq-labs.com/app/rest/builds/buildType:(id:AppliedResearch_mps)/statusIcon)](https://github.com/seeq12/seeq-mps/)

[![N|Solid](https://www.seeq.com/sites/default/files/seeq-content/seeq-logo-blue-web-33h.svg)](https://www.seeq.com)

[![N|Scheme](https://seeq12.github.io/seeq-mps/_static/mpsworkflowexample.png)](https://seeq12.github.io/seeq-mps/index.html)

----

**Multivariate Pattern Search [MPS]** is a Seeq Add-on for multivariate search and similarity assessment. This Add-on 
supports both continuous and batch processes. In continuous mode, the Add-on finds multivariate profiles in time that 
are similar to a visually captured reference. 
In batch mode, the Add-on computes a multivariate similarity score per batch that allows the user to identify batches that 
are similar or dissimilar to a prespecified ‘golden’ reference set ('golden batches'). Additionally, MPS also provides a contribution score
for each signal. This allows the user to determine which signals contributed to the observed similarity or dissimilarity
and utilize that information for accelerated diagnostics/troubleshooting.


----

# Documentation
[Documentation for **seeq-mps**](https://seeq12.github.io/seeq-mps/index.html).


----

# User Guide

[**seeq-MPS User Guide**](https://seeq12.github.io/seeq-mps/user_guide.html)
provides an in-depth explanation of reference search, batch analysis and how seeq-mps works. Examples of typical 
analyses using **seeq-mps** can be found in the
section [Use Cases](https://seeq12.github.io/seeq-mps/examples.html).

The video below is a short demonstration of the MPS add-on

https://user-images.githubusercontent.com/5995501/156315178-a55b7a52-4ea5-46cb-8f52-d3f7d7998ab8.mp4

-----

# Installation

The backend of **seeq-mps** requires **Python 3.7** or later.

## Dependencies

See [`requirements.txt`](https://github.com/seeq12/seeq-mps/tree/master/requirements.txt) file for a list of
dependencies and versions. Additionally, you will need to install the `seeq` module with the appropriate version that
matches your Seeq server. For more information on the `seeq` module see [seeq at pypi](https://pypi.org/project/seeq/)

## User Installation Requirements (Seeq Data Lab)

If you want to install **seeq-mps** as a Seeq Add-on, you will need:

- Seeq Data Lab (>=53.0.0 or >=R54.0.2)
- `seeq` module whose version matches the Seeq server version
- Seeq administrator access
- Enable Add-on in the Seeq server

## User Installation (Seeq Data Lab)

The latest build of the project can be found [here](https://pypi.org/) as a wheel file. The file is published as a
courtesy and does not imply any guarantee or obligation for support from the publisher. 

1. Create a **new** Seeq Data Lab project and open the **Terminal** window
2. Run `pip install seeq-mps`
3. Run `python -m seeq.addons.mps`

Follow the instructions when prompted. ("Username or Access Key" is what you use to log in to Seeq. "Password" is your 
password for logging into Seeq.)

There are additional **Options** for the addon installation. These include `--users` and `--groups`. These can be used 
to change permissions for the addon tool. For example to give permission to users `me` and `you` one would install the 
addon with as:

```bash
python -m seeq.addons.clustering --users me you
```
----

# Development

We welcome new contributors of all experience levels. The **Development Guide** has detailed information about
contributing code, documentation, tests, etc.

## Important links

* Official source code repo: https://github.com/seeq12/seeq-mps
* Issue tracker: https://github.com/seeq12/seeq-mps/issues

## Source code

You can get started by cloning the repository with the command:

```shell
git clone git@github.com:seeq12/seeq-mps.git
```

## Installation from source

For development work, it is highly recommended creating a python virtual environment and install the package in that
working environment. If you are not familiar with python virtual environments, you can take a
look [here](https://docs.python.org/3.8/tutorial/venv.html)

Once your virtual environment is activated, you can install requirements and **seeq-mps** from source with:

```shell
pip install -r requirements.txt
python setup.py install
```

### Troubleshooting

If you experience the following error:
```
Exception: The compiled dtaidistance C library is not available. See the documentation for alternative installation
options.
```
It could be from a known issue from the package **dtaidistance** and C library availability, please follow their
guide for troubleshooting: https://dtaidistance.readthedocs.io/en/latest/usage/installation.html

## Testing

There are several types of testing available for **seeq-mps**

### Automatic Testing

After installation, you can launch the test suite from the `tests` folder in the root directory of the project. You will
need to have pytest >= 4.3.1 installed.

To run all tests:

```shell
pytest
```

### User Interface Testing

To test the UI, use the `developer_notebook.ipynb` in the `development` folder of the project. This notebook can also be
used while debugging from your IDE. 

----

# Changelog

The changelog can be found [**here**](https://seeq12.github.io/seeq-mps/changelog.html)

----

# Support

Code related issues (e.g. bugs, feature requests) can be created in the
[issue tracker](https://github.com/seeq12/seeq-mps/issues)

Maintainer: James Higgie


----

# Citation

Please cite this work as:

```shell
seeq-mps
Seeq Corporation, 2021
https://github.com/seeq12/seeq-mps
```

 
