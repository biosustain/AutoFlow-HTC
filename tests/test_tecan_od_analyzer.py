'''
test.py
'''

import pytest
import unittest
import pandas as pd
import pandas.api.types as ptypes
import pandas.testing 
import re

from tecan_od_analyzer.tecan_od_analyzer import argument_parser, gr_plots, parse_data, read_xlsx, sample_outcome, time_formater, reshape_dataframe, vol_correlation, compensation_lm, gr_estimation, stats_summary, interpolation

"""The tests must run on some data, please provide an xlsx file as a result of the parsing and a file with the sample purpose named as 'calc.tsv' in the directory where the test is"""
df_gr, df_vl = sample_outcome("calc.tsv",read_xlsx())
df_gr_time = time_formater(df_gr)
df_vl_time = time_formater(df_vl)
cor_df = vol_correlation(df_vl_time)

fig, df_gr_comp = compensation_lm(cor_df, df_gr_time)
df_gr_final = reshape_dataframe(df_gr_comp)
df_data_series, df_annotations, errors = gr_estimation(df_gr_final)
summary_df, mean_df_species, mean_df_bs = stats_summary(df_annotations)
od_measurements = interpolation("od_measurements.tsv",df_annotations, mean_df_bs)
pd.set_option('mode.chained_assignment', None)
pd.options.mode.chained_assignment = None
class test_methods(unittest.TestCase) :

	pd.set_option('mode.chained_assignment', None)
	pd.options.mode.chained_assignment = None

	#----- TEST ARGUMENT PARSER METHOD -----
	

	def test_argument_parser_default(self):
		"""test that the argument parser returns the correct flags given different arguments"""
		
		#Check default input (no optional arguments)
		argv_list = []
		argv_list.append("tecan_od_analyzer")
		flag_all, flag_est, flag_sum, flag_fig, flag_ind, flag_bioshakercolor, flag_volumeloss, flag_bioshaker, flag_interpolation  = argument_parser(argv_list)
		self.assertTrue(flag_all)
		self.assertFalse(flag_est)
		self.assertFalse(flag_sum)
		self.assertFalse(flag_fig)
		self.assertFalse(flag_ind)
		self.assertFalse(flag_bioshaker)
		self.assertFalse(flag_bioshakercolor)
		self.assertTrue(flag_volumeloss)
		self.assertFalse(flag_interpolation)

	
	def test_argument_parser_non_default(self) :
		"""test that the argument parser returns the correct flags given for a non default argument"""
		argv_list = []
		arg_1 = "tecan_od_analyzer"
		arg_2 = "-s"
		argv_list.append(arg_1)
		argv_list.append(arg_2)
		flag_all, flag_est, flag_sum, flag_fig, flag_ind, flag_bioshakercolor, flag_volumeloss, flag_bioshaker, flag_interpolation  = argument_parser(argv_list)
		self.assertFalse(flag_all)
		self.assertFalse(flag_est)
		self.assertTrue(flag_sum)
		self.assertFalse(flag_fig)
		self.assertFalse(flag_ind)
		self.assertFalse(flag_bioshaker)
		self.assertFalse(flag_bioshakercolor)
		self.assertTrue(flag_volumeloss)
		self.assertFalse(flag_interpolation)



	#----- TEST read_xlsx METHOD -----


	def test_read_parsed_xlsx_is_dataframe(self):
		"""test that returned objected is a dataframe with 5 columns"""
		result = read_xlsx()
		cols = len(result.columns)
		self.assertIsInstance(result, pd.DataFrame)
		self.assertEqual(cols, 5)
		


	#----- TEST sample_outcome METHOD -----


	def test_sample_outcome_output_is_dataframe(self):
		"""test that 2 dataframes are returned and correspond to unique OD measurements"""
		file = read_xlsx()
		result1, result2 = sample_outcome("calc.tsv", file)
		self.assertIsInstance(result1, pd.DataFrame)
		self.assertIsInstance(result2, pd.DataFrame)

	
	def test_sample_outcome_output_contains_unique_OD_measurement(self):
		"""test that the 2 dataframes returned contain only one type of measurement and that the measurement corresponds to the sample purpose"""
		file = read_xlsx()
		result1, result2 = sample_outcome("calc.tsv", file)
		unique_OD_1 = result1["Measurement_type"].unique()
		unique_OD_2 = result2["Measurement_type"].unique()
		self.assertEqual(len(unique_OD_1), 1)
		self.assertEqual(len(unique_OD_1), 1)
		self.assertEqual(unique_OD_1, "OD600")
		self.assertEqual(unique_OD_2,"OD450")
		

	def test_sample_outcome_drop_out_wells_not_in_output(self) :
		"""test that drop_put wells are not included in the returned dataframe"""
		file = read_xlsx()
		result1, result2 = sample_outcome("calc.tsv", file)
		df_calc = df_calc = pd.read_csv("calc.tsv", sep="\t")
		dropped_wells = df_calc[df_calc.Drop_out == True]
		
		if dropped_wells.empty == False :
			self.assertIn(dropped_wells, result1)



	#----- TEST time_formater METHOD -----


	def test_time_formater_is_float(self):
		"""test that the expected time format is created on a given dataframe as a float variable"""
		result1 = time_formater(df_gr)
		self.assertIsInstance(result1, pd.DataFrame)
		self.assertTrue(ptypes.is_float_dtype(result1["time_hours"]))
	

	def test_gr_time_format_equal_row_length(self): 
		"""test that the row length of the input and output dataframe is the same"""
		result1 = time_formater(df_gr)
		#Add test for numbers
		#Add test for different days
		self.assertEqual(len(result1["Sample_ID"]),len(df_gr["Sample_ID"]))

	def test_time_formater_numeric(self):
		"""test function by comparing with a known output given different times, dates, samples and bioshakers"""
		output = pd.read_csv("test_time_formater.tsv", sep='\t')
		timeformated = time_formater(output)
		#compare known output with processed input
		self.assertEqual(timeformated["Known_output"].tolist(), timeformated["time_hours"].tolist())

	#----- TEST volume_loss_correlation METHOD -----


	def test_volume_loss_correlation_returned_variable(self):
		"""test that the returned variables are dataframes with correlation column containing floats"""
		result1 = vol_correlation(df_vl_time)
		colnames1 = (result1.columns.values)
		self.assertIsInstance(result1, pd.DataFrame)
		self.assertIn("Correlation", colnames1)
		self.assertTrue(ptypes.is_float_dtype(result1["Correlation"]))


	def test_volume_loss_correlation_correctness(self):
		"""test that the correlation is computed by dividing the first OD time point on every other value belonging to the same bioshaker"""
		result1 = vol_correlation(df_vl_time)
		
		#Assess manually the row containing the first OD time point and bioshaker
		t0_value_row = df_vl_time.iloc[0]
		t0_sample = t0_value_row["Sample_ID"]

		#Subset the df_time to 20 rows to compute the correlation with less data and we make sure they only contain the same bioshaker as in t0
		df_vl_temp = df_vl_time[df_vl_time["Sample_ID"] == t0_sample]
		
		#Compute the correlation manually and with the method we are testing
		man_result = df_vl_temp["Measurement"] / t0_value_row["Measurement"]
		method_result = vol_correlation(df_vl_time)
		method_result = method_result[method_result["Sample_ID"] == t0_sample]
		method_result = method_result["Correlation"]
		
		#Assert that both correlations are equal
		self.assertEqual(man_result.tolist(), method_result.tolist())

	#----- TEST compensation_lm METHOD -----


	def test_compensation_lm(self):
		"""test the compensation_lm method outputs"""

		result1, result2 = compensation_lm(cor_df, df_gr_time)
		colnames = (result2.columns.values)
		self.assertIsNotNone(result1)
		self.assertIsInstance(result2, pd.DataFrame)
		self.assertIn("Measurement", colnames)
		self.assertTrue(ptypes.is_float_dtype(result2["Measurement"]))


	def test_compensation_lm_check_not_loosen_samples(self):
		"""test the compensation_lm method does not loose samples"""
		result1, result2 = compensation_lm(cor_df, df_gr_time)
		self.assertEqual(len(result2), len(df_gr_time))
		#####Add test for values



	#----- TEST reshape_gr METHOD -----


	def test_reshape_dataframe(self):
		"""test the reshape method, checks that output is a dataframe and that all the Sample_IDs are contained and no variables are lost"""
		result = reshape_dataframe(df_gr_comp)
		original_IDs = df_gr_comp["Sample_ID"].unique()
		colnames = (result.columns.values)
		self.assertIsInstance(result, pd.DataFrame)



	#----- TEST gr_estimation METHOD -----

	
	def test_gr_estimation(self):
		"""test the estimation method, checks that that the ouputs consists of two df"""
		result1, result2, result3 = gr_estimation(df_gr_final)
		
		#data type assertion
		self.assertIsInstance(result1, pd.DataFrame)
		self.assertIsInstance(result2, pd.DataFrame)
		self.assertIsInstance(result3, list)

		#Length of outputs
		self.assertGreater(len(result1.columns.names), 0)
		self.assertEqual(len(set(result1.columns.values).intersection(result2.columns.values, result3)), 0)
		self.assertEqual(len(set(result2.columns.values) & set(result3)), 0)



	#----- TEST stats_summary METHOD -----

	def test_stats_summary(self):
		"""test the stats summary method"""
		result1, result2, result3 = stats_summary(df_annotations)
		#output type
		self.assertIsInstance(result1, pd.DataFrame)
		self.assertIsInstance(result2, pd.DataFrame)
		self.assertIsInstance(result3, pd.DataFrame)
		
		expected_result = pd.read_excel("expected_summary_stats.xlsx")
		result = pd.read_excel("summary_stats.xlsx")
		#Comparison to expected output
		pd.testing.assert_frame_equal(result, expected_result)

	def test_interpolation(self):
		"""test the interpolation method"""
		result = interpolation("od_measurements.tsv", df_annotations, mean_df_bs)
		expected_result = pd.read_excel("expected_interpolation_results.xlsx")
		result = pd.read_excel("interpolation_results.xlsx")
		#output type
		self.assertIsInstance(result, pd.DataFrame)
		#Comparison to expected output
		self.assertTrue(expected_result["Estimation"].tolist()-0.01<=result["Estimation"].tolist()<= expected_result["Estimation"].tolist()+0.01)



if __name__ == '__main__':
	unittest.main()
