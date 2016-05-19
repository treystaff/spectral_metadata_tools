import glob
from metadata import *
from datalogger import *
import re
import os
from utility import *
from aux import *
import logging
import time
import copy
import os
import shutil
process_dir = '/media/sf_O_DRIVE/reprocess_2001/test'
dirs_to_fix = ['2001_07_09', '2001_07_12']
newstrings = ['20010709', '20010712']
currstrings = ['20010907', '20011207']

for dir_to_fix, currstring, newstring in zip(dirs_to_fix, currstrings,newstrings):
    data_files = ['Downwelling Data01.txt', 'Raw Downwelling Data01.txt',
                  'Raw Upwelling Data01.txt', 'Reflectance Data01.txt',
                  'Upwelling Data01.txt']
    for data_file in data_files:

        data = readData(os.path.join(process_dir, dir_to_fix, data_file))
        for idx, entry in enumerate(data[0]):
            data[0][idx] = entry.replace(currstring, newstring)

        with open(os.path.join(process_dir, dir_to_fix, data_file), 'w') as f:
            writer = csv.writer(f, delimiter='\t')
            for row in data:
                writer.writerow(row)
        # Find the desired fields (aux & metadata fields)
        #   Maintain a dict of official name -> file key name

        
    """
    pics = glob.glob(os.path.join(process_dir,dir_to_fix,  '*.BMP'))
    for pic in pics:
        old_pic = os.path.join(process_dir, dir_to_fix, pic)
        pic = pic.replace(currstring, newstring)
        new_pic = os.path.join(process_dir, dir_to_fix, pic)
        shutil.move(old_pic, new_pic)
    """
    """
    binarys = glob.glob(os.path.join(process_dir,dir_to_fix,  '*.Downwelling'))
    binarys.extend(glob.glob(os.path.join(process_dir,dir_to_fix,
                                          '*.Upwelling')))
    binarys.extend(glob.glob(os.path.join(process_dir,dir_to_fix,'*.Calibration')))
    binarys = list(set(binarys))
    for binary in binarys:
        old_binary = os.path.join(process_dir, dir_to_fix, binary)
        binary = binary.replace(currstring, newstring)
        new_binary = os.path.join(process_dir, dir_to_fix, binary)
        shutil.move(old_binary, new_binary)
    """

