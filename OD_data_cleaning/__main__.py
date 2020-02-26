import sys
import pandas as pd 
from OD_data_cleaning import read_xlsx, sample_outcome, gr_time_format, reshape_gr,gr_plots, vol_correlation, compensation_lm
from croissance.estimation.outliers import remove_outliers
import matplotlib.pyplot as plt
import croissance
from croissance import process_curve
from croissance.estimation import AnnotatedGrowthCurve
from croissance.figures import PDFWriter
import numpy as np





#OD_DATA_CEALING
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
'''
print(len(df_gr["Sample_ID"].unique()))
print("----")
print(len(df_vl["Sample_ID"].unique()))
'''
cor_df = vol_correlation(df_gr, df_vl)

compensation_lm(cor_df)



#Change time format to hours
df_gr = gr_time_format(df_gr)

#Reshape data for croissance input
df_gr_final = reshape_gr(df_gr)

#print(gr_plots(df_gr_final))


#This is a piece of code that generates a series that works, I do not see the difference between this data and my_series
#This was taken from the test.py of the croissance repository ("https://github.com/meono/croissance/blob/master/test.py")
mu = .20
pph = 4.
data1 = pd.Series(
                    data=([i / 10. for i in range(10)] +
                          [np.exp(mu * i / pph) for i in range(25)] +
                          [np.exp(mu * 24 / pph)] * 15),
                    index=([i / pph for i in range(50)]))












