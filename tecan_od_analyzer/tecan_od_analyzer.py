# -*- coding: utf-8 -*-
"""Main module."""

# IMPORTANT FOR REVIEW:
# unused variables are commented out - need to be revised

# Libraries #
import pandas as pd

# process_curve causes issues or one of the test data sets
from croissance import process_curve
from croissance.estimation.outliers import remove_outliers
import re
import os
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit
import sys
from scipy import interpolate
import math
import argparse
import seaborn as sns
import shutil
import warnings
from scipy.optimize import OptimizeWarning
from tecan_od_analyzer.cli.cli import main as cli


__version__ = "0.1.6"


def argument_parser(argv_list=None):
    """Asesses the input arguments and outputs flags to run the different
        functions according to the user needs.

    Args:
        argv_list: List of arguments provided by the user when running the
        program.

    Returns:
        flags
    """

    # Initialize the argument parser
    parser = argparse.ArgumentParser()

    # Adding general arguments
    parser.add_argument(
        "-e",
        "--estimations",
        help="Get only the estimations \
                        for every sample",
        action="store_true",
    )
    parser.add_argument(
        "-f",
        "--figures",
        help="Get only the growth curve \
                        figures",
        action="store_true",
    )
    parser.add_argument(
        "-s",
        "--summary",
        help="Get only the summary of \
                        growth rate estimations",
        action="store_true",
    )
    parser.add_argument(
        "-it",
        "--interpolation",
        help="Get interpolation of \
                        growth rate measurements with given od",
        action="store_true",
    )
    parser.add_argument(
        "-r", "--resultsdir", help="Name results directory", action="store"
    )
    parser.add_argument("-p", "--path", help="Path to data", action="store")

    # Visualization arguments
    parser.add_argument(
        "-b",
        "--bioshaker",
        help="Get one growth rate figure \
                        for every individual bioshaker",
        action="store_true",
    )
    parser.add_argument(
        "-i",
        "--individual",
        help="Get one growth rate figure \
                        for every individual sample",
        action="store_true",
    )
    parser.add_argument(
        "-bc",
        "--bioshakercolor",
        help="Get one growth rate \
                        figure for every species not colored by bioshaker",
        action="store_true",
    )
    parser.add_argument(
        "-ip",
        "--interpolationplot",
        help="Shows \
                        interpolation between points on growth rate curves",
        action="store_true",
    )
    parser.add_argument(
        "-svg",
        "--exportsvg",
        help="Changes .png output \
                        to .svg output for use in publications",
        action="store_true",
    )
    parser.add_argument(
        "-os",
        "--onlyspecies",
        help="Get separate growth rate \
                        figures for every species on every bioshaker",
        action="store_true",
    )
    parser.add_argument(
        "-l",
        "--legendoff",
        help="Do not show the legend in plots",
        action="store_true",
    )

    # Volume loss related arguments
    parser.add_argument(
        "-v",
        "--novolumeloss",
        help="Volume loss compesation \
                        is not computed",
        action="store_false",
    )
    parser.parse_args()
    args = parser.parse_args(argv_list[1:])

    # Create flags

    if not args.estimations and not args.figures and not args.summary:

        flag_all = True
        flag_est = False
        flag_sum = False
        flag_fig = False
        flag_ind = args.individual
        flag_bioshakercolor = args.bioshakercolor
        # flag_volume_loss = args.novolumeloss
        flag_bioshaker = args.bioshaker
        flag_interpolation = args.interpolation
        cmd_dir = args.resultsdir
        path = args.path
        interpolationplot = args.interpolationplot
        flag_svg = args.exportsvg
        flag_os = args.onlyspecies
        flag_loff = args.legendoff

    elif args.estimations or args.figures or args.summary:

        flag_all = False
        flag_est = args.estimations
        flag_sum = args.summary
        flag_fig = args.figures
        flag_ind = args.individual
        flag_bioshakercolor = args.bioshakercolor
        # flag_volume_loss = args.novolumeloss
        flag_bioshaker = args.bioshaker
        flag_interpolation = args.interpolation
        cmd_dir = args.resultsdir
        path = args.path
        interpolationplot = args.interpolationplot
        flag_svg = args.exportsvg
        flag_os = args.onlyspecies
        flag_loff = args.legendoff

    return (
        flag_all,
        flag_est,
        flag_sum,
        flag_fig,
        flag_ind,
        flag_bioshakercolor,
        args.novolumeloss,
        flag_bioshaker,
        flag_interpolation,
        cmd_dir,
        path,
        interpolationplot,
        flag_svg,
        flag_os,
        flag_loff,
    )


# ------ INTERPRET INPUT ARGUMENTS AND CREATE OUTPUT DIR


def input_output(cmd_dir, path):
    """Interprets input arguments related to the path to the data and
    output directory
    Args:
    cmd_dir : Name of directory where output will be sent
    path : path where the data is
    """

    # Interpret path input
    if path is None:
        pass

    else:

        try:
            os.chdir(str(path))
        except not os.path.exists(str(path)):
            sys.exit("Entered path does not exist: " + str(path))

    # Output directory naming

    if cmd_dir is None:

        if os.path.exists("Results"):
            shutil.rmtree("Results", ignore_errors=True)

        else:
            pass

        try:
            os.mkdir("Results")
            print("Successfully created the Results directory")
        except OSError:
            sys.exit("Error! Creation of the directory failed")

        dir_ = "Results"

    else:

        if os.path.exists(cmd_dir):
            shutil.rmtree(cmd_dir, ignore_errors=True)

        else:
            pass

        try:
            os.mkdir(str(cmd_dir))
            print(f"Successfully created the {cmd_dir} directory")

        except OSError:
            sys.exit("Error! Creation of the directory failed")

        dir_ = str(cmd_dir)

    return dir_


# ------ PARSE THE DATA USING THE autoflow_parser LIBRARY ------


def parse_data():
    """Calls the autoflow_parser and returns a merged xlsx document with all
    the OD readings combined"""
    cli(".", 60)


# ------ DATA LOADING AND VARIABLE SELECTION ------


def read_xlsx(filename="results.xlsx"):
    """Reads .xlsx file, returns a dataframe with relevant variables.
    The output of the parser is set to be "results.xlsx", the default
    reads the mentioned file without any additional argument"""
    try:
        # Open data file
        df = pd.read_excel(filename)
    except FileNotFoundError:
        return sys.exit("Could not find the parsed data file (XLSX extension)")
    # Select valuable columns
    cols = [
        "Sample ID",
        "Measurement",
        "Measurement type",
        "Sampling time",
        "Sampling date",
    ]  # relevant variables
    df = df[cols]
    # header spaces replaced with underscore
    df.columns = df.columns.str.replace(" ", "_")

    return df


# ------ SEPARATION OF GROWTH RATE SAMPLE AND VOLUME LOSS SAMPLES ------


def sample_outcome(sample_file, df):
    """Uses an external file containing individual sample purposes, returns
    two classifed dataframes based on sample purposes and labelled by
    bioshaker.

    Args:
        sample_file: variable or string containing the name of the file and
        its extension.
        df: dataframe obtained by using the read_xlsx method on the merged
        xlsx file.

    Returns:
        df_gr: dataframe containing observations related to the microbial
        growth rate, labelled by bioshaker.
        df_vl: dataframe containing observations related to the volume loss
        estimation, labelled by bioshaker.
    """

    # Open the file containing sample purposes
    # Info about the purpose of the sample (growth rate, volume loss
    # compensation, species and drop-out samples)
    df_calc = pd.read_csv(sample_file, sep="\t")

    # Remove whitespaces in Sample_IDs
    df.loc[:, "Sample_ID"] = df["Sample_ID"].str.replace(" ", "")
    df_calc.loc[:, "Sample_ID"] = df_calc["Sample_ID"].str.replace(" ", "")

    # Remove special characters from species names
    df_calc.loc[:, "Species"] = df_calc["Species"].str.replace(r"\W+", "_")

    # Check format consistency across files
    IDs_parsed = df["Sample_ID"].tolist()
    IDs_calc = df_calc["Sample_ID"].tolist()

    # Check that two random identifiers are in the calc file
    if IDs_parsed[0] not in IDs_calc and IDs_parsed[10] not in IDs_calc:

        print(
            f"""Warning: The format of the Sample IDs is not matching across \
                the input files:
            \n
            results.xlsx : {IDs_parsed[0]}
            calc.tsv : {IDs_calc[0]}\n
            """
        )

        if re.search(r"BS\d[.]\d_[A-Z]\d", IDs_calc[0]) is not None:
            df_calc.loc[:, "Sample_ID"] = df_calc["Sample_ID"].str.replace(
                ".0_", "_"
            )
            print("The ID format will be redefined to match the results file.")
            print(f'e.g {IDs_calc[0]} --> {df_calc["Sample_ID"].tolist()[0]}')

        elif re.search(r"BS\d[.]\d_[A-Z]\d", IDs_calc[0]) is None:
            df_calc.loc[:, "Sample_ID"] = df_calc["Sample_ID"].str.replace(
                "_", ".0_"
            )
            print("The ID format will be redefined to match the results file.")
            print(f'e.g {IDs_calc[0]} --> {df_calc["Sample_ID"].tolist()[0]}')

        else:
            sys.exit(
                "The ID format of the calc.tsv file could not be \
                converted to match the results.xlsx file"
            )

    # Remove wells to drop
    df_calc.loc[:, "Drop_out"] = [not elem for elem in df_calc["Drop_out"]]
    df_calc = df_calc[df_calc["Drop_out"]]

    # Add species and bioshaker labels to every observation
    cols = ["Sample_ID", "Species", "Dilution"]
    temp_df = df_calc[cols]

    # Check if there is an issue with the species names;
    # if one name is entirely included in a different one the
    # later functions will crash. Here we check for that and add
    # unique identifiers (numbering the species) if necessary
    rename = False
    species_list = list(temp_df["Species"].unique())
    for pos, species in enumerate(species_list):
        if pos == len(species_list) - 1:
            if any(species in s for s in species_list[:pos]):
                rename = True
                break
            else:
                continue
        elif pos == 0:
            if any(species in s for s in species_list[pos + 1:]):
                rename = True
                break
            else:
                continue
        else:
            if any(
                species in s
                for s in species_list[:pos] + species_list[pos + 1:]
            ):
                rename = True
                break
            else:
                continue
    if rename:
        species_col = temp_df["Species"]
        for pos, species in enumerate(species_list):
            species_col = [
                "0" + str(pos + 1) + "_" + x if x == species else x
                for x in species_col
            ]
        temp_df.loc[:, "Species"] = species_col

    # Add bioshaker label and correct Measurements by dilution
    df = pd.merge(df, temp_df, how="left", on="Sample_ID")
    df.loc[:, "bioshaker"] = df["Sample_ID"].str[0:3]
    df.loc[:, "Measurement"] = df["Measurement"] * df["Dilution"]

    # Separate samples for growth rate or volume loss according to calc.tsv
    gr_samples = df_calc[df_calc["calc_gr"]]
    gr_samples = gr_samples["Sample_ID"].tolist()
    vol_loss_samples = df_calc[df_calc["calc_volumeloss"]]
    vol_loss_samples = vol_loss_samples["Sample_ID"].tolist()

    # Separate initial dataframe in 2
    df_gr = df[df.Sample_ID.isin(gr_samples)]
    df_gr = df_gr[df_gr["Measurement_type"] == "OD600"]
    df_vl = df[df.Sample_ID.isin(vol_loss_samples)]
    df_vl450 = df_vl[df_vl["Measurement_type"] == "OD450"]
    df_vl600 = df_vl[df_vl["Measurement_type"] == "OD600"]
    return df_gr, df_vl450, df_vl600


# ------- GROWTH RATE FORMATTING FOR SUITABLE CROISSANCE ANALYSIS INPUT ------


def time_formater(df):
    """Takes a dataframe and turns date and time variables into differential
    time in hours for every bioshaker, returns modified dataframe.

    Args:
        df: dataframe with containing date and time measurements.

    Returns:
        df_out: dataframe with differential time measurements in hours.
    """
    # Get list of bioshakers
    unique_bioshakers = df["bioshaker"].unique()

    # Measurement type variable removal
    df = df.drop(columns=["Measurement_type"])

    # Initialize empty output dataframe
    df_out = pd.DataFrame()

    for bioshaker in unique_bioshakers:

        # Subset initial dataframe by bioshaker
        df_temp = df[df["bioshaker"] == bioshaker]
        # unique_date = df["Sampling_date"].unique()

        # Merge date and time variable to datetime format
        df_temp.loc[:, "date_time"] = (
            df_temp["Sampling_time"] + " " + df_temp["Sampling_date"]
        )
        df_temp.loc[:, "date_time"] = pd.to_datetime(df_temp["date_time"],
                                                     dayfirst=True)
        # Substracting the time of the first obs to all obs
        df_temp.loc[:, "time_hours"] = (
            df_temp["date_time"] - df_temp.loc[df_temp.index[0], "date_time"]
        )
        df_temp.loc[:, "d"] = df_temp["time_hours"].dt.components.days
        df_temp.loc[:, "h"] = df_temp["time_hours"].dt.components.hours
        df_temp.loc[:, "m"] = df_temp["time_hours"].dt.components.minutes
        df_temp.loc[:, "s"] = df_temp["time_hours"].dt.components.seconds
        df_temp.loc[:, "time_hours"] = (
            df_temp["d"] * 24
            + df_temp["h"]
            + df_temp["m"] / 60
            + df_temp["s"] / 360
        )

        # df_temp["time_hours"] = df_temp["time_hours"].dt.total_seconds()/3600
        # Append dataframes together
        df_out = df_out.append(df_temp)

    # Removal of temporary variables
    df_out = df_out.drop_duplicates()
    # df_out = df_out.drop(columns=["Sampling_date", "Sampling_time"])
    # df_out = df_out.drop(columns=["date_time"])

    return df_out


# ------ VOLUME LOSS CORRELATION FOR EVERY SAMPLE ------


def vol_correlation(df_vl):  # done
    """Assess the volume loss with OD450 measurements and correlates the
    OD450 readings to time for every different bioshaker, returns a
    correlation dataframe.

    Args:
        df_vl: dataframe containing only volume loss measurements.

    Returns:
        cor_df: dataframe containing correlation values of the volume loss
        according to time measurements.
    """

    # Subset initial df_raw according to OD measurement and get unique IDs
    unique_IDs_vl = df_vl["Sample_ID"].unique()
    # unique_bioshaker = df_vl["bioshaker"].unique()
    cor_df = pd.DataFrame()

    # Compute correlation for every sample
    for pos in range(len(unique_IDs_vl)):
        df_vl_ID = df_vl[df_vl["Sample_ID"] == unique_IDs_vl[pos]]
        init_val = float((df_vl_ID["Measurement"].tolist()[0]))
        df_vl_ID.loc[:, "Correlation"] = df_vl_ID["Measurement"] / init_val
        cor_df = cor_df.append(df_vl_ID)
        df_vl_ID = pd.DataFrame()

    return cor_df


# ------ VOLUME LOSS COMPENSATION FOR EVERY SAMPLE ------


def compensation_lm(cor_df, df_gr, df_vl600, flag_svg=False, flag_loff=False):
    """Given the correlation between volume and time, a linear model is built
    and plotted, the correction is applied to the growth measurements using
    the linear model, returns a figure with the LM and a dataframe with the
    corrected growth rate measurements.

    Args:
        df_gr: dataframe containing only growth rate measurements and
        differential time in hours.
        cor_df: dataframe containing correlation measures between volume loss
        and time for different bioshakers.

    Returns:
        fig: figure representing the linear model between the correlation and
        the time for every bioshaker.
        df_gr_comp_out: dataframe containing corrected growth rate
        measurements and differential time in hours."""

    # For every bioshaker a linear model is created
    unique_bioshaker = cor_df["bioshaker"].unique()

    def linear(x, a, b):
        return a * x + b

    sns.set(style="white", palette="muted", color_codes=True)
    fig = plt.figure()
    fig.suptitle("Volume loss correlation over time", fontweight="bold")
    lm_eq = []

    # Iterate through unique shakers and compute linear model and plot
    for shaker in range(len(unique_bioshaker)):

        sub_cor_df = cor_df[cor_df["bioshaker"] == unique_bioshaker[shaker]]
        popt, pcov = curve_fit(
            linear,
            sub_cor_df["time_hours"],
            sub_cor_df["Correlation"],
            p0=[1, 1],
        )
        lm_eq.append(popt)

        ax = fig.add_subplot(
            math.ceil(len(unique_bioshaker)),
            math.ceil(len(unique_bioshaker) / 2),
            shaker + 1,
        )
        ax.plot(
            sub_cor_df["time_hours"],
            sub_cor_df["Correlation"],
            "o",
            label="Empirical data",
            markerfacecolor="skyblue",
            markeredgecolor="dodgerblue",
            alpha=0.5,
        )
        ax.plot(
            sub_cor_df["time_hours"],
            linear(sub_cor_df["time_hours"], *popt),
            "b-",
            label="Linear model",
            color="darkred",
        )
        ax.set_ylabel("Correlation", labelpad=10)
        ax.set_xlabel("Time (h)", labelpad=10)
        ax.set_title("\n" + str(unique_bioshaker[shaker]))
        plt.tight_layout()
    if not flag_loff:
        plt.legend(bbox_to_anchor=(1.2, 1.1))

    # Use the linear models to correct the volume loss by bioshaker
    df_gr_comp = pd.DataFrame()
    df_gr_comp_out = pd.DataFrame()
    # prepare df for background correction
    df_gr_background = pd.DataFrame()
    # prepare dict for volume correction correlation value
    corr_val_dict = {}
    for pos in range(len(lm_eq)):
        df_gr_comp = df_gr[df_gr["bioshaker"] == unique_bioshaker[pos]]
        # Save the volume correction correlation value
        corr_val_dict[pos] = {
            "BS": unique_bioshaker[pos],
            "Corr_val": lm_eq[pos][0],
        }

        # The following two loops are there for background correction
        # get OD600 values of volume correction samples to use for
        # background correction
        df_gr_background = df_vl600[
            df_vl600["bioshaker"] == unique_bioshaker[pos]
        ]
        sample_IDs = list(df_gr_comp["Sample_ID"].unique())
        for sample in sample_IDs:
            df_gr_comp_sample_limited = df_gr_comp[
                df_gr_comp["Sample_ID"] == sample
            ]
            times = list(
                df_gr_comp.loc[
                    df_gr_comp["Sample_ID"] == sample, "time_hours"
                ].unique()
            )
            for time in times:
                df_gr_comp_sample_time_limited = df_gr_comp_sample_limited[
                    df_gr_comp_sample_limited["time_hours"] == time
                ]
                df_gr_comp_index = df_gr_comp_sample_time_limited.index[0]
                df_gr_background_time_limited = df_gr_background[
                    df_gr_background["time_hours"] == time
                ]
                background_mean = np.mean(
                    df_gr_background_time_limited["Measurement"]
                )
                df_gr_comp.loc[df_gr_comp_index, "Measurement"] = (
                    df_gr_comp["Measurement"].loc[df_gr_comp_index]
                    - background_mean
                )
        # 1 is added instead of the calculated intercept to only account
        # for the trend of volume loss and not an adjusted intercept
        df_gr_comp.loc[:, "Correlation"] = (
            lm_eq[pos][0] * df_gr_comp["time_hours"] + 1
        )
        df_gr_comp.loc[:, "Measurement"] = (
            df_gr_comp["Measurement"] / df_gr_comp["Correlation"]
        )
        df_gr_comp_out = df_gr_comp_out.append(df_gr_comp)

    #  Save the volume correction correlation value
    corr_val = pd.DataFrame.from_dict(corr_val_dict, "index")
    corr_val.to_csv(
        "correlation_value.txt", header=None, index=None, sep=" ", mode="a"
    )

    if flag_svg:
        plt.savefig("lm_volume_loss.svg", dpi=250)
    else:
        plt.savefig("lm_volume_loss.png", dpi=250)
    plt.close()
    print("Volume loss correction : DONE")

    return fig, df_gr_comp_out


# ------ RESHAPE GROWTH RATE DATAFRAME FOR CROISSANCE INPUT ------


def reshape_dataframe(df_gr, flag_species=False, flag_bioshaker=False):
    """Collects the times belonging to every sample and creates a time column
    relative to a specific sample, returns the modified dataframe.

    Args:
        df_gr: dataframe containing growth rate measurements and differential
        time in hours.
        species_flag: flag that corresponds to the presence of more than one
        species (True), False if only one species

    Returns:
        if species_flag is False

            df_gr: dataframe with differential time measurements in hours
            displayed horizontally (one column containing the time measurements
            and one column contaning the OD measurements PER SAMPLE).

        if flag is True :

            df_gr_final:  dataframe with differential time measurements in
            hours displayed horizontally (one column containing the time
            measurements and one column contaning the OD measurements PER
            SAMPLE).
            df_gr_final_list: list of dataframes originated from df_gr_final
            and split by common sample species
    """

    df_gr_temp = df_gr
    # relevant variables
    cols = ["Sample_ID", "Measurement", "time_hours", "Species"]
    df_gr = df_gr[cols]

    # Get unique ID and times
    df_gr.loc[:, "Sample_ID"] = df_gr["Sample_ID"] + "_" + df_gr["Species"]
    df_gr.drop(columns=["Species"])
    unique_IDs = df_gr["Sample_ID"].unique()
    # unique_times = df_gr["time_hours"].unique()

    # Initiate new dataframe
    df_gr_final = pd.DataFrame()
    # An ID column is created for the measurement of every sample and another
    # column timeID is created to relate it to the times

    for i in range(len(unique_IDs)):

        n_list = df_gr.loc[
            df_gr["Sample_ID"] == unique_IDs[i], "Measurement"
        ].tolist()
        column1 = pd.DataFrame({unique_IDs[i]: n_list})
        t_list = df_gr.loc[
            df_gr["Sample_ID"] == unique_IDs[i], "time_hours"
        ].tolist()
        column2 = pd.DataFrame({"time_" + unique_IDs[i]: t_list})
        df_gr_final = pd.concat(
            [df_gr_final, column1], ignore_index=False, axis=1
        )
        df_gr_final = pd.concat(
            [df_gr_final, column2], ignore_index=False, axis=1
        )

    if not flag_species and not flag_bioshaker:
        return df_gr_final

    elif not flag_species and flag_bioshaker:

        df_gr_temp.loc[:, "Sample_ID"] = (
            df_gr_temp["Sample_ID"] + "_" + df_gr_temp["Species"]
        )
        unique_species = df_gr_temp["Species"].unique()
        unique_bioshaker = (df_gr_temp["Sample_ID"].str[0:3]).unique()
        # relevant variables
        cols = ["Sample_ID", "Measurement", "time_hours", "Species"]
        df_gr = df_gr_temp[cols]

        list_df_species = []
        df_gr_final_list = []
        df_temp = pd.DataFrame()

        for pos in range(len(unique_bioshaker)):

            df_temp = df_gr[
                df_gr_temp.Sample_ID.str.contains(unique_bioshaker[pos])
            ]
            list_df_species.append(df_temp)

            for df in list_df_species:

                unique_IDs = df["Sample_ID"].unique()
                # unique_times = df["time_hours"].unique()
                df_fin = pd.DataFrame()
                # Initialize new dataframe
                # An ID column is created for the measurement of every sample
                # and another column timeID is created to relate it to the
                # times

                for i in range(len(unique_IDs)):

                    m_list = df.loc[
                        df["Sample_ID"] == unique_IDs[i], "Measurement"
                    ].tolist()
                    column1 = pd.DataFrame({unique_IDs[i]: m_list})
                    t_list = df.loc[
                        df["Sample_ID"] == unique_IDs[i], "time_hours"
                    ].tolist()
                    column2 = pd.DataFrame({"time_" + unique_IDs[i]: t_list})
                    df_fin = pd.concat(
                        [df_fin, column1], ignore_index=False, axis=1
                    )
                    df_fin = pd.concat(
                        [df_fin, column2], ignore_index=False, axis=1
                    )
                    column1 = pd.DataFrame()
                    column2 = pd.DataFrame()

                df_gr_final_list.append(df_fin)

        return df_gr_final, df_gr_final_list

    else:

        df_gr_temp.loc[:, "Sample_ID"] = (
            df_gr_temp["Sample_ID"] + "_" + df_gr_temp["Species"]
        )
        unique_species = df_gr_temp["Species"].unique()
        unique_bioshaker = (df_gr_temp["Sample_ID"].str[0:3]).unique()
        # relevant variables
        cols = ["Sample_ID", "Measurement", "time_hours", "Species"]
        df_gr = df_gr_temp[cols]

        list_df_species = []
        df_gr_final_list = []

        if flag_bioshaker:

            for pos1 in range(len(unique_species)):

                df_temp = pd.DataFrame()

                for pos2 in range(len(unique_bioshaker)):

                    df_temp = df_gr[
                        df_gr.Species.str.contains(unique_species[pos1])
                    ]
                    df_temp = df_temp[
                        df_temp.Sample_ID.str.contains(unique_bioshaker[pos2])
                    ]
                    df_temp = df_temp.drop(columns=["Species"])
                    list_df_species.append(df_temp)

        elif not flag_bioshaker:

            for pos in range(len(unique_species)):

                df_temp = pd.DataFrame()
                df_temp = df_gr[
                    df_gr.Species.str.contains(unique_species[pos])
                ]
                df_temp = df_temp.drop(columns=["Species"])

                list_df_species.append(df_temp)

        for df in list_df_species:

            unique_IDs = df["Sample_ID"].unique()
            # unique_times = df["time_hours"].unique()
            df_fin = pd.DataFrame()
            # Initialize new dataframe
            # An ID column is created for the measurement of every
            # sample and another column timeID is created to relate
            # it to the times

            for i in range(len(unique_IDs)):

                m_list = df.loc[
                    df["Sample_ID"] == unique_IDs[i], "Measurement"
                ].tolist()
                column1 = pd.DataFrame({unique_IDs[i]: m_list})
                t_list = df.loc[
                    df["Sample_ID"] == unique_IDs[i], "time_hours"
                ].tolist()
                column2 = pd.DataFrame({"time_" + unique_IDs[i]: t_list})
                df_fin = pd.concat(
                    [df_fin, column1], ignore_index=False, axis=1
                )
                df_fin = pd.concat(
                    [df_fin, column2], ignore_index=False, axis=1
                )
                column1 = pd.DataFrame()
                column2 = pd.DataFrame()

            df_gr_final_list.append(df_fin)

        return df_gr_final, df_gr_final_list


# ----- AUTOMATED GROWTH ESTIMATION FOR EVERY SAMPLE  -----


def gr_estimation(df_gr_final):
    """removes outliers for every sample and outputs growth rate estimates
    for every given sample ID as a text file

    Args:
        df_gr_final: dataframe containing growth rate measurements and
        differential time in hours.

    Returns:
        estimations: List of growth rate estimations for every sample in
        df_gr_final
        errors: due to croissance noise handling some samples can not be
        estimated and list of series is returned for every non-estimated sample
    """

    # croissance series input format

    df_gr_est = df_gr_final.loc[:, ~df_gr_final.columns.str.startswith("time")]
    colnames = df_gr_est.columns.values
    # estimations = []
    errors = []
    # est_IDs = []
    # err_IDs = []
    df_data_series = pd.DataFrame()
    df_annotations = pd.DataFrame()
    list_annotations = []

    df_annotations.loc[:, "Parameter"] = [
        "Start",
        "End",
        "Slope",
        "Intercept",
        "n0",
        "SNR",
        "rank",
    ]

    for col in range(len(colnames)):

        # Series format for process_curve input
        my_series = pd.Series(
            data=(df_gr_final[colnames[col]]).tolist(),
            index=df_gr_final["time_" + colnames[col]].tolist(),
        )

        # Estimation computation
        with warnings.catch_warnings():
            warnings.simplefilter("error", OptimizeWarning)
            try:
                # Some samples are too noise to handle by the croissance
                # library and raise an error
                gr_estimation = process_curve(my_series)
            except Exception:
                # For those samples that raise errors, the outliers
                # are removed and a series is returned
                gr_estimation = remove_outliers(my_series)
                errors.append(colnames[col])
            except OptimizeWarning:
                # For those samples that raise errors, the outliers
                # are removed and a series is returned
                gr_estimation = remove_outliers(my_series)
                errors.append(colnames[col])

        # --Outlier free series--
        est_series = gr_estimation[0]
        # Dataframe generation with outlier free data
        df_temp = pd.DataFrame(
            {
                colnames[col] + "_time": est_series.index,
                colnames[col] + "_data": est_series.values,
            }
        )
        df_data_series = pd.concat(
            [df_data_series, df_temp], ignore_index=False, axis=1
        )

        # --Annotated growth curve--

        if colnames[col] in errors or len(gr_estimation[2]) == 0:

            if colnames[col] not in errors:

                errors.append(colnames[col])
            else:

                pass

        else:

            # Initialize objects
            list_annotations = []

            df_temp_annotations = pd.DataFrame()

            # Get annotations
            Annotated_gc = gr_estimation[2]

            try:

                # Extract annotations from namedtuple
                list_annotations.append(Annotated_gc[0].start)
                list_annotations.append(Annotated_gc[0].end)
                list_annotations.append(Annotated_gc[0].slope)
                list_annotations.append(Annotated_gc[0].intercept)
                list_annotations.append(Annotated_gc[0].n0)
                list_annotations.append(Annotated_gc[0].SNR)
                list_annotations.append(Annotated_gc[0].rank)

            except IndexError:

                errors.append(colnames[col])

            # Append Annotations to returned dataframe
            df_temp_annotations[colnames[col]] = list_annotations
            df_annotations = pd.concat(
                [df_annotations, df_temp_annotations],
                ignore_index=False,
                axis=1,
            )

    if len(errors) > 0 and len(list_annotations) != 0:

        print(
            "\nSome samples linear phase could not be estimated, the list \
            of non estimated samples can be seen in the \
            estimation_logfile.txt\n"
        )

    elif len(errors) > 0 and len(list_annotations) == 0:

        print(
            "\nNone of the samples linear phase could be estimated due to \
            noisy data\n"
        )

    return df_data_series, df_annotations, errors


# ----- ESTIMATION WRITTER TO XLSX FILE -----
# The writter function goes here


def estimation_writter(df_data_series, df_annotations, error_list):
    """Writes a xlsx file with the estimations for every sample and outputs
    the errors on a log file.

    Args:
        df_data_series: dataframe containing the time series without outliers.
         df_annotations: dataframe containing the annotations of the linear
         phase.
        error_list: list containing the non-estimated samples by croissance
        due to noisy data

    Returns:
        series_xlsx_file: file containing the estimations and IDs
        annotations_xlsx_file: file containing the data series and IDs without
        outliers of the non-estimated samples
        log_file: file containing the non estimated samples
    """

    df_data_series.to_excel(r"Data_series.xlsx", header=True, index=False)
    df_annotations.to_excel(r"Annotations.xlsx", header=True, index=False)

    outfile = open("estimations_logfile.txt", "w")

    outfile.write("List of non estimated samples :\n")

    for error in error_list:

        outfile.write(error + "\n")

    outfile.close()

    return None


# ----- CALCULATING GROWTH RATE FOR EACH TIME POINT -----


def step_gr_calculator(df, flag_svg=False):
    sample_name = df.columns.values[1]
    rates = []
    times = []
    for i, row_val in enumerate(df.iloc[:, 1]):
        if i == 0:
            continue
        else:
            previous_val = df.iloc[:, 1][i - 1]
            if previous_val <= 0 or row_val <= 0:
                continue
            else:
                previous_time = df.iloc[:, 0][i - 1]
                time_val = df.iloc[:, 0][i]
                gr = (np.log(row_val) - np.log(previous_val)) / (
                    time_val - previous_time
                )
                rates.append(gr)
                times.append(time_val)
    if rates:
        plt.violinplot(rates, positions=[0], showmeans=True, showextrema=True)
        plt.plot(
            times, rates, linestyle="-", color=(0.18, 0.31, 0.31), alpha=0.25
        )
        plt.ylabel("Growth rate ($h^{-1}$)", fontname="Arial", fontsize=12)
        plt.xlabel("Time (h)", fontname="Arial", fontsize=12)
        plt.title(
            "Growth rates of " + sample_name, fontname="Arial", fontsize=12
        )
        plt.tight_layout()
        if flag_svg:
            plt.savefig(
                "Temporary_GR_check/Temporary_GR_check_"
                + str(sample_name)
                + "_GRs.svg"
            )
        else:
            plt.savefig(
                "Temporary_GR_check/Temporary_GR_check_"
                + str(sample_name)
                + "_GRs.png"
            )

        plt.close()
    return sample_name, rates, times


# ----- PLOTTING GROWTH RATE CURVE -----


def gr_plots(
    df,
    sample,
    interpolationplot,
    color_=None,
    ind=False,
    legend_="bioshaker",
    title_="species",
    separate_species=False,
    flag_svg=False,
    flag_loff=False,
):
    """Generates a growth curve plot for a given series for common species,
    returns the plot.

    Args:
        df: dataframe containing differential times and OD measurements
        sample: sample used
        ind: flag that indicates to output individual plots if True or merged
        plots by sample species if False

    Returns:
        fig: object containing the figure
        plt.savefig: saving the figure as a png or svg file
    """

    # Create plots individually

    sns.set(style="white", palette="muted", color_codes=True)

    # Individual plots
    if ind:

        if interpolationplot:
            try:
                x_new = np.linspace(df["time"].min(), df["time"].max(), 500)
                a_BSpline = interpolate.make_interp_spline(
                    df["time"], df[sample]
                )
                y_new = a_BSpline(x_new)
                plt.figure()
                plt.plot(x_new, y_new)

            except ValueError:
                pass

        fig = plt.scatter(
            df["time"],
            df[sample],
            5,
            facecolor=(0.18, 0.31, 0.31),
            label=sample,
        )
        plt.plot(
            df["time"],
            df[sample],
            linestyle="-",
            color=(0.18, 0.31, 0.31),
            alpha=0.25,
        )
        plt.ylabel("Absorbance (OD)", fontname="Arial", fontsize=12)
        plt.xlabel("Time (h)", fontname="Arial", fontsize=12)
        plt.title(
            "Growth curve of " + str(sample), fontname="Arial", fontsize=12
        )
        if not flag_loff:
            plt.legend(bbox_to_anchor=(1.05, 1.0), loc="upper left")
        plt.tight_layout()
        if flag_svg:
            return fig, plt.savefig(str(sample) + "_GR_curve.svg")
        else:
            return fig, plt.savefig(str(sample) + "_GR_curve.png")

    # Create plots by combined by species
    elif not ind:

        # Set the legend label
        if legend_ == "bioshaker":

            legend_label = sample[:3]

        elif legend_ == "species":

            legend_label = re.search(
                r"^\S{3}.\d?_?\S{2,3}_(\S+)", sample
            ).group(1)

        else:

            legend_label = ""

        # Set the title label
        if title_ == "bioshaker":

            title_label = sample[:3]

        elif title_ == "species":

            title_label = re.search(
                r"^\S{3}.\d?_?\S{2,3}_(\S+)", sample
            ).group(1)

        elif title_ == "species_bioshaker":

            title_label = (
                sample[:3]
                + "_"
                + re.search(r"^\S{3}.\d?_?\S{2,3}_(\S+)", sample).group(1)
            )

        else:
            pass

        if interpolationplot:
            try:
                x_new = np.linspace(df["time"].min(), df["time"].max(), 500)
                a_BSpline = interpolate.make_interp_spline(
                    df["time"], df[sample]
                )
                y_new = a_BSpline(x_new)
                plt.plot(x_new, y_new, color=color_, label=legend_label)

            except ValueError:
                pass

        if separate_species:
            fig = plt.scatter(
                df["time"],
                df[sample],
                5,
                facecolor=(0.18, 0.31, 0.31),
                color=color_,
                label=legend_label,
                linestyle="-",
            )
            plt.plot(
                df["time"], df[sample], linestyle="-", color=color_, alpha=0.1
            )
            plt.ylabel("Absorbance (OD)", fontname="Arial", fontsize=12)
            plt.xlabel("Time (h)", fontname="Arial", fontsize=12)
            plt.title(
                "Growth curves of all species", fontname="Arial", fontsize=12
            )
            plt.tight_layout()

        else:
            fig = plt.scatter(
                df["time"],
                df[sample],
                5,
                facecolor=(0.18, 0.31, 0.31),
                color=color_,
                label=legend_label,
                linestyle="-",
            )
            plt.plot(
                df["time"], df[sample], linestyle="-", color=color_, alpha=0.1
            )
            plt.ylabel("Absorbance (OD)", fontname="Arial", fontsize=12)
            plt.xlabel("Time (h)", fontname="Arial", fontsize=12)
            plt.title(
                "Growth curve of " + str(title_label),
                fontname="Arial",
                fontsize=12,
            )
            plt.tight_layout()

        return fig


def stats_summary(df_annotations):

    """Generates a statistics summary of the growth rate annotations.

    Args:
        df_annotations: dataframe containing growth rate annotations

    Returns:
        summary_df: dataframe containing the summary statistics
    """

    # -- Summary by species and bioshaker --

    # Label column names of df according to species

    # Initialize object
    summary_df = pd.DataFrame()

    # Species and bioshaker labels
    species_list = [
        re.sub(r"\S+[.]?\S+[_](\S+)", r"\1", i)
        for i in (df_annotations.columns.values[1:])
    ]
    x = slice(0, 3)
    bioshaker_list = [i[x] for i in (df_annotations.columns.values[1:])]
    summary_df.loc[:, "species"] = species_list
    summary_df.loc[:, "bioshaker"] = bioshaker_list

    # Append annotations as rows in df_summary
    summary_df.loc[:, "start"] = pd.to_numeric(
        (df_annotations.iloc[0, 1:]).values
    )
    summary_df.loc[:, "end"] = pd.to_numeric(
        (df_annotations.iloc[1, 1:]).values
    )
    summary_df.loc[:, "slope"] = pd.to_numeric(
        (df_annotations.iloc[2, 1:]).values
    )
    summary_df.loc[:, "intercep"] = pd.to_numeric(
        (df_annotations.iloc[3, 1:]).values
    )
    summary_df.loc[:, "n0"] = pd.to_numeric(
        (df_annotations.iloc[4, 1:]).values
    )
    summary_df.loc[:, "SNR"] = pd.to_numeric(
        (df_annotations.iloc[5, 1:]).values
    )
    # Mean and std on annotations per species
    summary_df_species = summary_df.drop(columns=["bioshaker"])
    mean_df_species = (
        summary_df_species.groupby("species").mean().reset_index()
    )
    std_df_species = summary_df_species.groupby("species").std().reset_index()

    # Mean and std on annotations split by bioshaker and species
    mean_df_bs = (
        summary_df.groupby(["species", "bioshaker"]).mean().reset_index()
    )
    std_df_bs = (
        summary_df.groupby(["species", "bioshaker"]).std().reset_index()
    )

    # Create a Pandas Excel writer using XlsxWriter as the engine.
    writer = pd.ExcelWriter("summary_stats.xlsx", engine="xlsxwriter")

    # Write each dataframe to a different worksheet.
    mean_df_species.to_excel(writer, sheet_name="species mean")
    mean_df_bs.to_excel(writer, sheet_name="species bioshaker mean")
    std_df_species.to_excel(writer, sheet_name="Species std")
    std_df_bs.to_excel(writer, sheet_name="Species bioshaker std")

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()

    return summary_df, mean_df_species, mean_df_bs


def stats_plot(summary_df, flag_svg=False):
    """Box plots of annotation growth rate parameters by species and bioshaker
    Args:
    summary_df : dataframe containing the annotation parameters
    Return:
    call: string with status of plots creation
    """

    if len(summary_df.index) == 0:
        call = ("Summary statistics plots not computed: No parameters were "
                "estimated and thus no plots can be shown")
        return call

    else:
        plt.close()
        sns.boxplot(
            x="species",
            y="start",
            hue="bioshaker",
            data=summary_df,
            palette="Pastel1",
        )
        if flag_svg:
            plt.savefig("start_boxplot.svg", dpi=250)
        else:
            plt.savefig("start_boxplot", dpi=250)
        plt.close()

        # plot_end = sns.boxplot(x="species", y="end", hue="bioshaker",
        #                       data=summary_df, palette="Pastel1")
        # plt.savefig("end_boxplot",  dpi=250)
        # plt.close()

        # plot_slope = sns.boxplot(x="species", y="slope", hue="bioshaker",
        #                         data=summary_df, palette="Pastel1")
        # plt.savefig("slope_boxplot",  dpi=250)
        # plt.close()

        # plot_intercep = sns.boxplot(x="species", y="intercep",
        #                            hue="bioshaker",
        #                            data=summary_df, palette="Pastel1")
        # plt.savefig("intercept_boxplot",  dpi=250)
        # plt.close()

        # plot_n0 = sns.boxplot(x="species", y="n0", hue="bioshaker",
        #                      data=summary_df, palette="Pastel1")
        # plt.savefig("n0_boxplot",  dpi=250)
        # plt.close()

        # plot_SNR = sns.boxplot(x="species", y="SNR", hue="bioshaker",
        #                       data=summary_df, palette="Pastel1")
        # plt.savefig("SNR_boxplot",  dpi=250)
        # plt.close()

        call = "Summary statistics : DONE"

        return call


def exponential(x, intercep, slope, n0):
    """Calculates the od for a given time with the parameters estimated with
    the croissance package"""
    estimation = n0 * np.exp(slope * x)
    return estimation


def interpolation(od_measurements, df_annotations, mean_df_bs):
    """Interpolates the values of given od readings and returns growth rate
    measurements.

    Args:
        od_measurements: Dataframe containing the desired samples to estimate
        df_annotations: Dataframe containing growth rate annotations of every
        sample
        mean_df_bs: Dataframe containing the growth rate annotations grouped
        by common species and bioshaker

    Returns:
        od_measurements: Returned estimated od measurements and if the
        prediction lies in the model's range
    """
    od_measurements = pd.read_csv(od_measurements, sep="\t")

    # estimation using only well specific fitted regression model

    # Initialize list object
    estimation_list = list()
    range_list = list()

    # List of samples to estimate
    estimated_samples_list = od_measurements["Sample_ID"]
    time_points_list = od_measurements["Time"]
    method_used_list = od_measurements["Regression_used"]

    # Computation of estimations for every sample
    for sample_pos in range(len(estimated_samples_list)):

        time = float(time_points_list[sample_pos])
        method = method_used_list[sample_pos]

        if method == "well":

            parameters = df_annotations[
                estimated_samples_list[sample_pos]
            ].tolist()
            estimation = exponential(
                time, parameters[3], parameters[2], parameters[4]
            )

            if time < parameters[0] or time > parameters[1]:

                estimation_range = "outside model range"
            else:

                estimation_range = "inside model range"

        else:

            # subset to select appropriate bioshaker parameters
            df_temp = mean_df_bs[
                (
                    mean_df_bs["bioshaker"]
                    == (estimated_samples_list[sample_pos])[:3]
                )
            ]

            # subset to select appropriate species parameteres
            parameters = df_temp[
                df_temp["species"]
                == re.search(
                    r"([A-Z0-9]+$)", estimated_samples_list[sample_pos]
                ).group(1)
            ]

            # estimation
            estimation = exponential(
                time,
                parameters["intercep"].values[0],
                parameters["slope"].values[0],
                parameters["n0"].values[0],
            )

            # extract start and end times
            start = parameters["start"].values[0]
            end = parameters["end"].values[0]

            if time < start or time > end:

                estimation_range = "outside model range"

            else:

                estimation_range = "inside model range"

        # output if the time is outside the range of the model

        estimation_list.append(estimation)
        range_list.append(estimation_range)

    # Append estimation and model range to od_measurements dataframe
    od_measurements.loc[:, "Estimation"] = estimation_list
    od_measurements.loc[:, "Estimation range"] = range_list

    # Drop unnamed columns
    od_measurements = od_measurements.loc[
        :, ~od_measurements.columns.str.contains("^Unnamed")
    ]

    # Export to excel
    od_measurements.to_excel(
        r"interpolation_results.xlsx", header=True, index=False
    )

    return od_measurements
