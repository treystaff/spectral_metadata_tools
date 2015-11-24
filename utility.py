"""Support functions"""

from matplotlib import pyplot as plt
from matplotlib import rcParams
import csv
import simplekml
import os


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


def create_raw_scans_files(file_paths, cal_idxs, loc_idxs, loc_meta, cal_meta, key_dict, data_type, out_dir):
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
        else:
            first = False
            odata = readData(file_path)
            for idx, row in enumerate(odata):
                data[idx].extend(row[1:-1])

            del odata

    fields = getFields(data)

    # Deal with the cal data
    cal_data, _ = split_cal_scans(data, cal_idxs)
    cal_dict, cal_scans, _ = data2dict(cal_data)

    cal_dir = os.path.join(out_dir, cal_dict[key_dict['Date']][0], 'cal_data')
    dataset_id = cal_meta['Dataset ID']
    if cal_dict[key_dict['Replication']]:
        create_scan_file(cal_dict, key_dict, cal_scans, dataset_id,
                        os.path.join(cal_dir, 'Raw_{0}_Cal_data.csv'.format(data_type)))

    # Split the data into locations ( for non-cal data)
    for loc in loc_idxs.keys():
        loc_data = split_by_idxs(data, loc_idxs[loc])

        reps = loc_data[fields.index(key_dict['Replication'])][1:-1]
        loc_cal_idxs = find_cal_reps(reps)

        # Now split each location's data into scan and cal data.
        _, scan_data = split_cal_scans(loc_data, loc_cal_idxs)

        # Create the data dicts
        data_dict, data_scans, _ = data2dict(scan_data)

        # Save the scandata files
        loc_dir = os.path.join(out_dir,data_dict[key_dict['Date']][0], loc)
        dataset_id = loc_meta[loc]['Dataset ID']

        if data_dict[key_dict['Replication']]:
            create_scan_file(data_dict, key_dict, data_scans, dataset_id,
                             os.path.join(loc_dir, 'Raw_{0}_data.csv'.format(data_type)))


def standardize_project_name(data_dict, key_dict):
    """
    Standardizes Carbon Plot project names.

    Parameters:
        data_dict - CDAP derived data dictionary
        key_dict - Keyword-mapping dictionary

    Returns:
        Modified verison of data_dict
    """

    project_names = data_dict[key_dict['Project']]
    for idx, project_name in enumerate(project_names):
        project_name = project_name.lower()
        if project_name in {'csp01', 'cspg01', 'csp1', 'cspo1', 'cps01', 'carbon1'}:
            project_names[idx] = 'CSP01'
        elif project_name in {'csp02', 'cspg02', 'csp2', 'cspo2', 'cps02', 'carbon2'}:
            project_names[idx] = 'CSP02'
        elif project_name in {'csp03', 'cspg03', 'csp3', 'cspo3', 'carbon3', 'cps03', 'carbon3'}:
            project_names[idx] = 'CSP03'
        elif project_name in {'csp03a', 'cspo3a', 'cspg03a', 'carbon3a'}:
            project_names[idx] = 'CSP03A'
        elif project_name in {'bidirectionalcsp01', 'csp1brdf'}:
            project_names[idx] = 'CSP01_BDRF'
        elif project_name in {'bidirectionalcsp02', 'csp2brdf'}:
            project_names[idx] = 'CSP02_BDRF'
        elif project_name in {'bidirectionalcsp03', 'csp3brdf'}:
            project_names[idx] = 'CSP03_BDRF'

    data_dict[key_dict['Project']] = project_names

    return data_dict


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

        # Now add the scandata
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


def find_cal_reps(reps):
    """
    Finds and returns the index position of cal scans

    Parameters:
        reps - List of rep names

    Returns:
        idxs - A set of index positions for cal scans. If no cal scans are found, returns an empty list.
    """
    idxs = []
    for idx, rep in enumerate(reps):
        if 'cal' in rep.lower() or 'panel' in rep.lower():
            idxs.append(idx + 1)

    return set(idxs)


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
        elif rep.find('soy') > -1 or rep.find('bean') > -1:
            targets.append('Soybean')
        elif rep in {'water', 'clearwater'}:
            targets.append('Water')
        elif rep in {'soil', 'baresoil'}:
            targets.append('Soil')

    return targets


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
    key_dict['Calibration Mode'] = find_cdap_key(hkeys_list, {'calibration mode'})

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


def data2dict(data):
    """
    Converts CDAP datalist to a dictionary indexed by fieldname.
    Currently does not work w/ CDAP2
    """
    # We will split the data into 'header' and scan data.
    headerdata = {}
    scandata = []
    # Maintain a list of headerkeys bc order of insert is important. for later processing
    hkeys = []
    for row in data:
        try:
            # If the field can be turned to float, it should be a wavelength.
            float(row[0])
            # Add the original string wavelength as key to maintain precision.
            scandata.append(row)
        except ValueError:
            if row[0].lower().startswith('dc'):
                scandata.append(row)
                #scandata[row[0]] = row[1:]
            else:
                headerdata[row[0]] = row[1:]
                hkeys.append(row[0])

    return headerdata, scandata, hkeys


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


def mean(l):
    """Returns the mean of a list"""
    return sum(map(float, l))/float(len(l))


def determine_loc(lats,lons, project):
    """
    Returns the location of data collection

    Parameters:
        lats - List of latitutde values for a project
        lons - List of longitude values for a project
        project - name of the project

    Return:
        location - A string. 'CSP01', 'CSP02', or 'CSP03'. If a location cannot be determined,
            or if a location other than one of the CSP plots is detected, None is returned.
        country - String. Country name where data was collected. Currently only returns "United States"
        state - String. State name data was collected. Currently only returns "Nebraska"
        county - String. County name data was collected. Currently only returns "Saunders"
    """
    # Convert lats & lons to floats from strings
    lats = [float(lat) for lat in lats if lat != '']
    lons = [float(lon) for lon in lons if lon != '']

    # The rep has no GPS values.
    if len(lats) < 1 or len(lons) < 1:
        return 'UNKNOWN'

    # Find the mean lat/lon
    lat = mean(lats)
    lon = mean(lons)

    if (41.161607 <= lat <= 41.169437) and (-96.483063 <= lon <= -96.47315):
        location = 'CSP01'
    elif (41.161405 <= lat <= 41.168761) and (-96.473668 <= lon <= -96.463818):
        location = 'CSP02'
    elif (41.17547 <= lat <= 41.1793) and (-96.444978 <= lon <= -96.43475):
        location = 'CSP03A'
    elif (41.17937 <= lat <= 41.183) and (-96.44494 <= lon <= -96.43465):
        location = 'CSP03'
    else:
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
            print('Project {0} location not determined!'.format(project))
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
