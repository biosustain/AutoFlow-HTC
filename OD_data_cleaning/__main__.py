import sys
import pandas as pd 
from OD_data_cleaning import read_xlsx, sample_outcome, gr_time_format, reshape_gr, vol_correlation, compensation_lm, gr_estimation
from croissance.estimation.outliers import remove_outliers
import matplotlib.pyplot as plt
import croissance
from croissance import process_curve
from croissance.estimation import AnnotatedGrowthCurve
import numpy as np
import subprocess
from matplotlib.backends.backend_pdf import PdfPages

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
from pandas import Series

subprocess.call("autoflow_parser",shell = True)

try :
	if sys.argv[1] == "-h" or sys.argv[1] == "--help" :
		print('''		usage: OD_data_clean <autoflow_parser_output_file.xlxs>  <sample_purpose.tsv>\n		help: OD_data_clean [-h]  [--help]''')
		sys.exit(1)
	elif len(sys.argv) == 3 :
		if sys.argv[1].endswith(".xlsx") and sys.argv[2].endswith(".tsv") :
			ODS_file = sys.argv[1]
			sample_purpose = sys.argv[2]

	else :
		sys.exit("usage: OD_data_clean <autoflow_parser_output_file.xlxs>  <sample_purpose.tsv>")
except IndexError :
	sys.exit("IndexError!\nusage: OD_data_clean <autoflow_parser_output_file.xlxs>  <sample_purpose.tsv>")

#Read data file
df_raw = read_xlsx(ODS_file)



#Separate data depending on sample purpose (growth rate or volume loss)
df_gr, df_vl = sample_outcome(sample_purpose, df_raw)

#Compute correlation for every sample 
cor_df, df_gr = vol_correlation(df_gr, df_vl)


#Change time format to hours
df_gr = gr_time_format(df_gr)

#Compute compensation
fig, df_gr = compensation_lm(cor_df, df_gr)
plt.savefig("lm_volume_loss.pdf")

#Reshape data for croissance input
df_gr_final = reshape_gr(df_gr)


#Get estimations of every sample

estimations, errors = gr_estimation(df_gr_final)
outfile = open("estimations.txt", 'w')
for est in estimations :
	print(est,"\n", file = outfile)
if len(errors) > 0 :
	print("Some samples could not be estimated :\n", file = outfile)
	for err in errors :
		print(err,"\n", file = outfile)
outfile.close()

# Get plots for every sample

df_gr_est = df_gr_final.loc[:,~df_gr_final.columns.str.startswith('Raw')]
df_gr_est = df_gr_est.loc[:,~df_gr_est.columns.str.startswith('time')]
colnames = (df_gr_est.columns.values)

for col in range(len(colnames)):
	my_series = pd.Series(data = (df_gr_final[colnames[col]]).tolist(), index= df_gr_final[colnames[col].replace("Corrected","time")].tolist())
	my_series = Series.dropna(my_series)
	clean_series = remove_outliers(my_series)[0]	#Extract series withoyt outliers
	df = pd.DataFrame({"time":clean_series.index, colnames[col]:clean_series.values})
	x_new = np.linspace(df["time"].min(),df["time"].max(),500)
	a_BSpline = interpolate.make_interp_spline(df["time"], df[colnames[col]])
	y_new = a_BSpline(x_new)
	sd_pos = y_new+np.std(df[colnames[col]])
	sd_neg = y_new-np.std(df[colnames[col]])
	plt.figure()
	plt.plot(x_new,y_new)
	fig = plt.scatter(df["time"],df[colnames[col]],5, facecolor=(.18, .31, .31))
	plt.fill_between(x_new, sd_pos, sd_neg, facecolor="red", color="dodgerblue", alpha=0.3)
	plt.ylabel('Absorbance (OD)', fontname="Arial", fontsize=12)
	plt.xlabel('Time (h)', fontname="Arial", fontsize=12)
	plt.title("Growth rate curve of "+str(colnames[col]), fontname="Arial", fontsize=12)
	plt.savefig(colnames[col]+"_GR_curve.png")






