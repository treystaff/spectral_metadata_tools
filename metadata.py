"""Functions related to metadata managment"""
import csv
#from utility import get_instrument_info, reps_to_targets, filter_floats
from utility import *
import re


def create_metadata_file(metadata,  out_path):
    """
    Creates a metadata file 
    (note, this function may not work properly in an
    interpreter because it assumes the file attribute exists.)

    Parameters:
        metadata - dict. A calmit metadata dictionary (created with
            create_metadata_dict)
        path - path of the output metadata file.
            In the form [name, value, unit, description]
    """
    meta_list_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                  'METADATA_DESCRIPTIONS.csv')
    # Read metadata elements from the meta list file.
    # (In the form [name, unit, desc., keyword_id]) we don't need the
    # keyword_id.
    elements = []
    with open(meta_list_path, 'r') as meta_list_file:
        reader = csv.reader(meta_list_file, delimiter=',')
        for row in reader:
            elements.append(row[:-1])

    # Now write the calmit metadata to file.
    with open(out_path, 'w') as f:
        write = csv.writer(f, delimiter=',')
        for element in elements:
            attribute = element[0]
            if attribute in metadata.keys():
                value = metadata[attribute]
                if isinstance(value, list):
                    if len(value) > 1:
                        # A couple of metadata entries have multiple values
                        # (target, cal panel). Join them, separated by a ';'
                        element.insert(1, ';'.join(value))
                    else:
                        if len(value) >= 1:
                            element.insert(1, value[0])
                else:
                    # Just insert the value into the element list.
                    element.insert(1, value)

                # Write the metadata result to file. [name, value, unit, desc.]
                write.writerow(element)


def create_metadata_dict(data_dict, key_dict, data_dir, cal=False):
    """
    Constructs the metadata dictionary from a data dictionaries

    Parameters:
        data_dict - Dicitonary of CALMIT
        key_dict - A key dictionary created via create_key_dict()
        data_dir - String. Path to data directory
        cal - Boolean (defualt: False). Specifies if this will be a cal meta
            dict

    Returns:
        meta_dict - A dictionary
    """
    meta_dict = dict()
    #   Get the project name
    if cal:
        project = 'CSP-CAL'
    else:
        project = data_dict[key_dict['Project']][0]

    meta_dict['Project'] = project
    #   Date
    date = data_dict[key_dict['Date']][0]
    meta_dict['Date'] = date
    #   Construct the datasetID
    start_times = data_dict[key_dict['Start Time']]
    # Have a regular expression filter malformed timestamps
    time_pattern = re.compile(r'\d{2}:\d{2}:\d{2}')
    start_times = [time for time in start_times if time_pattern.match(time)]
    start_times.sort()
    min_start_time = start_times[0]
    dataset_id = '{0}_{1}_{2}'.format(project, date, min_start_time)
    meta_dict['Dataset ID'] = dataset_id
    #   Starttime
    meta_dict['Start Time'] = min_start_time
    #   Stoptime
    stop_times = data_dict[key_dict['Stop Time']]
    stop_times = [time for time in stop_times if time_pattern.match(time)]
    stop_times.sort()
    meta_dict['Stop Time'] = stop_times[-1]

    #   Upwelling instrument
    instrument_str = data_dict[key_dict['Instrument']][0]
    instrument_name, snumber, fov = get_instrument_info(instrument_str)
    meta_dict['Upwelling Instrument Name'] = instrument_name
    meta_dict['Upwelling Instrument Serial Number'] = snumber
    meta_dict['Upwelling Instrument FOV'] = fov

    #   Cal panel
    meta_dict['Calibration Panel'] = list(set(data_dict[key_dict['Calibration Panel']]))
    #   Software
    meta_dict['Software Version'] = data_dict[key_dict['Acquisition Software']][0]
    #   Target information
    if cal:
        meta_dict['Target'] = meta_dict['Calibration Panel']
    else:
        meta_dict['Target'] = reps_to_targets(data_dict[key_dict['Replication']])
    #   Legacy Path
    meta_dict['Legacy Path'] = data_dir[data_dir.find('sf_') + 3:]  # Remove the /media/sf_ prefix from using the VM.
    #   Calibration Mode
    if key_dict['Calibration Mode']:
        meta_dict['Calibration Mode'] = data_dict[key_dict['Calibration Mode']][0]

    #   Min and Max solar zenith
    zeniths = data_dict[key_dict['Solar Zenith']]
    zeniths = filter_floats(zeniths)
    zeniths.sort()
    meta_dict['Min Solar Zenith'] = zeniths[0]
    meta_dict['Max Solar Zenith'] = zeniths[-1]
    #   Min and Max solar Elevatoin
    elevs = data_dict[key_dict['Solar Elevation']]
    elevs = filter_floats(elevs)
    elevs.sort()
    meta_dict['Min Solar Elevation'] = elevs[0]
    meta_dict['Max Solar Elevation'] = elevs[-1]
    #   Min & max solar azimuth
    azimuths = data_dict[key_dict['Solar Azimuth']]
    azimuths = filter_floats(azimuths)
    azimuths.sort()
    meta_dict['Min Solar Azimuth'] = azimuths[0]
    meta_dict['Max Solar Azimuth'] = azimuths[-1]
    #   Min and Max lat/lon
    lats = data_dict[key_dict['Latitude']]
    if lats and not all(val == '-9999' or val == '' for val in lats):  # check if GPS was active
        lats = filter_floats(lats)
        lats.sort()
        meta_dict['Min Latitude'] = lats[0]
        meta_dict['Max Latitude'] = lats[-1]
        meta_dict['Average Latitude'] = mean(lats)
        # Min and max lon (only do this if there were lats)
        lons = data_dict[key_dict['Longitude']]
        lons = filter_floats(lons)
        lons.sort()
        meta_dict['Min Longitude'] = lons[0]
        meta_dict['Max Longitude'] = lons[-1]
        meta_dict['Average Longitude'] = mean(lons)

    # Aux related metadata
    if 'Canopy Temperature' in key_dict.keys():
        temp1 = data_dict[key_dict['Canopy Temperature']]
        if temp1 and not all(val == '-9999' for val in temp1):
            temp1 = filter_floats(temp1)

            temp1.sort()
            meta_dict['Min Canopy Temperature'] = temp1[0]
            meta_dict['Max Canopy Temperature'] = temp1[-1]
    if 'Wheel Temperature' in key_dict.keys() and 'Wheel Temperature' in data_dict.keys():
        temp2 = data_dict[key_dict['Wheel Temperature']]
        if temp2 and not all(val == '-9999' for val in temp2):
            temp2 = filter_floats(temp2)
            temp2.sort()
            meta_dict['Min Wheel Temperature'] = temp2[0]
            meta_dict['Max Wheel Temperature'] = temp2[-1]
    if 'Pyranometer' in key_dict.keys() and 'Pyranometer' in data_dict.keys():
        pyro = data_dict[key_dict['Pyranometer']]
        if pyro and not all(val == '-9999' for val in pyro):
            pyro = filter_floats(pyro)
            pyro.sort()
            meta_dict['Min Pyranometer'] = pyro[0]
            meta_dict['Max Pyranometer'] = pyro[-1]
    if 'Quantum Sensor' in key_dict.keys() and 'Quantum Sensor' in data_dict.keys():
        quant = data_dict[key_dict['Quantum Sensor']]
        if quant and not all(val == '-9999' for val in quant):
            quant = filter_floats(quant)
            quant.sort()
            meta_dict['Min Quantum Sensor'] = quant[0]
            meta_dict['Max Quantum Sensor'] = quant[-1]

    # Number of scans (cal and data)
    meta_dict['Scans Count'] = len(data_dict[key_dict['File Name']])

    # Finally, we maintain a set of info on project names, dates, reps, and scan numbers that go along with
    #   this data so we can copy the proper files from the original directory (pics, etc.)

    meta_dict['scans_info'] = [data_dict['File Name'], data_dict[key_dict['Stop Time']]]

    return meta_dict


def read_metadata(path):
    """
    Read metadata file and return results as dictionary.
    """
    with open(path) as mfile:
        reader = csv.reader(mfile, delimiter=',')
        meta_dict = dict()
        for row in reader:
            try:
                meta_dict[row[0]] = row[1]
            except IndexError:
                pass

    return meta_dict

