"""Functions for dealing w/ Aux Files"""
import csv
import re
import os
import shutil
from utility import readData
import logging
import warnings


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


def copy_otherfiles(in_dir, out_dir, filenames, scan_info):
    """Does the work of matching otherfiles and copying them to the appropriate directory"""
    img_filenames = []  # Maintain a record of image filenames for the vegfrac file
    pic_dir = os.path.join(out_dir, 'Pictures')
    for project, date, rep, scan_number, _ in zip(*scan_info):
        # Create a regex for matching files corresponding to this.
        pattern = '{0}_{1}_{2}_.*_.*_{3}*'.format(project, date, rep, scan_number)
        pattern = re.compile(pattern.lower())
        for filename in filenames:
            if pattern.match(filename.lower()):
                # Copy the file to the new directory
                if filename.lower().endswith(('.jpg', '.png', '.tif', '.bmp')):
                    # Copy to pictures dir
                    # Check that the Pictures directory exists
                    if not os.path.exists(pic_dir):
                        os.makedirs(pic_dir)

                    # Copy the file
                    shutil.copy2(os.path.join(in_dir, filename),
                                   pic_dir)

                    # Maintain a record of image filenames for the vegfrac file
                    img_filenames.append(filename)
                else:
                    # Copy to base dir
                    shutil.copy2(os.path.join(in_dir, filename),
                                    out_dir)

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


def process_otherfiles(in_dir, out_dir, cal_meta, loc_meta):
    """
    Copy appropriate pictures and raw data (.Upwelling, etc.) over to new reorganized directory.

    Also processes vegfraction (calls process_vegfraction)

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

    # Check if a vegfraction file exists. If so, read the data.
    vegfrac_fn = [f for f in filenames if 'veg' in f.lower() and 'fraction' in f.lower()]
    if len(vegfrac_fn) == 1:
        vegfrac_data = read_vegfraction(os.path.join(in_dir, vegfrac_fn[0]))
    elif len(vegfrac_fn) > 1:
        raise RuntimeError('More than one VegFraction file found in {0}!'.format(in_dir))
    else:
        vegfrac_data = False

    # Check if a log file exists. if so, read the data.
    logfile = [f for f in filenames if '_log.txt' in f.lower()]
    if len(logfile) == 1:
        logdata = read_log(os.path.join(in_dir, logfile[0]))
    elif len(logfile) > 1:
        raise RuntimeError('MULTIPLE LOGFILES FOUND IN {0}'.format(in_dir))
    elif len(logfile) == 0:
        raise RuntimeError('NO LOGFILE FOUND IN {0}'.format(in_dir))
    else:
        logdata = False

    # Do the calibration stuff first
    cal_dir = os.path.join(out_dir, cal_meta['Date'], 'cal_data')
    scans_info = parse_scans_info(cal_meta['scans_info'])
    image_filenames = copy_otherfiles(in_dir, cal_dir, filenames, scans_info)
    # Process vegfrac for cal data
    if vegfrac_data:
        process_vegfraction(vegfrac_data, image_filenames, cal_dir)
    if logdata:
        process_logfile(logdata, scans_info, cal_dir)

    # Now handle the location-specific scandata
    for loc in loc_meta:
        meta_dict = loc_meta[loc]
        loc_dir = os.path.join(out_dir, meta_dict['Date'], loc)
        scans_info = parse_scans_info(meta_dict['scans_info'])
        image_filenames = copy_otherfiles(in_dir, loc_dir, filenames, scans_info)
        if vegfrac_data:
            process_vegfraction(vegfrac_data, image_filenames, loc_dir)
        if logdata:
            process_logfile(logdata, scans_info, loc_dir)


def read_vegfraction(path):
    """
    Reads the vegfraction file. Currently only prints a warning for unexpected vegfraction header/footer.

    Throws RuntimeError if data format is unexpected.

    Relies on readData from utility.py

    Parameters:
        path - string. Full path to vegfraction file.

    Returns:
        header - List of strings.
        data - List of strings. Vegfraction data.
        footer - List of one string. Footer (should be processing date and time). None if no footer detected.
    """
    vf_data = readData(path)
    header = vf_data[0]
    if header[0].lower() != 'name':
        print('Unexpected Vegfraction header from {0}!:\n{1}\n'.format(path, header))

    # Define some picture suffixes
    pic_sufs = ('.jpg', '.png', '.tif', '.bmp')
    footer = vf_data[-1]
    if not footer[0].lower().startswith('processing') and not footer[0].endswith(pic_sufs):
        print('Unexpected Vegfraction footer from {0}!:\n{1}\n'.format(path, footer))

    if footer[0].endswith(pic_sufs):
        footer = None
        data = vf_data[1:]
    else:
        data = vf_data[1:-1]

    # Make sure the data is formatted as expected. Raise error otherwise
    if not data[0][0].endswith(pic_sufs):
        raise RuntimeError('Vegfraction data {0} not formatted as expected! '
                           'First element is not image filename!'.format(path))

    if len(data[0]) != len(header):
        raise RuntimeError('Vegfration data {0} is not formatted as expected! '
                           'Number of header elements does not match number of data elements!'.format(path))

    return header, data, footer


def process_vegfraction(vegfrac_data, img_filenames, out_dir):
    """
    Process vegfraction file

    Parameters:
        vegfrac_data - output from read_vegfration as a tuple (header, data, footer)
        img_filenames - List of image filenames (return from copy_otherfiles()0
        out_dir - Directory to place new vegfrac file.

    Returns:
        Nothing!
    """
    # Split up the vegfrac_data
    header, data, footer = vegfrac_data

    # Open a new vegfrac file in the output directory
    with open(os.path.join(out_dir, 'VegFraction.csv'), 'w') as vegfrac_file:
        writer = csv.writer(vegfrac_file)
        writer.writerow(header)
        for row in data:
            if row[0] in img_filenames:
                writer.writerow(row)

        if footer is not None:
            writer.writerow(footer)


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
        for row in header:
            writer.writerow(row)

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

                if row[5] != scan_num:
                    continue

                if row[1].lower() != project.lower() or row[2].lower() != rep.lower():
                    # As a fallback, check if logtime == scan end time. If so, can write, otherwise continue.
                    if row[0] != end_time:
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
        warn_str = 'Inconsistent numbers of scan and log entries for {0} !'.format(out_dir)
        logging.warning(warn_str)
        warnings.warn(warn_str)


