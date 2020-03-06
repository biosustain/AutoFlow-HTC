# OD_handler

## Description

OD_handler is a Python library for dealing with optical density (OD) measurements related to time from TECAN. The tool creates growth rate plots and estimates the phases of each sample.


 The OD_handler first parses the xlsx files corresponding to every OD measurement using the autoflow_parser. Then, the resulting merged xlsx file is read as a dataframe and everysample is labelled according to its purpose; some samples are used for the growth rate plotting and estimation and other are used to estimate the volume loss. The resulting plots and estimation are corrected according to the volume loss estimation and are free of outliers. They are subsequently plotted and the phases are estimated.

## Installation

### Windows users 

I do not know yet hot to do it with windows

### Mac users
Use the package manager [pip](https://pip.pypa.io/en/stable/) to install OD_handler from [GitHub](https://github.com/felixpacheco/AutoFlow-HTC)

pip installation :
```bash

get-pip.py

```
OD_handler installation :
```bash
#install the OD_handler
pip install git+https://github.com/felixpacheco/AutoFlow-HTC

```

## Usage : From the terminal console



```bash

OD_handler can be used from the command-line or as a Python library. The input to the command-line tool consists of the *.tsv file (tab-separated file) with the following format :

========== ======== ======== ==========
Sample_ID  gr_calc  vl_calc  Strain_ID
========== ======== ======== ==========
BS1.A1     0.0   	0.01     ...
BS1.A2	   0.14     0.06     ...
...   	   ...      ...      ...
========== ======== ======== ==========
```


## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)