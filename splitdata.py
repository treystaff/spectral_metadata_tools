"""
Working draft of functions for splitting CALMIT CDAP datafiles into data, metadata, and auxiliary files.
"""

import simplekml
import os
import csv
import traceback
import re

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
                        '''
                        # Just append results to file
                        f = open(auxfile, 'a')
                        write = csv.writer(f, delimiter=',')
                        '''
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

    else:
        # CDAP2
        pass

def processYear(year, outpath):
    """Process a year's worth of data files"""
    #Setup some patterns for recognizing valid data files:
    upPattern = re.compile('.*Upwelling.*\.txt')
    downPattern = re.compile('.*Downwelling.*\.txt')
    outPattern = re.compile('.*Outgoing.*\.txt')
    refPattern = re.compile('.*Reflectance.*\.txt')

    for root, dirs, files in os.walk('/media/sf_Field-Data/' + str(year)):
        # If files contains one or more supported types, get
        if '/'+str(year)+'/'+str(year) + '/' not in root and ('csp' in root.lower() or 'mead' in root.lower() or 'BLMV' in root):
            upwelling = [file for file in files if upPattern.match(file)]
            for up in upwelling:
                try:

                    splitdata(root,up,year,outpath)

                except Exception as e:
                    print(root + up + ' Failed processing: \n')
                    traceback.print_exc()

            downwelling = [file for file in files if downPattern.match(file)]
            for down in downwelling:
                try:
                    splitdata(root,down,year,outpath)
                except Exception as e:
                    print(root + down + ' Failed processing: \n')
                    traceback.print_exc()

            outgoing = [file for file in files if outPattern.match(file)]
            for out in outgoing:
                try:
                    splitdata(root,out,year,outpath)
                except Exception as e:
                    print(root + out + ' Failed processing: \n')
                    traceback.print_exc()

            reflect = [file for file in files if refPattern.match(file)]
            for ref in reflect:
                try:
                    splitdata(root,ref,year,outpath)
                except Exception as e:
                    print(root + ref + ' Failed processing: \n')
                    traceback.print_exc()

    print str(year) + ' PROCESSED'