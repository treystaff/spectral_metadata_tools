"""Functions for dealing w/ Aux Files"""
import csv
import re
import os
import shutil
from utility import readData, filter_floats
import logging
import warnings
from datetime import datetime, timedelta
import xlrd


def create_aux_file(data_dict, key_dict, other_keys, dataset_id, path):
    """
    Creates an aux file for a dataset.
    """
    # Define what to include in Aux.
    elements = ['Project', 'Replication', 'X', 'Y', 'Scan Number', 'Solar Azimuth', 'Solar Elevation', 'Solar Zenith',
                'GPS', 'Altitude', 'Latitude', 'Longitude', 'Battery Voltage', 'Canopy Temperature', 'Temperature 1',
                'Wheel Temperature', 'Temperature 2', 'Pyranometer', 'Quantum Sensor']

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
                if data_dict[other_key] and any(entry != '' for entry in data_dict[other_key]):
                    row = [other_key]
                    row.extend(data_dict[other_key])
                    write.writerow(row)


def copy_otherfiles(in_dir, out_dir, filenames, scan_info):
    """Does the work of matching otherfiles and copying them to the appropriate directory"""
    img_filenames = []  # Maintain a record of image filenames for the file
    pic_dir = os.path.join(out_dir, 'Pictures')
    raw_dir = os.path.join(out_dir, 'Binary')  # Raw, binary files 
    for project, date, rep, scan_number, _ in zip(*scan_info):
        # Create a regex for matching files corresponding to this.
        pattern = '{0}_{1}_{2}_.*_.*_{3}*'.format(project, date, rep, scan_number)
        pattern = re.compile(pattern.lower())
        for filename in filenames:
            if pattern.match(filename.lower()):
                # Copy the file to the new directory
                if filename.lower().endswith(('.jpg', '.png', '.tif', '.bmp', '.tiff')):
                    # Copy to pictures dir
                    # Check that the Pictures directory exists
                    if not os.path.exists(pic_dir):
                        os.makedirs(pic_dir)

                    # Copy the file
                    shutil.copy2(os.path.join(in_dir, filename),
                                 pic_dir)

                    # Maintain a record of image filenames for the file
                    img_filenames.append(filename)
                else:
                    # Copy raw, binary files to a 'raw' folder
                    if not os.path.exists(raw_dir):
                        os.makedirs(raw_dir)
                    shutil.copy2(os.path.join(in_dir, filename),
                                 raw_dir)

    return img_filenames


def parse_scans_info(scans_info):
    '''
    Parses information contained in the scans_info list. Workaround and a bit of a hack...

    Parameters:
        scans_info - list. [raw_filenames, end_times]

    Returns:
        parsed_info - list. [projects, dates, reps, scan_numbers, end_times]
    '''
    parsed_info = [[], [], [], [], []]
    for filename, end_time in zip(*scans_info):
        filename = filename[:filename.find('.')]
        project, date, rep, _, _, scan_num = filename.split('_')
        parsed_info[0].append(project)
        parsed_info[1].append(date)
        parsed_info[2].append(rep)
        parsed_info[3].append(scan_num)
        parsed_info[4].append(end_time)

    return parsed_info


def process_otherfiles(in_dir, cal_meta, loc_meta):
    """
    Copy appropriate pictures and raw data (.Upwelling, etc.) over to new reorganized directory.

    Need: project name, date, rep name, x, y, and scan number.
     Probs just need project name, date, scan num.  Maybe just scan num?

    Parameters:
        in_dir - String. Path to directory containing scan data
        out_dir - String. Path to directory reorganized data is being place into
        cal_meta - Dict. From process_upwelling.
        loc_meta - Dict. From process_upwelling.
    """
    # Get a list of all filenames in in_dir
    filenames = os.walk(in_dir).next()[2]

    # Check if a log file exists. if so, read the data.
    logfile = [f for f in filenames if '_log.txt' in f.lower() or '_log.xls' in f.lower()]
    if len(logfile) == 1:
        if logfile[0].endswith('.xls'):
            # Special handling for .xls logfiles because they only occur in two years worth of data and are
            #   badly inconsistent
            logdata = read_xls_log(os.path.join(in_dir, logfile[0]))
            process_xls_logfile(logdata, cal_meta, loc_meta)
            logdata = None
        else:
            logdata = read_log(os.path.join(in_dir, logfile[0]))
    elif len(logfile) > 1:
        if '20030721_log.xls' in logfile and '20030724_log.xls' in logfile:
            # For some reason, 0721 is included in the folder with 0724...
            logdata = read_xls_log(os.path.join(in_dir, '20030724_log.xls'))
            process_xls_logfile(logdata, cal_meta, loc_meta)
            logdata = None
        else:
            raise RuntimeError('MULTIPLE LOGFILES FOUND IN {0}'.format(in_dir))
    elif len(logfile) == 0:
        warnstr = 'NO LOGFILE FOUND IN {0}'.format(in_dir)
        warnings.warn(warnstr)
        logging.warning(warnstr)
        logdata = False
    else:
        logdata = False

    # Do the calibration stuff first
    cal_dir = cal_meta['out_dir']
    scans_info = parse_scans_info(cal_meta['scans_info'])
    copy_otherfiles(in_dir, cal_dir, filenames, scans_info)
    if logdata:
        process_logfile(logdata, scans_info, cal_dir)

    # Now handle the location-specific scandata
    for loc in loc_meta:
        meta_dict = loc_meta[loc]
        loc_dir = meta_dict['out_dir']
        scans_info = parse_scans_info(meta_dict['scans_info'])
        copy_otherfiles(in_dir, loc_dir, filenames, scans_info)
        if logdata:
            process_logfile(logdata, scans_info, loc_dir)


def read_log(path):
    """
    Reads the log file

    Returns:
        header, data - Tuple. Headerrow and log entries
    """
    log = readData(path)
    header = log[0]
    if 'CDAP LOG for' not in header[0]:
        print('Unexpected CDAP LOG header {0} in {1}!!'.format(header, path))

    if 'Time' in log[1]:
        # Add second headerline to log
        header = [header, log[1]]
        data = log[1:]
    else:
        data = log[2:]

    return header, data


def read_xls_log(path):
    """
    Reads a log file in .xls format. Years 2002-2003 have logs formatted this way.

    Returns:
        header, data
    """
    # Open the excel workbook and extract the first sheet (which contains the data)
    book = xlrd.open_workbook(path)
    sheet = book.sheet_by_index(0)

    # Create a data dictionary that will hold location-specific data
    data = {}

    # Create the header obj
    header = []
    header_flag = True

    cur_loc = None
    cur_plot = None

    # Iterate over the rows
    for row_idx in range(sheet.nrows):
        sheet_row = sheet.row(row_idx)
        row = []
        for element in sheet_row:
            if element.ctype == 3:
                # It is an excel date. 
                xl_date = xlrd.xldate.xldate_as_datetime(element.value, book.datemode)
                xl_date = xl_date.strftime('%m%d%Y')
                row.append(xl_date)
            else:
                row.append(element.value)

        if all(element == '' for element in row):
            continue

        if not header_flag and str(row[0]).startswith('Scan'):
            continue

        if str(row[0]).startswith('CSP'):
            # Indicates start of a location.
            if header_flag:
                header_flag = False
            data[row[0]] = [row, {}]
            cur_loc = row[0]
            continue

        if str(row[0]).startswith('Plot') and len(str(row[0])) > 4:
            if header_flag:
                header_flag = False
            # Determine what plot number it is and make naming consistent.
            plot_nums = filter_floats(row[0])
            if len(plot_nums) != 0:
                cur_plot = 'Plot '
                for num in plot_nums:
                    cur_plot += str(int(num))

                row[0] = cur_plot

        if cur_loc and cur_plot:
            if cur_plot not in data[cur_loc][1].keys():
                data[cur_loc][1][cur_plot] = [row]
            else:
                data[cur_loc][1][cur_plot].append(row)

        #if str(row[0]) == 'Plot' or str(row[0]).startswith('Data collection log'):
        if header_flag:
            header.append(row)

    return header, data


def process_xls_logfile(logdata, cal_meta, loc_meta):
    """
    Process the CDAP xls logfile
    """
    header, data = logdata
    cal_logs = []

    scan_num_idx = None

    cal_dir = cal_meta['out_dir']

    for loc in loc_meta:
        # Only process entries for which we have the location in the data....
        if loc not in data.keys():
            warnings.warn('Location {0} Not found in logfile'.format(loc))
            continue

        # Extract location-specific metadata and what scannumbers are associated with it
        meta_dict = loc_meta[loc]
        _, _, _, scan_numbers, _ = parse_scans_info(meta_dict['scans_info'])
        scan_numbers = filter_floats(scan_numbers)

        # Obtain the output dir
        loc_dir = meta_dict['out_dir']

        # Extract the log data for the location
        loc_info, logdata = data[loc]

        # Get the plots for the location from the logdata
        plots = logdata.keys()
        plots.sort()

        # Create a temp list to hold loc-based logdata.
        loc_log = []

        # Iterate through each row, determining if loc-scan, cal scan, or neither
        for plot in plots:
            plotdata = logdata[plot]
            loc_log.append([plot])

            for row in plotdata:
                if str(row[0]).startswith('Plot'):
                    continue
                # Try to figure out which row the scan numbers are on.
                if not scan_num_idx:
                    if row[0] == '':
                        try:
                            int(row[2])
                            scan_num_idx = 2
                        except ValueError:
                            raise RuntimeError('ENCOUNTERED UNEXPECTED XLS LOG FORMATTING IN {0}'
                                               .format(meta_dict['Legacy Path']))
                    else:
                        try:
                            int(row[0])
                            int(row[1])
                            scan_num_idx = 1
                        except ValueError:
                            import pdb;pdb.set_trace()
                            raise RuntimeError('ENCOUNTERED UNEXPECTED XLS LOG FORMATTING IN {0}'
                                               .format(meta_dict['Legacy Path']))

                if row[scan_num_idx] in scan_numbers:
                    if any('cal' in str(element).lower() for element in row):
                        warnings.warn('Possible cal scan log in non-cal scan numbers')
                    loc_log.append(row)

                elif any('cal' in str(element).lower() for element in row):
                    # Call it a cal scan
                    cal_logs.append(row)

        # Now create the loc logfile
        with open(os.path.join(loc_dir, 'log.csv'), 'w') as logfile:
            writer = csv.writer(logfile)

            # Write the header
            for row in header:
                writer.writerow(row)

            # Write the location info
            writer.writerow(loc_info)

            # Write the other rows
            for row in loc_log:
                writer.writerow(row)

    # now create the cal logfile
    with open(os.path.join(cal_dir, 'log.csv'), 'w') as logfile:
        writer = csv.writer(logfile)
        # Write the header
        for row in header:
            writer.writerow(row)

        # Write the other rows
        for row in cal_logs:
            writer.writerow(row)


def process_logfile(logdata, scans_info, out_dir):
    """
    Process the CDAP logfile.
    """
    # Separate the header from the rest of the log info
    header, data = logdata

    # Split out the scan info
    projects, _, _, _, _ = scans_info

    # Create a new file for the log
    outpath = os.path.join(out_dir, 'log.csv')
    with open(outpath, 'w') as newlog:
        # keep track of how many rows were written, as a check
        rowcount = 0

        writer = csv.writer(newlog)
        # Write the header
        if len(header) > 1:
            for row in header:
                writer.writerow(row)
        else:
            writer.writerow(header)

        # Now write every other row
        for row in data:
            # Don't include rows indicating where program started, for now.
            if len(row) < 6:
                continue

            for project, date, rep, scan_num, end_time in zip(*scans_info):
                # May not want BLMV...but make sure compatable for now.
                #   Have to make special case bc for some reason MV are sometimes swiched
                #   (e.g., BLMV == BLVM)
                if row[1].lower() in {'blmv', 'blvm'} and project.lower() in {'blmv', 'blvm'}:
                    row[1] = 'blmv'
                    project = 'blmv'

                # Special case for soybean. Seems to be a recurring problem
                if row[2].lower() in {'soy', 'soybean'} and rep.lower() in {'soy', 'soybean'}:
                    row[2] = 'soybean'
                    rep = 'soybean'

                if row[5] != scan_num:
                    continue

                if row[1].lower() != project.lower() or row[2].lower() != rep.lower():
                    # As a fallback, check if logtime is within a couple seconds of scan end time.
                    #   If so, can write, otherwise continue.
                    try:
                        logtime = datetime.strptime(row[0], '%H:%M:%S')
                        end_time = datetime.strptime(end_time, '%H:%M:%S')
                    except ValueError:
                        # If the time is malformed for the log or data file, just continue.
                        continue

                    if logtime < end_time - timedelta(0, 1):
                        # If the logged time is less than a second before the end time, discard.
                        continue
                    if logtime > end_time + timedelta(0, 2):
                        # If the logged time is greater than two seconds after the end time, discard.
                        continue

                writer.writerow(row)
                rowcount += 1
                break

    if rowcount == 0:
        # this should raise an exception because every scan should have a log entry. Going to log and warn for now tho
        # raise RuntimeError('NO MATCHING LOG ENTRIES WERE FOUND FOR {0}'.format(out_dir))
        warn_str = 'NO MATCHING LOG ENTRIES WERE FOUND FOR {0}'.format(out_dir)
        logging.warning(warn_str)
        warnings.warn(warn_str)

    elif rowcount != len(projects):
        warn_str = 'Inconsistent numbers of scans ({0}) and ' \
                   'log entries ({1}) for {2} !'.format(len(projects), rowcount, out_dir)
        logging.warning(warn_str)
        warnings.warn(warn_str)

    # TODO: if rowcount > #scans, reprocess to remove those that don't match
