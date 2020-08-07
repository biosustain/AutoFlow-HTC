### Libraries ###
import pandas as pd
from datetime import datetime
import numpy as np
import croissance
import re

# ------ DATA LOADING AND VARIABLE SELECTION ------

#Open the file
df_raw = pd.read_excel("results5.xlsx")

#We select the valuable columns
cols = ["Sample ID", "Measurement", "Measurement type", "Sampling time","Sampling date"] #Include dilution rate ?
df_raw = df_raw[cols]
df_raw.columns = df_raw.columns.str.replace(' ', '_')			#replace white spaces on headers by underscores

''' This is a piece of code that generates the data
#We create a dataframe with the purpose of every sample (this is just for tests, known input)
df_raw["calc_volumeloss"] = df_raw.Sample_ID.str.contains(r"\S{3}_[A-H]12")
df_raw["calc_gr"] = ~df_raw.Sample_ID.str.contains(r"\S{3}_[A-H]12")    
df_test = pd.DataFrame()

df_test = df_raw[["Sample_ID", "calc_gr","calc_volumeloss"]]

df_test = df_test.drop_duplicates() 
df_test.to_csv('calc.tsv', sep = '\t')
'''


# ------ SEPARATION OF GROWTH RATE SAMPLE AND VOLUME LOSS SAMPLES ------

#Open the file containing sample purposes
df_calc = pd.read_csv(r"calc.tsv", sep="\t")		#Info about the purpose of the sample (growth rate or volume loss compensation)

#Separate samples for growth rate or volume loss according to calc.tsv

gr_samples = df_calc.loc[df_calc["calc_gr"] == True]
gr_samples = gr_samples["Sample_ID"].tolist()

vol_loss_samples = df_calc.loc[df_calc["calc_volumeloss"] == True]
vol_loss_samples = vol_loss_samples["Sample_ID"].tolist()

#Separate initial dataframe in 2
df_gr = df_raw[df_raw.Sample_ID.isin(gr_samples)]
df_vl = df_raw[df_raw.Sample_ID.isin(vol_loss_samples)]



# ------- GROWTH RATE FORMATTING FOR SUITABLE CROISSANCE ANALYSIS INPUT ------

#Select rows with only a OD600 measurement 
df_gr = df_gr.loc[df_gr["Measurement_type"] == "OD600"]

'''
#This is to check if the measurements are equal between 2 plates
example_list1 = df_gr.loc[df_gr["Sample_ID"]== "BS5_H12", "Measurement"].tolist()
example_list2 = df_gr.loc[df_gr["Sample_ID"]== "BS1_A1", "Measurement"].tolist()
print(len(example_list1))
print((len(example_list2)))
'''

#Measurement type variable removal
df_gr = df_gr.drop(columns=["Measurement_type"])


# ------ FORMATTING TIME VARIABLE TO CROISSANCE INPUT NEEDS FOR GR SAMPLES ------

#Merge date and time variable to datetime format
df_gr["date_time"] = df_gr["Sampling_time"]+" "+df_gr["Sampling_date"]
df_gr = df_gr.drop(columns=["Sampling_date", "Sampling_time"])
df_gr["date_time"] = pd.to_datetime(df_gr["date_time"])


#Substracting the time of the first one to all obs
df_gr['time_int'] = df_gr["date_time"] - df_gr.loc[df_gr.index[0], 'date_time']
df_gr["time_int"] = df_gr["time_int"].dt.total_seconds()/3600


#Removal of date_time temporary variable
df_gr = df_gr.drop(columns=["date_time"])


# ------ RESHAPE GROWTH RATE DATAFRAME FOR CROISSANCE INPUT ------

#Get unique ID and times
unique_IDs = df_gr["Sample_ID"].unique()
unique_times = df_gr["time_int"].unique()


#New dataframe
df_gr_final = pd.DataFrame()


#An ID column is created for the measurement of every sample and another column timeID is created to relate it to the times
for i in range(len(unique_IDs)) :
	m_list = df_gr.loc[df_gr["Sample_ID"]== unique_IDs[i], "Measurement"].tolist()
	column1 = pd.DataFrame({unique_IDs[i] : m_list})
	t_list = df_gr.loc[df_gr["Sample_ID"]== unique_IDs[i], "time_int"].tolist()
	column2 = pd.DataFrame({"time"+unique_IDs[i] : t_list})
	df_gr_final = pd.concat([df_gr_final,column1], ignore_index=False, axis=1)
	df_gr_final = pd.concat([df_gr_final,column2], ignore_index=False, axis=1)

print(df_gr_final.tail())



# ------ CROISSANCE LIBRARY APPLICATION BY GROWTH RATE SAMPLE ID ------

#subset the dataframe to 1 variable to try the croissance library

df_test = df_gr_final[df_gr_final.columns[0:2]]
df_test = df_test.rename({"BS1_A1":"A1", "timeBS1_A1":"time"}, axis="columns")
df_test = df_test[['time', 'A1']]


df_gr_final.to_csv("clean_data.tsv", sep="\t")
df_test.to_csv('test.tsv', sep = '\t')





