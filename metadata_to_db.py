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
                    meta_dict[row[0]] = row[1]
                except IndexError:
                    pass

        # Insert the meta values into the database.
        # Check if the project exists. if not, insert.
        project_id = db.query('SELECT id from projects where name = ?', meta_dict['Project'])
        if not project_id:
            project_id = str(uuid.uuid4())
            db.query('INSERT INTO projects (id, user_id, name, created_date, organization) VALUES (?, ?, ?,datetime(), ?)',
                     project_id, user_uuid, meta_dict['Project'], 'CALMIT')

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
                        include_latlon = True
                        print('including caclulated lat/lon for {0}'.format(restruct_dir))
                    if entry[0] == 'Longitude' and not all(val == '-9999' or val == '' for val in entry[1:]):
                        avg_lon = mean(filter_floats(entry[1:]))

        else:
            if 'Average Latitude' in meta_dict.keys():
                avg_lat = meta_dict['Average Latitude']
                avg_lon = meta_dict['Average Longitude']
                include_latlon = True

        if include_latlon:
                query_str = 'INSERT INTO datasets (id, user_id, project_id, date, start_time, stop_time, ' \
                            'created_date, lat, lon) VALUES (?, ?,?, ?, ?, ?, datetime(), ?, ?)'

                db.query(query_str, dataset_uuid, user_uuid,project_id, meta_dict['Date'],meta_dict['Start Time'],
                         meta_dict['Stop Time'], avg_lat, avg_lon)
        else:
            db.query('INSERT INTO datasets (id, user_id, project_id, date, start_time, stop_time, created_date)'
                         'VALUES (?, ?,?, ?, ?, ?, datetime());',dataset_uuid, user_uuid, project_id, meta_dict['Date'],
                         meta_dict['Start Time'], meta_dict['Stop Time'])

        dataset_id = db.get_last_id()

        # Insert records
        for other_file in other_files:
            db.query('INSERT INTO records (id, dataset_id, path, filename, user_id, last_updated) '
                     'VALUES (?,?, ?, ?, ?, datetime())',
                     str(uuid.uuid4()), dataset_id, restruct_dir, other_file, user_uuid)

        # Meta values
        for key in meta_dict.keys():
            metadata_id = db.query('SELECT id FROM metadata where name = ?', key)

            if metadata_id:
                metadata_id = metadata_id[0][0]
                db.query('INSERT INTO meta_values (id, metadata_id, dataset_id, value, user_id, last_updated) VALUES '
                         '(?,?, ?, ?, ?,datetime())',
                         str(uuid.uuid4()), metadata_id, dataset_id, meta_dict[key], user_uuid)

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
    execfile('initDb.py')
    for root, subdirs, files in os.walk('/media/sf_tmp/restruct2/'):
        if 'Metadata.csv' in files:
            load_metadata(root, '/tmp/MetaDataDb.db', calc_avg_latlon=True)


    #load_metadata('/media/sf_tmp/restruct_test/CSP02/20070809/', '/tmp/MetaDatadb.db')