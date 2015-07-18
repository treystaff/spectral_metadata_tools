
"""
Standalone script for getting information about existing data files...
Not very clean, but works...
Scroll to bottom for setup code, definitions first...
"""
# execfile('/home/trey/CODE/investigate.py')

execfile('/home/trey/CODE/createTables.py')

execfile('/home/trey/CODE/mySqlite.py')

import pdb
import logging
import itertools
import os
import re

# Remove the current log if it exists.
try:
    os.remove('/home/trey/CODE/LOG.log')
except:
    pass

logging.basicConfig(filename='/home/trey/CODE/LOG.log')

def mean(l):
    return sum(l)/float(len(l))

def find_loc(lats,lons, prep):
    locations = ''

    # Convert lats & lons to floats from strings
    lats = [float(lat) for lat in lats if lat != '']
    lons = [float(lon) for lon in lons if lon != '']

    # The rep has no GPS values.
    if len(lats) < 1 or len(lons) < 1:
        return 'UNKNOWN','UNKNOWN'

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

    if (41.161607 <= any(lats) <= 41.169437) and (-96.483063 <= any(lons) <= -96.47315):
        locations += 'CSP1; '
    if (41.161405 <= any(lats) <= 41.168761) and (-96.473668 <= any(lons) <= -96.463818):
        locations += 'CSP2; '
    if (41.175715 <= any(lats) <= 41.183072) and (-96.444978 <= any(lons) <= -96.434610):
        locations += 'CSP3; '

    if locations == '':
        locations = 'OUT OF RANGE'

    return location, locations

def process_cdap(path, filename, subdirs):
    logging.basicConfig(filename='/home/trey/CODE/LOG.log')
    try:
        # Open a db connection, to keep track of everything.
        db = mySqlite('/home/trey/CODE/investigate.db')

        # Search for files in the current dir that match Upwelling/Outgoing name, open & extract from them.
        with open(path + '/' + filename, 'r') as f:
            datas = f.readlines()

        odirs = []
        records = []
        reps = []
        software = None
        project = None
        instrument = None
        datalogger = None

        # Split each line of data by tab. (this is true for all types)
        data = []
        for row in datas:
            row = row[0:-2]
            data.append(row.split('\t'))
        del datas

        # Check if not cdap 2 (cdap 2 has to be uniquely handled...
        if not data[0][0].startswith('PROCESSED'):

            # Now create a data dict
            dat = {}
            keys = []  # Keep track of unique keys
            for row in data:
                try:
                    float(row[0])
                except:
                    keys.append(row[0])
                    dat[row[0]] = row[1:-1]

            data = dat
            del dat

            # Extract relevant data
            try:
                projects = data['Project']  # There can be multiple projects per file.
            except KeyError:
                logging.exception('WARNING: ' + path + filename + ' PROJECT WAS NOT FOUND')
                print('WARNING: ' + path + filename + ' PROJECT WAS NOT FOUND')
                raise

            try:
                reps = data['Replication']  # There are multiple reps per file.
            except KeyError:
                logging.exception('WARNING: ' + path + filename + ' REPS WERE NOT FOUND')
                print('WARNING: ' + path + filename + ' REPS WERE NOT FOUND')
                raise

            try:
                lats = data['Latitude']  # Multiple latitude values per file.
            except KeyError:
                logging.exception('WARNING: ' + path + filename + ' LATITUDE WAS NOT FOUND')
                print('WARNING: ' + path + filename + ' LATITUDE WAS NOT FOUND')
                raise

            try:
                lons = data['Longitude']  # Multiple longitude values per file
            except KeyError:
                logging.exception('WARNING: ' + path + filename + ' LONGITUDE WAS NOT FOUND')
                print('WARNING: ' + path + filename + ' LONGITUDE WAS NOT FOUND')
                raise

            try:
                software = data['Software Version'][0]  # Should only be one software version per collection
            except KeyError:
                try:
                    software = data['Program Version'][0]
                except KeyError:
                    logging.exception('WARNING: ' + path + filename + ' software WAS NOT FOUND')
                    print('WARNING: ' + path + filename + ' software WAS NOT FOUND')
                    raise

            try:
                instrument = data['Instrument'][0]  # Should be only one instrument per file
            except KeyError:
                try:
                    instrument = data['Instrument Type'][0]
                except KeyError:
                    logging.exception('WARNING: ' + path + filename + ' instrument WAS NOT FOUND')
                    print('WARNING: ' + path + filename + ' instrument WAS NOT FOUND')
                    raise

            try:
                datalogger = data['Data Logger'][0]  # Just want an example from each file of the datalogger.
            except KeyError:
                logging.exception('WARNING: ' + path + filename + ' datalogger WAS NOT FOUND')
                print('WARNING: ' + path + filename + ' datalogger WAS NOT FOUND')
                raise

            # Get the file recorded date. Should be only one date per file?
            try:
                dates = data['Date']
            except KeyError:
                logging.exception('WARNING: ' + path + filename + ' date WAS NOT FOUND')
                print('WARNING: ' + path + filename + ' date WAS NOT FOUND')
                raise

        else:
            # Get info from CDAP2
            instrument = data[4][0]
            software = data[2][1]
            projects = data[9][1:-1]
            datalogger = data[18][1]
            reps = data[10][1:-1]
            dates = [data[2][0]]  # CDAP2 only records one acquire date.

            # CDAP2 has a GPS string but does not split lat/lon.
            gps = data[17][1:-1]
            if gps:
                # There are currently no examples of the CDAP2 gps string, so don't process right now.
                logging.exception('FOUND CDAP2 WITH GPS COORDS. LOCATION EXTRACTION NOT SUPPORTED: ' + path + filename)
                print('FOUND CDAP2 WITH GPS COORDS. LOCATION EXTRACTION NOT SUPPORTED: ' + path + filename)

        # insert relevant info into the db (this happens regardless of filetype)

        # Dataset
        # Check if the dataset already exists
        dataset_id = db.query('SELECT id from datasets WHERE path = ? and year = ?', [path, year])
        if not dataset_id:
            # Create a new entry
            db.query('INSERT INTO datasets (path,year) VALUES (?,?)', [path, year])  # NEED TO DEFINE PATH
            dataset_id = db.get_last_id()[0]
        else:
            dataset_id = dataset_id[0][0]  # Should be only one datset id returned

        # Process the extracted data. Want to obtain unique reps, lats, and lons, and dates for each unique project.
        distinct_projects = list(set(projects))
        for project in distinct_projects:
            # Insert the current project into the db and get an id for that entry.
            db.query('INSERT INTO projects (dataset_id,name) VALUES (?,?)', [dataset_id, project])
            project_id = db.get_last_id()[0]

            # Now get the reps,lats,lons, and dates of the current project.
            preps = [x for x, y in zip(reps,projects) if y == project]  # Project reps

            # Get all of the current project's dates.
            if len(dates) > 1:  # CDAP2 will only have one date associated per file...
                pdates = [x for x, y in zip(dates, projects) if y == project]

            # Get the current project's lat/lon values
            locCheck = all(x == '' for x in lats) and all(x == '' for x in lons) # Ensure lat/lon are not empty strings.
            if not locCheck:
                plats = [x for x, y in zip(lats, projects) if y == project]
                plons = [x for x, y in zip(lons, projects) if y == project]

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

                    location, locations = find_loc(prep_lats, prep_lons,prep)
                else:  # If locCheck is false, GPS not taken and location is unknown.
                    location = 'UNKNOWN'
                    locations = 'UNKNOWN'

                # Insert information about a project's reps (project id, name, and location).
                db.query('INSERT INTO reps (project_id, name, location, locations) VALUES (?,?,?,?)',
                         [project_id, prep, location,locations])
                rep_id = db.get_last_id()[0]

                # Keep track of all dates associated with a given project's rep (should be 1,
                # but sometimes more in special cases).
                for date in prep_dates:
                    db.query('INSERT INTO dates (rep_id,date) VALUES (?,?)', [rep_id, date])

        # OTHER INSERTS
        # meta
        db.query('INSERT INTO meta (dataset_id,software,instrument,datalogger) VALUES (?,?,?,?)',
                 [dataset_id,  software, instrument, datalogger])

        # Fields
        for field in keys:
            db.query('INSERT INTO fields (dataset_id,name) VALUES (?,?)', [dataset_id, field])

        db.query('INSERT INTO records (dataset_id, filename) VALUES (?,?)', [dataset_id, filename])

        # Subdirs
        for subdir in subdirs:
            db.query('INSERT INTO subdirs (dataset_id,name) VALUES (?,?)', [dataset_id, subdir])

        # odirs
        for odir in odirs:
            db.query('INSERT INTO odirs (dataset_id,name) VALUES (?,?)', [dataset_id, odir])

        db.commit()
    except Exception as e:
        print e
        raise
    finally:
        db.close()



#Setup some patterns for recognizing valid data files:
upPattern = re.compile('.*Upwelling.*\.txt')
downPattern = re.compile('.*Downwelling.*\.txt')
outPattern = re.compile('.*Outgoing.*\.txt')
refPattern = re.compile('.*Reflectance.*\.txt')


import traceback
years = range(2000, 2015)  # The range of years we're looking at.
#years = [2011]
for year in years:
    lastdirs = []
    for root, dirs, files in os.walk('/media/sf_Field-Data/' + str(year)):
        # If files contains one or more supported types, get
        if 'csp' in root or 'CSP' in root or 'Mead' in root or 'mead' in root or 'BLMV' in root:
            upwelling = [file for file in files if upPattern.match(file)]
            for up in upwelling:
                try:
                    process_cdap(root, up, dirs)
                except Exception as e:
                    print(root + up + ' Failed processing: \n')
                    traceback.print_exc()

            downwelling = [file for file in files if downPattern.match(file)]
            for down in downwelling:
                try:
                    process_cdap(root, down, dirs)
                except Exception as e:
                    print(root + down + ' Failed processing: \n')
                    traceback.print_exc()

            outgoing = [file for file in files if outPattern.match(file)]
            for out in outgoing:
                try:
                    process_cdap(root, out, dirs)
                except Exception as e:
                    print(root + out + ' Failed processing: \n')
                    traceback.print_exc()

            reflect = [file for file in files if refPattern.match(file)]
            for ref in reflect:
                try:
                    process_cdap(root, ref, dirs)
                except Exception as e:
                    print(root + ref + ' Failed processing: \n')
                    traceback.print_exc()

    print str(year) + ' PROCESSED'

