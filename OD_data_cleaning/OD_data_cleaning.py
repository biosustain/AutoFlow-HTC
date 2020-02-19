### Libraries ###
import pandas as pd
from datetime import datetime
from croissance import process_curve
from croissance.estimation.outliers import remove_outliers
import re

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
	df_vl = df_raw[df_raw.Sample_ID.isin(vol_loss_samples)]
	
	return df_gr, df_vl


# ------- GROWTH RATE FORMATTING FOR SUITABLE CROISSANCE ANALYSIS INPUT ------

def gr_time_format(df_gr) :
	''' discards non relevant OD measurements, turns date and time variables into differential time in hours, returns modified dataframe'''

	#Select rows with only a OD600 measurement 
	df_gr = df_gr.loc[df_gr["Measurement_type"] == "OD600"]
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

def gr_plots(df_gr_final) :
	''' removes outliers for every sample and outputs a growth curve plot for every sample ID'''
	for 
		my_series = pd.Series(data = (df_gr_final["BS1_D1"]).tolist(), index=(df_gr_final["timeBS1_D1"]).tolist())
		outliers = remove_outliers(my_series, window=30, std=2)











'''
def gr_plots(df_gr_final) :

	#Turn dataframe columns into series

#my_series = pd.Series(data = (df_gr_final["BS1_D1"]).tolist(), index=(df_gr_final["timeBS1_D1"]).tolist())
#result = process_curve(my_series)

#This is a piece of code that generates a series that works, I do not see the difference between this data and my_series
#This was taken from the test.py of the croissance repository ("https://github.com/meono/croissance/blob/master/test.py")
mu = .20
pph = 4.
my_series = pd.Series(
                    data=([i / 10. for i in range(10)] +
                          [np.exp(mu * i / pph) for i in range(25)] +
                          [np.exp(mu * 24 / pph)] * 15),
                    index=([i / pph for i in range(50)]))

#This gives an error on my_series but not on data1


result = process_curve(my_series)
print(result)



#result = AnnotatedGrowthCurve(my_series, outliers = remove_outliers(my_series, window=30, std=2),  growth_phases = )
#print(result.growth_phases)



# ------ VOLUME LOSS COMPENSATION ------

#Select rows with only a OD450 measurement 
df_vl = df_vl.loc[df_vl["Measurement_type"] == "OD450"]
df_vl 
#print(df_vl)
'''
