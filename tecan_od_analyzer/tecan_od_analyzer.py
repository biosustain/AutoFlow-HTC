# -*- coding: utf-8 -*-
"""Main module."""

### Libraries ###
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
import math
import argparse

__version__ = "0.0.5"



# ------ MAIN RUNNER ------


def argument_parser(argv_list=None):
	'''Asesses the input arguments and outputs flags to run the different functions according to the user needs.
	Keyword arguments:
    argv_list -- List of arguments provided by the user when running the program.
    Returned variables:
    flags
	'''

	#Initialize the argument parser
	parser = argparse.ArgumentParser()

	#Adding
	parser.add_argument("-e", "--estimations", help="Get only the estimations for every sample", action = "store_true")
	parser.add_argument("-f", "--figures", help="Get only the growth curve figures", action = "store_true")
	parser.add_argument("-s", "--summary", help="Get only the summary of growth rate estimations",action = "store_true")
	parser.add_argument("-b", "--bioshaker", help="Get one growth rates figures for every individual bioshaker", action = "store_true")
	parser.add_argument("-i", "--individual", help="Get one growth rates figures for every individual sample", action = "store_true")
	parser.parse_args()
	args = parser.parse_args(argv_list[1:])

	#Create flags 

	if args.estimations == False and args.figures == False and args.individual == False and  args.summary == False and args.bioshaker == False:
		
		flag_all = True
		flag_est = False
		flag_sum = False
		flag_fig = False
		flag_ind = False
		flag_bioshaker = False

	elif args.estimations == False and args.figures == False and args.individual == True and  args.summary == False :

		flag_all = True
		flag_est = False
		flag_sum = False
		flag_fig = False
		flag_ind = True
		flag_bioshaker = False

	elif args.estimations == False and args.figures == False and args.individual == False and  args.summary == False and args.bioshaker == True:

		flag_all = True
		flag_est = False
		flag_sum = False
		flag_fig = False
		flag_ind = False
		flag_bioshaker = True
	
	else :

		flag_all = False
		flag_est = args.estimations
		flag_sum = args.summary
		flag_fig = args.figures
		flag_ind = args.individual
		flag_bioshaker = args.bioshaker

	return flag_all, flag_est, flag_sum, flag_fig, flag_ind, flag_bioshaker



# ------ PARSE THE DATA USING THE autoflow_parser LIBRARY ------


def parse_data() :
	'''Calls the autoflow_parser and returns a merged xlsx document with all the OD readings combined'''
	try :
		call = subprocess.call("autoflow_parser",shell = True)
	except :
		return sys.exit("The data could not be parsed due to some error, check the input documentation")
	return call



# ------ DATA LOADING AND VARIABLE SELECTION ------


def read_xlsx(filename = "results.xlsx") : #done
	'''Reads .xlsx file, returns a dataframe with relevant variables. The output of the parser is set to be "results.xlsx", the default reads the mentioned file without any additional argument'''
	try :
		#Open data file
		df = pd.read_excel(filename)
	except FileNotFoundError :
		return sys.exit("Could not find the parsed data file (XLSX extension)")
	#Select valuable columns
	cols = ["Sample ID", "Measurement", "Measurement type", "Sampling time","Sampling date"]	#relevant variables
	df = df[cols]
	df.columns = df.columns.str.replace(' ', '_')	#header spaces replaced with underscore
	
	return df



# ------ SEPARATION OF GROWTH RATE SAMPLE AND VOLUME LOSS SAMPLES ------


def sample_outcome(sample_file, df) : #done
	'''Uses an external file containing individual sample purposes, returns two classifed dataframes based on sample purposes and labelled by bioshaker.
	Keyword arguments:
    sample_file -- variable or string containing the name of the file and its extension.
    df 			-- dataframe obtained by using the read_xlsx method on the merged xlsx file.
	
	Returned variables:
	df_gr -- dataframe containing observations related to the microbial growth rate, labelled by bioshaker.
	df_vl -- dataframe containing observations related to the volume loss estimation, labelled by bioshaker.
    '''

	#Open the file containing sample purposes
	df_calc = pd.read_csv(sample_file, sep="\t")  #Info about the purpose of the sample (growth rate, volume loss compensation, species and drop-out samples)
	df_calc = df_calc[df_calc.Drop_out == False]
	
	#Add species and bioshaker labels to every observation
	cols=["Sample_ID", "Species"]
	temp_df = df_calc[cols]
	df = pd.merge(df, temp_df, how="left", on="Sample_ID")
	df["bioshaker"] = df["Sample_ID"].str[0:3]

	#Separate samples for growth rate or volume loss according to calc.tsv
	gr_samples = df_calc.loc[df_calc["calc_gr"] == True]
	gr_samples = gr_samples["Sample_ID"].tolist()
	vol_loss_samples = df_calc.loc[df_calc["calc_volumeloss"] == True]
	vol_loss_samples = vol_loss_samples["Sample_ID"].tolist()

	#Separate initial dataframe in 2
	df_gr = df[df.Sample_ID.isin(gr_samples)]
	df_gr = df_gr.loc[df_gr["Measurement_type"] == "OD600"]
	df_vl = df[df.Sample_ID.isin(vol_loss_samples)]
	df_vl = df_vl.loc[df_vl["Measurement_type"] == "OD450"]
	
	return df_gr, df_vl



# ------- GROWTH RATE FORMATTING FOR SUITABLE CROISSANCE ANALYSIS INPUT ------


def time_formater(df) :
	'''Takes a dataframe and turns date and time variables into differential time in hours for every bioshaker, returns modified dataframe.
	Keyword arguments:
    df 		-- dataframe with containing date and time measurements.
	
	Returned variables:
	df_out 	-- dataframe with differential time measurements in hours.
	'''
	#Get list of bioshakers
	unique_bioshakers = df["bioshaker"].unique()
	
	#Measurement type variable removal
	df = df.drop(columns=["Measurement_type"])
	
	#Initialize empty output dataframe
	df_out = pd.DataFrame()

	for bioshaker in unique_bioshakers :

		#Subset initial dataframe by bioshaker
		df_temp = df.loc[df["bioshaker"] == bioshaker]

		#Merge date and time variable to datetime format
		df_temp["date_time"] = df_temp["Sampling_time"]+" "+df_temp["Sampling_date"]
		df_temp = df_temp.drop(columns=["Sampling_date", "Sampling_time"])
		df_temp["date_time"] = pd.to_datetime(df_temp["date_time"])

		#Substracting the time of the first obs to all obs
		df_temp['time_hours'] = df_temp["date_time"] - df_temp.loc[df_temp.index[0], 'date_time']
		df_temp["time_hours"] = df_temp["time_hours"].dt.total_seconds()/3600

		#Append dataframes together
		df_out = df_out.append(df_temp)

	#Removal of date_time temporary variable
	df_out = df_out.drop(columns=["date_time"])
	
	return df_out



# ------ VOLUME LOSS CORRELATION FOR EVERY SAMPLE ------


def vol_correlation(df_vl): #done
	''' Assess the volume loss with OD450 measurements and correlates the OD450 readings to time for every different bioshaker, returns a correlation dataframe.
	Keyword arguments:
	df_vl	-- dataframe containing only volume loss measurements.
	
	Returned variables:
	cor_df 	-- dataframe containing correlation values of the volume loss according to time measurements.
	'''
	#Subset initial df_raw according to OD measurement and get unique IDs
	unique_IDs_vl = df_vl["Sample_ID"].unique()
	unique_bioshaker = df_vl["bioshaker"].unique()
	cor_df = pd.DataFrame()

	#Compute correlation for every sample
	for pos in range(len(unique_IDs_vl)) :
		df_vl_ID = df_vl.loc[df_vl["Sample_ID"] == unique_IDs_vl[pos]]
		init_val = float((df_vl_ID["Measurement"].tolist()[0]))
		df_vl_ID["Correlation"] = df_vl_ID["Measurement"]/init_val
		cor_df = cor_df.append(df_vl_ID)
		df_vl_ID = pd.DataFrame()
	
	return cor_df



# ------ VOLUME LOSS COMPENSATION FOR EVERY SAMPLE ------


def compensation_lm(cor_df, df_gr) : #done
	''' Given the correlation between volume and time, a linear model is built and plotted, the correction is applied to the growth measurements using the linear model, returns a figure with the LM and a dataframe with the corrected growth rate measurements.
	Keyword arguments:
    df_gr	-- dataframe containing only growth rate measurements and differential time in hours.
	cor_df	-- dataframe containing correlation measures between volume loss and time for different bioshakers.
	
	Returned variables:
	fig 			-- figure representing the linear model between the correlation and the time for every bioshaker.
	df_gr_comp_out 	-- dataframe containing corrected growth rate measurements and differential time in hours.'''
	

	#For every bioshaker a linear model is created
	unique_bioshaker = cor_df["bioshaker"].unique()
	linear = lambda x, a, b: a * x + b
	fig, axes = plt.subplots(nrows=math.ceil(len(unique_bioshaker)), ncols=math.ceil(len(unique_bioshaker)/2))
	fig.subplots_adjust(hspace=0.4, wspace=0.4)
	fig.suptitle('Linear models of volume loss correlation to time for different plates')
	lm_eq = []
	
	#Iterate through unique shakers and compute linear model and plot
	for shaker in range(len(unique_bioshaker)) :
		sub_cor_df = cor_df[cor_df["bioshaker"]== unique_bioshaker[shaker]]
		popt, pcov = curve_fit(linear, sub_cor_df["time_hours"], sub_cor_df["Correlation"], p0=[1, 1])
		lm_eq.append(popt)
		ax = fig.add_subplot(math.ceil(len(unique_bioshaker)), math.ceil(len(unique_bioshaker)/2), shaker+1)
		ax.plot(sub_cor_df["time_hours"], sub_cor_df["Correlation"], "o")
		ax.get_xaxis().set_visible(False)
		ax.get_yaxis().set_visible(False)
		ax.plot(sub_cor_df["time_hours"], linear(sub_cor_df ["time_hours"], *popt), "b-")
		ax.set_title(unique_bioshaker[shaker])
	
	#Use the linear models to correct the volume loss by bioshaker
	df_gr_comp = pd.DataFrame()
	df_gr_comp_out = pd.DataFrame()
	for pos in range(len(lm_eq)) :
		df_gr_comp = df_gr[df_gr["bioshaker"] ==  unique_bioshaker[pos]]
		df_gr_comp["Correlation"] = lm_eq[pos][0]*df_gr_comp["time_hours"]+lm_eq[pos][1]
		df_gr_comp["Corrected_Measurement"] = df_gr_comp["Measurement"]*df_gr_comp["Correlation"]
		df_gr_comp_out = df_gr_comp_out.append(df_gr_comp)
	return fig, df_gr_comp_out




# ------ RESHAPE GROWTH RATE DATAFRAME FOR CROISSANCE INPUT ------


def reshape_dataframe(df_gr, flag = False) :
	''' Collects the times belonging to every sample and creates a time column relative to a specific sample, returns the modified dataframe.
	Keyword arguments:
    df_gr 	-- dataframe containing growth rate measurements and differential time in hours.
	flag  	-- flag that corresponds to the presence of more than one species (True), False if only one species
	Returned variables:
	if flag is False 
	df_gr -- dataframe with differential time measurements in hours displayed horizontally (one column containing the time measurements and one column contaning the OD measurements PER SAMPLE).

	if flag is True :
	df_gr_final 	 --  dataframe with differential time measurements in hours displayed horizontally (one column containing the time measurements and one column contaning the OD measurements PER SAMPLE).
	df_gr_final_list -- list of dataframes originated from df_gr_final and split by common sample species
	'''
	df_gr_temp = df_gr
	cols = ["Sample_ID", "Measurement", "Corrected_Measurement", "time_hours"]	#relevant variables
	df_gr = df_gr[cols]
	
	#Get unique ID and times
	unique_IDs = df_gr["Sample_ID"].unique()
	unique_times = df_gr["time_hours"].unique()

	#Initiate new dataframe
	df_gr_final = pd.DataFrame()
	#An ID column is created for the measurement of every sample and another column timeID is created to relate it to the times
	
	for i in range(len(unique_IDs)) :
		m_list = df_gr.loc[df_gr["Sample_ID"] == unique_IDs[i], "Measurement"].tolist()
		column1 = pd.DataFrame({"Raw_"+unique_IDs[i] : m_list})
		n_list = df_gr.loc[df_gr["Sample_ID"] == unique_IDs[i], "Corrected_Measurement"].tolist()
		column2 = pd.DataFrame({"Corrected_"+unique_IDs[i] : n_list})
		t_list = df_gr.loc[df_gr["Sample_ID"] == unique_IDs[i], "time_hours"].tolist()
		column3 = pd.DataFrame({"time_"+unique_IDs[i] : t_list})
		df_gr_final = pd.concat([df_gr_final,column1], ignore_index=False, axis=1)
		df_gr_final = pd.concat([df_gr_final,column2], ignore_index=False, axis=1)
		df_gr_final = pd.concat([df_gr_final,column3], ignore_index=False, axis=1)

	if flag == False :

		return df_gr_final
	
	df_gr_temp["Sample_ID"] = df_gr_temp["Sample_ID"]+"_"+df_gr_temp["Species"]
	unique_species = df_gr_temp["Species"].unique()
	cols = ["Sample_ID", "Measurement", "Corrected_Measurement", "time_hours", "Species"]	#relevant variables
	df_gr = df_gr_temp[cols]

	list_df_species = []
	df_gr_final_list = []

	for pos in range(len(unique_species)) :

		df_temp = df_gr[df_gr.Species.str.contains(unique_species[pos])]
		df_temp = df_temp.drop(columns=["Species"])
		list_df_species.append(df_temp)
	
	for df in list_df_species :

		unique_IDs = df["Sample_ID"].unique()
		unique_times = df["time_hours"].unique()
		df_fin = pd.DataFrame()
		#Initialize new dataframe
		#An ID column is created for the measurement of every sample and another column timeID is created to relate it to the times
		
		for i in range(len(unique_IDs)) :

			m_list = df.loc[df["Sample_ID"] == unique_IDs[i], "Measurement"].tolist()
			column1 = pd.DataFrame({"Raw_"+unique_IDs[i] : m_list})
			n_list = df.loc[df["Sample_ID"] == unique_IDs[i], "Corrected_Measurement"].tolist()
			column2 = pd.DataFrame({"Corrected_"+unique_IDs[i] : n_list})
			t_list = df.loc[df["Sample_ID"] == unique_IDs[i], "time_hours"].tolist()
			column3 = pd.DataFrame({"time_"+unique_IDs[i] : t_list})
			df_fin = pd.concat([df_fin,column1], ignore_index=False, axis=1)
			df_fin = pd.concat([df_fin,column2], ignore_index=False, axis=1)
			df_fin = pd.concat([df_fin,column3], ignore_index=False, axis=1)
			column1 = pd.DataFrame()
			column2 = pd.DataFrame()
			column3 = pd.DataFrame()

		df_gr_final_list.append(df_fin)

	else :

		return df_gr_final, df_gr_final_list




# ----- AUTOMATED GROWTH ESTIMATION FOR EVERY SAMPLE  -----


def gr_estimation(df_gr_final) :
	''' removes outliers for every sample and outputs growth rate estimates for every given sample ID as a text file
	Keyword arguments:
    df_gr_final 	-- dataframe containing growth rate measurements and differential time in hours.
	
	Returned variables:
	estimations -- List of growth rate estimations for every sample in df_gr_final
	errors 		-- due to croissance noise handling some samples can not be estimated and list of series is returned for every non-estimated sample
	'''
	
	#croissance series input format 
	df_gr_est = df_gr_final.loc[:,~df_gr_final.columns.str.startswith('Raw')]
	df_gr_est = df_gr_est.loc[:,~df_gr_est.columns.str.startswith('time')]
	colnames = []
	colnames = (df_gr_est.columns.values)
	estimations = []
	errors = []
	est_IDs = []
	err_IDs = []
	
	for col in range(len(colnames)):
		my_series = pd.Series(data = (df_gr_final[colnames[col]]).tolist(), index= df_gr_final[colnames[col].replace("Corrected","time")].tolist())
		
		# Estimation for every sample
		try :
			gr_estimation = process_curve(my_series)
			estimations.append(gr_estimation)
			est_IDs.append(colnames[col])
		
		except :
			errors.append(remove_outliers(my_series)[0])
			err_IDs.append(colnames[col])
	
	return estimations , errors, est_IDs, err_IDs



# ----- ESTIMATION WRITTER TO XLSX FILE -----
#The writter function goes here

def estimation_writer(estimation_list, error_list) :
	'''Writes a xlsx file with the estimations for every sample and outputs the errors on a log file.
	Keyword arguments:
    estimation_list		-- list containing the estimations (output from gr_estimation).
    sample 				-- list containing the non-estimated samples.	
	Returned variables:
	est_xlsx_file 		-- file containing the estimations and IDs
	err_xlsx_file 		-- file containing the data series and IDs without outliers of the non-estimated samples
	log_file 			-- file containing the non estimated samples 
	'''
	pass
	return None



# ----- PLOTTING GROWTH RATE CURVE -----


def gr_plots(df, sample, color_ = None, ind = False) :
	'''Generates a growth curve plot for a given series for common species, returns the plot.
	Keyword arguments:
    df		-- dataframe containing differential times and OD measurements
    sample 	-- 
    ind 	-- flag that indicates to output individual plots if True or merged plots by sample species if False
	
	Returned variables:
	fig 		-- object containing the figure
	plt.savefig -- saving the figure as a png file
	'''
	#Create plots individually
	if ind == True :
		x_new = np.linspace(df["time"].min(),df["time"].max(),500)
		a_BSpline = interpolate.make_interp_spline(df["time"], df[sample])
		y_new = a_BSpline(x_new)
		plt.figure()
		plt.plot(x_new,y_new)
		fig = plt.scatter(df["time"],df[sample],5, facecolor=(.18, .31, .31))
		plt.ylabel('Absorbance (OD)', fontname="Arial", fontsize=12)
		plt.xlabel('Time (h)', fontname="Arial", fontsize=12)
		plt.title("Growth rate curve of "+str(sample), fontname="Arial", fontsize=12)
		return fig, plt.savefig(sample+"_GR_curve.png")

	#Create plots by species
	elif ind == False :

		x_new = np.linspace(df["time"].min(),df["time"].max(),500)
		a_BSpline = interpolate.make_interp_spline(df["time"], df[sample])
		y_new = a_BSpline(x_new)
		plt.plot(x_new,y_new , color = color_)
		fig = plt.scatter(df["time"],df[sample],5, facecolor=(.18, .31, .31))
		plt.ylabel('Absorbance (OD)', fontname="Arial", fontsize=12)
		plt.xlabel('Time (h)', fontname="Arial", fontsize=12)
		plt.title("Growth rate curve of "+str(sample), fontname="Arial", fontsize=12)
		return fig



