# FAIM Robocopy

FAIM Robocopy provides a user interface for the windows tool
```robocopy```.

## Installation

Requirements: ```python```, ```git```,

First, clone the repository using ```git clone --recursive```.

Then, setup the environment, e.g. with ```conda```:

```
conda create -n faim-robocopy python=3.6
conda activate faim-robocopy
conda install --yes --file requirements.txt
```

Finally, we recommend creating a shortcut to ```FAIM-robocopy.pyw```
and select the python executable from the previously
set-up environment as application under ```run with```.

### Remarks

If you dont have ```git``` on your system, you can start by creating
the conda environment and install it first, before continuing with the
dependencies:

```
conda create -n faim-robocopy python=3.6
conda activate faim-robocopy
conda install git

git clone --recursive https://github.com/fmi-basel/faim-robocopy.git
conda install --yes --file requirements.txt
```



If you cloned without the ```--recursive``` option, you have to
initialize the submodules manually:

```
cd faim-robocopy/
git submodule init
git submodule update
```