"""
Working draft of functions for splitting CALMIT CDAP datafiles into data, metadata, and auxiliary files.
"""

import simplekml
import os
import csv
import traceback
import re
import pdb  # FOR DEBUGGING ONLY

def readData(filepath):
    """
    Read a CDAP datafile into a list
    """
    with open(filepath, 'r') as f:
            data = f.readlines()

    datas = []
    for row in data:
        row = row[0:-2]
        datas.append(row.split('\t'))
    return datas

def data2dict(data):
    """
    Converts CDAP datalist to a dictionary indexed by fieldname.
    Does not work w/ CDAP2
    """
    # We will split the data into 'header' and scan data.
    headerdata = {}
    scandata = {}
    hkeys = []  # Headerkeys order of insert is important...
    for row in data:
        try:
            # If the field can be turned to float, it should be a wavelength.
            float(row[0])
            # Add the original string wavelength as key to maintain precision.
            scandata[row[0]] = row[1:-1]
        except ValueError:
            if row[0].startswith('DC'):
                scandata[row[0]] = row[1:-1]
            else:
                headerdata[row[0]] = row[1:-1]
                hkeys.append(row[0])

    return headerdata, scandata, hkeys

def getFields(data):
    """
    Gets the field names of cdap data list
    Does not work with CDAP 2
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
    return sum(l)/float(len(l))

def determine_loc(lats,lons):

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
        location = 'CSP1'
    elif (41.161405 <= lat <= 41.168761) and (-96.473668 <= lon <= -96.463818):
        location = 'CSP2'
    elif (41.175715 <= lat <= 41.183072) and (-96.444978 <= lon <= -96.434610):
        location = 'CSP3'
    else:
        location = 'OUT OF RANGE'

    return location

def findScanIdx(fields):
    """Finds the file row number where scandata begins"""
    for idx,field in enumerate(fields):
        try:
            float(field)
            return idx
        except ValueError:
            if field.startswith('DC'):
                return idx

def splitdata(path, filename, year, outpath, vertical=True):
    """
    Split a CDAP datafile into cal, meta, aux, and data files by location.

    Parameters:
        path - path to cdap data file
        filename - Name of cdap data file
        year - year of cdap data file
        outpath - base path into which split files will be placed.
        vertical - Optional. Default = True. Determines if data should be oriented vertically
            (legacy CDAP - one observation per column instead of by row)

    Returns:
        A split CDAP datafile, placed in outpath according to a location-based directory structure.
    """

    data = readData(path + '/' + filename)
    zdata = zip(*data)

    # Check if the data is CDAP 2
    if not data[0][0].startswith('PROCESSED'):
        # Not CDAP 2

        fields = getFields(data)

        # Pull out some necessary data
        projects = data[fields.index('Project')][1:-1]
        reps = data[fields.index('Replication')][1:-1]
        lats = data[fields.index('Latitude')][1:-1]
        lons = data[fields.index('Longitude')][1:-1]
        dates = data[fields.index('Date')][1:-1]
        starttimes = data[fields.index('Start Time')][1:-1]

        # Find the field position where scan data begins:
        scanIdx = findScanIdx(fields)

        # We will keep a dictionary of direcotires created and their projects/reps:
        dir_dict = {}

        # Split each file into unique projects.
        distinct_projects = list(set(projects))
        for project in distinct_projects:
            # For each unique project, get the unique reps associated with it
            preps = [x for x, y in zip(reps,projects) if y == project]  # Project reps

            # Get all of the current project's dates.
            if len(dates) > 1:  # CDAP2 will only have one date associated per file...
                pdates = [x for x, y in zip(dates, projects) if y == project]

            # Get the current project's lat/lon values
            locCheck = all(x == '' for x in lats) and all(x == '' for x in lons)  # Ensure lat/lon are not empty strings.
            if not locCheck:
                plats = [x for x, y in zip(lats, projects) if y == project]
                plons = [x for x, y in zip(lons, projects) if y == project]

            # Project starttimes
            ptimes = [x for x, y in zip(starttimes, projects) if y == project]

            # Process each unique prep (project rep) separately.
            distinct_preps = list(set(preps))
            for prep in distinct_preps:
                # Get the current project rep's unique dates. A list of dates of length == 1 is CDAP2
                if len(dates) > 1:  # CDAP2 will only have one date associated per file...
                    prep_dates = list(set([x for x, y in zip(pdates, preps) if y == prep]))
                else:
                    prep_dates = dates

                # Get the lats and lons for the current project rep
                if not locCheck:
                    prep_lats = [x for x, y in zip(plats, preps) if y == prep]
                    prep_lons = [x for x, y in zip(plons, preps) if y == prep]
                    # Determint the current project rep's location
                    location = determine_loc(prep_lats, prep_lons)

                else:  # If locCheck is false, GPS not taken and location is unknown.
                    location = 'UNKNOWN'

                # Rep starttimes
                prep_times = [x for x, y in zip(ptimes, preps) if y == prep]

                # Get all of the data for the project reps
                prepData = []
                # prepIdxs = [i for i, val in enumerate(reps) if val == prep]
                prepIdxs = [i for i, val1, val2 in zip(range(1, len(reps)+1), reps, projects)
                            if val1 == prep and val2 == project]

                if vertical:
                    for i, row in enumerate(data):
                        prepData.append([row[0]])  # Add the vertical header info.
                        for idx in prepIdxs:
                            prepData[i].append(row[idx])
                else:
                    for idx in prepIdxs:
                        prepData.append(zdata[idx])

                # Save the data to the correct locations

                # location/project directory
                projectDir = outpath + str(year) + '/' + location + '/' + project + '/' + prep_dates[0] + '/'

                if not os.path.exists(projectDir):
                    os.makedirs(projectDir)

                # Keep a log of what datafiles are being used to create newfiles.
                log = open(projectDir + 'log.txt', 'a')

                # Check if cal file
                if 'cal' in prep.lower():
                    cal = '_CAL_'
                else:
                    cal = '_'

                # Save KML file (MOSTLY JUST FOR TESTING, REMOVE / CHANGE LATER?
                kmlFilename = projectDir + prep + '.kml'
                ptName = project + ' ' + prep
                coords2KML(prep_lats, prep_lons, [ptName]*len(prep_lats), prep_times, kmlFilename)

                # Save aux data file.
                auxfile = projectDir + filename[0:-4] + cal + 'AUX' + '.csv'

                try:
                    if not os.path.isfile(auxfile):
                        # Create a new file
                        f = open(auxfile, 'w+')
                        write = csv.writer(f, delimiter=',')

                        # Write headerline if not vertical orientation.
                        if not vertical:
                            write.writerow(fields[0:scanIdx])

                    else:
                        # Should not be appending (maybe change later?)
                        raise IOError('File ' + auxfile + ' already exists! Trying to create from '
                                      + path + '/' + filename)

                    # Now write the results to the file.
                    if vertical:
                        for idx in range(0, scanIdx):
                            write.writerow(prepData[idx])
                    else:
                        for pdata in prepData:
                            write.writerow(pdata[0:scanIdx])

                    # Log that this occured.
                    log.write(auxfile[len(projectDir):] + ' created from ' + path + '/' + filename + '\n')

                except:
                    raise
                finally:
                    f.close()

                # Save the scan data file.
                scanfile = projectDir + filename[0:-4] + cal + 'SCANS' + '.csv'
                try:
                    if not os.path.isfile(scanfile):
                        # Create a new file
                        f = open(scanfile, 'w+')
                        write = csv.writer(f, delimiter=',')
                        # Write headerline if not vertical orientation.
                        if not vertical:
                            write.writerow(fields[scanIdx:])

                    else:
                        # Should not be appending (maybe change later?)
                        raise IOError('File ' + scanfile + ' already exists! Trying to create from '
                            + path + '/' + filename)
                        '''
                        # Just append results to file
                        f = open(scanfile, 'a')
                        write = csv.writer(f, delimiter=',')
                        '''
                    # Now write the results to the file.
                    if vertical:
                        for idx in range(scanIdx, len(prepData)):
                            write.writerow(prepData[idx])
                    else:
                        for pdata in prepData:
                            write.writerow(pdata[scanIdx:])

                    # Log that this occured.
                    log.write(scanfile[len(projectDir):] + ' created from ' + path + '/' + filename + '\n')

                except:
                    raise
                finally:
                    f.close()

                # Should be a new dir for every prep.
                dir_dict[projectDir] = {'date': prep_dates[0], 'project': project, 'reps': distinct_preps}

        return dir_dict

    else:
        # CDAP2
        pass

def create_files_manifest(dirpath, splitpaths):
    """
    Function for finding other files in directory containing data and creating a manifest of them.
    """
    # Walk through the current directory
    for root, dirs, files in os.walk(dirpath):
        # Check if there are any images in the current dir.
        images = [file for file in files if file.lower().endswith(('.jpg', '.png', '.tif'))]

        # Get a list of any of the raw data files
        raw_files = [file for file in files if file.lower().endswith(('.downwelling', '.upwelling', '.calibration', '.aux'))]

        # Get list of any logfiles.
        logs = [file for file in files if file.lower().endswith('log.txt')]

        # Get list of veg fraction files
        vegfrac_files = [file for file in files if file.lower().endswith('vegfraction.txt')]

        # Get all other files
        otherfiles = list(set(files) - set(images) - set(raw_files) - set(logs))

        # Open the log file(s) and record their data.
        log_data = []
        if len(logs) > 1:
            raise ValueError('THERE SHOULD ONLY BE ONE LOG FILE? MORE THAN ONE FOUND: ' + root)
        elif len(logs) == 1:
            log_data = readData(root + '/' + logs[0])  # Only look at the first log for now (should only be one).
            # Get and remove the log header from the logfile.
            log_header = log_data[1]
            log_data = log_data[2:]  # First two rows are headerlines, remove them.


        #Open the vegfraction file(s) and record their data.
        vegfrac_data = []
        if len(vegfrac_files) > 1:
            raise ValueError('THERE SHOULD ONLY BE ONE VEGFRACTION FILE? MORE THAN ONE FOUND: ' + root)
        elif len(vegfrac_files) == 1:
            vegfrac_data = readData(root + '/' + vegfrac_files[0])
            # Extract header
            vegfrac_header = vegfrac_data[0]
            # Remove header from data.
            vegfrac_data = vegfrac_header[1:]

        # Now split by directory and write results to manifest
        for dir in splitpaths.keys():
            # Extract the necessary information.
            project = splitpaths[dir]['project']
            date = splitpaths[dir]['date']
            reps = splitpaths[dir]['reps']

            # Make sure to grab every rep
            prep_images = []
            prep_rawfiles = []
            prep_logdata = []
            prep_vegfracdata = []
            for rep in reps:
                # Create a regex for finding files that match project/rep (prep)
                pattern = '{0}_{1}_{2}_*'.format(project, date, rep)
                pattern = re.compile(pattern)

                # Get the list of images that match the project/rep
                prep_images.extend([file for file in images if pattern.match(file.lower())])

                # Get the list of raw files that match the project/rep.
                prep_rawfiles.extend([file for file in raw_files if pattern.match(file.lower())])

                # Extract log matching project/rep
                if log_data:
                    prep_logdata.extend([row for row in log_data
                                         if row[1].lower() == project and row[2].lower() == rep])

                # Extract the vegfraction rows matching the prep_images found above.
                if vegfrac_data:
                    prep_vegfracdata.extend([row for row in vegfrac_data if row[0] in prep_images])

            # Create the directory if it doesn't yet exist:
            subdir = root[len(dirpath):]

            if subdir:
                savedir = dir + root[len(dirpath) + 1:] + '/'
            else:
                savedir = dir


            if date == '20050906' and project == 'csp02':
                pdb.set_trace()
            

            if not os.path.exists(savedir):
                os.makedirs(savedir)

            # Write the image manifest
            if prep_images:
                with open(savedir + 'images_log.txt', 'a') as imgfile:
                    for image in prep_images:
                        imgfile.write(image + '\n')

            # Write the raw files manifest
            if prep_rawfiles:
                with open(savedir +'raw_datafiles_log.txt','a') as rawfile:
                    for raw in prep_rawfiles:
                        rawfile.write(raw + '\n')

            # Write the other files manifest (include rootdir for back-tracing ?)
            if otherfiles:
                with open(savedir + 'other_files_log.txt', 'a') as otherfile:
                    for other in otherfiles:
                        otherfile.write(other + '\n')

            # Write the new logfile
            if log_data:
                # Now write the new log
                with open(savedir + logs[0][:-3] + '.csv', 'a') as logfile:
                    writer = csv.writer(logfile, delimiter=',')
                    writer.writerow(log_header)
                    for row in prep_logdata:
                        writer.writerow(row)

            # Write the new vegfraction file
            if vegfrac_data:
                with open(savedir + vegfrac_files[0][:-3] + '.csv', 'a') as vegfile:
                    writer = csv.writer(vegfile, delimiter = ',')
                    writer.writerow(vegfrac_header)
                    for row in prep_vegfracdata:
                        writer.writerow(row)

def processYear(year, outpath):
    """Process a year's worth of data files"""
    #Setup some patterns for recognizing valid data files:
    upPattern = re.compile('.*Upwelling.*\.txt')
    downPattern = re.compile('.*Downwelling.*\.txt')
    outPattern = re.compile('.*Outgoing.*\.txt')
    refPattern = re.compile('.*Reflectance.*\.txt')

    for root, dirs, files in os.walk('/media/sf_Field-Data/' + str(year)):
        # If files contains one or more supported types, get
        dirs = {}
        if '/'+str(year)+'/'+str(year) + '/' not in root and ('csp' in root.lower() or 'mead' in root.lower() or 'BLMV' in root):
            getOtherFiles = False  # Flag for logging presence of other files (only happens if a match happens below).

            upwelling = [file for file in files if upPattern.match(file)]
            for up in upwelling:
                try:
                    dirs = splitdata(root,up,year,outpath)

                except Exception as e:
                    print(root + up + ' Failed processing: \n')
                    traceback.print_exc()

            downwelling = [file for file in files if downPattern.match(file)]
            for down in downwelling:
                try:
                    dirs = splitdata(root,down,year,outpath)

                except Exception as e:
                    print(root + down + ' Failed processing: \n')
                    traceback.print_exc()

            outgoing = [file for file in files if outPattern.match(file)]
            for out in outgoing:
                try:
                    dirs = splitdata(root,out,year,outpath)

                except Exception as e:
                    print(root + out + ' Failed processing: \n')
                    traceback.print_exc()

            reflect = [file for file in files if refPattern.match(file)]
            for ref in reflect:
                try:
                    dirs = splitdata(root,ref,year,outpath)
                except Exception as e:
                    print(root + ref + ' Failed processing: \n')
                    traceback.print_exc()

            if dirs:
                # Get a listing of all other files/subdirs and include a manifest in outpath.
                create_files_manifest(root, dirs)

    print str(year) + ' PROCESSED'