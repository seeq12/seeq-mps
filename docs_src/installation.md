# Installation

The backend of **seeq-mps** requires **Python 3.7** or later.

## Dependencies

See [`requirements.txt`](https://github.com/seeq12/seeq-mps/tree/master/requirements.txt) file for a list of
dependencies and versions. Additionally, you will need to install the `seeq` module with the appropriate version that
matches your Seeq server. For more information on the `seeq` module see [seeq at pypi](https://pypi.org/project/seeq/)

## User Installation Requirements (Seeq Data Lab)

If you want to install **seeq-mps** as a Seeq Add-on, you will need:

- Seeq Data Lab (>=R51.1.0, >=R52.1.0, >=53.0.0 or >=R54.0.2)
- `seeq` module whose version matches the Seeq server version
- Seeq administrator access
- Enable Add-on in the Seeq server

## User Installation (Seeq Data Lab)

The latest build of the project can be found [here](https://pypi.org/) as a wheel file. The file is published as a
courtesy and does not imply any guarantee or obligation for support from the publisher. 

1. Create a **new** Seeq Data Lab project and open the **Terminal** window
2. Run `pip install seeq-mps`
3. Run `python -m seeq.addons.mps [--users <users_list> --groups <groups_list>]`

###Troubleshooting
If you experience the following error:
```
Exception: The compiled dtaidistance C library is not available. See the documentation for alternative installation
options.
```
It could be from a known issue from the package **dtaidistance** and C library availability, please follow their
guide for troubleshooting: https://dtaidistance.readthedocs.io/en/latest/usage/installation.html
