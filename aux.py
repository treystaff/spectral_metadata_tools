"""Functions for dealing w/ Aux Files"""
import csv
import re
import os
import shutil
from utility import readData


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
    for project, date, rep, scan_number in zip(*scan_info):
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
    image_filenames = copy_otherfiles(in_dir, cal_dir, filenames, cal_meta['scans_info'])
    # Process vegfrac for cal data
    if vegfrac_data:
        process_vegfraction(vegfrac_data, image_filenames, cal_dir)
    if logdata:
        process_logfile(logdata, cal_meta['scans_info'], cal_dir)

    # Now handle the location-specific scandata
    for loc in loc_meta:
        meta_dict = loc_meta[loc]
        loc_dir = os.path.join(out_dir, meta_dict['Date'], loc)
        image_filenames = copy_otherfiles(in_dir, loc_dir, filenames, meta_dict['scans_info'])
        if vegfrac_data:
            process_vegfraction(vegfrac_data, image_filenames, loc_dir)
        if logdata:
            process_logfile(logdata, meta_dict['scans_info'], loc_dir)


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

    footer = vf_data[-1]
    if not footer[0].lower().startswith('processing'):
        print('Unexpected Vegfraction footer from {0}!:\n{1}\n'.format(path, footer))

    if footer[0].endswith(('.jpg', '.png', '.tif', '.bmp')):
        footer = None
        data = vf_data[1:]
    else:
        data = vf_data[1:-1]

    # Make sure the data is formatted as expected. Raise error otherwise
    if not data[0][0].endswith(('.jpg', '.png', '.tif', '.bmp')):
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

    data = log[1:]

    return header, data


def process_logfile(logdata, scans_info, out_dir):
    """
    Process the CDAP logfile.
    """
    # Separate the header from the rest of the log info
    header, data = logdata

    # Split out the scan info
    projects, dates, reps, scan_nums = scans_info
    projects = [p.lower() for p in projects]
    reps = [r.lower() for r in reps]

    # Create a new file for the log
    outpath = os.path.join(out_dir, 'log.csv')
    with open(outpath, 'w') as newlog:
        # keep track of how many rows were written, as a check
        rowcount = 0

        writer = csv.writer(newlog)
        # Write the header
        writer.writerow(header)

        # Now write every other row
        for row in data:
            if 'camera' in row[-1].lower():
                import pdb
                pdb.set_trace()
            # Don't include rows indicating where program started, for now.
            if len(row) < 6:
                continue

            # Skip entries that don't match the project/rep/scan number combos for this directory
            if row[1].lower() not in projects:
                continue
            if row[2].lower() not in reps:
                continue
            if row[5] not in scan_nums:
                continue

            # Write rows that get thru!
            writer.writerow(row)
            rowcount += 1

    if rowcount == 0:
        # this should raise an exception because every scan should have a log entry
        raise RuntimeError('NO MATCHING LOG ENTRIES WERE FOUND FOR {0}'.format(out_dir))
    elif rowcount != len(projects):
        import pdb
        pdb.set_trace()
        raise RuntimeError('Inconsistent numbers of scan and log entries for {0} !'.format(out_dir))


