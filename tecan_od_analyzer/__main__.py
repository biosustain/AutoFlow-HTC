# -*- coding: utf-8 -*-

# IMPORTANT FOR REVIEW:
# unused variables are commented out - need to be revised

# Libraries
import sys
from tecan_od_analyzer.tecan_od_analyzer import (
    argument_parser,
    gr_plots,
    parse_data,
    read_xlsx,
    sample_outcome,
    time_formater,
    reshape_dataframe,
    vol_correlation,
    compensation_lm,
    gr_estimation,
    estimation_writter,
    stats_summary,
    input_output,
    stats_plot,
    step_gr_calculator,
)
from croissance.estimation.outliers import remove_outliers
import pandas as pd
import re
import os
import matplotlib.pyplot as plt
from pandas import Series
import itertools


def main():

    pd.set_option("mode.chained_assignment", None)

    # ----- INPUT INTERPRETATION AND FILE READING ------

    # Interpretation of the command line arguments

    (
        flag_all,
        flag_est,
        flag_sum,
        flag_fig,
        flag_ind,
        flag_bioshakercolor,
        flag_volumeloss,
        flag_bioshaker,
        flag_interpolation,
        cmd_dir,
        path,
        interpolationplot,
        flag_svg,
        flag_os
    ) = argument_parser(argv_list=sys.argv)

    # path input and output directory creation
    dir_ = input_output(cmd_dir, path)

    # Data parsing
    parse_data()

    # Data reading
    try:
        df_raw = read_xlsx()

    except FileNotFoundError:
        sys.exit(
            "Error: The output file from the autoflow_parser was not \
                 found"
        )

    # ----- LABELLING ACCORDING TO SAMPLE PURPOSE -----

    # Separate data depending on sample purpose (growth rate or volume loss)
    try:
        df_gr, df_vl450, df_vl600 = sample_outcome("calc.tsv", df_raw)

    except FileNotFoundError:
        sys.exit("Error!\n calc.tsv file not found")

    # ----- FORMATING TIME VARIABLE TO DIFFERENTIAL HOURS -----

    df_gr = time_formater(df_gr)
    df_vl450 = time_formater(df_vl450)
    df_vl600 = time_formater(df_vl600)

    # Assess different species, this will be used as an argument in the
    # reshape method
    if len(df_gr["Species"].unique()) > 1:
        multiple_species_flag = True

    else:
        multiple_species_flag = False

    # Once the data is read, change dir to output dir
    os.chdir(dir_)

    # ----- CORRELATION AND CORRECTION -----

    if flag_volumeloss:

        # Compute correlation for every sample
        cor_df = vol_correlation(df_vl450)
        # Compute compensation
        fig, df_gr = compensation_lm(
            cor_df, df_gr, df_vl600, flag_svg=flag_svg
        )

    else:
        print("Volume loss correction : NOT COMPUTED")

        # bioshakers = df_gr["bioshaker"].unique()

    # ----- DATA RESHAPING FOR CROISSANCE INPUT REQUIREMENTS -----

    # Reshape data for croissance input

    # If only one species one dataframe is returned only
    if (
        not multiple_species_flag
        and not flag_bioshaker
        and not flag_bioshakercolor
    ):
        df_gr_final = reshape_dataframe(
            df_gr, flag_species=multiple_species_flag, flag_bioshaker=False
        )

    # Split dataframes by species and bioshakers
    elif multiple_species_flag and flag_bioshaker:
        df_gr_final, df_gr_final_list = reshape_dataframe(
            df_gr, flag_species=multiple_species_flag, flag_bioshaker=True
        )

    # If more than one species, the dataframe is split by species and returned
    # as a list of dataframes.
    # The unsplit dataframe is also returned, which will be used for the
    # summary and estimations
    elif multiple_species_flag and not flag_bioshaker:
        df_gr_final, df_gr_final_list = reshape_dataframe(
            df_gr, flag_species=multiple_species_flag, flag_bioshaker=False
        )

    else:
        df_gr_final, df_gr_final_list = reshape_dataframe(
            df_gr, flag_species=multiple_species_flag, flag_bioshaker=True
        )

    # ----- COMPLETE FUNCTIONALITY : ESTIMATIONS, FIGURES AND
    # STATISTICAL SUMMARY -----

    if flag_all or flag_est or flag_sum:

        # ----- ESTIMATIONS -----

        # Compute estimations
        df_data_series, df_annotations, error_list = gr_estimation(df_gr_final)

        # Write estimation files
        estimation_writter(df_data_series, df_annotations, error_list)
        print("Growth rate phases estimation : DONE")

    if flag_all or flag_sum:

        # ----- SUMMARY STATISTICS -----

        # Compute summary statistics
        summary_df, mean_df_species, mean_df_bs = stats_summary(df_annotations)

        # Compute plot of the annotation parameters
        status = stats_plot(summary_df, flag_svg=flag_svg)
        print(status)

    # ----- CALCULATION OF GROWTH RATES BETWEEN EACH POINT -----

    df_gr_est = df_gr_final.loc[:, ~df_gr_final.columns.str.startswith("time")]
    colnames = df_gr_est.columns.values

    os.mkdir("Temporary_GR_check")

    step_df = pd.DataFrame(columns=["Sample_name", "T2", "GR_T1_to_T2"])

    for col in range(len(colnames)):
        my_series = pd.Series(
            data=(df_gr_final[colnames[col]]).tolist(),
            index=df_gr_final["time_" + colnames[col]].tolist(),
        )
        my_series = Series.dropna(my_series)
        df = pd.DataFrame(
            {"time": my_series.index, colnames[col]: my_series.values}
        )
        sample_name, rates, times = step_gr_calculator(df, flag_svg=flag_svg)

        for cnt, rate in enumerate(rates):

            temp_step_df = pd.DataFrame(
                {
                    "Sample_name": [sample_name],
                    "T2": [times[cnt]],
                    "GR_T1_to_T2": [rates[cnt]],
                }
            )

            step_df = step_df.append(temp_step_df)

    # Create a Pandas Excel writer using XlsxWriter as the engine.
    writer = pd.ExcelWriter(
        "Temporary_GR_check/stepwise_growth_rates.xlsx", engine="xlsxwriter"
    )
    step_df.to_excel(writer, sheet_name="growth_rates", index=False)
    writer.save()

    print("Calculating specific growth rates for each interval : DONE")

    if flag_all or flag_fig:

        # ----- FIGURES -----

        # Get plots individually for every sample

        if flag_ind:

            # Get plots for every sample

            df_gr_est = df_gr_final.loc[
                :, ~df_gr_final.columns.str.startswith("time")
            ]
            colnames = df_gr_est.columns.values

            for col in range(len(colnames)):
                my_series = pd.Series(
                    data=(df_gr_final[colnames[col]]).tolist(),
                    index=df_gr_final["time_" + colnames[col]].tolist(),
                )
                my_series = Series.dropna(my_series)
                # Extract series without outliers
                clean_series = remove_outliers(my_series)[0]
                df = pd.DataFrame(
                    {
                        "time": clean_series.index,
                        colnames[col]: clean_series.values,
                    }
                )
                gr_plots(df, colnames[col], ind=True,
                         interpolationplot=interpolationplot,
                         flag_svg=flag_svg)
                plt.close()

        # Get plots combined together by species

        elif not flag_ind:

            # Get plots combined by species and colored by bioshaker
            # plot without bioshaker coloring (combined by species and
            # containing the two bioshakers undiferentiated)

            if flag_bioshakercolor and not flag_bioshaker:

                color_palette = "r"

                if not multiple_species_flag:

                    df_gr_est = df_gr_final.loc[
                        :, ~df_gr_final.columns.str.startswith("time")
                    ]
                    colnames = df_gr_est.columns.values

                    plt.figure()

                    for col in range(len(colnames)):

                        bioshaker_label = re.search(
                            r"([B][S]\d)", colnames[col]
                        ).group(1)
                        my_series = pd.Series(
                            data=(df_gr_final[colnames[col]]).tolist(),
                            index=df_gr_final[
                                "time_" + colnames[col]
                            ].tolist(),
                        )
                        my_series = Series.dropna(my_series)
                        # Extract series without outliers
                        clean_series = remove_outliers(my_series)[0]
                        df = pd.DataFrame(
                            {
                                "time": clean_series.index,
                                colnames[col]: clean_series.values,
                            }
                        )
                        gr_plots(
                            df,
                            colnames[col],
                            color_=color_palette,
                            legend_="exclude",
                            title_="species",
                            interpolationplot=interpolationplot,
                            flag_svg=flag_svg,
                        )

                    last_name = colnames[col]
                    bioshaker_ = last_name[:3]
                    species_ = re.search(
                        r"^\S{3}.\d?_?\S{2,3}_(\S+)", last_name
                    ).group(1)
                    if flag_svg:
                        plt.savefig(species_ + "_GR_curve.svg", dpi=250)
                    else:
                        plt.savefig(species_ + "_GR_curve.png", dpi=250)

                else:
                    for df_gr_final in df_gr_final_list:
                        df_gr_est = df_gr_final.loc[
                            :, ~df_gr_final.columns.str.startswith("time")
                        ]
                        colnames = df_gr_est.columns.values

                        plt.figure()

                        for col in range(len(colnames)):

                            bioshaker_label = re.search(
                                r"([B][S]\d)", colnames[col]
                            ).group(1)
                            my_series = pd.Series(
                                data=(df_gr_final[colnames[col]]).tolist(),
                                index=df_gr_final[
                                    "time_" + colnames[col]
                                ].tolist(),
                            )
                            my_series = Series.dropna(my_series)
                            # Extract series without outliers
                            clean_series = remove_outliers(my_series)[0]
                            df = pd.DataFrame(
                                {
                                    "time": clean_series.index,
                                    colnames[col]: clean_series.values,
                                }
                            )
                            gr_plots(
                                df,
                                colnames[col],
                                color_=color_palette,
                                legend_="exclude",
                                title_="species",
                                interpolationplot=interpolationplot,
                                flag_svg=flag_svg,
                            )

                        last_name = colnames[col]
                        bioshaker_ = last_name[:3]
                        species_ = re.search(
                            r"^\S{3}.\d?_?\S{2,3}_(\S+)", last_name
                        ).group(1)
                        if flag_svg:
                            plt.savefig(species_ + "_GR_curve.svg", dpi=250)
                        else:
                            plt.savefig(species_ + "_GR_curve.png", dpi=250)

            # Get plots split by species and bioshaker
            # Add new flag for this
            elif flag_os:

                color_palette = "r"

                for df_gr_final in df_gr_final_list:
                    if not df_gr_final.empty:
                        df_gr_est = df_gr_final.loc[
                            :, ~df_gr_final.columns.str.startswith("time")
                        ]
                        colnames = df_gr_est.columns.values

                        plt.figure()

                        for col in range(len(colnames)):
                            bioshaker_label = re.search(
                                r"([B][S]\d)", colnames[col]
                            ).group(1)
                            my_series = pd.Series(
                                data=(df_gr_final[colnames[col]]).tolist(),
                                index=df_gr_final[
                                    "time_" + colnames[col]
                                ].tolist(),
                            )
                            my_series = Series.dropna(my_series)
                            # Extract series without outliers
                            clean_series = remove_outliers(my_series)[0]
                            df = pd.DataFrame(
                                {
                                    "time": clean_series.index,
                                    colnames[col]: clean_series.values,
                                }
                            )
                            gr_plots(
                                df,
                                colnames[col],
                                color_=color_palette,
                                legend_="exclude",
                                title_="species_bioshaker",
                                interpolationplot=interpolationplot,
                                flag_svg=flag_svg,
                            )

                        last_name = colnames[col]
                        bioshaker_ = last_name[:3]
                        species_ = re.search(
                            r"^\S{3}.\d?_?\S{2,3}_(\S+)", last_name
                        ).group(1)
                        if flag_svg:
                            plt.savefig(
                                bioshaker_ + "_" + species_ + "_GR_curve.svg",
                                dpi=250,
                            )
                        else:
                            plt.savefig(
                                bioshaker_ + "_" + species_ + "_GR_curve.png",
                                dpi=250,
                            )
                        # plt.close()

            # Get plots split by bioshaker and coloured by species

            elif flag_bioshaker and not flag_ind:

                bioshaker_list = (df_gr["Sample_ID"]).str.slice(0, 3).unique()
                species_list = (df_gr["Species"]).unique()
                colors = itertools.cycle(["g", "b", "r", "c"])
                color_dict = dict()

                df_gr_final_total = pd.concat(df_gr_final_list, axis=1)
                for species in species_list:
                    color_dict.update({species: next(colors)})
                for bioshaker in bioshaker_list:
                    df_gr_bioshaker_cols = [col for col in
                                            df_gr_final_total.columns
                                            if bioshaker in col]
                    df_gr_bioshaker = df_gr_final_total[df_gr_bioshaker_cols]
                    if len(df_gr_bioshaker) > 0:
                        df_gr_est = df_gr_bioshaker.loc[
                            :, ~df_gr_bioshaker.columns.str.startswith("time")
                        ]
                        colnames = df_gr_est.columns.values

                        plt.figure()

                        start_leg = ""

                        for col in range(len(colnames)):
                            bioshaker_label = re.search(
                                r"([B][S]\d)", colnames[col]
                            ).group(1)
                            my_series = pd.Series(
                                data=(df_gr_bioshaker[colnames[col]]).tolist(),
                                index=df_gr_bioshaker[
                                    "time_" + colnames[col]
                                ].tolist(),
                            )
                            my_series = Series.dropna(my_series)
                            # Extract series without outliers
                            clean_series = remove_outliers(my_series)[0]
                            df = pd.DataFrame(
                                {
                                    "time": clean_series.index,
                                    colnames[col]: clean_series.values,
                                }
                            )

                            last_name = colnames[col]
                            species_ = re.search(
                                r"^\S{3}.\d?_?\S{2,3}_(\S+)", last_name
                            ).group(1)

                            # First time
                            if start_leg == "":
                                gr_plots(
                                    df,
                                    colnames[col],
                                    color_=color_dict[species_],
                                    legend_="species",
                                    title_="bioshaker",
                                    interpolationplot=interpolationplot,
                                    flag_svg=flag_svg,
                                )

                                start_leg = species_

                            # New Species
                            elif species_ != start_leg:

                                gr_plots(
                                    df,
                                    colnames[col],
                                    color_=color_dict[species_],
                                    legend_="species",
                                    title_="bioshaker",
                                    interpolationplot=interpolationplot,
                                    flag_svg=flag_svg,
                                )
                                start_leg = species_

                            # Repeated species
                            else:
                                gr_plots(
                                    df,
                                    colnames[col],
                                    color_=color_dict[species_],
                                    legend_="",
                                    title_="bioshaker",
                                    interpolationplot=interpolationplot,
                                    flag_svg=flag_svg,
                                )
                        plt.legend()
                        last_name = colnames[col]
                        bioshaker_ = last_name[:3]
                        species_ = re.search(
                            r"^\S{3}.\d?_?\S{2,3}_(\S+)", last_name
                        ).group(1)
                        if flag_svg:
                            plt.savefig(
                                bioshaker_ + "_GR_curve.svg",
                                dpi=250,
                            )
                        else:
                            plt.savefig(
                                bioshaker_ + "_GR_curve.png",
                                dpi=250,
                            )
                        plt.close()

            # Default plot with bioshaker coloring (combined by species and
            # all together)

            else:

                # Color the plot according to bioshaker

                bioshaker_list = (df_gr["Sample_ID"]).str.slice(0, 3).unique()
                colors = itertools.cycle(["g", "b", "r", "c"])
                color_dict = dict()

                for bioshaker in bioshaker_list:
                    color_dict.update({bioshaker: next(colors)})

                # Plots when only one species is present

                if not multiple_species_flag:

                    for df_gr_est in df_gr_final_list:

                        df_gr_est = df_gr_final.loc[
                            :, ~df_gr_final.columns.str.startswith("time")
                        ]
                        colnames = df_gr_est.columns.values

                        plt.figure()

                        start_leg = ""

                        for col in range(len(colnames)):

                            bioshaker_label = re.search(
                                r"([B][S]\d)", colnames[col]
                            ).group(1)
                            my_series = pd.Series(
                                data=(df_gr_final[colnames[col]]).tolist(),
                                index=df_gr_final[
                                    "time_" + colnames[col]
                                ].tolist(),
                            )
                            my_series = Series.dropna(my_series)
                            # Extract series without outliers
                            clean_series = remove_outliers(my_series)[0]
                            df = pd.DataFrame(
                                {
                                    "time": clean_series.index,
                                    colnames[col]: clean_series.values,
                                }
                            )

                            # First time
                            if start_leg == "":

                                gr_plots(
                                    df,
                                    colnames[col],
                                    color_=color_dict[bioshaker_label],
                                    legend_="bioshaker",
                                    title_="species",
                                    interpolationplot=interpolationplot,
                                    flag_svg=flag_svg,
                                )
                                start_leg = (colnames[col])[:3]

                            # New Bioshaker
                            elif (colnames[col])[:3] != start_leg:

                                gr_plots(
                                    df,
                                    colnames[col],
                                    color_=color_dict[bioshaker_label],
                                    legend_="bioshaker",
                                    title_="species",
                                    interpolationplot=interpolationplot,
                                    flag_svg=flag_svg,
                                )
                                start_leg = (colnames[col])[:3]

                            # Repeated bioshaker
                            else:
                                gr_plots(
                                    df,
                                    colnames[col],
                                    color_=color_dict[bioshaker_label],
                                    legend_="exclude",
                                    title_="species",
                                    interpolationplot=interpolationplot,
                                    flag_svg=flag_svg,
                                )

                        last_name = colnames[col]
                        bioshaker_ = last_name[:3]
                        species_ = re.search(
                            r"^\S{3}.\d?_?\S{2,3}_(\S+)", last_name
                        ).group(1)

                        plt.legend(
                            bbox_to_anchor=(1.05, 1.0), loc="upper left"
                        )
                        if flag_svg:
                            plt.savefig(species_ + "_GR_curve.svg", dpi=250)
                        else:
                            plt.savefig(species_ + "_GR_curve.png", dpi=250)

                # Plots when more than one species is present

                else:
                    for df_gr_final in df_gr_final_list:

                        df_gr_est = df_gr_final.loc[
                            :, ~df_gr_final.columns.str.startswith("time")
                        ]
                        colnames = df_gr_est.columns.values

                        plt.figure()

                        start_leg = ""

                        for col in range(len(colnames)):
                            bioshaker_label = re.search(
                                r"([B][S]\d)", colnames[col]
                            ).group(1)
                            my_series = pd.Series(
                                data=(df_gr_final[colnames[col]]).tolist(),
                                index=df_gr_final[
                                    "time_" + colnames[col]
                                ].tolist(),
                            )
                            my_series = Series.dropna(my_series)
                            # Extract series without outliers
                            clean_series = remove_outliers(my_series)[0]
                            df = pd.DataFrame(
                                {
                                    "time": clean_series.index,
                                    colnames[col]: clean_series.values,
                                }
                            )

                            # First time
                            if start_leg == "" and (colnames[col])[:3] != "":
                                gr_plots(
                                    df,
                                    colnames[col],
                                    color_=color_dict[bioshaker_label],
                                    legend_="bioshaker",
                                    title_="species",
                                    interpolationplot=interpolationplot,
                                    flag_svg=flag_svg,
                                )
                                start_leg = (colnames[col])[:3]

                            # New Bioshaker
                            elif (colnames[col])[:3] != start_leg:

                                gr_plots(
                                    df,
                                    colnames[col],
                                    color_=color_dict[bioshaker_label],
                                    legend_="bioshaker",
                                    title_="species",
                                    interpolationplot=interpolationplot,
                                    flag_svg=flag_svg,
                                )
                                start_leg = (colnames[col])[:3]

                            # Repeated bioshaker
                            else:
                                gr_plots(
                                    df,
                                    colnames[col],
                                    color_=color_dict[bioshaker_label],
                                    legend_="exclude",
                                    title_="species",
                                    interpolationplot=interpolationplot,
                                    flag_svg=flag_svg,
                                )

                        plt.legend()
                        last_name = colnames[col]
                        species_name = re.search(
                            r"^\S{3}.\d?_?\S{2,3}_(\S+)", last_name
                        ).group(1)
                        # species_name = last_name[-6:]
                        if flag_svg:
                            plt.savefig(
                                species_name + "_GR_curve.svg", dpi=250
                            )
                        else:
                            plt.savefig(
                                species_name + "_GR_curve.png", dpi=250
                            )
                    df_gr_final_total = pd.concat(df_gr_final_list, axis=1)
                    df_gr_est = df_gr_final_total.loc[
                        :, ~df_gr_final_total.columns.str.startswith("time")
                    ]
                    colnames = df_gr_est.columns.values

                    plt.figure()
                    species_list = []

                    color_palette = ["r", "b", "y", "g", "m", "c"] * 20
                    for col in range(len(colnames)):

                        bioshaker_label = re.search(
                            r"([B][S]\d)", colnames[col]
                        ).group(1)
                        my_series = pd.Series(
                            data=(df_gr_final_total[colnames[col]]).tolist(),
                            index=df_gr_final_total[
                                "time_" + colnames[col]
                            ].tolist(),
                        )
                        my_series = Series.dropna(my_series)
                        # Extract series without outliers
                        clean_series = remove_outliers(my_series)[0]
                        df = pd.DataFrame(
                            {
                                "time": clean_series.index,
                                colnames[col]: clean_series.values,
                            }
                        )
                        last_name = colnames[col]
                        bioshaker_ = last_name[:3]
                        species_ = re.search(
                            r"^\S{3}.\d?_?\S{2,3}_(\S+)", last_name
                        ).group(1)
                        species_list.append(species_)
                        species_list = list(set(species_list))
                        col_nr = len(species_list) - 1
                        gr_plots(
                            df,
                            colnames[col],
                            color_=color_palette[col_nr],
                            legend_="species",
                            title_="species",
                            interpolationplot=interpolationplot,
                            separate_species=True,
                            flag_svg=flag_svg,
                        )
                    if flag_svg:
                        plt.savefig("Combined_GR_curve.svg", dpi=250)
                    else:
                        plt.savefig("Combined_GR_curve.png", dpi=250)

        print("Plotting growth curves : DONE")

    if flag_interpolation:
        # od_measurements = interpolation("../od_measurements.tsv",
        #                                 df_annotations, mean_df_bs)

        print("Computing optical density estimations : DONE")
