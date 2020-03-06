===========
OD_handler
===========

Description
============

OD_handler is a Python library for dealing with optical density (OD) measurements related to time from TECAN. The tool creates growth rate plots and estimates the phases of each sample.


 The OD_handler first parses the xlsx files corresponding to every OD measurement using the autoflow_parser. Then, the resulting merged xlsx file is read as a dataframe and everysample is labelled according to its purpose; some samples are used for the growth rate plotting and estimation and some others are used to estimate the volume loss. The resulting plots and estimation are corrected according to the volume loss estimation and are free of outliers. They are subsequently plotted and the phases are estimated.

Installation
==============

- Windows users 



-  Mac users
Use the package manager ``pip`` to install OD_handler from ``GitHub``

pip installation :


``get-pip.py``


OD_handler installation :

``pip install git+https://github.com/felixpacheco/AutoFlow-HTC``

```

Usage 
======

OD_handler can be used from the command-line or as a Python library.

- Command line usage :

``OD_handler <calc.tsv>``

When used with the command the user must execute the programme in the data directory. Additionally, the input to the command-line tool consists of the *.tsv file (tab-separated file) with the following format :

========== ======== ======== ========== =======
Sample_ID  gr_calc  vl_calc  Strain_ID  Group
========== ======== ======== ========== =======
BS1.A1     True   	 False    ...        1
BS1.A2	    False    True     ...        1
...   	    ...      ...      ...        2
========== ======== ======== ========== =======

- Plotting options :

The plots can be customized by selecting how to group the samples combine them on a single plot. By default, the generated plot will contain all the samples in one plot. Although, the samples can be grouped by the Strain_ID or by the group. The plots can also be generated separately. The commands for the different options are shown below :
Default :
``OD_handler <calc.tsv>``

Plot by strain :
``OD_handler <calc.tsv>  by_strain``

Plot by group :
``OD_handler <calc.tsv>  by_group``

Plot individually :
``OD_handler <calc.tsv>  individual``


Contributing
=============
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

License
=========
``MIT
