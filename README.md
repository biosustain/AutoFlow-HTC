# tecan_od_analyzer


## Description


tecan_od_analyzer is a Python package for analysing optical density (OD) measurements taken from the Tecan Nano plate reader. 

The tool parses the individual xlsx files from the plate reader and merges them into a single xlsx file. The merged file is read as a dataframe and every sample is labelled according to the calc.tsv file that should be provided by the user. The labelling is used since some samples are used for the growth rate plotting and estimation and some others are used to estimate the volume loss. The next step concerns the outlier detection and growth phase estimation, which are done by using the croissance package. Subsequently, growth rate plots and summary statistics are also computed.


## Installation

### Installation using pip 

``pip install tecan_od_analyzer``

### Installation from GitHub using pip

``pip install git+https://github.com/felixpacheco/AutoFlow-HTC``


## Usage 


tecan_od_analyzer can be used from the command-line by executing it in the directory where the xlsx files are located.

### Command line usage

``tecan_od_analyzer``

- Options :

``tecan_od_analyzer --estimations``     outputs estimations for every sample in a text file.

``tecan_od_analyzer --figures``         outputs the growth curves.

``tecan_od_analyzer --summary``         outputs the estimations for every species and bioshaker.

``tecan_od_analyzer --individual``      outputs the growth curve for every sample individually.

``tecan_od_analyzer --bioshaker``       splits the visualization of the growth rate plots according to the bioshaker.


When used with the command line the user must execute the program in the data directory. The default outputs the estimations, the figures and the statistics summary.

- Required input 


In order to run the program the user has to execute it where the data is. The inputs to the program correspond to the ones required for the autoflow_parser (log file, xlsx file, etc). 

Furthermore, to classify the samples, a file where the purpose of each sample figures is needed. This file must be a tab-separated file (.tsv) with the following format :


| Sample_ID | gr_calc | vl_calc | Species      | Drop_out |
|-----------|---------|---------|--------------|----------|
| BS1.A1    | TRUE    | FALSE   | <species_id1> | TRUE     |
| BS1.A2    | FALSE   | TRUE    | <species_id2>          | FALSE    |
| ...       | ...     | ...     | ...          | ...      |


It is important that the headers of every column must be written as it can be seen in the table. Concerning the Sample_ID, the bioshaker must appear at the beggining of the string.

## Plotting options

The plots can be customized by selecting how to group the samples and combine them on a single plot. By default, the generated plot will contain all the samples within the same species in one plot. The plots can also be generated separately and split by bioshaker.


The different options can be consulted by typing : ``tecan_od_analyzer --help`` or ``tecan_od_analyzer -h``

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

MIT