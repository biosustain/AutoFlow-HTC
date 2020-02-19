import sys
import pandas as pd 
from OD_data_cleaning import read_xlsx, sample_outcome, gr_time_format, reshape_gr
from croissance.estimation.outliers import remove_outliers

try :
	if sys.argv[1] == "-h" or sys.argv[1] == "--help" :
		print('''		usage: OD_data_clean <ODS_file.xlxs>  <sample_purpose.tsv>\n		help: OD_data_clean [-h]  [--help]''')
		sys.exit(1)
	elif len(sys.argv) == 3 :
		if sys.argv[1].endswith(".xlsx") and sys.argv[2].endswith(".tsv") :
			ODS_file = sys.argv[1]
			sample_purpose = sys.argv[2]
			print("a")

	else :
		sys.exit("usage: OD_data_clean <file.xlxs>  <sample_purpose.tsv>")
except IndexError :
	sys.exit("IndexError!\nusage: OD_data_clean <file.xlxs>  <sample_purpose.tsv>")

#Read data file
df_raw = read_xlsx(ODS_file)
print(df_raw)
#Separate data depending on sample purpose (growth rate or volume loss)
df_gr, df_vl = sample_outcome(sample_purpose, df_raw)

#Change time format to hours
df_gr = gr_time_format(df_gr)

#Reshape data for croissance input
df_gr_final = reshape_gr(df_gr)

my_series = pd.Series(data = (df_gr_final["BS1_D1"]).tolist(), index=(df_gr_final["timeBS1_D1"]).tolist())
outliers = remove_outliers(my_series, window=30, std=2)
print(outliers)
