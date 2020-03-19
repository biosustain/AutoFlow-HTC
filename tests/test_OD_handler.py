'''
test.py
'''

import pytest
import unittest
import pandas as pd
import pandas.api.types as ptypes

from OD_handler.OD_handler import gr_plots, parse_data, read_xlsx, sample_outcome, gr_time_format, reshape_gr, vol_correlation, compensation_lm, gr_estimation

"""The tests must run on some data, please provide an xlsx file as a result of the parsing and a file with the sample purpose named as 'calc.tsv' in the directory where the test is"""
df_gr, df_vl = sample_outcome("calc.tsv",read_xlsx())
df_time = gr_time_format(df_gr)
cor_df, df_gr_cor = vol_correlation(df_time, df_vl)
fig, df_gr_comp = compensation_lm(cor_df, df_gr_cor)
df_gr_final = reshape_gr(df_gr_comp)



class test_methods(unittest.TestCase) :

 	def test_read_parsed_xlsx_is_dataframe(self):
 		"""test that returned objected is a dataframe with 5 columns"""
 		result = read_xlsx()
 		cols = len(result.columns)
 		self.assertIsInstance(result, pd.DataFrame)
 		self.assertEqual(cols, 5)

 	def test_sample_outcome_output_is_dataframe(self):
 		"""test that 2 dataframes are returned and correspond to unique OD measurements"""
 		file = read_xlsx()
 		result1, result2 = sample_outcome("calc.tsv", file)
 		unique_OD_1 = result1["Measurement_type"].unique()
 		unique_OD_2 = result2["Measurement_type"].unique()
 		self.assertIsInstance(result1, pd.DataFrame)
 		self.assertIsInstance(result2, pd.DataFrame)
 		self.assertEqual(len(unique_OD_1), 1)
 		self.assertEqual(len(unique_OD_1), 1)

 	def test_gr_time_format(self):
 		"""test that the expected time format is created on a given dataframe"""
 		result1 = gr_time_format(df_gr)
 		self.assertTrue(ptypes.is_float_dtype(result1["time_hours"]))

 	def test_volume_loss_correlation(self):
 		"""test that the correlations are calculated,"""
 		result1 , result2 = vol_correlation(df_time, df_vl)
 		colnames1 = (result1.columns.values)
 		colnames2 = (result2.columns.values)
 		self.assertIsInstance(result1, pd.DataFrame)
 		self.assertIsInstance(result2, pd.DataFrame)
 		self.assertIn("Correlation", colnames1)
 		self.assertIn("bioshaker", colnames2)

 	def test_compensation_lm(self):
 		"""test the compensation_lm method"""
 		result1, result2 = compensation_lm(cor_df, df_gr_cor)
 		colnames = (result2.columns.values)
 		self.assertIsNotNone(result1)
 		self.assertIsInstance(result2, pd.DataFrame)
 		self.assertIn("Corrected_Measurement", colnames)

 	def test_reshape_gr(self):
 		"""test the reshape method"""
 		result = reshape_gr(df_gr_comp)
 		original_IDs = df_gr_comp["Sample_ID"].unique()
 		colnames = (result.columns.values)
 		self.assertIsInstance(result, pd.DataFrame)
 		self.assertIn(original_IDs, colnames)
 		## ESTE FALLA SIMPLEMENTE HAY QUE AÑADIR UNA PALABRA raw a colnames (mirar luego)

 	def test_gr_estimation(self):
 		"""test the estimation method"""
 		result1, result2 = gr_estimation(df_gr_final)
 		self.assertIsInstance(result1, list)
 		self.assertIsInstance(result2, list)
 		self.assertGreater(len(result1), 0)

if __name__ == '__main__':
    unittest.main()
