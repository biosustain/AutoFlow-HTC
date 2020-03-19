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

__version__ = "0.0.1"


# ------ PARSE THE DATA USING THE autoflow_parser LIBRARY ------
def parse_data() :
	try :
		call = subprocess.call("autoflow_parser",shell = True)
	except :
		return sys.exit("The data could not be parsed due to some error, check the input documentation")
	return call

# ------ DATA LOADING AND VARIABLE SELECTION ------

def read_xlsx() :
	'''Reads .xlsx file, returns a dataframe with relevant variables'''
	try :
		#Open data file
		df_raw = pd.read_excel("results.xlsx")
	except FileNotFoundError :
		return sys.exit("Could not find the parsed data file (XLSX extension)")
	#Select valuable columns
	cols = ["Sample ID", "Measurement", "Measurement type", "Sampling time","Sampling date"]	#relevant variables
	df_raw = df_raw[cols]
	df_raw.columns = df_raw.columns.str.replace(' ', '_')	#header spaces replaced with underscore
	
	return df_raw


# ------ SEPARATION OF GROWTH RATE SAMPLE AND VOLUME LOSS SAMPLES ------

def sample_outcome(sample_file, df_raw) :
	''' Uses an external file containing individual sample purposes, returns two classifed dataframes based on sample purposes '''
	#Open the file containing sample purposes
	df_calc = pd.read_csv(sample_file, sep="\t")		#Info about the purpose of the sample (growth rate or volume loss compensation)
	
	#add species to every observation
	cols=["Sample_ID", "Species"]
	temp_df = df_calc[cols]
	df_raw = pd.merge(df_raw, temp_df, how="left", on="Sample_ID")

	#Separate samples for growth rate or volume loss according to calc.tsv
	gr_samples = df_calc.loc[df_calc["calc_gr"] == True]
	gr_samples = gr_samples["Sample_ID"].tolist()
	vol_loss_samples = df_calc.loc[df_calc["calc_volumeloss"] == True]
	vol_loss_samples = vol_loss_samples["Sample_ID"].tolist()

	#Separate initial dataframe in 2
	df_gr = df_raw[df_raw.Sample_ID.isin(gr_samples)]
	df_gr = df_gr.loc[df_gr["Measurement_type"] == "OD600"]
	df_vl = df_raw[df_raw.Sample_ID.isin(vol_loss_samples)]
	df_vl = df_vl.loc[df_vl["Measurement_type"] == "OD450"]
	return df_gr, df_vl



# ------- GROWTH RATE FORMATTING FOR SUITABLE CROISSANCE ANALYSIS INPUT ------

def gr_time_format(df_gr) :
	''' discards non relevant OD measurements to growth rate estimation, turns date and time variables into differential time in hours, returns modified dataframe'''

	#Select rows with only a OD600 measurement 
	#Measurement type variable removal
	df_gr = df_gr.drop(columns=["Measurement_type"])

	#Merge date and time variable to datetime format
	df_gr["date_time"] = df_gr["Sampling_time"]+" "+df_gr["Sampling_date"]
	df_gr = df_gr.drop(columns=["Sampling_date", "Sampling_time"])
	df_gr["date_time"] = pd.to_datetime(df_gr["date_time"])

	#Substracting the time of the first obs to all obs
	df_gr['time_hours'] = df_gr["date_time"] - df_gr.loc[df_gr.index[0], 'date_time']
	df_gr["time_hours"] = df_gr["time_hours"].dt.total_seconds()/3600
	#Removal of date_time temporary variable
	df_gr = df_gr.drop(columns=["date_time"])
	
	return df_gr



# ------ VOLUME LOSS COMPENSATION FOR EVERY SAMPLE ------

def vol_correlation(df_gr, df_vl):
	''' Assess the volume loss with OD450 measurements and compesate the OD600 growth rate readings for every different bioshaker, returns a correlation dataframe and a modified growth rate dataframe containing the bioshaker category'''
	#Subset initial df_raw according to OD measurement and get unique IDs
	df_vl = df_vl.loc[df_vl["Measurement_type"] == "OD450"]
	unique_IDs_vl = df_vl["Sample_ID"].unique()
	df_vl["bioshaker"] = df_vl["Sample_ID"].str[0:3]
	df_gr["bioshaker"] = df_gr["Sample_ID"].str[0:3]
	unique_bioshaker = df_vl["bioshaker"].unique()
	cor_df = pd.DataFrame()


	for pos in range(len(unique_IDs_vl)) :
		df_vl_ID = df_vl.loc[df_vl["Sample_ID"] == unique_IDs_vl[pos]]
		init_val = float((df_vl_ID["Measurement"].tolist()[0]))
		df_vl_ID["Correlation"] = df_vl_ID["Measurement"]/init_val
		cor_df = cor_df.append(df_vl_ID)
		df_vl_ID = pd.DataFrame()
		cor_df = gr_time_format(cor_df)
	return cor_df, df_gr



def compensation_lm(cor_df, df_gr) :
	''' Given the correlation between volume and time, a linear model is built and plotted, the correction is applied to the growth measurements using the linear model, returns a figure with the LM and a dataframe with the corrected growth rate measurements'''
	#For every bioshaker a linear model is created
	unique_bioshaker = cor_df["bioshaker"].unique()
	linear = lambda x, a, b: a * x + b
	fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(10,10))
	fig.subplots_adjust(hspace=0.4, wspace=0.4)
	fig.suptitle('Linear models of volume loss correlation to time for different plates')
	lm_eq = []
	
	#Iterate through unique shakers and compute linear model and plot
	for shaker in range(len(unique_bioshaker)) :
		sub_cor_df = cor_df[cor_df["bioshaker"]== unique_bioshaker[shaker]]
		popt, pcov = curve_fit(linear, sub_cor_df ["time_hours"], sub_cor_df["Correlation"], p0=[1, 1])
		lm_eq.append(popt)
		ax = fig.add_subplot(2, 2, shaker+1)
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

def reshape_gr(df_gr, flag = False) :
	''' Collects the times belonging to every sample and creates a time column relative to a specific sample, returns the modified dataframe '''
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


# --- AUTOMATED GROWTH ESTIMATION FOR EVERY SAMPLE

def gr_estimation(df_gr_final) :
	''' removes outliers for every sample and outputs growth rate estimates for every given sample ID as a text file'''
	
	#OPTION 1 : USE CROISSANCE
	#croissance series input format 
	#To start with we try it with one column
	df_gr_est = df_gr_final.loc[:,~df_gr_final.columns.str.startswith('Raw')]
	df_gr_est = df_gr_est.loc[:,~df_gr_est.columns.str.startswith('time')]
	colnames = []
	colnames = (df_gr_est.columns.values)
	estimations = []
	errors = []
	for col in range(len(colnames)):
		my_series = pd.Series(data = (df_gr_final[colnames[col]]).tolist(), index= df_gr_final[colnames[col].replace("Corrected","time")].tolist())
		# Estimation for every sample
		try :
			gr_estimation = process_curve(my_series)
			estimations.append(colnames[col])
			estimations.append(gr_estimation)
		except :
			errors.append(colnames[col])
			errors.append(remove_outliers(my_series)[0])

	return estimations , errors

def gr_plots(df, sample) :
	''' generates a growth curve plot for a given series for common species, returns the plot'''
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
	



