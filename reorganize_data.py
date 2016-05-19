"""
Function(s) for reogranizing CDAP data.

Takes a CDAP data directory and reorganizes
raw data files into scan data, auxiliary data, and
metadata files. These files are then placed in a
new directory organized by location.

Returns a dictionary indexed by directory path with
project names and rep names. This is then used to
move images, vegfraction data, etc. to new directories.
"""

from metadata import *
from datalogger import *
import re
import os
from utility import *
from aux import *
import logging
import time
import copy


def process_upwelling(data_dir, out_dir):
    """
    Processes the upwelling file(s) in a CDAP data directory.

    Parameters:
        data_dir - String. Path to CDAP data directory.
        out_dir - String. Path to store reorganized data.

    Returns:
        - A dictionary (?) mapping CDAP file fields to their locations and standardized names (so other files don't have
            to do the same work twice)
        - A dictionary containing metadata to be saved at end of restructuring process.
    """
    # Find CDAP upwelling files in the data directory
    up_pattern = r'^Upwelling.*\.txt'
    upwelling_files = [f for f in os.listdir(data_dir) if re.search(up_pattern, f)]

    if not upwelling_files:
        # Could be an 'outgoing' file
        up_pattern = r'^Outgoing.*\.txt'
        upwelling_files = [f for f in os.listdir(data_dir) if re.search(up_pattern, f)]

    # If not upwelling files found, return None.
    # TODO: Handle missing data files better. Probably should log this, along with other errors.
    if not upwelling_files:
        return None, None, None, None

    # Log that we are processing this directory. Note this is a stopgap for a better solution in the future....:
    logging.info('-------------------------------------------------------------\n'
                 'Processing {0}. Started {1} \n'.format(data_dir, time.strftime('%d/%m/%Y at %H:%M:%S')))

    upwelling_files.sort()  # Sort the files so *Data01.txt is first

    raw_pattern = r'Raw Upwelling.*\.txt'
    raw_upwelling_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if re.search(raw_pattern, f)]
    if not raw_upwelling_files:
        raw_pattern = r'Raw Outgoing.*\.txt'
        raw_upwelling_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if re.search(raw_pattern, f)]

    # Load the file(s). If more than one, join into one data structure for easy access.
    first = True
    for upwelling_file in upwelling_files:
        if first:
            data = readData(os.path.join(data_dir, upwelling_file))
            first = False
        else:
            odata = readData(os.path.join(data_dir, upwelling_file))
            for idx, row in enumerate(odata):
                data[idx].extend(row[1:])

            del odata

    if data[0][0].startswith('PROCESSED'):
        raise NotImplementedError('CDAP 2 NOT IMPLEMENTED YET!')
        cdap2 = True
    else:
        cdap2 = False

    # Get the fields of the data
    fields = getFields(data)
    # Find the scan starting idx
    scanidx = findScanIdx(fields)
    # Create a list of just the wavelengths
    scan_keys = fields[scanidx:]
    # Get only those that are actual wavelength numbers
    wavelengths = filter_floats(scan_keys)
    # Create a list of just the header keys
    hkeys = fields[0:scanidx]

    # Find the desired fields (aux & metadata fields)
    #   Maintain a dict of official name -> file key name
    key_dict = create_key_dict(hkeys)

    # Find other keys that are not 'reserved' or 'other data'
    #   Find optional keys
    # Average Adjustment
    try:
        key_dict['Average Adj'] = find_cdap_key(hkeys, {'average adj'})
    except KeyError:
        pass

    # Find unanticipated keys not 'reserved' or 'other data'
    other_keys = [key for key in hkeys if key not in key_dict.values() and
                  key.lower() not in {'reserved', 'additional data', 'lamp', 'shutter status',
                                      'battery voltage', 'scan begin & end', 'solar angles', 'unispec dc'}]

    # So that each scan can be processed, we get the index position of key fields needed to determine
    #   a scan's status (cal or not), location, and project.
    # Get lats and lons idx position
    lat_idx = fields.index(key_dict['Latitude'])
    lon_idx = fields.index(key_dict['Longitude'])
    # Get the idx of the project names
    project_idx = fields.index(key_dict['Project'])
    # Get the index position of rep names and filenames
    rep_idx = fields.index(key_dict['Replication'])
    filename_idx = fields.index('File Name')

    # Create data structures that will contain relevant info
    loc_dict = dict()  # Location-based non-calibration data.
    loc_idxs = dict()  # Dictionary containing idxs of columns belonging to non-cal data scans indexed by location
    cal_idxs = []  # List containing idxs of columns that have cal-data in them.
    standard_project_names = [] # List containing the standardized project name for each scan.

    # Create a list for holding subsets of cdap data. First element of each row is a field name
    empty_data = []   # Just call it 'empty_data' for now bc it doesn't have any data in it...
    for row in data:
        empty_data.append([row[0]])

    # Prepare the cal data structure
    cal_data = copy.deepcopy(empty_data)  # Just make a copy of the empty_data

    # Process each col individually to determine if cal or spectral data.
    num_scans = len(data[filename_idx][1:])
    for col_idx in range(1, num_scans + 1):
        col_data = extract_col(col_idx, data)

        # Find the location of each rep
        lat = col_data[lat_idx]
        lon = col_data[lon_idx]
        project = col_data[project_idx]
        location, country, state, county = determine_loc(lat, lon, project)
        if location is None:
            location = 'Unknown'
            country = 'Unknown'
            state = 'Unknown'
            county = 'Unknown'

        # Once we have the location, we can standardize this scan's project name.
        col_data[project_idx] = standardize_project_name(project, location)
        standard_project_names.append(col_data[project_idx])

        # Figure out if this is a cal scan
        rep = col_data[rep_idx]
        filename = col_data[filename_idx]

        if is_cal_rep(rep, filename):
            cal_idxs.append(col_idx)

            # Ensure the cal rep is appropriately named
            col_data[rep_idx] = 'CAL'

            # Add the column to the cal_data
            for row_idx, row in enumerate(col_data):
                cal_data[row_idx].append(row)

        else:
            # Current col is not a cal scan
            if location in loc_idxs.keys():
                loc_idxs[location].append(col_idx)

                # Extend the existing data list
                for row_idx, row in enumerate(col_data):
                    loc_dict[location][row_idx].append(row)
            else:
                loc_idxs[location] = [col_idx]

                # Create a new entry.
                loc_list = copy.deepcopy(empty_data)
                for row_idx, row in enumerate(col_data):
                            loc_list[row_idx].append(row)

                loc_dict[location] = loc_list
                del loc_list

    # Now that every scan has been processed, deal with cal data first:
    # -----------------------------------------------------------------
    # -------------------------cal processing--------------------------
    # -----------------------------------------------------------------
    # Convert to dicts for ease of access
    cal_dict, cal_scans, _ = data2dict(cal_data)

    # Modify the datalogger entry: split datalogger values into respective fields
    if not cal_dict[key_dict['Date']][0].startswith('2001'):
        if cal_dict[key_dict['Data Logger']]:
            cal_dict, key_dict = datalogger_to_dict(cal_dict, key_dict, data_dir)

    # Create the calibration metadata dict
    cal_meta = create_metadata_dict(cal_dict, key_dict, data_dir, cal=True)

    # Add instrument-specific meta to cal_meta.
    cal_meta['Upwelling Instrument Max Wavelength'] = max(wavelengths)
    cal_meta['Upwelling Instrument Min Wavelength'] = min(wavelengths)
    cal_meta['Upwelling Instrument Channels'] = len(wavelengths)

    # Also edit the project

    if cdap2 is False:
        cal_meta['Acquisition Software'] = 'CALMIT Data Acquisition Program (CDAP)'
    else:
        cal_meta['Acquisition Software'] = 'CALMIT Data Acquisition Program (CDAP) 2'

    # Create the directory cal info will be stored in
    cal_dir = os.path.join(out_dir, cal_meta['Date'], 'cal_data')
    if not os.path.exists(cal_dir):
        os.makedirs(cal_dir)
    else:
        # We have an issue...There appears to already be cal data here.
        # For now, we will place cal data from each dataset into separate directories.
        # TODO possibly combine caldata into one file. Need to investigate this first.
        cal_dir = create_dataset_dirs(cal_dir, cal_meta['Dataset ID'])
        warn_str = 'Another Calibration dataset with the same date was found. Placing data in {0}'.format(cal_dir)
        warnings.warn(warn_str)
        logging.warning(warn_str)

    cal_meta['out_dir'] = cal_dir

    # Create the cal aux and scan files
    if cal_dict[key_dict['Replication']]:
        dataset_id = cal_meta['Dataset ID']
        create_aux_file(cal_dict, key_dict, other_keys, dataset_id, os.path.join(cal_dir, 'Auxiliary_Cal.csv'))
        create_scan_file(cal_dict, key_dict, cal_scans, dataset_id, os.path.join(cal_dir, 'Upwelling_Cal_data.csv'))

    # Now process each location-specific non-cal data
    # -----------------------------------------------------------------
    # -----------------------non-cal processing------------------------
    # -----------------------------------------------------------------
    loc_meta = dict()
    for loc in loc_dict.keys():
        # Load the data for the location, and convert to a dictionary for easy-access.
        data = loc_dict[loc]

        # Convert to dicts for ease of access
        data_dict, data_scans, _ = data2dict(data)

        # Modify the datalogger entry: split datalogger values into respective fields
        if not data_dict[key_dict['Date']][0].startswith('2001'):
            if data_dict[key_dict['Data Logger']]:
                data_dict, key_dict = datalogger_to_dict(data_dict, key_dict, data_dir)

        # Construct the metadata for this location.
        loc_meta[loc] = create_metadata_dict(data_dict, key_dict, data_dir)
        loc_meta[loc]['Location'] = loc
        loc_meta[loc]['County'] = county
        loc_meta[loc]['State'] = state
        loc_meta[loc]['Country'] = country
        if loc in {'CSP01', 'CSP02', 'CSP03', 'CSP03A'}:
            # We know it's outside.
            loc_meta[loc]['Illumination Source'] = 'Sun'

        # Add instrument-specific entries to loc_meta
        loc_meta[loc]['Upwelling Instrument Max Wavelength'] = max(wavelengths)
        loc_meta[loc]['Upwelling Instrument Min Wavelength'] = min(wavelengths)
        loc_meta[loc]['Upwelling Instrument Channels'] = len(wavelengths)

        if cdap2 is False:
            loc_meta[loc]['Acquisition Software'] = 'CALMIT Data Acquisition Program (CDAP)'
        else:
            loc_meta[loc]['Acquisition Software'] = 'CALMIT Data Acquisition Program (CDAP) 2'

        # Construct a directory to put the restructured data in. (ou_dir/location/date/)
        loc_dir = os.path.join(out_dir, data_dict[key_dict['Date']][0], loc)
        if not os.path.exists(loc_dir):
            os.makedirs(loc_dir)
        else:
            # We have a problem. This probably means there is more than one project per loc/date combo.
            loc_dir = create_dataset_dirs(loc_dir, loc_meta[loc]['Dataset ID'])
            warn_str = 'Another dataset with the same location/date was found. Placing data in {0}'.format(loc_dir)
            warnings.warn(warn_str)
            logging.warning(warn_str)

        loc_meta[loc]['out_dir'] = loc_dir

        # Save the Aux and scandata files (data and cal) if they have data.
        dataset_id = loc_meta[loc]['Dataset ID']
        if data_dict[key_dict['Replication']]:
            create_aux_file(data_dict, key_dict, other_keys, dataset_id, os.path.join(loc_dir, 'Auxiliary.csv'))
            create_scan_file(data_dict, key_dict, data_scans, dataset_id, os.path.join(loc_dir, 'Upwelling_data.csv'))

    # Create raw scandata files if raw data files exist
    if raw_upwelling_files:
        create_raw_scans_files(raw_upwelling_files, cal_idxs, loc_idxs, loc_meta, cal_meta, key_dict, 'Upwelling')

    # Return the metadata dict and key_dict
    return cal_idxs, loc_idxs, loc_meta, cal_meta, key_dict, standard_project_names


def process_downwelling(data_dir, cal_idxs, loc_idxs, loc_meta, cal_meta, key_dict, standardized_project_names):
    """
    Processes the upwelling file(s) in a CDAP data directory.

    Parameters:
        data_dir - String. Path to CDAP data directory.
        out_dir - String. Path to store reorganized data.
        cal_idxs - List. From process_upwelling
        loc_idxs - Dict. From process_upwelling
        loc_meta - Dict. From process_upwelling
        cal_meta - Dict. From process_upwelling
        key_dict - Dict. From process_upwelling

    Returns:
        - A dictionary (?) mapping CDAP file fields to their locations and standardized names (so other files don't have
            to do the same work twice)
        - A dictionary containing metadata to be saved at end of restructuring process.
    """

    # Find CDAP downwelling files in the data directory
    down_pattern = r'^Downwelling.*\.txt'
    downwelling_files = [f for f in os.listdir(data_dir) if re.search(down_pattern, f)]
    if not downwelling_files:
        # Could be an 'incoming' file
        down_pattern = r'^Incoming.*\.txt'
        downwelling_files = [f for f in os.listdir(data_dir) if re.search(down_pattern, f)]

    downwelling_files.sort()  # Sort the files so *Data01.txt is first

    # Process raw files if necessary
    raw_pattern = r'Raw Downwelling.*\.txt'
    raw_downwelling_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if re.search(raw_pattern, f)]
    if not raw_downwelling_files:
        raw_pattern = r'Raw Incoming.*\.txt'
        raw_downwelling_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if re.search(raw_pattern, f)]
    if raw_downwelling_files:
        create_raw_scans_files(raw_downwelling_files, cal_idxs, loc_idxs, loc_meta, cal_meta, key_dict, 'Downwelling')

    if not downwelling_files:
        if raw_downwelling_files:
            print('n No Downwelling but there are RAW DOWNWELLING...{0}'.format(data_dir))
            return
        else:
            print('No Downwelling. {0}'.format(data_dir))
            cal_dir = cal_meta['out_dir']
            create_metadata_file(cal_meta, os.path.join(cal_dir, 'Metadata.csv'))
            for loc in loc_idxs.keys():
                loc_dir = loc_meta[loc]['out_dir']
                create_metadata_file(loc_meta[loc], os.path.join(loc_dir, 'Metadata.csv'))
            return

    # Load the file(s). If more than one, join into one data structure for easy access.
    first = True
    for downwelling_file in downwelling_files:
        if first:
            data = readData(os.path.join(data_dir, downwelling_file))
            first = False
        else:
            odata = readData(os.path.join(data_dir, downwelling_file))
            for idx, row in enumerate(odata):
                data[idx].extend(row[1:])

            del odata

    # Get the fields of the data
    fields = getFields(data)
    scanidx = findScanIdx(fields)

    # Standardize the project names
    data[fields.index(key_dict['Project'])][1:] = standardized_project_names

    # Deal with cal data first
    cal_data, _ = split_cal_scans(data, cal_idxs)
    cal_dict, cal_scans, _ = data2dict(cal_data)

    cal_dir = cal_meta['out_dir']
    dataset_id = cal_meta['Dataset ID']

    if cal_dict[key_dict['Replication']]:
            create_scan_file(cal_dict, key_dict, cal_scans, dataset_id,
                             os.path.join(cal_dir, 'Downwelling_Cal_data.csv'))

    # Update the metadata
    instrument_str = cal_dict[key_dict['Instrument']][0]
    instrument_name, snumber, fov = get_instrument_info(instrument_str)
    cal_meta['Downwelling Instrument Name'] = instrument_name
    cal_meta['Downwelling Instrument Serial Number'] = snumber
    cal_meta['Downwelling Instrument FOV'] = fov
    # Add instrument-specific entries to loc_meta.
    # Create a list of just the wavelengths
    scan_keys = fields[scanidx:]
    # Get only those that are actual wavelength numbers
    wavelengths = filter_floats(scan_keys)
    cal_meta['Downwelling Instrument Max Wavelength'] = max(wavelengths)
    cal_meta['Downwelling Instrument Min Wavelength'] = min(wavelengths)
    cal_meta['Downwelling Instrument Channels'] = len(wavelengths)

    # Write the new metadata entry
    create_metadata_file(cal_meta, os.path.join(cal_dir, 'Metadata.csv'))

    # Split the data into locations
    for loc in loc_idxs.keys():
        loc_data = split_by_idxs(data, loc_idxs[loc])

        reps = loc_data[fields.index(key_dict['Replication'])][1:]
        raw_filenames = loc_data[fields.index('File Name')][1:]
        loc_cal_idxs = find_cal_reps(reps, raw_filenames)

        # Now split each location's data into scan and cal data.
        _, scan_data = split_cal_scans(loc_data, loc_cal_idxs)

        # Create the data dicts
        data_dict, data_scans, _ = data2dict(scan_data)

        # Save the scandata files
        loc_dir = loc_meta[loc]['out_dir']
        dataset_id = loc_meta[loc]['Dataset ID']

        if data_dict[key_dict['Replication']]:
            create_scan_file(data_dict, key_dict, data_scans, dataset_id,
                             os.path.join(loc_dir, 'Downwelling_data.csv'))

        # Update the metadata
        instrument_str = data_dict[key_dict['Instrument']][0]
        instrument_name, snumber, fov = get_instrument_info(instrument_str)
        loc_meta[loc]['Downwelling Instrument Name'] = instrument_name
        loc_meta[loc]['Downwelling Instrument Serial Number'] = snumber
        loc_meta[loc]['Downwelling Instrument FOV'] = fov
        # Add instrument-specific entries to loc_meta.
        loc_meta[loc]['Downwelling Instrument Max Wavelength'] = max(wavelengths)
        loc_meta[loc]['Downwelling Instrument Min Wavelength'] = min(wavelengths)
        loc_meta[loc]['Downwelling Instrument Channels'] = len(wavelengths)

        # Write the new metadata entry
        create_metadata_file(loc_meta[loc], os.path.join(loc_dir, 'Metadata.csv'))


def process_reflectance(data_dir, cal_idxs, loc_idxs, loc_meta, cal_meta, key_dict, standardized_project_names):
    # Find CDAP downwelling files in the data directory
    ref_pattern = r'^Reflectance.*\.txt'
    ref_files = [f for f in os.listdir(data_dir) if re.search(ref_pattern, f)]
    if ref_files:
        ref_files.sort()  # Sort the files so *Data01.txt is first

        # Load the file(s). If more than one, join into one data structure for easy access.
        first = True
        for ref_file in ref_files:
            if first:
                data = readData(os.path.join(data_dir, ref_file))
                first = False
            else:
                odata = readData(os.path.join(data_dir, ref_file))
                for idx, row in enumerate(odata):
                    data[idx].extend(row[1:])

                del odata

        fields = getFields(data)
        # Standardize the project names
        data[fields.index(key_dict['Project'])][1:] = standardized_project_names

        # Deal with cal data first.
        cal_data, _ = split_cal_scans(data, cal_idxs)
        cal_dict, cal_scans, _ = data2dict(cal_data)

        dataset_id = cal_meta['Dataset ID']
        cal_dir = cal_meta['out_dir']
        if cal_dict[key_dict['Replication']]:
            create_scan_file(cal_dict, key_dict, cal_scans, dataset_id,
                             os.path.join(cal_dir, 'Reflectance_Cal_data.csv'))

        # Split the data into locations
        for loc in loc_idxs.keys():
            loc_data = split_by_idxs(data, loc_idxs[loc])

            # Now split each location's data into scan and cal data.
            reps = loc_data[fields.index(key_dict['Replication'])][1:]
            raw_filenames = loc_data[fields.index('File Name')][1:]
            loc_cal_idxs = find_cal_reps(reps, raw_filenames)

            _, scan_data = split_cal_scans(loc_data, loc_cal_idxs)

            # Create the data dicts
            data_dict, data_scans, _ = data2dict(scan_data)
            
            # Save the scandata files
            loc_dir = loc_meta[loc]['out_dir']
            dataset_id = loc_meta[loc]['Dataset ID']

            if data_dict[key_dict['Replication']]:
                create_scan_file(data_dict, key_dict, data_scans, dataset_id,
                                 os.path.join(loc_dir, 'Reflectance_data.csv'))
