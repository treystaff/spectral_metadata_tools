from mySqlite import mySqlite
import os
import csv
import uuid
from utility import *
import warnings
import traceback
import glob


def load_metadata(restruct_dir, dbpath, user_uuid ='7367a141-eaf0-4aee-8f9a-ca059150acca', calc_avg_latlon=False):

    # Find the metadata file associated with the directory.
    files = os.listdir(restruct_dir)
    meta_file = [f for f in files if f == 'Metadata.csv']

    # Check that the metaadata file exists, and that there is only one.
    if not meta_file:
        raise IOError('No metadata file found in directory')
    elif len(meta_file) > 1:
        raise IOError("SOMEHOW, MORE THAN ONE METADATA FILE FOUND IN DIRECTORY!")

    # Get a list of other files
    other_files = [f for f in files if f != 'Metadata.csv']
    # We don't need files anymore.
    del files

    # Connect to the database.
    try:
        db = mySqlite(dbpath)
        # Open the CSV file and read its contents
        with open(os.path.join(restruct_dir, meta_file[0])) as mfile:
            reader = csv.reader(mfile, delimiter=',')
            meta_dict = dict()
            for row in reader:
                try:
                    # Correct some errors found in earlier versions of metadata
                    # files (only necessary until data is re-processed).
                    if  'Pyronometer' in row[0]:
                        row[0] = row[0].replace('Pyronometer', 'Pyranometer')
                    if 'Temperature 1' in row[0]:
                        row[0] = row[0].replace('Temperature 1', 'Canopy Temperature')
                    if 'Temperature 2' in row[0]:
                        row[0] = row[0].replace('Temperature 2', 'Wheel Temperature') 

                    meta_dict[row[0]] = row[1:]

                except IndexError:
                    pass

        # Once again, a quickfix to get data to shilpa. This can be removed
        # after re-processing:
        if meta_dict['Target'] and meta_dict['Target'][0] == meta_dict['Calibration Panel'][0]:
            meta_dict['Project'][0] = 'CSP-CAL'
            d_id = meta_dict['Dataset ID'][0]
            meta_dict['Dataset ID'][0] = 'CSP-CAL' + d_id[d_id.find('_'):]

        # Insert the meta values into the database.
        # Check if the project exists. if not, insert.
        project_id = db.query('SELECT id from projects where name = ?',
                              meta_dict['Project'][0])
        if not project_id:
            project_id = str(uuid.uuid4())
            db.query('INSERT INTO projects (id, user_id, name, created_date, organization) VALUES (?, ?, ?,datetime(), ?)',
                     project_id, user_uuid, meta_dict['Project'][0], 'CALMIT')

        else:
            project_id = project_id[0][0]

        # Now create the dataset.
        dataset_uuid = str(uuid.uuid4())
        include_latlon = False
        if calc_avg_latlon:
            aux_path = glob.glob(os.path.join(restruct_dir, 'Auxiliary*.csv'))
            if not aux_path:
                warnings.warn('NO AUX FILE FOUND IN {0}'.format(restruct_dir))
            else:
                aux_path = aux_path[0]
                # Read data from the aux file and calculate avg. lat/lon 
                data = readData(aux_path) 
                for entry in data: 
                    entry = entry[0].split(',')
                    if entry[0] == 'Latitude' and not all(val == '-9999' or val == '' for val in entry[1:]): 
                        avg_lat = mean(filter_floats(entry[1:])) 
                        meta_dict['Average Latitude'] = [avg_lat,
                                                         'Decimal degrees', 
                                                         'The average latitude \
                                                         in geographic decimal degrees'] 
                        include_latlon = True 
                        print('including caclulated lat/lon for {0}'.format(restruct_dir)) 
                    if entry[0] == 'Longitude' and not all(val == '-9999' or val == '' for val in entry[1:]): 
                        avg_lon = mean(filter_floats(entry[1:]))
                        meta_dict['Average Longitude'] = [avg_lon, 
                                                          'Decimal degrees', 
                                                          'The average \
                                                          longitude in \
                                                          geographic decimal \
                                                          degrees']
                    
        else: 
            if 'Average Latitude' in meta_dict.keys(): 
                avg_lat = meta_dict['Average Latitude'][0]

                avg_lon = meta_dict['Average Longitude'][0]
                include_latlon = True

        # Check if other location-information is present. 
        if 'County' in meta_dict.keys():
            county = meta_dict['County'][0]
        else:
            county = None
        if 'State' in meta_dict.keys():
            state = meta_dict['State'][0]
        else:
            state = None
        if 'Country' in meta_dict.keys():
            country = meta_dict['Country'][0]
        else:
            country = None
        if 'Location' in meta_dict.keys():
            location = meta_dict['Location'][0]
        else:
            location = None

        if not include_latlon:
            avg_lat = None
            avg_lon = None

        # insert the dataset info 
        db.query('INSERT INTO datasets (id, user_id, project_id, date, start_time, stop_time, created_date, '
                 'country, location, State, county, lat, lon)'
                 'VALUES (?, ?,?, ?, ?, ?, datetime(), ?, ?, ?, ?, ?, ?);',
                 dataset_uuid, user_uuid, project_id, meta_dict['Date'][0],
                  meta_dict['Start Time'][0], meta_dict['Stop Time'][0],
                  country, location, state, county, avg_lat, avg_lon)

        # Insert records
        for other_file in other_files:
            db.query('INSERT INTO records (id, dataset_id, path, filename, user_id, last_updated) '
                     'VALUES (?,?, ?, ?, ?, datetime())',
                     str(uuid.uuid4()), dataset_uuid, restruct_dir, other_file, user_uuid)

        # Meta values
        for key in meta_dict.keys():
            metadata_id = db.query('SELECT id FROM metadata where name = ?', key)

            if metadata_id:
                metadata_id = metadata_id[0][0]
                if not meta_dict[key]: 
                    # There are a few cases (Target) where the absence of a
                    # value should be noted...
                    meta_dict[key] = [None]

                db.query('INSERT INTO meta_values '
                         '(id, metadata_id, dataset_id, value, user_id, last_updated) '
                         'VALUES (?,?, ?, ?, ?,datetime())',
                         str(uuid.uuid4()), metadata_id, dataset_uuid,
                         meta_dict[key][0], user_uuid)
            else:
                print('WARNING: AN ENTRY IN THE METADATA TABLE WAS NOT FOUND \
                      FOR {0}!'.format(key))

        # Commit all changes.
        db.commit()

        print('Metadata from {0} loaded!!'.format(restruct_dir))
    except Exception, e:
        print('METADATA FROM {0} FAILED TO LOAD'.format(restruct_dir))
        print(traceback.format_exc())
        raise e
    finally:
        db.close()

if __name__ == '__main__':
    execfile('/code/spectral_metadata_tools/initDb.py')
    for root, subdirs, files in os.walk('/media/sf_tmp/restruct2/'):
        if 'Metadata.csv' in files:
            load_metadata(root, '/tmp/MetaDataDb.db', calc_avg_latlon=True)


    #load_metadata('/media/sf_tmp/restruct_test/CSP02/20070809/', '/tmp/MetaDatadb.db')
