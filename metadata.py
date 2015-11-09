"""Functions related to metadata managment"""
import csv
from utility import get_instrument_info, reps_to_targets, filter_floats


def create_metadata_file(metadata, path):
    """Creates a metadata file"""
    elements = ['Dataset ID', 'Project', 'Date', 'Start Time', 'Stop Time', 'Upwelling Instrument Name',
                'Upwelling Instrument Serial Number',
                'Upwelling Instrument FOV', 'Upwelling Instrument Channels', 'Upwelling Instrument Max Wavelength',
                'Upwelling Instrument Min Wavelength',
                'Downwelling Instrument Name', 'Downwelling Instrument Serial Number',
                'Downwelling Instrument FOV', 'Downwelling Instrument Channgels',
                'Downwelling Instrument Max Wavelength',
                'Downwelling Instrument Min Wavelength', 'Calibration Panel', 'Calibration Mode', 'Location',
                'Country', 'State', 'County', 'Target',
                'Acquisition Software', 'Software Version', 'Min Solar Elevation', 'Max Solar Elevation',
                'Min Solar Azimuth', 'Max Solar Azimuth', 'Min Solar Zenith', 'Max Solar Zenith', 'Min Latitude',
                'Max Latitude', 'Min Longitude', 'Max Longitude', 'Max Temperature 1', 'Min Temperature 1',
                'Max Temperature 2', 'Min Temperature 2', 'Max Pyronometer', 'Min Pyronometer', 'Max Quantum Sensor',
                'Min Quantum Sensor','Illumination Source', 'Cal Scans Count', 'Data Scans Count', 'Legacy Path']

    with open(path, 'w') as f:
        write = csv.writer(f, delimiter=',')
        for element in elements:
            if element in metadata.keys():
                if element == 'Target':
                    row = [element]
                    row.extend(metadata[element])
                    write.writerow(row)
                else:
                    write.writerow([element, metadata[element]])


def create_metadata_dict(cal_dict, data_dict, key_dict, data_dir):
    """
    Constructs the metadata dictionary from a calibration data and scandata dictionaries

    Parameters:
        cal_dict - Dictionary of CALMIT calibration data
        data_dict - Dicitonary of CALMIT scandata (not cal)
        key_dict - A key dictionary created via create_key_dict()
        data_dir - String. Path to data directory

    Returns:
        meta_dict - A dictionary
    """
    meta_dict = dict()
    #   Get the project name
    project = data_dict[key_dict['Project']][0]

    meta_dict['Project'] = project
    #   Date
    date = data_dict[key_dict['Date']][0]
    meta_dict['Date'] = date
    #   Construct the datasetID
    start_times = []
    start_times.extend(data_dict[key_dict['Start Time']])
    start_times.extend(cal_dict[key_dict['Start Time']])
    start_times.sort()
    min_start_time = start_times[0]
    dataset_id = '{0}_{1}_{2}'.format(project, date, min_start_time)
    meta_dict['Dataset ID'] = dataset_id
    #   Starttime
    meta_dict['Start Time'] = min_start_time
    #   Stoptime
    stop_times = []
    stop_times.extend(data_dict[key_dict['Stop Time']])
    stop_times.extend(cal_dict[key_dict['Stop Time']])
    stop_times.sort()
    meta_dict['Stop Time'] = stop_times[-1]

    #   Upwelling instrument
    instrument_str = data_dict[key_dict['Instrument']][0]
    instrument_name, snumber, fov = get_instrument_info(instrument_str)
    meta_dict['Upwelling Instrument Name'] = instrument_name
    meta_dict['Upwelling Instrument Serial Number'] = snumber
    meta_dict['Upwelling Instrument FOV'] = fov

    #   Cal panel
    meta_dict['Calibration Panel'] = data_dict[key_dict['Calibration Panel']][0]
    #   Software
    meta_dict['Software Version'] = data_dict[key_dict['Acquisition Software']][0]
    #   Target information
    meta_dict['Target'] = reps_to_targets(data_dict[key_dict['Replication']])
    #   Legacy Path
    meta_dict['Legacy Path'] = data_dir
    #   Calibration Mode
    if key_dict['Calibration Mode']:
        meta_dict['Calibration Mode'] = data_dict[key_dict['Calibration Mode']][0]

    #   Min and Max solar zenith
    zeniths = []
    zeniths.extend(data_dict[key_dict['Solar Zenith']])
    zeniths.extend(cal_dict[key_dict['Solar Zenith']])
    zeniths = filter_floats(zeniths)
    zeniths.sort()
    meta_dict['Min Solar Zenith'] = zeniths[0]
    meta_dict['Max Solar Zenith'] = zeniths[-1]
    #   Min and Max solar Elevatoin
    elevs = []
    elevs.extend(data_dict[key_dict['Solar Elevation']])
    elevs.extend(cal_dict[key_dict['Solar Elevation']])
    elevs = filter_floats(elevs)
    elevs.sort()
    meta_dict['Min Solar Elevation'] = elevs[0]
    meta_dict['Max Solar Elevation'] = elevs[-1]
    #   Min & max solar azimuth
    azimuths = []
    azimuths.extend(data_dict[key_dict['Solar Azimuth']])
    azimuths.extend(cal_dict[key_dict['Solar Azimuth']])
    azimuths = filter_floats(azimuths)
    azimuths.sort()
    meta_dict['Min Solar Azimuth'] = azimuths[0]
    meta_dict['Max Solar Azimuth'] = azimuths[-1]
    #   Min and Max lat/lon
    lats = []
    lats.extend(data_dict[key_dict['Latitude']])
    lats.extend(cal_dict[key_dict['Latitude']])
    if lats:  # check if GPS was active
        lats = filter_floats(lats)
        lats.sort()
        meta_dict['Min Latitude'] = lats[0]
        meta_dict['Max Latitude'] = lats[-1]
        # Min and max lon (only do this if there were lats)
        lons = []
        lons.extend(data_dict[key_dict['Longitude']])
        lons.extend(cal_dict[key_dict['Longitude']])
        lons = filter_floats(lons)
        lons.sort()
        meta_dict['Min Longitude'] = lons[0]
        meta_dict['Max Longitude'] = lons[-1]

    # Aux related metadata
    if 'Temperature 1' in key_dict.keys():
        temp1 = []
        temp1.extend(data_dict[key_dict['Temperature 1']])
        temp1.extend(cal_dict[key_dict['Temperature 1']])
        if temp1:
            temp1 = filter_floats(temp1)
            temp1.sort()
            meta_dict['Min Temperature 1'] = temp1[0]
            meta_dict['Max Temperature 1'] = temp1[-1]
    if 'Temperature 2' in key_dict.keys():
        temp2 = []
        temp2.extend(data_dict[key_dict['Temperature 2']])
        temp2.extend(cal_dict[key_dict['Temperature 2']])
        if temp2:
            temp2 = filter_floats(temp2)
            temp2.sort()
            meta_dict['Min Temperature 2'] = temp2[0]
            meta_dict['Max Temperature 2'] = temp2[-1]
    if 'Pyronometer' in key_dict.keys():
        pyro = []
        pyro.extend(data_dict[key_dict['Pyronometer']])
        pyro.extend(cal_dict[key_dict['Pyronometer']])
        if pyro:
            pyro = filter_floats(pyro)
            pyro.sort()
            meta_dict['Min Pyronometer'] = pyro[0]
            meta_dict['Max Pyronometer'] = pyro[-1]
    if 'Quantum Sensor' in key_dict.keys():
        quant = []
        quant.extend(data_dict[key_dict['Quantum Sensor']])
        quant.extend(cal_dict[key_dict['Quantum Sensor']])
        if quant:
            quant = filter_floats(quant)
            quant.sort()
            meta_dict['Min Quantum Sensor'] = quant[0]
            meta_dict['Max Quantum Sensor'] = quant[-1]

    # Number of scans (cal and data)
    meta_dict['Cal Scans Count'] = len(cal_dict[key_dict['File Name']])
    meta_dict['Data Scans Count'] = len(data_dict[key_dict['File Name']])

    return meta_dict
