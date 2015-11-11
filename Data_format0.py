# -*- coding: utf-8 -*-
"""
Created on Wed Oct  7 09:50:02 2015

@author: YcW
"""

import hyperspy.hspy as hspy
import hyperspy.axes as haxes
#import hyperspy.api as hs
import h5py
import glob
import os
import numpy as np
import re


class Acquisition(object):
    def __init__(self, path):        
        folder = []        
        if type(path) == h5py._hl.group.Group:  #read file
            folder = path.values()
        else:  #directly load file
            folder = [os.path.join(path, f) for f in os.listdir(path) if (os.path.isfile(os.path.join(path, f)) and ('.DS_Store' not in f))]    
        #folder is a list that contains path of each file in the folder
        #delet the hidden folder '.DS_Store' in MacOS
        
        for filename in folder:
            type_check = self.load_check(filename)
            if type_check == None:
                print "Data name: %s" % hspy.load(filename).metadata.General.original_filename
                type_check = str(input("Please input the datatype of the data (SURVEY, HAADF, EELS, EDS, etc...): "))
                print "\n"
            # let users'input always is uppercase
            type_check = type_check.upper()                     
            if type_check == 'SURVEY':
                if type(filename) == h5py._hl.group.Group:
                    self.survey = self.read_signal_from_EMDgroup(filename)
                else:
                    self.survey = hspy.load(filename)
            if type_check == 'HAADF':
                if type(filename) == h5py._hl.group.Group:
                    self.haadf = self.read_signal_from_EMDgroup(filename)
                else:
                    self.haadf = hspy.load(filename)        
            if type_check == 'EELS_L':
                if type(filename) == h5py._hl.group.Group:
                    self.eels_l = self.read_signal_from_EMDgroup(filename)
                else:
                    self.eels_l = hspy.load(filename)
            if type_check == 'EELS_H':
                if type(filename) == h5py._hl.group.Group:
                    self.eels_h = self.read_signal_from_EMDgroup(filename)
                else:
                    self.eels_h = hspy.load(filename)
            if type_check == 'EDS':
                if type(filename) == h5py._hl.group.Group:
                    self.eds = self.read_signal_from_EMDgroup(filename)
                else:
                    self.eds = hspy.load(filename)
    
    def load_check(self, filename):
        """Function to check what type of data is contained in a file to be loaded, if possible."""
        #read file from hdf5 file       
        data_type = ''        
        if type(filename) == h5py._hl.group.Group:  
            loaded_data = filename['data']
            if loaded_data.attrs.get('type'):  #check if the attribute 'type' attached on the data
                data_type = loaded_data.attrs.get('type')
            else:
                data_type = None
        #directly load file
        elif type(filename) == str:  
            loaded_data = hspy.load(filename)
            if loaded_data.metadata.Signal.signal_type == "EELS":
                if loaded_data.axes_manager.signal_axes[0].offset < 500:  #check if EELS is high/low-loss            
                    data_type = 'EELS_L'
                else:
                    data_type = 'EELS_H'
            elif (loaded_data.metadata.Signal.signal_type == "EDS_SEM") or (loaded_data.metadata.Signal.signal_type == "EDS_TEM"):
                data_type = 'EDS'
            else:
                data_type = None
        
        return (data_type)

    def read_signal_from_EMDgroup(self, group):
        #extract essential data:
        data = group.get('data')[...]#convert hdf5 dataset to numpy array
        record_by = group['data'].attrs.get('type', '').upper()
        #read data into hyperspy as Image, Spectrum or Signal:
        if record_by in ['SURVEY', 'HAADF', 'IMAGE']:
            signal = hspy.signals.Image(data)
        elif record_by in ['EELS', 'EELS_L', 'EELS_H', 'EDS', 'SPECTRUM']:
            signal = hspy.signals.Spectrum(data)
        else:
            signal = hspy.signals.Signal(data)
        #set signal properties by iterating over all dimensions:
        for i in range(len(data.shape)):
            dim = group.get('dim{}'.format(i+1))
            signal.axes_manager[i].name = dim.attrs.get('name', '')
            string = dim.attrs.get('navigate', '')
            if string == 'True':
                signal.axes_manager[i].navigate = True
            elif string == 'False':
                signal.axes_manager[i].navigate  = False
            signal.axes_manager[i].offset = float(dim.attrs.get('offset', ''))
            signal.axes_manager[i].scale = float(dim.attrs.get('scale', ''))
            signal.axes_manager[i].size = int(dim.attrs.get('size', ''))
            units = re.findall('[^_\W]+', dim.attrs.get('units', ''))
            signal.axes_manager[i].units = ''.join(units)
        #extract metadata:
        group_metadata = {}
        for key, value in group.attrs.items():
            group_metadata[key] = value
        signal.metadata.General.title = record_by
        
        return (signal)

       
class ExperimentalData(object):
    """Container class for experimental data associated with a particular experiment."""
    
    name = "experimental_data"
    
    def __init__(self, root):       
        if type(root) == str: #if root is a folder path on disk       
            AC_folders = []
            for (dir, _, _) in os.walk(root):
                if not '.DS_Store' in dir: #delet the hidden folder '.DS_Store' in MacOS  
                    if os.path.isdir(dir):
                        AC_folders.append(dir)
            del AC_folders[0]  #Without this line, the list will start with 'root' rather than 'root/dir' 
                #5AC_folders is a list contains physical pathnames of data on disk
        
        elif type(root) == list:  #if root is a list of group of HDF5 file
            AC_folders = root
        #AC_folders is a list contains group  of ac1, ac2 etc. in HDF5 file
        
        #Load class Acquisition(object)
        n = 1
        self.ac = {}
        for f in AC_folders:
            self.ac[n] = Acquisition(f)
            n += 1  #'n' is the keys of the dictionary 'ac'. e.g. as follow
                    #ac[1] = Acquisition(folder1)
                    #ac[2] = Acquisition(folder2)


class Experiment(object):
    def load_experimental_data(self, exp_data):
        """Function to load experimental data to the experiment.
        Example: Experiment.load_experimental_data(experimental_data)"""
        
        self.e_data = exp_data
        
    def save(self, filename, e_data):
        """Function to save all data associated with an experiment into group '/experimental_data'."""
        """Initializer to meet the EMD format specification"""
        
        f = h5py.File(filename, 'w')
        f.attrs['version_major'] = 0  #EMD format required
        f.attrs['version_minor'] = 2  #EMD format required
        grp_e = f.create_group('experimental_data')

        grp_m = f.create_group('microscope')  #EMD format recommended
        #for key, value in self.microscope.items():
        #    grp_e.aattrs[key] = value
        grp_s = f.create_group('sample')  #EMD format recommended
        #for key, value in self.sample.items():
        #    grp_e.aattrs[key] = value
        grp_u = f.create_group('user')  #EMD format recommended
        #for key, value in self.user.items():
        #    grp_e.aattrs[key] = value
        grp_c = f.create_group('comments')  #EMD format recommended 
        #for key, value in self.comments.items():
        #    grp_e.aattrs[key] = value
        
        for ac_key, ac_val in e_data.ac.items():
            ac_grp = grp_e.create_group('ac{}'.format(ac_key))  #create acqusition group named as 'ac1', 'ac2' etc.
            
            for acs_key, acs_val in ac_val.__dict__.items():
                
                axes_data = acs_val.axes_manager
                axes_dict = acs_val.axes_manager.as_dictionary()                
                
                g = ac_grp.create_group(acs_key)  #create groups named by variable names such as 'haadf, eels_h...'
                g.attrs['emd_group_type'] = 1  #EMD format required
                data = g.create_dataset('data', data = acs_val.data)  #create main dataset 'data'
                data.attrs['type'] = acs_key                                                    #.data convert data to numpy array  
                                
                for k in range(len(axes_dict)):
                    dim = 'dim{}'.format(k+1) #name variable 'dim' as 'dim1, dim2, dim3...'
                    dset = g.create_dataset(dim, data = axes_data[k].axis)  #create a dataset for axis
                    for keys, vals in axes_data[k].get_axis_dictionary().items(): 
                        if keys == 'units':  #??? units still not quite fit the EMD specification
                            dset.attrs[keys] = '[{}]'.format('_'.join(list(str(vals))))
                        else:
                            dset.attrs[keys] = str(vals)
                        
    def read(self, filename):
        self.r = h5py.File(filename, 'r')
        def func_1(path):  #  define a callable func for .visit(func)
            if 'experimental_data' in path:
                return path
        p = self.r.visit(func_1)  #find the path of the group 'experimental_data'
        AC_folders = self.r[p].values()  #it's a list of groups within the group 'experimental_data'   
        self.e_data = ExperimentalData(AC_folders)
    


        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
            

