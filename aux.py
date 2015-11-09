"""Functions for dealing w/ Aux Files"""
import csv

def create_aux_file(data_dict, key_dict, other_keys, dataset_id, path):
    """
    Creates an aux file for a dataset.
    """
    # Define what to include in Aux.
    elements = ['Project', 'Replication', 'X', 'Y', 'Scan Number', 'Solar Azimuth', 'Solar Elevation', 'Solar Zenith',
                'GPS', 'Altitude', 'Latitude', 'Longitude', 'Battery Voltage', 'Canopy Temperature', 'Temperature 1',
                'Temperature 2', 'Pyronometer', 'Quantum Sensor']

    # Open the csv file and write the results
    with open(path, 'w') as f:
        write = csv.writer(f, delimiter=',')

        # First write the dataset ID
        write.writerow(['Dataset ID', dataset_id])

        # Now add the other rows
        for element in elements:
            if element in key_dict.keys():
                row = [element]
                row.extend(data_dict[key_dict[element]])
                write.writerow(row)

        # Add other found keys.
        if other_keys:
            for other_key in other_keys:
                if data_dict[other_key]:
                    row = [other_key]
                    row.extend(data_dict[other_key])
                    write.writerow(row)