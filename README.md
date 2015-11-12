# Data_Format
Reorganise the data formats

# Examples as follow
For write file:
exp = ExperimentalData(FolderPath)
Experiment().save(Filename.h5, exp)
A file named as 'Filename' will be created in the folder

For read file:
e = Experiment()
e.read(Filename)
e.e_data.ac[1].haadf, 
e.e_data.ac[2].eels_h, etc. 
Functions in Hyperspy can be performed in these data.


# In the future, 
- For data loading, other formats rather than .dm3 need to be loaded. Distinguishing different data format (.dm3, .ser etc.) and different data type (eels, haadf, survey etc) need to consider.
- Besides, a folder in a more common structure should be loaded well, not just a folder like 'Experimental Data' folder (which can be found in dropbox link)

The dropbox share link is:
https://www.dropbox.com/sh/5y3c662vvgjb3b7/AAC5Dz0lg-6vHAEJnaOfdhGTa?dl=0
