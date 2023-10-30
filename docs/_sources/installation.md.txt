# Installation

## Installation Requirement
### Dependencies

See [`requirements.txt`](https://github.com/seeq12/seeq-mps/tree/master/requirements.txt) file for a list of
dependencies and versions. Additionally, you will need to install the `seeq` module with the appropriate version that
matches your Seeq server. For more information on the `seeq` module see [seeq at pypi](https://pypi.org/project/seeq/)

### User Installation Requirements (Seeq Data Lab)

If you want to install **seeq-mps** as a Seeq Add-on, you will need:

- Seeq Data Lab (>=53.0.0 or >=R54.0.2)
- `seeq` module whose version matches the Seeq server version 
  
- Seeq administrator access
- Enable Add-on in the Seeq server

## Installation Steps
### Seeq Add-on Installation via Add-on Manager (Recommended Method)

The **MPS** Add-on can be installed via the Add-on Manager in the home page of the Seeq server. 
Please refer to our knowledge base for more details on Add-on Manager [here](https://support.seeq.com/kb/latest/cloud/add-on-packaging).

From the Seeq home page, click on the "Add-on" icon at the left of the screen and then click the "Add-on Manager" 
icon in the new buttons displayed.

<br>
<td><img alt="image" src="_static/addon_manager_1.png"></td>
<br>

Now your in the Add-on Manager you will get a list of all the Add-ons available to you. Click on the "Install" button 
next to the **MPS** Add-on.

<br>
<td><img alt="image" src="_static/addon_manager_2.png"></td>
<br>

After some time the "Install" button will change to "Installed" with a tick next to it and the Add-on will be available to use in Seeq Workbench. 

### Upgrading the **MPS** Add-on 
If there is a new version of the **MPS** Add-on available, you will see an "Upgrade" button next to the add-on in the Add-on Manager. Click on the "Upgrade" button to upgrade the add-on to the latest version.

## Seeq Add-on Installation via Terminal Window (Depreciated Method)

### User Installation (Seeq Data Lab)

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
python -m seeq.addons.mps --users me you
```

----

### Installation from source

You can get started by cloning the repository with the command:

```shell
git clone git@github.com:seeq12/seeq-mps.git
```

For development work, it is highly recommended creating a python virtual environment and install the package in that
working environment. If you are not familiar with python virtual environments, you can take a
look [here](https://docs.python.org/3.8/tutorial/venv.html)

Once your virtual environment is activated, you can install requirements and **seeq-mps** from source with:

```shell
pip install -r requirements.txt
python setup.py install
```
----

### Troubleshooting

If you experience the following error:
```
Exception: The compiled dtaidistance C library is not available. See the documentation for alternative installation
options.
```
It could be from a known issue from the package **dtaidistance** and C library availability, please follow their
guide for troubleshooting: https://dtaidistance.readthedocs.io/en/latest/usage/installation.html
