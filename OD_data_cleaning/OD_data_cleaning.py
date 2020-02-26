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
from scipy import interpolate
import numpy as np
from scipy.optimize import curve_fit
from croissance.estimation.util import with_overhangs
from croissance.estimation import regression



# ------ DATA LOADING AND VARIABLE SELECTION ------

def read_xlsx(ODS_file) :
	'''Reads .xlsx file, returns a dataframe with relevant variables'''
	#Open data file
	df_raw = pd.read_excel(ODS_file)
	
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
	
	#Separate samples for growth rate or volume loss according to calc.tsv
	gr_samples = df_calc.loc[df_calc["calc_gr"] == True]
	gr_samples = gr_samples["Sample_ID"].tolist()
	vol_loss_samples = df_calc.loc[df_calc["calc_volumeloss"] == True]
	vol_loss_samples = vol_loss_samples["Sample_ID"].tolist()

	#Separate initial dataframe in 2
	df_gr = df_raw[df_raw.Sample_ID.isin(gr_samples)]
	df_gr = df_gr.loc[df_gr["Measurement_type"] == "OD600"]
	df_vl = df_raw[df_raw.Sample_ID.isin(vol_loss_samples)]
	
	return df_gr, df_vl




# ------- GROWTH RATE FORMATTING FOR SUITABLE CROISSANCE ANALYSIS INPUT ------

def gr_time_format(df_gr) :
	''' discards non relevant OD measurements, turns date and time variables into differential time in hours, returns modified dataframe'''

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
	''' Assess the volume loss with OD450 measurements and compesate the OD600 growth rate readings for every different bioshaker'''
	#Subset initial df_raw according to OD measurement and get unique IDs
	df_vl = df_vl.loc[df_vl["Measurement_type"] == "OD450"]
	unique_IDs_vl = df_vl["Sample_ID"].unique()
	df_vl["bioshaker"] = df_vl["Sample_ID"].str[0:3]
	unique_bioshaker = df_vl["bioshaker"].unique()
	cor_df = pd.DataFrame()


	for pos in range(len(unique_IDs_vl)) :
		df_vl_ID = df_vl.loc[df_vl["Sample_ID"] == unique_IDs_vl[pos]]
		init_val = float((df_vl_ID["Measurement"].tolist()[0]))
		df_vl_ID["Correlation"] = df_vl_ID["Measurement"]/init_val
		''' # This is done because I spotted something in the data and wanted to get rid of some noisy obs
		if df_vl_ID["Correlation"].max() < 5 :
			df_vl_ID = pd.DataFrame()
		
		else : 
			cor_df = cor_df.append(df_vl_ID)
			df_vl_ID = pd.DataFrame()
		'''
		cor_df = cor_df.append(df_vl_ID)
		df_vl_ID = pd.DataFrame()
	cor_df = gr_time_format(cor_df)
	#plt.scatter(cor_df["time_hours"],cor_df["Correlation"])
	return cor_df

def compensation_lm(cor_df) :
	unique_bioshaker = cor_df["bioshaker"].unique()
	linear = lambda x, a, b: a * x + b
	fig, axes = plt.subplots(nrows=2, ncols=2)
	fig.subplots_adjust(hspace=0.4, wspace=0.4)
	fig.suptitle('Linear models of volume loss correlation to time for different plates')
	for shaker in range(len(unique_bioshaker)) :
		sub_cor_df = cor_df[cor_df["bioshaker"]== unique_bioshaker[shaker]]
		popt, pcov = curve_fit(linear, sub_cor_df ["time_hours"], sub_cor_df["Correlation"], p0=[1, 1])
		ax = fig.add_subplot(2, 2, shaker+1)
		ax.plot(sub_cor_df["time_hours"], sub_cor_df["Correlation"], "rx")
		ax.plot(sub_cor_df["time_hours"], linear(sub_cor_df ["time_hours"], *popt), "b-")
	
	return plt.show()



# ------ RESHAPE GROWTH RATE DATAFRAME FOR CROISSANCE INPUT ------

def reshape_gr(df_gr) :
	''' Collects the times belonging to every sample and creates a time column relative the sample, returns the modified dataframe '''

	#Get unique ID and times
	unique_IDs = df_gr["Sample_ID"].unique()
	unique_times = df_gr["time_hours"].unique()

	#Initiate new dataframe
	df_gr_final = pd.DataFrame()
	#An ID column is created for the measurement of every sample and another column timeID is created to relate it to the times
	for i in range(len(unique_IDs)) :
		m_list = df_gr.loc[df_gr["Sample_ID"] == unique_IDs[i], "Measurement"].tolist()
		column1 = pd.DataFrame({unique_IDs[i] : m_list})
		t_list = df_gr.loc[df_gr["Sample_ID"] == unique_IDs[i], "time_hours"].tolist()
		column2 = pd.DataFrame({"time"+unique_IDs[i] : t_list})
		df_gr_final = pd.concat([df_gr_final,column1], ignore_index=False, axis=1)
		df_gr_final = pd.concat([df_gr_final,column2], ignore_index=False, axis=1)
	return df_gr_final


# --- AUTOMATED PLOT GENERATION FOR EVERY SAMPLE

#Attempt to do a linear model
def func(x, a, b, c):
	return a * np.exp(b * x) + c

def gr_plots(df_gr_final) :
	''' removes outliers for every sample and outputs a growth curve plot for a given sample ID'''
	
	#OPTION 1 : USE CROISSANCE
	#croissance series input format 
	#The idea is to produce the gr plots in a for loop interating through the datafrane every 2 cols
	#To start with we try it with one column
	my_series = pd.Series(data = (df_gr_final["BS1_A1"]).tolist(), index=(df_gr_final["timeBS1_A1"]).tolist())
	#gr_estimation = process_curve(my_series)  #This gives an error 
	#OPTION 2 :  USE CROISSANCE TO REMOVE OUTLIERS AND THEN PLOT THE SMOOTH CURVE WITH INTERPOLATION 
	'''
	clean_series = remove_outliers(my_series)[0]	#Extract series withoyt outliers
	df = pd.DataFrame({"time":clean_series.index, "BS1_A1":clean_series.values})
	x_new = np.linspace(df["time"].min(),df["time"].max(),500)
	a_BSpline = interpolate.make_interp_spline(df["time"], df["BS1_A1"])
	y_new = a_BSpline(x_new)
	sd_pos = y_new+np.std(df["BS1_A1"])
	sd_neg = y_new-np.std(df["BS1_A1"])
	plt.plot(x_new,y_new)
	fig = plt.scatter(df["time"],df["BS1_A1"],5, facecolor=(.18, .31, .31))
	plt.fill_between(x_new, sd_pos, sd_neg, facecolor="red", color="dodgerblue", alpha=0.3)
	plt.ylabel('Absorbance (OD)', fontname="Arial", fontsize=12)
	plt.xlabel('Time (h)', fontname="Arial", fontsize=12)
	plt.title("Growth rate curve for sample BS1_A1", fontname="Arial", fontsize=12)
	'''
	return my_series

