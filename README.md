# FAIM Robocopy

FAIM Robocopy provides a user interface for the windows tool
```robocopy```.

## Installation

Requirements: ```python 3.6```, ```git```. We recommend installing
[Anaconda](https://repo.continuum.io/) and will use it in this
installation guide.


Open an ```Anaconda prompt``` and change to the directory where you
want to keep ```FAIM-Robocopy```:

```
cd PATH/TO/DIR
```

where you substitute```PATH/TO/DIR``` with a path on your machine.

Then, create a new conda environment and activate it:

```
conda create -n faim-robocopy python=3.6 git
conda activate faim-robocopy
```

Next, clone the source code from github:

```
git clone --recursive https://github.com/fmi-basel/faim-robocopy.git
```

and install the remaining dependencies

```
cd faim-robocopy
conda install --yes --file requirements.txt
```

Finally, we recommend creating a shortcut to ```FAIM-robocopy.pyw```,
where you select the python executable from the ```faim-robocopy```
conda environment under ```run with```. You can determine the
corresponding location of this python executable with the command
```where pythonw``` in the anaconda prompt.