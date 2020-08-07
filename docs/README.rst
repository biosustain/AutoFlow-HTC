tecan\_od\_analyzer
===================

Description
-----------

tecan\_od\_analyzer is a Python package for analysing optical density
(OD) measurements taken from the Tecan Nano plate reader.

The tool parses the individual xlsx files from the plate reader and
merges them into a single xlsx file using the autoflow\_parse library.
The merged file is read as a dataframe and every sample is labelled
according to the calc.tsv file, provided by the user. The labelling
helps to differentiate the sample purpose, indeed, some samples
correspond to growth rate estimation and plotting while others are used
to estimate the volume loss.

Once the samples are labelled according to the experiment, the volume
loss throughout the culture is estimated and its effect is neutralized
using a simple regression model. The next step concerns the outlier
detection and growth phase estimation, which are done by using the
croissance package. Subsequently, growth rate plots and summary
statistics are also computed. The library also provides the
functionality of interpolating OD measurements on processed samples at
any given time.

Installation
------------

Installation using pip
~~~~~~~~~~~~~~~~~~~~~~

``pip install tecan_od_analyzer``

Installation from GitHub using pip
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``pip install git+https://github.com/biosustain/AutoFlow-HTC``

Usage
-----

tecan\_od\_analyzer can be used from the command-line by executing it in
the directory where the xlsx files are located. The outputs will be
gathered on a new directory called "results"..

Command line usage
~~~~~~~~~~~~~~~~~~

Standard usage :
^^^^^^^^^^^^^^^^

``tecan_od_analyzer``

The default command produces growth phase estimation, summary statistics
on the estimations and growth rate plots split only by species. By
default the volumess loss correction is computed.

Options :
'''''''''

``tecan_od_analyzer --estimations`` Outputs only estimations for every
sample in a text file.

``tecan_od_analyzer --figures`` Outputs only the growth curves.

``tecan_od_analyzer --summary`` Outputs only the estimations for every
species and bioshaker as well as boxplots of the growth rare annotation
parameters.

``tecan_od_analyzer --individual`` Outputs the growth curves for every
sample individually.

``tecan_od_analyzer --bioshaker`` Splits the visualization of the growth
rate plots according to the bioshaker and species.

``tecan_od_analyser --bioshakercolor`` Splits the visualization of the
growth rate plots according to species and colors by bioshaker.

``tecan_od_analyser --interpolation`` Computes interpolation of samples
given the measure time and outputs an xlsx file with the estimations.

``tecan_od_analyser --volumeloss`` This option allows the user to not
compute the volume loss correction. By default, the volume loss
correction is always computed.

Input
-----

Standard required input
~~~~~~~~~~~~~~~~~~~~~~~

In order to run the program the user has to execute it where the data
is. The inputs to the program correspond to the ones required for the
autoflow\_parser (log file, xlsx file, etc).

Furthermore, to classify the samples, a file where the purpose of each
sample figures is needed. This file must be a tab-separated file (.tsv)
with the following format :

+--------------+------------+------------+-----------+-------------+
| Sample\_ID   | gr\_calc   | vl\_calc   | Species   | Drop\_out   |
+==============+============+============+===========+=============+
| BS1.A1       | TRUE       | FALSE      |           | TRUE        |
+--------------+------------+------------+-----------+-------------+
| BS1.A2       | FALSE      | TRUE       |           | FALSE       |
+--------------+------------+------------+-----------+-------------+
| ...          | ...        | ...        | ...       | ...         |
+--------------+------------+------------+-----------+-------------+

It is important that the headers of every column must be written as it
can be seen in the table. Concerning the Sample\_ID, the bioshaker must
appear at the beggining of the string.

OD interpolation required input
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To compute the estimations the user must provide a tsv file named as
``od_measurements.tsv`` with the following format :

+--------------+--------+--------------------+
| Sample\_ID   | Time   | Regression\_used   |
+==============+========+====================+
| BS1.A1\_     | 0.9    | well               |
+--------------+--------+--------------------+
| BS1.A2\_     | 0.02   | mean               |
+--------------+--------+--------------------+
| ...          | ...    | ...                |
+--------------+--------+--------------------+

For the regression column, two options are possible. On the first hand,
the ``well``\ option corresponds to interpolate a given OD using only
the data of the corresponding well/sample. On the second hand, the
``mean``\ option computes the interpolation using all the samples that
share the same species and bioshaker.

It's relevant to remark, that the numbers appearing in the time column
must be written with dots and not with commas. The unit for the time
column corresponds to hours. The sample\_ID must be followed by the
species ID.

Plotting options
----------------

The plots can be customized by selecting how to group the samples and
combine them on a single plot. By default, the generated plot will
contain all the samples within the same species in one plot. The plots
can also be generated separately and split or color labelled by
bioshaker.

The different options can be consulted by typing :
``tecan_od_analyzer --help`` or ``tecan_od_analyzer -h``

Contributing
------------

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

License
-------

MIT
