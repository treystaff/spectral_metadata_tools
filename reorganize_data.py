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

import re
import os
from utility import *


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

    upwelling_files.sort()  # Sort the files so *Data01.txt is first

    raw_pattern = r'Raw Upwelling.*\.txt'
    raw_upwelling_files = [data_dir + f for f in os.listdir(data_dir) if re.search(raw_pattern, f)]
    if not raw_upwelling_files:
        raw_pattern = r'Raw Outgoing.*\.txt'
        raw_upwelling_files = [data_dir + f for f in os.listdir(data_dir) if re.search(raw_pattern, f)]


    # Load the file(s). If more than one, join into one data structure for easy access.
    first = True
    for upwelling_file in upwelling_files:
        if first:
            data = readData(data_dir + upwelling_file)
        else:
            first = False
            odata = readData(data_dir + upwelling_file)
            for idx, row in enumerate(odata):
                data[idx].extend(row[1:-1])

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

    # Extract lats and lons
    lats = data[fields.index(key_dict['Latitude'])][1:-1]
    lons = data[fields.index(key_dict['Longitude'])][1:-1]

    # Process each unique project. Add the results to a location-indexed dict
    loc_dict = dict()
    loc_idxs = dict()
    # Find the unique project names
    projects = data[fields.index(key_dict['Project'])][1:-1]
    distinct_projects = set(projects)
    for project in distinct_projects:
        # Find the location of each project
        plats, p_idxs = filter_lists(lats, projects, project)
        plons = filter_lists(lons, projects, project)
        location, country, state, county = determine_loc(lats, lons, project)

        # Maintain a dict of the indexes that match a location.
        if location in loc_idxs.keys():
            loc_idxs[location].extend(p_idxs)
        else:
            loc_idxs[location] = p_idxs

        if location in loc_dict.keys():
            # Extend the existing data list
            for idx, row in enumerate(data):
                # Some rows may be empty
                if len(row) > 1:
                    for p_idx in p_idxs:
                        try:
                            loc_dict[location][idx].append(row[p_idx])
                        except:
                            # some rows don't span the whole document
                            loc_dict[location][idx].append('')
        else:
            # Create a new entry.
            loc_list = []
            for idx, row in enumerate(data):
                loc_list.append([])
                loc_list[idx].append(row[0])
                # Some rows may be empty.
                if len(row) > 1:
                    for p_idx in p_idxs:
                        try:
                            loc_list[idx].append(row[p_idx])
                        except IndexError:
                            # Some rows don't span the whole document.
                            loc_list[idx].append('')


            loc_dict[location] = loc_list
            del loc_list

    # Now process each location individually
    loc_meta = dict()
    cal_idxs = dict()
    for loc in loc_dict.keys():
        # Load the data for the location, and convert to a dictionary for easy-access.
        data = loc_dict[loc]

        # Put the caldata in a separate list
        reps = data[fields.index(key_dict['Replication'])][1:-1]
        cal_idxs[loc] = find_cal_reps(reps)
        cal_data, scan_data = split_cal_scans(data, cal_idxs[loc])

        # Convert to dicts for ease of access
        data_dict, data_scans, _ = data2dict(scan_data)
        data_dict = standardize_project_name(data_dict, key_dict)

        cal_dict, cal_scans, _ = data2dict(cal_data)
        cal_dict = standardize_project_name(cal_dict, key_dict)

        # Construct the metadata for this location.
        loc_meta[loc] = create_metadata_dict(cal_dict, data_dict, key_dict, data_dir)
        loc_meta[loc]['Location'] = loc
        loc_meta[loc]['County'] = county
        loc_meta[loc]['State'] = state
        loc_meta[loc]['Country'] = country

        if cdap2 is False:
            loc_meta[loc]['Acquisition Software'] = 'CALMIT Data Acquisition Program (CDAP)'
        else:
            loc_meta[loc]['Acquisition Software'] = 'CALMIT Data Acquisition Program (CDAP) 2'

        # Modify the datalogger entry: split datalogger values into repsective fields
        cal_dict, data_dict = datalogger_to_dict(cal_dict, data_dict, key_dict)

        # Construct a directory to put the restructured data in. (ou_dir/location/date/)
        loc_dir = os.path.join(out_dir, loc, data_dict[key_dict['Date']][0])
        if not os.path.exists(loc_dir):
            os.makedirs(loc_dir)
        else:
            # We have a problem. This probably means there is more than one project per loc/date combo.
            raise IOError(loc_dir + ' already exists! This could mean there is another project with the same location '
                                    'and date as a previously restructured dataset.')

        # Save the Aux and scandata files (data and cal) if they have data.
        dataset_id = loc_meta[loc]['Dataset ID']
        if data_dict[key_dict['Replication']]:
            create_aux_file(data_dict, key_dict, other_keys, dataset_id, loc_dir + '/Auxiliary.csv')
            create_scan_file(data_dict, key_dict, data_scans, dataset_id, loc_dir + '/Upwelling_data.csv')
        if cal_dict[key_dict['Replication']]:
            create_aux_file(cal_dict, key_dict, other_keys, dataset_id, loc_dir + '/Auxiliary_Cal.csv')
            create_scan_file(cal_dict, key_dict, cal_scans, dataset_id, loc_dir + '/Upwelling_Cal_data.csv')

    # Create raw scandata files if raw data files exist
    if raw_upwelling_files:
        create_raw_scans_files(raw_upwelling_files, cal_idxs, loc_idxs, loc_meta, key_dict, 'Upwelling', out_dir)

    # Return the metadata dict and key_dict
    return cal_idxs, loc_idxs, loc_meta, key_dict

    # TODO Also return info on location directory paths w/ loc & reps so other files can be moved.


def process_downwelling(data_dir, out_dir, cal_idxs, loc_idxs, loc_meta, key_dict):
    """
    Processes the upwelling file(s) in a CDAP data directory.

    Parameters:
        data_dir - String. Path to CDAP data directory.
        out_dir - String. Path to store reorganized data.
        cal_idxs - Dict. From process_upwelling
        loc_idxs - Dict. From process_upwelling
        loc_meta - Dict. From process_upwelling
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
    raw_downwelling_files = [data_dir + f for f in os.listdir(data_dir) if re.search(raw_pattern, f)]
    if not raw_downwelling_files:
        raw_pattern = r'Raw Incoming.*\.txt'
        raw_downwelling_files = [data_dir + f for f in os.listdir(data_dir) if re.search(raw_pattern, f)]
    if raw_downwelling_files:
        create_raw_scans_files(raw_downwelling_files, cal_idxs, loc_idxs, loc_meta, key_dict, 'Downwelling', out_dir)

    # Load the file(s). If more than one, join into one data structure for easy access.
    first = True
    for downwelling_file in downwelling_files:
        if first:
            data = readData(data_dir + downwelling_file)
        else:
            first = False
            odata = readData(data_dir + downwelling_file)
            for idx, row in enumerate(odata):
                data[idx].extend(row[1:-1])

            del odata

    # Split the data into locations
    for loc in loc_idxs.keys():
        loc_data = split_by_idxs(data, loc_idxs[loc])

        # Now split each location's data into scan and cal data.
        cal_data, scan_data = split_cal_scans(loc_data, cal_idxs[loc])

        # Create the data dicts
        data_dict, data_scans, _ = data2dict(scan_data)
        data_dict = standardize_project_name(data_dict, key_dict)

        cal_dict, cal_scans, _ = data2dict(cal_data)
        cal_dict = standardize_project_name(cal_dict, key_dict)


        # Save the scandata files
        loc_dir = os.path.join(out_dir, loc, data_dict[key_dict['Date']][0])
        dataset_id = loc_meta[loc]['Dataset ID']

        if data_dict[key_dict['Replication']]:
            create_scan_file(data_dict, key_dict, data_scans, dataset_id, loc_dir + '/Downwelling_data.csv')
        if cal_dict[key_dict['Replication']]:
            create_scan_file(cal_dict, key_dict, cal_scans, dataset_id, loc_dir + '/Downwelling_Cal_data.csv')

        # Update the metadata
        instrument_str = data_dict[key_dict['Instrument']][0]
        instrument_name, snumber, fov = get_instrument_info(instrument_str)
        loc_meta[loc]['Downwelling Instrument Name'] = instrument_name
        loc_meta[loc]['Downwelling Instrument Serial Number'] = snumber
        loc_meta[loc]['Downwelling Instrument FOV'] = fov
        if loc in {'CSP01', 'CSP02', 'CSP03'}:
            # We know it's outside.
            loc_meta[loc]['Illumination Source'] = 'Sun'

        # Write the new metadata entry
        create_metadata_file(loc_meta[loc], loc_dir + '/Metadata.csv')


def process_reflectance(data_dir, out_dir, cal_idxs, loc_idxs, loc_meta, key_dict):
    # Find CDAP downwelling files in the data directory
    ref_pattern = r'^Reflectance.*\.txt'
    ref_files = [f for f in os.listdir(data_dir) if re.search(ref_pattern, f)]
    if ref_files:
        ref_files.sort()  # Sort the files so *Data01.txt is first

        # Load the file(s). If more than one, join into one data structure for easy access.
        first = True
        for ref_file in ref_files:
            if first:
                data = readData(data_dir + ref_file)
            else:
                first = False
                odata = readData(data_dir + ref_file)
                for idx, row in enumerate(odata):
                    data[idx].extend(row[1:-1])

                del odata

        # Split the data into locations
        for loc in loc_idxs.keys():
            loc_data = split_by_idxs(data, loc_idxs[loc])

            # Now split each location's data into scan and cal data.
            cal_data, scan_data = split_cal_scans(loc_data, cal_idxs[loc])

            # Create the data dicts
            data_dict, data_scans, _ = data2dict(scan_data)
            data_dict = standardize_project_name(data_dict, key_dict)

            cal_dict, cal_scans, _ = data2dict(cal_data)
            cal_dict = standardize_project_name(cal_dict, key_dict)

            # Save the scandata files
            loc_dir = os.path.join(out_dir, loc, data_dict[key_dict['Date']][0])
            dataset_id = loc_meta[loc]['Dataset ID']

            if data_dict[key_dict['Replication']]:
                create_scan_file(data_dict, key_dict, data_scans, dataset_id, os.path.join(loc_dir, 'Reflectance_data.csv'))
            if cal_dict[key_dict['Replication']]:
                create_scan_file(cal_dict, key_dict, cal_scans, dataset_id,
                                 os.path.join(loc_dir, 'Reflectance_Cal_data.csv'))


def test_split():
    import shutil
    data_dir = '/media/sf_tmp/exdata/'
    out_dir = '/media/sf_tmp/restruct_test/'
    shutil.rmtree(out_dir)
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    cal_idxs, loc_idxs, loc_meta, key_dict = process_upwelling(data_dir, out_dir)
    process_downwelling(data_dir, out_dir, cal_idxs, loc_idxs, loc_meta, key_dict)
    process_reflectance(data_dir, out_dir, cal_idxs, loc_idxs, loc_meta, key_dict)
