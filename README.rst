===========
OD_handler
===========

Description
============

OD_handler is a Python library for dealing with optical density (OD) measurements related to time from TECAN. The tool creates growth rate plots, estimates the phases of each sample as well as a statistics summary of the exponential growth pase by species.


The OD_handler first parses the xlsx files corresponding to every OD measurement using the autoflow_parser. Then, the resulting merged xlsx file is read as a dataframe and everysample is labelled according to its purpose and species; some samples are used for the growth rate plotting and estimation and some others are used to estimate the volume loss. The resulting plots and estimations are corrected according to the volume loss estimation and are free of outliers. They are subsequently plotted, the phases are estimated and statistics are computed.

Installation
==============

**- Windows users** 



**-  Mac users**
Use the package manager ``pip`` to install OD_handler from ``GitHub``

pip installation :

``get-pip.py``


OD_handler installation :

``pip install git+https://github.com/felixpacheco/AutoFlow-HTC``

```

Usage 
======

OD_handler can be used from the command-line by executing it in the directory where the xlsx files are located.

**- Command line usage :**

``od_handler``

- Options :

``od_handler --estimations``     outputs estimations for every sample in a text file.

``od_handler --figures``         outputs the growth curves are shown together in the same plot based on their species.

``od_handler --summary``         outputs the estimations for every species and bioshaker.

``od_handler --individual``      outputs the growth curve for every sample individually.

When used with the command line the user must execute the programme in the data directory. The default outputs the estimations, the figures and the statistics summary.

**- Command line usage :**

In order to run the program the user has to execute it where the data is. The inputs to the program correspond to the ones required for the autoflow_parser (log file, xlsx file, etc). 

Furthermore, to classify the samples, a file where the purpose of each sample figures is needed. This file must be a tab-separated file (*.tsv) with the following format :

========== ======== ======== ========== 
Sample_ID  gr_calc  vl_calc  Species   
========== ======== ======== ==========
BS1.A1     True   	 False    ...       
BS1.A2	    False    True     ...       
...   	    ...      ...      ...       
========== ======== ======== ==========

**- Plotting options :**

The plots can be customized by selecting how to group the samples and combine them on a single plot. By default, the generated plot will contain all the samples within the same species in one plot. The plots can also be generated separately.


The different options can be consulted by typing : ``OD_handler --figure_options``

Contributing
=============
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

License
=========
``MIT
