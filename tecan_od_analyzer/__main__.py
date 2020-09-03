# -*- coding: utf-8 -*-
# Libraries
import sys
from tecan_od_analyzer.tecan_od_analyzer import argument_parser, gr_plots, parse_data, read_xlsx, sample_outcome, time_formater, reshape_dataframe, vol_correlation, compensation_lm, gr_estimation, estimation_writter, stats_summary, interpolation, input_output, stats_plot
from croissance.estimation.outliers import remove_outliers
import pandas as pd
import re
import os
import matplotlib.pyplot as plt 
from pandas import Series
from matplotlib.pyplot import cm
import itertools
import path
import seaborn as sns
from scipy.optimize import curve_fit
from pandas import Series
from platform import platform

def main():

	pd.set_option('mode.chained_assignment', None)

	# ----- INPUT INTERPRETATION AND FILE READING ------

	#Interpretation of the command line arguments

	flag_all, flag_est, flag_sum, flag_fig, flag_ind, flag_bioshakercolor, flag_volumeloss, flag_bioshaker, flag_interpolation, cmd_dir, path, interpolationplot = argument_parser(argv_list= sys.argv)

	# path input and output directory creation
	dir_ = input_output(cmd_dir, path)

	#Data parsing
	parse_data()

	#Data reading 
	try :
		df_raw = read_xlsx()

	except FileNotFoundError :
		sys.exit("Error: The output file from the autoflow_parser was not found")


	# ----- LABELLING ACCORDING TO SAMPLE PURPOSE -----

	#Separate data depending on sample purpose (growth rate or volume loss)
	try :
		df_gr, df_vl = sample_outcome("calc.tsv", df_raw)

	except FileNotFoundError :
		sys.exit("Error!\n calc.tsv file not found")


	# ----- FORMATING TIME VARIABLE TO DIFFERENTIAL HOURS -----


	df_gr = time_formater(df_gr)
	df_vl = time_formater(df_vl)

	# Assess different species, this will be used as an argument in the reshape method
	if len(df_gr["Species"].unique()) > 1 :
		multiple_species_flag = True

	else :
		multiple_species_flag = False

	# Once the data is read, change dir to output dir
	os.chdir(dir_)

	# ----- CORRELATION AND CORRECTION -----


	if flag_volumeloss == True :

		#Compute correlation for every sample 
		cor_df = vol_correlation(df_vl)

		#Compute compensation
		fig, df_gr = compensation_lm(cor_df, df_gr)
	
	else : 
		print("Volume loss correction : NOT COMPUTED")

		bioshakers = df_gr["biosahker"].unique()
	
	
	# ----- DATA RESHAPING FOR CROISSANCE INPUT REQUIREMENTS -----

	# Reshape data for croissance input
	
	#If only one species one dataframe is returned only
	if multiple_species_flag == False and flag_bioshaker == False:
		df_gr_final = reshape_dataframe(df_gr, flag_species = multiple_species_flag, flag_bioshaker = False)

	
	#Split dataframes by species and bioshakers
	elif multiple_species_flag == True and flag_bioshaker == True:
		df_gr_final, df_gr_final_list = reshape_dataframe(df_gr, flag_species = multiple_species_flag, flag_bioshaker = True)


	# If more than one species, the dataframe is split by species and returned as a list of dataframes.
	# The unsplit dataframe is also returned, which will be used for the summary and estimations
	elif multiple_species_flag == True and flag_bioshaker == False:
		df_gr_final, df_gr_final_list = reshape_dataframe(df_gr, flag_species = multiple_species_flag, flag_bioshaker = False)

	else :
		df_gr_final, df_gr_final_list = reshape_dataframe(df_gr, flag_species = multiple_species_flag, flag_bioshaker = True)

	# ----- COMPLETE FUNCTIONALITY : ESTIMATIONS, FIGURES AND STATISTICAL SUMMARY -----

	if flag_all == True or flag_est == True or flag_sum == True:


		# ----- ESTIMATIONS -----

		# Compute estimations
		df_data_series, df_annotations, error_list = gr_estimation(df_gr_final)

		# Write estimation files
		estimation_writter(df_data_series, df_annotations, error_list)
		print("Growth rate phases estimation : DONE")
		

	if flag_all == True or flag_sum == True:
		
		# ----- SUMMARY STATISTICS ----- 

		#Compute summary statistics
		summary_df, mean_df_species, mean_df_bs = stats_summary(df_annotations)

		# Compute plot of the annotation parameters
		status = stats_plot(summary_df)
		print(status)
		

	if flag_all == True or flag_fig == True :

		
		# ----- FIGURES -----

		#Get plots individually for every sample
	

		if flag_ind == True :

			# Get plots for every sample
			
			df_gr_est = df_gr_final.loc[:,~df_gr_final.columns.str.startswith('time')]
			colnames = (df_gr_est.columns.values)

			for col in range(len(colnames)):
				my_series = pd.Series(data = (df_gr_final[colnames[col]]).tolist(), index= df_gr_final["time_"+colnames[col]].tolist())
				my_series = Series.dropna(my_series)
				clean_series = remove_outliers(my_series)[0]	#Extract series without outliers
				df = pd.DataFrame({"time":clean_series.index, colnames[col]:clean_series.values})
				plot = gr_plots(df, colnames[col], ind = True, interpolationplot=interpolationplot)
				plt.close()

		#Get plots combined together by species

		elif flag_ind == False :
			
			#Get plots combined by species and colored by bioshaker
			
			if flag_bioshakercolor == True and flag_bioshaker == False :

				#Color the plot according to bioshaker

				bioshaker_list = (df_gr["Sample_ID"]).str.slice(0,3).unique()
				colors = itertools.cycle(["g", "b", "g","o"])
				color_dict = dict()

				for bioshaker in bioshaker_list :
					color_dict.update( {bioshaker: next(colors)} )
				
				
				#Plots when only one species is present
				
				if multiple_species_flag == False :


					for df_gr_est in df_gr_final_list:

						df_gr_est = df_gr_final.loc[:,~df_gr_final.columns.str.startswith('time')]
						colnames = (df_gr_est.columns.values)

						plt.figure()

						start_leg = ""

						for col in range(len(colnames)):
							
							bioshaker_label = re.search(r"([B][S]\d)",colnames[col]).group(1)
							my_series = pd.Series(data = (df_gr_final[colnames[col]]).tolist(), index= df_gr_final["time_"+colnames[col]].tolist())
							my_series = Series.dropna(my_series)
							clean_series = remove_outliers(my_series)[0]	#Extract series without outliers
							df = pd.DataFrame({"time":clean_series.index, colnames[col]:clean_series.values})
							
							#First time 
							if start_leg == "" :
								
								gr_plots(df, colnames[col], color_ = color_dict[bioshaker_label], legend_ ="bioshaker", title_ = "species", interpolationplot=interpolationplot)
								start_leg = (colnames[col])[:3]

							#New Bioshaker
							elif (colnames[col])[:3] != start_leg :

								gr_plots(df, colnames[col], color_ = color_dict[bioshaker_label], legend_ ="bioshaker", title_ = "species", interpolationplot=interpolationplot)
								start_leg = (colnames[col])[:3]

							#Repeated bioshaker
							else:

								gr_plots(df, colnames[col], color_ = color_dict[bioshaker_label], legend_ ="exclude", title_ = "species", interpolationplot=interpolationplot)
						
						last_name = colnames[col]
						bioshaker_ = last_name[:3]
						species_ = re.search(r"^\S{3}.\d?_?\S{2,3}_(\S+)", last_name).group(1)

						plt.legend(bbox_to_anchor=(1.05, 1.0), loc='upper left')
						plt.savefig(species_+"_GR_curve.png",  dpi=250)

				
				#Plots when more than one species is present
				
				else :

					for df_gr_final in df_gr_final_list :

						df_gr_est = df_gr_final.loc[:,~df_gr_final.columns.str.startswith('time')]
						colnames = (df_gr_est.columns.values)
						
						plt.figure()

						start_leg = ""

						for col in range(len(colnames)):
							
							bioshaker_label = re.search(r"([B][S]\d)",colnames[col]).group(1)
							my_series = pd.Series(data = (df_gr_final[colnames[col]]).tolist(), index= df_gr_final["time_"+colnames[col]].tolist())
							my_series = Series.dropna(my_series)
							clean_series = remove_outliers(my_series)[0]	#Extract series without outliers
							df = pd.DataFrame({"time":clean_series.index, colnames[col]:clean_series.values})
							
							#First time 
							if start_leg == "" :
								
								gr_plots(df, colnames[col], color_ = color_dict[bioshaker_label], legend_ ="bioshaker", title_ = "species", interpolationplot=interpolationplot)
								start_leg = (colnames[col])[:3]

							#New Bioshaker
							elif (colnames[col])[:3] != start_leg :

								gr_plots(df, colnames[col], color_ = color_dict[bioshaker_label], legend_ ="bioshaker", title_ = "species", interpolationplot=interpolationplot)
								start_leg = (colnames[col])[:3]

							#Repeated bioshaker
							else:

								gr_plots(df, colnames[col], color_ = color_dict[bioshaker_label], legend_ ="exclude", title_ = "species", interpolationplot=interpolationplot)

						plt.legend()
						last_name = colnames[col]
						species_name =  re.search(r"^\S{3}.\d?_?\S{2,3}_(\S+)", last_name).group(1)
						# species_name = last_name[-6:]
						plt.savefig(species_name+"_GR_curve.png",  dpi=250)


			#Get plots split by species and bioshaker				

			elif flag_bioshaker == True :

				color_palette = "r"

				for df_gr_final in df_gr_final_list :
					if df_gr_final.empty == False :
						df_gr_est = df_gr_final.loc[:,~df_gr_final.columns.str.startswith('time')]
						colnames = (df_gr_est.columns.values)
					
						plt.figure()

						for col in range(len(colnames)):
						
							bioshaker_label = re.search(r"([B][S]\d)",colnames[col]).group(1)
							my_series = pd.Series(data = (df_gr_final[colnames[col]]).tolist(), index= df_gr_final["time_"+colnames[col]].tolist())
							my_series = Series.dropna(my_series)
							clean_series = remove_outliers(my_series)[0]	#Extract series without outliers
							df = pd.DataFrame({"time":clean_series.index, colnames[col]:clean_series.values})
							gr_plots(df, colnames[col], color_ = color_palette, legend_ = "exclude", title_ = "species_bioshaker", interpolationplot=interpolationplot)
						
						last_name = colnames[col]
						bioshaker_ = last_name[:3]
						species_ = re.search(r"^\S{3}.\d?_?\S{2,3}_(\S+)", last_name).group(1)
						plt.savefig(bioshaker_+"_"+species_+"_GR_curve.png",  dpi=250)
				


			#Default plot without bioshaker coloring (combined by species and containing the two bioshakers undiferentiated)
			
			else : 

				color_palette = "r"

				if multiple_species_flag == False :

					df_gr_est = df_gr_final.loc[:,~df_gr_final.columns.str.startswith('time')]
					colnames = (df_gr_est.columns.values)
					
					plt.figure()

					for col in range(len(colnames)):
						
						bioshaker_label = re.search(r"([B][S]\d)",colnames[col]).group(1)
						my_series = pd.Series(data = (df_gr_final[colnames[col]]).tolist(), index= df_gr_final["time_"+colnames[col]].tolist())
						my_series = Series.dropna(my_series)
						clean_series = remove_outliers(my_series)[0]	#Extract series without outliers
						df = pd.DataFrame({"time":clean_series.index, colnames[col]:clean_series.values})
						gr_plots(df, colnames[col], color_ = color_palette, legend_ = "exclude", title_ = "species", interpolationplot=interpolationplot)


					last_name = colnames[col]
					bioshaker_ = last_name[:3]
					species_ = re.search(r"^\S{3}.\d?_?\S{2,3}_(\S+)", last_name).group(1)
					plt.savefig(species_+"_GR_curve.png",  dpi=250)

				else :

					for df_gr_final in df_gr_final_list :
						df_gr_est = df_gr_final.loc[:,~df_gr_final.columns.str.startswith('time')]
						colnames = (df_gr_est.columns.values)
					
						plt.figure()

						for col in range(len(colnames)):
						
							bioshaker_label = re.search(r"([B][S]\d)",colnames[col]).group(1)
							my_series = pd.Series(data = (df_gr_final[colnames[col]]).tolist(), index= df_gr_final["time_"+colnames[col]].tolist())
							my_series = Series.dropna(my_series)
							clean_series = remove_outliers(my_series)[0]	#Extract series without outliers
							df = pd.DataFrame({"time":clean_series.index, colnames[col]:clean_series.values})
							gr_plots(df, colnames[col], color_ = color_palette, legend_ = "exclude", title_ = "species", interpolationplot=interpolationplot)

						last_name = colnames[col]
						bioshaker_ = last_name[:3]
						species_ = re.search(r"^\S{3}.\d?_?\S{2,3}_(\S+)", last_name).group(1)
						plt.savefig(species_+"_GR_curve.png",  dpi=250)

		print("Plotting growth curves : DONE")


	if  flag_interpolation == True :

		od_measurements = interpolation("../od_measurements.tsv",df_annotations, mean_df_bs)

		print("Computing optical density estimations : DONE")

		
