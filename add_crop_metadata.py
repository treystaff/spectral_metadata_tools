"""
Script to add crop vegetation metadata to metadata.
"""
import os
import csv
from metadata import create_metadata_file

# First, open the crop descriptions file and read it
crop_desc = {}
with open('/code/spectral_metadata_tools/csp_crops.csv', 'r') as f:
    reader = csv.reader(f, delimiter=',')
    for row in reader:
        if row[0] not in crop_desc.keys():
            crop_desc[row[0]] = {}

        crop_desc[row[0]][row[1]] = row[2:]

restruct_dir = '/media/sf_tmp/restruct2/'
for root, subdirs, files in os.walk(restruct_dir):
    if 'Metadata.csv' in files:
        meta_path = os.path.join(root, 'Metadata.csv')
        with open(meta_path, 'r') as mfile:
            reader = csv.reader(mfile, delimiter=',')
            meta_dict = dict()

            for row in reader:
                meta_dict[row[0]] = row[1]

        if 'Location' not in meta_dict.keys(): 
            continue

        date = meta_dict['Date']
        year = date[:4]

        location = meta_dict['Location']
        if 'CSP01' in location:
            plot_num = '1'
        elif 'CSP02' in location:
            plot_num = '2'
        elif 'CSP03' in location:
            plot_num = '3'
        else:
            continue

        crop_name, cultivar, plant_date = crop_desc[year][plot_num]
        meta_dict['Crop Name'] = crop_name
        meta_dict['Crop Cultivar'] = cultivar
        meta_dict['Planting Date'] = plant_date

        create_metadata_file(meta_dict, meta_path) 
