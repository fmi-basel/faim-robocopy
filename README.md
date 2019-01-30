# FAIM Robocopy

FAIM Robocopy provides a user interface for the windows tool
```robocopy```.

## Installation

Requirements: ```python```, ```git```,

First, clone the repository using ```git clone```, then initialize the
submodules:

```
cd faim-robocopy/
git submodule init
git submodule update
```

Setup the environment, e.g. with ```conda```:

```
conda create -n faim-robocopy python=3.6
conda install --yes --file requirements.txt
```

Finally, we recommend creating a shortcut to ```FAIM-robocopy.pyw```
and select the python executable from the previously
set-up environment as application under ```run with```.