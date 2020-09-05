# generate test_data
# Last date : 5 Sept 2020
# By : Felix Pacheco (s192496@student.dtu.dk)
# This script is intended to generate sample data and save them into the test_data file. The saved objects will then be used to test the tecan_od_analyzer using unit testing.
import pickle
import pandas as pd
from tecan_od_analyzer.tecan_od_analyzer import argument_parser, gr_plots, parse_data, read_xlsx, sample_outcome, time_formater, reshape_dataframe, vol_correlation, compensation_lm, gr_estimation, stats_summary, interpolation

pd.set_option('mode.chained_assignment', None)
# Use pickle to save python variables
filehandler = open("test_data.obj", 'wb') 

# Generate variables to save
df_gr, df_vl = sample_outcome("calc.tsv",read_xlsx())
df_gr_time = time_formater(df_gr)
df_vl_time = time_formater(df_vl)
cor_df = vol_correlation(df_vl_time)
fig, df_gr_comp = compensation_lm(cor_df, df_gr_time)
df_gr_final = reshape_dataframe(df_gr_comp)
df_data_series, df_annotations, errors = gr_estimation(df_gr_final)
summary_df, mean_df_species, mean_df_bs = stats_summary(df_annotations)
od_measurements = interpolation("od_measurements.tsv",df_annotations, mean_df_bs)
estimation = exponential(1, 2, 3, 0)

pickle.dump([df_gr, df_vl, df_gr_time, df_vl_time, cor_df, fig, df_gr_comp, df_gr_final, df_data_series, df_annotations, errors, summary_df, mean_df_species, mean_df_bs, od_measurements, estimation], filehandler)

filehandler.close()