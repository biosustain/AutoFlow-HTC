# -*- coding: utf-8 -*-
### Libraries ###
import sys
from tecan_od_analyzer.tecan_od_analyzer import argument_parser, gr_plots, parse_data, read_xlsx, sample_outcome, time_formater, reshape_dataframe, vol_correlation, compensation_lm, gr_estimation
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
from matplotlib.pyplot import cm
import argparse
import itertools


import pandas as pd
from datetime import datetime
import croissance
from croissance import process_curve
from croissance.estimation.outliers import remove_outliers
import re
import os
import matplotlib.pyplot as plt 
import matplotlib
import numpy as np
from scipy.optimize import curve_fit
from croissance.estimation.util import with_overhangs
from croissance.estimation import regression
from pandas import Series
import subprocess
import sys
from scipy import interpolate
from matplotlib.pyplot import cm

def main():



	# ----- INPUT INTERPRETATION AND FILE READING ------


	flag_all, flag_est, flag_sum, flag_fig, flag_ind, flag_bioshaker = argument_parser(argv_list= sys.argv)
	parse_data()

	try :
		df_raw = read_xlsx()

	except FileNotFoundError :
		sys.exit("Error!\n parsed file not found")
	


	# ----- LABELLING ACCORDING TO SAMPLE PURPOSE -----
	

	#Separate data depending on sample purpose (growth rate or volume loss)
	try :
		df_gr, df_vl = sample_outcome("calc.tsv", df_raw)

	except FileNotFoundError :
		sys.exit("Error!\n calc.tsv file not found")
	

	# ----- FORMATING TIME VARIABLE TO DIFFERENTIAL HOURS -----


	#Convert time variable to differential hours for both dataframes
	df_gr = time_formater(df_gr)
	df_vl = time_formater(df_vl)

	
	#Assess different species, this will be used as an argument in the reshape method
	multiple_species_flag = False
	
	if len(df_gr["Species"].unique()) > 1 :

		multiple_species_flag = True

	else :

		pass



	# ----- CORRELATION AND CORRECTION -----


	#Compute correlation for every sample 
	cor_df = vol_correlation(df_vl)


	#Compute compensation
	fig, df_gr = compensation_lm(cor_df, df_gr)
	plt.savefig("lm_volume_loss.png")
	plt.close()
	


	# ----- DATA RESHAPING FOR CROISSANCE INPUT REQUIREMENTS -----


	
	#Reshape data for croissance input
	
	#If only one species one dataframe is returned only
	if multiple_species_flag == False :

		df_gr_final = reshape_dataframe(df_gr, flag = multiple_species_flag)

	#If more than one species, the dataframe is splitted by species and returned as a list of dataframes. The original dataframe is also returned
	else :
		df_gr_final, df_gr_final_list = reshape_dataframe(df_gr, flag = multiple_species_flag)



	# ----- USER INPUT REQUIRES ESTIMATIONS, FIGURES AND STATS SUMMARY -----



	if flag_all == True :


		#Get estimations of every sample
		estimations, errors, est_IDs, err_IDs = gr_estimation(df_gr_final)
		outfile = open("estimations.txt", 'w')
		
		#Here would go the estimation writter
		for pos in range(len(estimations)):
			print(est_IDs[pos],"\n", file = outfile)
			print(estimations[pos],"\n", file = outfile)
			
		if len(errors) > 0 :
			print("Some samples could not be estimated :\n", file = outfile)
			print(str(len(errors))+"samples could not be estimated, see estimation file\n", file = outfile)
			
			for pos in range(len(errors)) :
				print(err_IDs[pos],"\n", file = outfile)
				print(errors[pos],"\n", file = outfile)
		
		outfile.close()

		#Get summary statistics of the estimations
		#---Here will go the method to output summary statistics---


		#Get plots individually for every sample
		if flag_ind == True :

			# Get plots for every sample
			df_gr_est = df_gr_final.loc[:,~df_gr_final.columns.str.startswith('Raw')]
			df_gr_est = df_gr_est.loc[:,~df_gr_est.columns.str.startswith('time')]
			colnames = (df_gr_est.columns.values)

			for col in range(len(colnames)):
				my_series = pd.Series(data = (df_gr_final[colnames[col]]).tolist(), index= df_gr_final[colnames[col].replace("Corrected","time")].tolist())
				my_series = Series.dropna(my_series)
				clean_series = remove_outliers(my_series)[0]	#Extract series without outliers
				df = pd.DataFrame({"time":clean_series.index, colnames[col]:clean_series.values})
				plot = gr_plots(df, colnames[col], ind = True)
		

		#Get plots combined together by spcies
		elif flag_ind == False :


			if flag_bioshaker == True :
				
				#Color the plot according to bioshaker
				bioshaker_list = cor_df["bioshaker"].unique()
				colors = itertools.cycle(["g", "b", "g","o"])
				color_dict = dict()

				for bioshaker in bioshaker_list :
					color_dict.update( {bioshaker: next(colors)} )
				
				for df_gr_final in df_gr_final_list :

					df_gr_est = df_gr_final.loc[:,~df_gr_final.columns.str.startswith('Raw')]
					df_gr_est = df_gr_est.loc[:,~df_gr_est.columns.str.startswith('time')]
					colnames = (df_gr_est.columns.values)
					
					plt.figure()

					for col in range(len(colnames)):
						
						bioshaker_label = re.search(r"\S+[_]([B][S]\d)",colnames[col]).group(1)
						my_series = pd.Series(data = (df_gr_final[colnames[col]]).tolist(), index= df_gr_final[colnames[col].replace("Corrected","time")].tolist())
						my_series = Series.dropna(my_series)
						clean_series = remove_outliers(my_series)[0]	#Extract series without outliers
						df = pd.DataFrame({"time":clean_series.index, colnames[col]:clean_series.values})
						gr_plots(df, colnames[col], color_ = color_dict[bioshaker_label])

					plt.savefig(colnames[col]+"_GR_curve.png")


			else : 

				color_palette = "r"

				for df_gr_final in df_gr_final_list :

					df_gr_est = df_gr_final.loc[:,~df_gr_final.columns.str.startswith('Raw')]
					df_gr_est = df_gr_est.loc[:,~df_gr_est.columns.str.startswith('time')]
					colnames = (df_gr_est.columns.values)
					
					plt.figure()

					for col in range(len(colnames)):
						
						bioshaker_label = re.search(r"\S+[_]([B][S]\d)",colnames[col]).group(1)
						my_series = pd.Series(data = (df_gr_final[colnames[col]]).tolist(), index= df_gr_final[colnames[col].replace("Corrected","time")].tolist())
						my_series = Series.dropna(my_series)
						clean_series = remove_outliers(my_series)[0]	#Extract series without outliers
						df = pd.DataFrame({"time":clean_series.index, colnames[col]:clean_series.values})
						gr_plots(df, colnames[col], color_ = color_palette)

					plt.savefig(colnames[col]+"_GR_curve.png")


	if flag_fig == True :

		if flag_ind == True :

			# Get plots for every sample
			df_gr_est = df_gr_final.loc[:,~df_gr_final.columns.str.startswith('Raw')]
			df_gr_est = df_gr_est.loc[:,~df_gr_est.columns.str.startswith('time')]
			colnames = (df_gr_est.columns.values)

			for col in range(len(colnames)):
				my_series = pd.Series(data = (df_gr_final[colnames[col]]).tolist(), index= df_gr_final[colnames[col].replace("Corrected","time")].tolist())
				my_series = Series.dropna(my_series)
				clean_series = remove_outliers(my_series)[0]	#Extract series without outliers
				df = pd.DataFrame({"time":clean_series.index, colnames[col]:clean_series.values})
				plot = gr_plots(df, colnames[col],ind = True)
		
		elif flag_ind == False :
			
			if flag_bioshaker == True :
				
				#Color the plot according to bioshaker
				bioshaker_list = cor_df["bioshaker"].unique()
				colors = itertools.cycle(["g", "b", "g","o"])
				color_dict = dict()

				for bioshaker in bioshaker_list :
					color_dict.update( {bioshaker: next(colors)} )
				
				for df_gr_final in df_gr_final_list :

					df_gr_est = df_gr_final.loc[:,~df_gr_final.columns.str.startswith('Raw')]
					df_gr_est = df_gr_est.loc[:,~df_gr_est.columns.str.startswith('time')]
					colnames = (df_gr_est.columns.values)
					
					plt.figure()

					for col in range(len(colnames)):
						
						bioshaker_label = re.search(r"\S+[_]([B][S]\d)",colnames[col]).group(1)
						my_series = pd.Series(data = (df_gr_final[colnames[col]]).tolist(), index= df_gr_final[colnames[col].replace("Corrected","time")].tolist())
						my_series = Series.dropna(my_series)
						clean_series = remove_outliers(my_series)[0]	#Extract series without outliers
						df = pd.DataFrame({"time":clean_series.index, colnames[col]:clean_series.values})
						gr_plots(df, colnames[col], color_ = color_dict[bioshaker_label])

					plt.savefig(colnames[col]+"_GR_curve.png")


			else : 

				color_palette = "r"

				for df_gr_final in df_gr_final_list :

					df_gr_est = df_gr_final.loc[:,~df_gr_final.columns.str.startswith('Raw')]
					df_gr_est = df_gr_est.loc[:,~df_gr_est.columns.str.startswith('time')]
					colnames = (df_gr_est.columns.values)
					
					plt.figure()

					for col in range(len(colnames)):
						
						bioshaker_label = re.search(r"\S+[_]([B][S]\d)",colnames[col]).group(1)
						my_series = pd.Series(data = (df_gr_final[colnames[col]]).tolist(), index= df_gr_final[colnames[col].replace("Corrected","time")].tolist())
						my_series = Series.dropna(my_series)
						clean_series = remove_outliers(my_series)[0]	#Extract series without outliers
						df = pd.DataFrame({"time":clean_series.index, colnames[col]:clean_series.values})
						gr_plots(df, colnames[col], color_ = color_palette)

					plt.savefig(colnames[col]+"_GR_curve.png")


	elif flag_est == True :

		estimations, errors, est_IDs, err_IDs = gr_estimation(df_gr_final)
		outfile = open("estimations.txt", 'w')
		
		for est in estimations :
			print(est,"\n", file = outfile)
		
		if len(errors) > 0 :
			print("Some samples could not be estimated :\n", file = outfile)
			for err in errors :
				print(err,"\n", file = outfile)
		
		outfile.close()

	elif flag_sum == True :

		estimations, errors, est_IDs, err_IDs = gr_estimation(df_gr_final)
		#Do something with the estimations

	
	

