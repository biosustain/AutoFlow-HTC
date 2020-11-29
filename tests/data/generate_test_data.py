# generate test_data
# Last date : 20 Nov 2020
# By : Matthias Mattanovich (matmat@biosustain.dtu.dk)
# This script is intended to generate sample data and save them into the
# test_data file. The saved objects will then be used to test the
# tecan_od_analyzer using unit testing.

import pickle
import pandas as pd
from tecan_od_analyzer.tecan_od_analyzer import read_xlsx, \
    sample_outcome, time_formater, reshape_dataframe, \
    vol_correlation, compensation_lm, gr_estimation, stats_summary, \
    interpolation, exponential

pd.set_option('mode.chained_assignment', None)
# Use pickle to save python variables
filehandler = open("test_data.obj", 'wb')

# Generate variables to save
df_gr, df_vl450, df_vl600 = sample_outcome("calc.tsv", read_xlsx())
df_gr_time = time_formater(df_gr)
df_vl_time = time_formater(df_vl450)
df_vl600_time = time_formater(df_vl600)
cor_df = vol_correlation(df_vl_time)
fig, df_gr_comp = compensation_lm(cor_df, df_gr_time, df_vl600_time)
df_gr_final = reshape_dataframe(df_gr_comp)
df_data_series, df_annotations, errors = gr_estimation(df_gr_final)
summary_df, mean_df_species, mean_df_bs = stats_summary(df_annotations)
od_measurements = interpolation("od_measurements.tsv", df_annotations,
                                mean_df_bs)
estimation = exponential(1, 2, 3, 0)

pickle.dump([df_gr, df_vl450, df_vl600, df_gr_time, df_vl_time, df_vl600_time,
            cor_df, df_gr_comp, df_gr_final, df_data_series, df_annotations,
            errors, summary_df, mean_df_species, mean_df_bs, od_measurements,
            estimation], filehandler)

filehandler.close()
