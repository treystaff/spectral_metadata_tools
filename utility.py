"""Support functions"""

from matplotlib import pyplot as plt
from matplotlib import rcParams
import csv
import simplekml
import os
import warnings
import logging
import metadata as meta
import shutil


def filter_floats(l, convert=True, remove_val=-9999):
    """
    Given a list, returns a list of elements that can be converted to floats.

    Parameters:
        l - List. List to filter.
        convert=True - Returned list has elements that can be converted to floats as floats, otherwise remains as was
            (e.g., str, int)
        remove_val=-9999 - Optionally remove value from list. Defaults to removing nodata value.

    Returns:
        filtered - List of filtered list elements.
    """
    filtered = []
    for element in l:
        try:
            converted = float(element)
            if convert and converted != remove_val:
                filtered.append(converted)
            elif converted != remove_val:
                filtered.append(element)
        except ValueError:
            pass

    return filtered


def create_raw_scans_files(file_paths, cal_idxs, loc_idxs, loc_meta, cal_meta, key_dict, data_type):
    """
    Creates a raw scans file
    """
    # make sure the filepaths are sorted
    file_paths.sort()

    # Load the file(s)
    first = True
    for file_path in file_paths:
        if first:
            data = readData(file_path)
            first = False
        else:
            odata = readData(file_path)
            for idx, row in enumerate(odata):
                data[idx].extend(row[1:-1])

            del odata

    fields = getFields(data)

    # Deal with the cal data
    cal_data = split_by_idxs(data, cal_idxs)
    cal_dict, cal_scans, _ = data2dict(cal_data)
    cal_dir = cal_meta['out_dir']
    dataset_id = cal_meta['Dataset ID']
    if cal_dict[key_dict['Replication']]:
        create_scan_file(cal_dict, key_dict, cal_scans, dataset_id,
                        os.path.join(cal_dir, 'Raw_{0}_Cal_data.csv'.format(data_type)))

    # Split the data into locations (for non-cal data)
    for loc in loc_idxs.keys():
        loc_data = split_by_idxs(data, loc_idxs[loc])

        # Create the data dicts
        data_dict, data_scans, _ = data2dict(loc_data)

        # Save the scandata files
        loc_dir = loc_meta[loc]['out_dir']
        dataset_id = loc_meta[loc]['Dataset ID']

        if data_dict[key_dict['Replication']]:
            create_scan_file(data_dict, key_dict, data_scans, dataset_id,
                             os.path.join(loc_dir, 'Raw_{0}_data.csv'.format(data_type)))


def standardize_project_name(project_name, location_name):
    """
    Standardizes Carbon Plot project names.

    Parameters:
        project_name - String. A scan's project name.
        location_name - String. A scan's location name.

    Returns:
        String. Modified verison of project_name.
    """
    # Define some lists with common project names
    csp01_list = ['csp01', 'cspg01', 'csp1', 'cspo1', 'cps01', 'carbon1']
    csp02_list = ['csp02', 'cspg02', 'csp2', 'cspo2', 'cps02', 'carbon2']
    csp03_list = ['csp03', 'cspg03', 'csp3', 'cspo3', 'carbon3', 'cps03', 'carbon3']
    csp03a_list = ['csp03a', 'cspo3a', 'cspg03a', 'carbon3a', 'csp03']
    all_csp_names = []
    all_csp_names.extend(csp01_list)
    all_csp_names.extend(csp02_list)
    all_csp_names.extend(csp03_list)
    all_csp_names.extend(csp03a_list)

    project_name = project_name.lower()
    if location_name == 'CSP01':
        if project_name in csp01_list:
            project_name = 'CSP01'
        elif project_name in {'bidirectionalcsp01', 'csp1brdf', 'bi-directional', 'bidirectional2'}:
            if project_name == 'bidirectional2':
                project_name = 'CSP01_BDRF2'
            else:
                project_name = 'CSP01_BDRF'
        elif project_name in all_csp_names:
            warn_str = 'Project name {0} does not match detected location {1}. ' \
                       'Renaming to {1}'.format(project_name, location_name)
            project_name = 'CSP01'
            warnings.warn(warn_str)
            logging.warning(warn_str)
        else:
            new_project_name = 'CSP01_{0}'.format(project_name)
            warn_str = 'Project name {0} does not match location {1}! Renaming to {2}'\
                .format(project_name, location_name, new_project_name)
            project_name = new_project_name
            warnings.warn(warn_str)
            logging.warning(warn_str)

    elif location_name == 'CSP02':
        if project_name in csp02_list:
            project_name = 'CSP02'

        elif project_name in {'bidirectionalcsp02', 'csp2brdf', 'bi-directional', 'bidirectional2'}:
            if project_name == 'bidirectional2':
                project_name = 'CSP02_BDRF2'
            else:
                project_name = 'CSP02_BDRF'
        elif project_name in all_csp_names:
            warn_str = 'Project name {0} does not match detected location {1}. ' \
                       'Renaming to {1}'.format(project_name, location_name)
            project_name = 'CSP02'
            warnings.warn(warn_str)
            logging.warning(warn_str)
        else:
            new_project_name = 'CSP02_{0}'.format(project_name)
            warn_str = 'Project name {0} does not match location {1}! Renaming to {2}'\
                .format(project_name, location_name, new_project_name)
            project_name = new_project_name

            warnings.warn(warn_str)
            logging.warning(warn_str)

    elif location_name == 'CSP03':
        if project_name in csp03_list:
            project_name = 'CSP03'
        elif project_name in {'bidirectionalcsp03', 'csp3brdf', 'bi-directional', 'bidirectional2'}:
            if project_name == 'bidirectional2':
                project_name = 'CSP03_BDRF2'
            else:
                project_name = 'CSP03_BDRF'
        elif project_name in all_csp_names:
            warn_str = 'Project name {0} does not match detected location {1}. ' \
                       'Renaming to {1}'.format(project_name, location_name)
            project_name = 'CSP03'
            warnings.warn(warn_str)
            logging.warning(warn_str)
        else:
            new_project_name = 'CSP03_{0}'.format(project_name)
            warn_str = 'Project name {0} does not match location {1}! Renaming to {2}'\
                .format(project_name, location_name, new_project_name)
            project_name = new_project_name
            logging.warning(warn_str)

    elif location_name == 'CSP03A':
        if project_name in csp03a_list:
            project_name = 'CSP03A'
        elif project_name in all_csp_names:
            warn_str = 'Project name {0} does not match detected location {1}. ' \
                       'Renaming to {1}'.format(project_name, location_name)
            project_name = 'CSP03A'
            warnings.warn(warn_str)
            logging.warning(warn_str)
        else:
            new_project_name = 'CSP03A_{0}'.format(project_name)
            warn_str = 'Project name {0} does not match location {1}! Renaming to {2}'\
                .format(project_name, location_name, new_project_name)
            project_name = new_project_name
            warnings.warn(warn_str)
            logging.warning(warn_str)

    # If none of the above conditions are met, the location is unknown. Just return the project name.
    return project_name


def split_by_idxs(data, idxs):
    """
    Splits a CDAP data list by a list of indexes.

    Parameters:
        data - List. CDAP derived data list.
        loc_idxs - List. List of idxes corresponding to columns of the CDAP data lsit.

    Returns:
        selected_data - List. CDAP data list with only those columns specified by loc_idxs.
    """

    selected_data = []
    for idx, row in enumerate(data):
        selected_data.append([row[0]])
        # Some rows may be empty
        if len(row) > 1:
            for idx2 in idxs:
                try:
                    selected_data[idx].append(row[idx2])
                except IndexError:
                    selected_data[idx].append('')

    return selected_data


def split_cal_scans(data, cal_idxs):
    """
    Splits Calibration data from scan data.

    Parameters:
        data - CDAP derived data list
        cal_idxs - Index positions of columns that correspond to cal scans

    returns:
        cal_data, scan_data - Lists of calibration and scan data.
    """

    cal_data = []
    scan_data = []
    for idx, row in enumerate(data):
        cal_data.append([row[0]])
        scan_data.append([row[0]])
        for idx2 in range(1, len(row)):
            if idx2 in cal_idxs:
                cal_data[idx].append(row[idx2])
            else:
                scan_data[idx].append(row[idx2])

    return cal_data, scan_data


def create_scan_file(data_dict, key_dict, scan_data, dataset_id, path):
    """
    Creates a scan data file for a dataset.
    """
    elements = ['File Name','Project', 'Replication', 'X', 'Y', 'Scan Number', 'Start Time', 'Stop Time',
                'Integration Time', 'Averaged Scans', 'Average Adj']
    # Open the csv file and writ ethe results
    with open(path, 'w') as f:
        write = csv.writer(f, delimiter=',')

        # First write the dataset ID
        write.writerow(['Dataset ID', dataset_id])

        # Now add the other rows.
        for element in elements:
            if element in key_dict.keys():
                row = [element]
                row.extend(data_dict[key_dict[element]])
                write.writerow(row)

        for row in scan_data:
            write.writerow(row)


def get_instrument_info(instrument_str):
    """
    Gets the instrument's information from the instrument string.
    """

    if instrument_str.startswith(('OO', 'Ocean Optics')):
        # Ocean Optics instrument
        if instrument_str.find('USB2') < 0:
            raise IndexError('Ocean Optics Instrument not recognized!')

        inst = [s for s in instrument_str.split(' ') if s.startswith('USB')]
        plus = instrument_str.find('+')
        if plus > 0:
            # It's a USB 2000+
            instrument_name = 'Ocean Optics USB 2000+'
            # Find the instrument serial number
            if inst:
                snumber = inst[0][5:]
            else:
                snumber = instrument_str.split(' ')[1]
        else:
            # It's just a normal USB
            instrument_name = 'Ocean Optics USB 2000'
            if inst:
                snumber = inst[0][4:]
            else:
                snumber = instrument_str.split(' ')[1]

        if instrument_str.find('High Sensitivity') > 0:
            instrument_name += ' High Sensitivity'

        # Find the FOV, if it exists.
        fov_loc = instrument_str.find('Degree')
        fov = instrument_str[fov_loc-4:fov_loc-1]

    elif 'Spectron' in instrument_str:
        insrument_loc = instrument_str.find('Spectron')
        instrument_name = instrument_str[:insrument_loc + 8]
        # Check that the FOV is included.
        fov_loc = instrument_str.find('Degree')
        fov = instrument_str[fov_loc-4:fov_loc-1]
        # The Spectron instrument names don't seem to have serial numbers associated wtih them.
        snumber = ''

    else:
        # Some other instrument
        raise NotImplementedError('NEED TO INCLUDE SUPPORT FOR UNSUPPORTED INSTRUMENT.')

    return instrument_name, snumber, fov


def find_cal_reps(reps, filenames):
    """
    Finds and returns the index position of cal scans

    Parameters:
        reps - List of rep names
        filenames - list of rep filenames (e.g., *.calibration, *.upwelling, *.downwelling, etc.)

    Returns:
        idxs - A set of index positions for cal scans. If no cal scans are found, returns an empty list.
    """
    idxs = []
    for idx, filename in enumerate(filenames):
        if '.cal' in filename.lower():
            if 'cal' not in reps[idx].lower() and 'panel' not in reps[idx].lower():
                # Calibration scan not labeled as such. Issue a warning
                warn_str = 'Cal rep from {0} mislabeled as {1}'.format(filename, reps[idx])
                logging.warning(warn_str)
                warnings.warn(warn_str)

            # As long as it's marked as cal in filename, add it to the list of cal reps.
            idxs.append(idx + 1)

    return set(idxs)


def is_cal_rep(rep, filename):
    """
    Determines if a given rep/filename combo represent a cal scan.

    Parameters:
        rep - String. Rep Name
        filename - String. Name of scan's filename (e.g., *.calibration, *.upwelling, *.downwelling, etc.)

    Returns:
        True/False - Boolean. True if rep/filename combo is a cal rep
    """

    if '.cal' in filename.lower() or '.ref' in filename.lower():
        if 'cal' not in rep.lower() and 'panel' not in rep.lower():
            # Calibration scan not labeled as such. Issue a warning
            warn_str = 'Cal rep from {0} mislabeled as {1}'.format(filename, rep)
            logging.warning(warn_str)
            warnings.warn(warn_str)

        # As long as it's marked as cal in filename, add it to the list of cal reps.
        return True

    return False


def reps_to_targets(reps):
    """
    Converts a list of rep names into a list of standardized target names. Currently only 'Corn' and 'Soybean' are fully
        supported, although includes 'Water' and 'Soil' as well.

    Paramters:
        reps - A list of rep names
    Returns:
        targets - A list of standardized target names. List is empty if no matches found.
    """
    targets = []
    reps = set(reps)
    for rep in reps:
        rep = rep.lower()
        if rep.find('corn') > -1:
            targets.append('Corn')
        elif rep.find('tassel') > -1:
            targets.append('Corn (Tassel)')
        elif rep.find('soy') > -1:
            targets.append('Soybean')
        elif rep.find('bean') > -1:
            targets.append('Great Northern Beans')
        elif rep in {'water', 'clearwater'}:
            targets.append('Water')
        elif rep in {'soil', 'baresoil'}:
            targets.append('Soil')

    return list(set(targets))


def filter_lists(list1, list2, val):
    """
    Filters list one by a value of list two.

    Parameters:
        list1 - A list. List to filter.
        list2 - A list. The list with which to filter list 1.
        val - A value that is contained within list2. This is the value to filter by.

    Returns:
        filt_list - A list. A filtered version of list2.
        idxs - A list. The column indexes of the project.
    """
    idxs = []
    filt_list = []
    for idx, element1, element2 in zip(range(len(list1)), list1, list2):
        if element2 == val:
            idxs.append(idx+1)
            filt_list.append(element1)

    return filt_list, idxs


def find_cdap_key(hkeys_list, match_list):
    """
    Finds the name of the cdap header key that matches a list of strings

    Parameters:
        hkeys_list - A list of header keys extracted from a CDAP data file using data2dict() or getFields()
        match_list - A list of lowercase strings to match to headerkeys

    Returns:
        key - String. The name of the CDAP data field matching one of the strings in match_list
    """
    key = [hkey for hkey in hkeys_list if hkey.lower() in match_list]

    if len(key) > 1:
        raise KeyError('More than one header key matches the match list!')
    elif len(key) == 0:
        raise KeyError('No matching header key found for {0}'.format(match_list))
    else:
        return key[0]


def create_key_dict(hkeys_list):
    """
    Constructs the dictionary mapping standardized data fieldnames to CDAP file fieldnames

    Parameters:
        hkeys_list - A list of header keys extracted from a CDAP data file using data2dict() or getFields()
    Returns:
        key_dict - A dictionary mapping standardized data field names to CDAP file fieldnames
    """
    key_dict = dict()

    # Find the rep row first.
    key_dict['Replication'] = find_cdap_key(hkeys_list, {'rep', 'replication'})
    # 'X' or 'Plot'
    key_dict['X'] = find_cdap_key(hkeys_list, {'x', 'plot'})
    # 'Y' or 'Plot Scan'
    key_dict['Y'] = find_cdap_key(hkeys_list, {'y', 'plot scan'})
    # 'Cumulative scan' or 'count.' The scan number
    key_dict['Scan Number'] = find_cdap_key(hkeys_list, {'cumulative scan', 'count'})
    # Solar Azimuth
    key_dict['Solar Azimuth'] = find_cdap_key(hkeys_list, {'solar azimuth', 'solar aiz', 'solar azimuthal'})
    # Solar Elevation
    key_dict['Solar Elevation'] = find_cdap_key(hkeys_list, {'solar elevation', 'solar elev'})
    # Solar Zenith
    key_dict['Solar Zenith'] = find_cdap_key(hkeys_list, {'solar zenith'})
    # Altitude
    key_dict['Altitude'] = find_cdap_key(hkeys_list, {'altitude'})
    # Longitude
    key_dict['Longitude'] = find_cdap_key(hkeys_list, {'longitude'})
    # Latitude
    key_dict['Latitude'] = find_cdap_key(hkeys_list, {'latitude'})
    # Comments
    key_dict['Comments'] = find_cdap_key(hkeys_list, {'comments', 'comment'})
    # GPS
    key_dict['GPS'] = find_cdap_key(hkeys_list, {'gps'})
    # Data Logger
    key_dict['Data Logger'] = find_cdap_key(hkeys_list, {'data logger', 'dl'})
    # Software
    key_dict['Acquisition Software'] = find_cdap_key(hkeys_list, {'software', 'software version', 'version'})
    # Integration Time
    key_dict['Integration Time'] = find_cdap_key(hkeys_list, {'integration time', 'int time', 'integration time (ms)'})
    # Instrument
    key_dict['Instrument'] = find_cdap_key(hkeys_list, {'instrument', 'instruments'})
    # Date
    key_dict['Date'] = find_cdap_key(hkeys_list, {'date', 'acquire date'})
    # Start Time
    key_dict['Start Time'] = find_cdap_key(hkeys_list, {'start time', 'stime'})
    # Stop Time
    key_dict['Stop Time'] = find_cdap_key(hkeys_list, {'end time', 'etime'})
    # Cal panel
    key_dict['Calibration Panel'] = find_cdap_key(hkeys_list, {'processing panel', 'panel'})
    # Project
    key_dict['Project'] = find_cdap_key(hkeys_list, {'project'})
    # File names
    key_dict['File Name'] = find_cdap_key(hkeys_list, {'file name'})
    # Averaged scans
    key_dict['Averaged Scans'] = find_cdap_key(hkeys_list, {'averaged scans', 'used scans', 'instrument scans'})
    # Calibration Mode
    try:
        key_dict['Calibration Mode'] = find_cdap_key(hkeys_list, {'calibration mode'})
    except KeyError:
        key_dict['Calibration Mode'] = ''

    return key_dict


def readData(filepath):
    """
    Read a CDAP datafile into a list
    """
    with open(filepath, 'r') as f:
            data = f.readlines()
    datas = []
    for row in data:
        # Remove the tab, return, and newline at the end of the row.
        row = row.strip('\t\r\n')
        datas.append(row.split('\t'))

    return datas


def data2dict(data, fix_dc_scans=True):
    """
    Converts CDAP datalist to a dictionary indexed by fieldname.
    Currently does not work w/ CDAP2
    """
    # We will split the data into 'header' and scan data.
    headerdata = {}
    scandata = []
    final_scandata = []
    # Maintain a list of headerkeys bc order of insert is important. for later processing
    hkeys = []
    # Determine the idx at which scans begin
    scan_idx = None
    for idx, row in enumerate(data):
        if scan_idx is None:
            try:
                # If the field can be turned to float, it should be a wavelength.
                float(row[0])
                # Add the original string wavelength as key to maintain precision.
                scandata.append(row)
                scan_idx = idx
            except ValueError:
                if row[0].lower().startswith('dc'):
                    scandata.append(row)
                    scan_idx = idx
                    #scandata[row[0]] = row[1:]
                else:
                    headerdata[row[0]] = row[1:]
                    hkeys.append(row[0])
        else:
            # All the following rows should be scan data
            scandata.append(row)

    # Now, modify the scandata list
    # Check if the 24th and 25th scan rows are what we expected.
    remove_rows = []
    if fix_dc_scans:
        if scandata[24][0] != 'DC25' or scandata[0][0] != 'DC01':
            if scandata[0][0] != 'DC01':
                try:
                    float(scandata[0][0])
                except ValueError:
                    err_str = 'UNEXPECTED FIRST SCAN ENTRY {0}'.format(scandata[0][0])
                    logging.error(err_str)
                    raise RuntimeError(err_str)
            # Warn that we had to fix this.
            warn_str = 'DC SCANS NOT PROPERLY LABELED. DC01 IS {0} and DC25 IS {1}'.format(scandata[0][0], scandata[24][0])
            warnings.warn(warn_str)
            logging.warning(warn_str)
            # The DC scans are either not specified or last few were removed.
            try:
                # If the 25th scan can be converted to float, first 25 scans should be DC
                float(scandata[24][0])
                for row_idx in range(25):
                    scandata[row_idx][0] = 'DC{0}'.format(str(row_idx + 1).zfill(2))
            except ValueError:
                # Some of the scandata entries have been converted to
                #   'extra' data (e.g., min/max that were never really used)
                for row_idx in range(25):
                    if not scandata[row_idx][0].startswith('DC'):
                        try:
                            # If it can be converted to float, its a DC scan
                            float(scandata[row_idx][0])
                            scandata[row_idx][0] = 'DC{0}'.format(str(row_idx + 1).zfill(2))
                        except ValueError:
                            # Just remove those rows. They aren't needed.
                            remove_rows.append(row_idx)

    if remove_rows:
        for idx, row in enumerate(scandata):
            if idx not in remove_rows:
                final_scandata.append(row)
    else:
        final_scandata = scandata

    return headerdata, final_scandata, hkeys


def getFields(data):
    """
    Gets the field names of cdap data list
    Currently does not work with CDAP 2
    This was made because a dictionary actually slows things down longrun.
    """
    fields = []
    for row in data:
        fields.append(row[0])
    return fields


def coords2KML(lats, lons, starttimes, reps, saveto):
    """
    Converts latitudes and longitudes to KML file for inspection in Google Earth

    Parameters:
        lats - List of latitudes
        lons - List of longitudes
        starttimes - List of start times corresponding to each lat/lon collection.
        reps - List of rep names corresponding to each lat/lon collection.
        saveto - Path to save KML file to.
    """
    # Create a new kml object
    kml = simplekml.Kml(open=1)

    # Add each entry to the kml object.
    for lat, lon, starttime, rep in zip(lats, lons, starttimes, reps):
        pt = kml.newpoint()
        pt.name = starttime
        pt.description = rep
        pt.coords = [(lon, lat)]

    # Save the result.
    kml.save(saveto)


def create_kml_from_file(cdap_file, kml_file):
    """
    Creaes a KML file from a CDAP file using lat/lon

    Point's name = project: rep
    Point's description = Detected location
    """
    # Read the data
    data = readData(cdap_file)
    # Get the fields of the data
    fields = getFields(data)
    # Find the scan starting idx
    scanidx = findScanIdx(fields)

    # Create a list of just the header keys
    hkeys = fields[0:scanidx]
    # Generate the keydict
    key_dict = create_key_dict(hkeys)

    # Convert to a dict for easy access
    data_dict, _, _ = data2dict(data)

    # Get desired info from the dict.
    lats = data_dict[key_dict['Latitude']]
    if not lats:
        raise RuntimeError('Lat/Lon not found in {0}'.format(cdap_file))
    lons = data_dict[key_dict['Longitude']]
    projects = data_dict[key_dict['Project']]
    reps = data_dict[key_dict['Replication']]

    # Create a new kml object and add a point for each scan.
    kml = simplekml.Kml(open=1)
    for lat, lon, project, rep in zip(lats, lons, projects, reps):
        loc, _, _, _ = determine_loc(lat, lon, project)
        pt = kml.newpoint()
        pt.name = '{0}: {1}'.format(project, rep)
        pt.description = 'Detected Location: {0}\nProject: {1}\nRep: {2}\n'.format(loc, project, rep)
        pt.coords = [(float(lon), float(lat))]

    # Save the kml data to a file that can be opened in Google Earth.
    kml.save(kml_file)


def mean(l):
    """Returns the mean of a list"""
    return sum(map(float, l))/float(len(l))


def determine_loc(lat, lon, project):
    """
    Returns the location of data collection

    Parameters:
        lat - The latitutde value for a scan
        lon - The longitude value for a scan
        project - name of the project. If lat/lon fails to find the location, try using project name.

    Return:
        location - A string. 'CSP01', 'CSP02', or 'CSP03'. If a location cannot be determined,
            or if a location other than one of the CSP plots is detected, None is returned.
        country - String. Country name where data was collected. Currently only returns "United States"
        state - String. State name data was collected. Currently only returns "Nebraska"
        county - String. County name data was collected. Currently only returns "Saunders"
    """
    location = None
    # Convert lat & lon to floats from strings
    if lat != '' and lon != '':
        lat = float(lat)
        lon = float(lon)

        if (41.161607 <= lat <= 41.169437) and (-96.483063 <= lon <= -96.47315):
            location = 'CSP01'
        elif (41.161405 <= lat <= 41.168761) and (-96.473668 <= lon <= -96.463818):
            location = 'CSP02'
        elif (41.17547 <= lat <= 41.1793) and (-96.444978 <= lon <= -96.43475):
            location = 'CSP03A'
        elif (41.17937 <= lat <= 41.183) and (-96.44494 <= lon <= -96.43465):
            location = 'CSP03'

    if location is None:
        # Fall back on project name
        project = project.lower()
        if project in {'csp01', 'cspo1', 'csp1', 'bidirectionalcsp01', 'carbon1', 'cspg01', 'cps01'}:
            location = 'CSP01'
        elif project in {'csp02', 'cspo2', 'csp2', 'bidirectionalcsp02', 'carbon2', 'cspg02', 'cps02', 'csp2brdf'}:
            location = 'CSP02'
        elif project in {'csp03', 'cspo3', 'cspg03', 'bidirectionalcsp03', 'cps03'}:
            location = 'CSP03'
        elif project in {'csp03a', 'cspo3a', 'csp3_a', 'cspg03a'}:
            location = 'CSP03A'
        elif project.find('mead') > -1 or project.find('csp') > -1 or project.find('cps') > -1:
            location = 'MEAD'
        else:
            if project not in {'blvm', 'blmv'}:
                # We know the BLVM/BLMV project needs to be dealt with...don't bother reporting it for now...
                # TODO perhaps remove this check on blvm.
                warn_str = 'Project {0} location not determined!'.format(project)
                logging.warn(warn_str)
                warnings.warn(warn_str)
            return None, None, None, None

    return location, 'United States', 'Nebraska', 'Saunders'


def findScanIdx(fields):
    """Finds the file row number where scandata begins"""
    for idx,field in enumerate(fields):
        try:
            float(field)
            return idx
        except ValueError:
            if field.lower().startswith('dc'):
                return idx


def plot_scans(prep, prep_data,vheader, scanidx,saveto=None):
    """"Plots prep data and optionally saves to file"""
    rcParams['xtick.direction'] = 'out'
    rcParams['ytick.direction'] = 'out'

    # Get the data in a desirable format.
    #   Extract wavelengths
    wavelengths = vheader[scanidx+25:-1]
    #   Transpose rows to cols
    scan_data = zip(*prep_data[scanidx+25: -1])

    # Plot
    fig = plt.figure(figsize=(6.5,8.5))
    for scan in scan_data:
        plt.plot(wavelengths, scan, linewidth=0.2)
    plt.title(prep)
    plt.xlabel('Wavelength')

    # Show or save the plot
    if saveto is not None:
        plt.savefig(saveto, bbox_inches='tight')
    else:
        plt.show()

    plt.cla()
    plt.close(fig)


def create_dataset_dirs(base_dir, current_dataset_id):
    """
    Function to facilitate creation of sub-directories for datasets.
    This function is called when a dataset being processed encounters a restructured dataset with the same date
    and location. They may be separate collections or duplicates. If separate collections, we want to make sure to
    save data from each! Otherwise thrown an error or something.

    Parameters:
        base_dir - path to directory containing the already existing dataset that conflicts with the current dataset.
        current_dataset_id - String. The dataset id of the dataset currently being processed.

    Returns:
        new_dir - path to the new directory the dataset currently being processed will reside within.
    """

    # Read metadata from existing dataset
    metadata = meta.read_metadata(os.path.join(base_dir, 'Metadata.csv'))
    # Get the dataset id from the existing dataset
    existing_dataset_id = metadata['Dataset ID']

    # Ensure current dataset id != existing dataset id
    if existing_dataset_id == current_dataset_id:
        # For now, we will create a copy for further investigation.

        # Warn that this is happening.
        warn_str = 'DUPLICATE DATASETS DETECTED IN {0}. DATASET ID {1}'.format(base_dir, existing_dataset_id)
        warnings.warn(warn_str)
        logging.warning(warn_str)

        # Modify the dataset ids of the two datasets so they are different
        #   (existing will have _1 appended to end and current will have _2 appended to end).
        existing_dataset_id += '_1'
        current_dataset_id += '_2'

    # Move the current contents of directory to the new, dataset id based directory.
    new_existing_dir = os.path.join(base_dir, existing_dataset_id.replace(':', ''))
    dirlist = os.listdir(base_dir)
    os.makedirs(new_existing_dir)
    for element in dirlist:
        shutil.move(os.path.join(base_dir, element),
                    os.path.join(new_existing_dir, element))

    # Define a new location directory using the current dataset id.
    #   For now, also replaece the :'s between timestamp elements with nothing.
    new_dir = os.path.join(base_dir, current_dataset_id.replace(':', ''))
    # Make the directory.
    os.makedirs(new_dir)

    return new_dir


def extract_col(col_idx, data):
    """
    Extracts a single column from a CDAP data list

    Parameters:
        col_idx - int. The index for the column to extract
        data - list. CDAP data list

     Returns:
        col - list. One column from the cdap data list.
    """
    col = []
    for row in data:
        if len(row) >= 1:
            try:
                col.append(row[col_idx])
            except IndexError:
                col.append('')

    return col


def split_path(path_str):
    """
    Split a path string into its constitutent directories

    Note: Currently assumes unix-style path

    Parameters:
        path_str - Path string

    Returns:
        List of strings representing directories of the path string
    """
    # Split any file/object out from the path_str, if there:
    if os.path.isfile(path_str):
        path_str, _ = os.path.split(path_str)

    elif not os.path.isdir(path_str):
        # Path is not a directory. Warn the user.
        print('path string {0} is not a valid file/directory!'.format(path_str))

    return path_str.split('/')

