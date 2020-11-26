import pytest
import unittest
import pandas as pd
import pandas.api.types as ptypes
import pandas.testing
import re
import pickle
import sys
sys.path.insert(1, '../')
from tecan_od_analyzer.tecan_od_analyzer import argument_parser, gr_plots, \
    parse_data, read_xlsx, sample_outcome, time_formater, reshape_dataframe, \
    vol_correlation, compensation_lm, gr_estimation, stats_summary, \
    interpolation, exponential
import pathlib
current_dir = str(pathlib.Path(__file__).parent.absolute())


class test_methods(unittest.TestCase):

    # Create method to compare dataframes
    def assertDataframeEqual(self, a, b, msg):
        try:
            pd.testing.assert_frame_equal(a, b)
        except AssertionError as e:
            raise self.failureException(msg) from e

    def setUp(self):
        file_obj = open(current_dir + '/data/test_data.obj', 'rb')
        df_gr, df_vl450, df_vl600, df_gr_time, df_vl_time, df_vl600_time, \
            cor_df, df_gr_comp, df_gr_final, df_data_series, df_annotations, \
            errors, summary_df, mean_df_species, mean_df_bs, od_measurements, \
            estimation = pickle.load(file_obj)
        file_obj.close()

        self.df_gr = df_gr
        self.df_vl450 = df_vl450
        self.df_vl600 = df_vl600
        self.df_gr_time = df_gr_time
        self.df_vl_time = df_vl_time
        self.df_vl600_time = df_vl600_time
        self.cor_df = cor_df
        self.df_gr_comp = df_gr_comp
        self.df_gr_final = df_gr_final
        self.df_data_series = df_data_series
        self.df_annotations = df_annotations
        self.errors = errors
        self.summary_df = summary_df
        self.mean_df_species = mean_df_species
        self.mean_df_bs = mean_df_bs
        self.od_measurements = od_measurements
        self.estimation = estimation

        # Add the method to compare dataframes in the class
        self.addTypeEqualityFunc(pd.DataFrame, self.assertDataframeEqual)

    # ----- TEST ARGUMENT PARSER METHOD -----

    def test_argument_parser_default(self):
        """test that the argument parser returns the correct flags given
        different arguments"""

        # Check default input (no optional arguments)
        argv_list = []
        argv_list.append("tecan_od_analyzer")
        flag_all, flag_est, flag_sum, flag_fig, flag_ind, \
            flag_bioshakercolor, flag_volumeloss, flag_bioshaker, \
            flag_interpolation, cmd_dir, path, \
            flag_interpolationplot, \
            flag_svg = argument_parser(argv_list)
        self.assertTrue(flag_all)
        self.assertFalse(flag_est)
        self.assertFalse(flag_sum)
        self.assertFalse(flag_fig)
        self.assertFalse(flag_ind)
        self.assertFalse(flag_bioshaker)
        self.assertFalse(flag_bioshakercolor)
        self.assertTrue(flag_volumeloss)
        self.assertFalse(flag_interpolation)
        self.assertFalse(flag_interpolationplot)

    def test_argument_parser_non_default(self):
        """test that the argument parser returns the correct flags given for a
        non default argument"""
        argv_list = []
        arg_1 = "tecan_od_analyzer"
        arg_2 = "-s"
        argv_list.append(arg_1)
        argv_list.append(arg_2)
        flag_all, flag_est, flag_sum, flag_fig, flag_ind, \
            flag_bioshakercolor, flag_volumeloss, flag_bioshaker, \
            flag_interpolation, cmd_dir, path, \
            flag_interpolationplot, \
            flag_svg = argument_parser(argv_list)
        self.assertFalse(flag_all)
        self.assertFalse(flag_est)
        self.assertTrue(flag_sum)
        self.assertFalse(flag_fig)
        self.assertFalse(flag_ind)
        self.assertFalse(flag_bioshaker)
        self.assertFalse(flag_bioshakercolor)
        self.assertTrue(flag_volumeloss)
        self.assertFalse(flag_interpolation)
        self.assertFalse(flag_interpolationplot)

    # ----- TEST WHITESPACE REMOVAL -----

    def test_whitespace_removal(self):
        """test that .str.replace(" ","") works as intended"""
        space_test_df = pd.DataFrame(
                            data={"Test": [" ", "a b", "c  d  e",
                                           "B. 02", "fg"]},
                            columns=["Test"])
        ctrl_test_df = pd.DataFrame(
                            data={"Test": ["", "ab", "cde",
                                           "B.02", "fg"]},
                            columns=["Test"])
        test_df = pd.DataFrame(space_test_df["Test"].str.replace(" ", ""))
        self.assertEqual(
            ctrl_test_df, test_df)

    # ----- TEST read_xlsx METHOD -----

    def test_read_parsed_xlsx_is_dataframe(self):
        """test that returned objected is a dataframe with 5 columns"""
        result = read_xlsx(current_dir + "/data/results.xlsx")
        cols = len(result.columns)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(cols, 5)

    # ----- TEST sample_outcome METHOD -----

    def test_sample_outcome_output_is_dataframe(self):
        """test that 2 dataframes are returned and correspond to
        unique OD measurements"""
        file = read_xlsx(current_dir + "/data/results.xlsx")
        result1, result2, result3 = sample_outcome(
            current_dir + "/data/calc.tsv", file)
        result_1, result_2, result_3 = self.df_gr, self.df_vl450, self.df_vl600

        # Output type
        self.assertIsInstance(result1, pd.DataFrame)
        self.assertIsInstance(result2, pd.DataFrame)
        self.assertIsInstance(result3, pd.DataFrame)

        # Consistency of the method
        self.assertEqual(result1, result_1)
        self.assertEqual(result2, result_2)
        self.assertEqual(result3, result_3)

    def test_sample_outcome_output_contains_unique_OD_measurement(self):
        """test that the 2 dataframes returned contain only one
        type of measurement and that the measurement corresponds
        to the sample purpose"""
        file = read_xlsx(current_dir + "/data/results.xlsx")
        result1, result2, result3 = sample_outcome(current_dir +
                                                   "/data/calc.tsv", file)
        unique_OD_1 = result1["Measurement_type"].unique()
        unique_OD_2 = result2["Measurement_type"].unique()
        unique_OD_3 = result3["Measurement_type"].unique()

        self.assertEqual(len(unique_OD_1), 1)
        self.assertEqual(len(unique_OD_2), 1)
        self.assertEqual(len(unique_OD_3), 1)
        self.assertEqual(unique_OD_1, "OD600")
        self.assertEqual(unique_OD_2, "OD450")
        self.assertEqual(unique_OD_3, "OD600")

    def test_sample_outcome_drop_out_wells_not_in_output(self):
        """test that drop_put wells are not included in the
        returned dataframe"""
        file = read_xlsx(current_dir + "/data/results.xlsx")
        result1, result2, result3 = sample_outcome(current_dir +
                                                   "/data/calc.tsv", file)
        df_calc = df_calc = pd.read_csv(
            current_dir + "/data/calc.tsv", sep="\t")
        dropped_wells = df_calc[df_calc.Drop_out]

        if not dropped_wells.empty:
            self.assertIn(dropped_wells, result1)

    # ----- TEST time_formater METHOD -----

    def test_time_formater_is_float(self):
        """test that the expected time format is created on a given
        dataframe as a float variable"""
        result1 = time_formater(self.df_gr)
        result_1 = self.df_gr_time
        self.assertIsInstance(result1, pd.DataFrame)
        self.assertTrue(ptypes.is_float_dtype(result1["time_hours"]))
        self.assertEqual(result1, result_1)

    def test_gr_time_format_equal_row_length(self):
        """test that the row length of the input and output
        dataframe is the same"""
        result1 = self.df_gr_time
        # Add test for numbers
        # Add test for different days
        self.assertEqual(
            len(
                result1["Sample_ID"]), len(self.df_gr["Sample_ID"]))

    def test_time_formater_numeric(self):
        """test function by comparing with a known output given
        different times, dates, samples and bioshakers"""
        output = pd.read_csv(
            current_dir + "/data/test_time_formater.tsv", sep='\t')
        timeformated = time_formater(output)
        # compare known output with processed input
        self.assertEqual(
            timeformated["Known_output"].tolist(),
            timeformated["time_hours"].tolist())

    # ----- TEST volume_loss_correlation METHOD -----

    def test_volume_loss_correlation_returned_variable(self):
        """test that the returned variables are dataframes with
        correlation column containing floats"""
        result1 = vol_correlation(self.df_vl_time)
        result_1 = self.cor_df
        colnames1 = (result1.columns.values)

        self.assertIsInstance(result1, pd.DataFrame)
        self.assertIn("Correlation", colnames1)
        self.assertTrue(ptypes.is_float_dtype(result1["Correlation"]))
        self.assertEqual(result1, result_1)

    def test_volume_loss_correlation_correctness(self):
        """test that the correlation is computed by dividing the first
        OD time point on every other value belonging to the same bioshaker"""
        # delete later once working
        # result1 = vol_correlation(self.df_vl_time)

        # Assess manually the row containing the first
        # OD time point and bioshaker
        t0_value_row = self.df_vl_time.iloc[0]
        t0_sample = t0_value_row["Sample_ID"]

        # Subset the df_time to 20 rows to compute the correlation with less
        # data and we make sure they only contain the same bioshaker as in t0
        df_vl_temp = self.df_vl_time[self.df_vl_time["Sample_ID"] == t0_sample]

        # Compute the correlation manually and with the method we are testing
        man_result = df_vl_temp["Measurement"] / t0_value_row["Measurement"]
        method_result = vol_correlation(self.df_vl_time)
        method_result = method_result[method_result["Sample_ID"] == t0_sample]
        method_result = method_result["Correlation"]

        # Assert that both correlations are equal
        self.assertEqual(man_result.tolist(), method_result.tolist())

    # ----- TEST compensation_lm METHOD -----

    def test_compensation_lm(self):
        """test the compensation_lm method outputs"""
        result1, result2 = compensation_lm(self.cor_df, self.df_gr_time,
                                           self.df_vl600_time, self.flag_svg)
        result_2 = self.df_gr_comp
        colnames = (result2.columns.values)

        self.assertIsNotNone(result1)
        self.assertIsInstance(result2, pd.DataFrame)
        self.assertIn("Measurement", colnames)
        self.assertTrue(ptypes.is_float_dtype(result2["Measurement"]))
        self.assertEqual(result2, result_2)

    def test_compensation_lm_check_not_loosen_samples(self):
        """test the compensation_lm method does not loose samples"""
        result2 = self.df_gr_comp
        self.assertEqual(len(result2), len(self.df_gr_time))

    # ----- TEST reshape_gr METHOD -----

    def test_reshape_dataframe(self):
        """test the reshape method, checks that output is a dataframe and
        that all the Sample_IDs are contained and no variables are lost"""
        result = reshape_dataframe(self.df_gr_comp)
        result_ = self.df_gr_final
        # original_IDs = self.df_gr_comp["Sample_ID"].unique()
        # colnames = (result.columns.values)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result, result_)
        # Add ID test

    # ----- TEST gr_estimation METHOD -----

    def test_gr_estimation(self):
        """test the estimation method, checks that that the ouputs
        consists of two df"""
        result1, result2, result3 = self.df_data_series, \
            self.df_annotations, self.errors
        result_1, result_2, result_3 = gr_estimation(self.df_gr_final)

        # data type assertion
        self.assertIsInstance(result1, pd.DataFrame)
        self.assertIsInstance(result2, pd.DataFrame)
        self.assertIsInstance(result3, list)

        # Test all samples are appended either error file
        # or in the annotations file
        self.assertGreater(len(result1.columns.names), 0)
        self.assertEqual(
            len(set(result1.columns.values).intersection(
                result2.columns.values, result3)), 0)
        self.assertEqual(len(set(result2.columns.values) & set(result3)), 0)

    # ----- TEST stats_summary METHOD -----

    def test_stats_summary(self):
        """test the stats summary method"""
        result1, result2, result3 = stats_summary(self.df_annotations)
        result_1, result_2, result_3 = self.summary_df, \
            self.mean_df_species, self.mean_df_bs

        # output type
        self.assertIsInstance(result1, pd.DataFrame)
        self.assertIsInstance(result2, pd.DataFrame)
        self.assertIsInstance(result3, pd.DataFrame)

        # Comparison to expected output
        self.assertEqual(result1, result_1)
        self.assertEqual(result2, result_2)
        self.assertEqual(result3, result_3)

    def test_interpolation(self):
        """test the interpolation method"""
        result = interpolation(
            current_dir + "/data/od_measurements.tsv",
            self.df_annotations, self.mean_df_bs)
        expected_result = self.od_measurements

        # output type
        self.assertIsInstance(result, pd.DataFrame)

        expected_result = expected_result["Estimation"].tolist()
        result = result["Estimation"].tolist()

        for i in range(len(result)):

            # Comparison to expected output
            self.assertTrue(result[i] == expected_result[i])

    def test_exponential(self):
        """test the exponential method"""
        result = exponential(1, 2, 3, 0)
        result_ = self.estimation
        self.assertEqual(result, result_)


"""
    def test_background_correction(self, cor_df, df_gr, df_vl600):

    def test_volume_correction
"""
if __name__ == '__main__':
    unittest.main()
