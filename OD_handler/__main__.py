# -*- coding: utf-8 -*-
### Libraries ###
import sys
from OD_handler.OD_handler import gr_plots, parse_data, read_xlsx, sample_outcome, gr_time_format, reshape_gr, vol_correlation, compensation_lm, gr_estimation
from croissance.estimation.outliers import remove_outliers
import croissance
from croissance import process_curve
import numpy as np
import pandas as pd
from datetime import datetime
import re
import os
import matplotlib.pyplot as plt 
import matplotlib
from pandas import Series


def main():

	#Default, the three options are computed
	flag_all = True
	flag_est = False
	flag_sum = False
	flag_fig = False
	# ----- INPUT INTERPRETATION AND FILE READING ------

	if len(sys.argv) == 2 :
		
		if sys.argv[1] == "-h" or sys.argv[1] == "--help" :
			print('''\nUsage:\n OD_handler [OPTIONS]\n\nOptions:\n --help				Shows the help\n --estimations			Returns estimations in a text file\n --figures			Returns the growth rate curves\n --summary			returns the summary of growth rates\n\nDefault:\n Returns the estimations, the figures and the summary.''')
			sys.exit(1)
		elif sys.argv[1] == "--estimations" :
			flag_est = True
			flag_all = False
		elif sys.argv[1] == "--figures" :
			flag_fig = True
			flag_all = False
		elif sys.argv[1] == "--summary" :
			flag_sum = True
			flag_all = False
		elif sys.argv[1] == "--individualplots" :
			flag_ind = True
			flag_all = False
		
		parse_data()
		try :
			df_raw = read_xlsx()
		except FileNotFoundError :
			sys.exit("Error!\n parsed file not found")

	else :
		parse_data()
		try :
			df_raw = read_xlsx()
		except FileNotFoundError :
			sys.exit("Error!\n parsed file not found")

	#Separate data depending on sample purpose (growth rate or volume loss)
	df_gr, df_vl = sample_outcome("calc.tsv", df_raw)
	
	#look at the amount of different species, this will be used as an argument in the reshape method
	multiple_species_flag = False
	
	if len(df_gr["Species"].unique()) > 1 :

		multiple_species_flag = True

	else :

		pass
	
	#Compute correlation for every sample 
	cor_df, df_gr = vol_correlation(df_gr, df_vl)


	#Change time format to hours
	df_gr = gr_time_format(df_gr)

	#Compute compensation
	fig, df_gr = compensation_lm(cor_df, df_gr)
	plt.savefig("lm_volume_loss.pdf")

	#Reshape data for croissance input
	
	if multiple_species_flag == False :
		df_gr_final = reshape_gr(df_gr, flag = multiple_species_flag)
		print("a")
	else :
		df_gr_final, df_gr_final_list = reshape_gr(df_gr, flag = multiple_species_flag)

	#Get estimations of every sample

	if flag_all == True :
		
		estimations, errors = gr_estimation(df_gr_final)
		outfile = open("estimations.txt", 'w')
		
		for est in estimations :
			print(est,"\n", file = outfile)
		
		if len(errors) > 0 :
			print("Some samples could not be estimated :\n", file = outfile)
			print(str(len(errors))+"samples could not be estimated, see estimation file\n", file = outfile)
			
			for err in errors :
				print(err,"\n", file = outfile)
		
		outfile.close()

		if flag_ind == True :

			# Get plots for every sample
			df_gr_est = df_gr_final.loc[:,~df_gr_final.columns.str.startswith('Raw')]
			df_gr_est = df_gr_est.loc[:,~df_gr_est.columns.str.startswith('time')]
			colnames = (df_gr_est.columns.values)

			for col in range(len(colnames)):
				my_series = pd.Series(data = (df_gr_final[colnames[col]]).tolist(), index= df_gr_final[colnames[col].replace("Corrected","time")].tolist())
				my_series = Series.dropna(my_series)
				clean_series = remove_outliers(my_series)[0]	#Extract series withoyt outliers
				df = pd.DataFrame({"time":clean_series.index, colnames[col]:clean_series.values})
				plot = gr_plots(df, colnames[col])
		
		elif flag_ind == False :
			pass#Create plots by species

	if flag_fig == True :
		if flag_ind == True :
			# Get plots for every sample
			df_gr_est = df_gr_final.loc[:,~df_gr_final.columns.str.startswith('Raw')]
			df_gr_est = df_gr_est.loc[:,~df_gr_est.columns.str.startswith('time')]
			colnames = (df_gr_est.columns.values)

		for col in range(len(colnames)):
				my_series = pd.Series(data = (df_gr_final[colnames[col]]).tolist(), index= df_gr_final[colnames[col].replace("Corrected","time")].tolist())
				my_series = Series.dropna(my_series)
				clean_series = remove_outliers(my_series)[0]	#Extract series withoyt outliers
				df = pd.DataFrame({"time":clean_series.index, colnames[col]:clean_series.values})
				plot = gr_plots(df, colnames[col])
		else :
			pass#create plots for every species

	elif flag_est == True :

		estimations, errors = gr_estimation(df_gr_final)
		outfile = open("estimations.txt", 'w')
		
		for est in estimations :
			print(est,"\n", file = outfile)
		
		if len(errors) > 0 :
			print("Some samples could not be estimated :\n", file = outfile)
			for err in errors :
				print(err,"\n", file = outfile)
		
		outfile.close()

	elif flag_sum == True :

		estimations, errors = gr_estimation(df_gr_final)
		#Do something with the estimations
	

