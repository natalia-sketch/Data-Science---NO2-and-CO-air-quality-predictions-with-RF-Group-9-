# Data-Science---NO2-and-CO-air-quality-predictions-with-RF-Group-9-
This is Group 9's project submission for the Master course: Data Science in bioscience engineering. Using data from ERA5, MODIS, Sentinel 5p, Global Landcover and OpenAQ we created a machine learning approach to predict ground level NO2 and CO concentrations for the country of India valid for 2025. The algorithm used is Random Forest Regressor. 

# Data aquisition 
Data from MODIS, ERA5, Sentinel-5p and and Landcover were downloaded from data portals. 
The other files for aquiring the data from the different data sources include: 1_OpenAQ_api_CO_2025_working.py, 1_ERAS_pre_treatment.py, 1_MODIS_pre_treatment.py. 

# Data pretreatment
The majority of data pre-treatent ocurs within the data aquisition files with the exception of the interpolation of the Sentinel-5p which occurs in this script: 2_Interpolation_Sentinel5p.py. 

# Data Integration
The script to merge the data is 3_Data_Integration.ipynb. 
The data is integrated into a merged cvs file which results in this file: merged_all_with_landcover.zip. 
This file contains all data sources including ground truth data, and can be downloaded and used to run the models. 

# Running the model
The scripts for running the models for the prediction of NO2 and CO can be found respectively within NO2_RF_model.ipynb and CO_RF_model.ipynb. 
The scripts are almost identical with the exception of selecting the corresponding ground truth data per pollutant and predicting for each corresponding pollutant (NO2, CO). 
To run the model on your computer, it is important to change the file paths for the input file as well as output files to your repository. 

# Model outputs
Running the model scripts will produce monthly predictions of ground truth levels NO2 or CO for India 2025, depending on the model that is run. 
