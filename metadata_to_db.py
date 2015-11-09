from mySqlite import mySqlite
import os
import csv


def load_metadata(restruct_dir, dbpath):

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
            db.query('INSERT INTO projects (name) VALUES (?)', meta_dict['Project'])
            project_id = db.get_last_id()
        else:
            project_id = project_id[0][0]

        # Now create the dataset.
        db.query('INSERT INTO datasets (project_id, date, start_time, stop_time) VALUES (?, ?, ?, ?)',
                 project_id, meta_dict['Date'],meta_dict['Start Time'], meta_dict['Stop Time'])

        dataset_id = db.get_last_id()

        # Insert records
        for other_file in other_files:
            db.query('INSERT INTO records (dataset_id, path, filename) VALUES (?, ?, ?)',
                     dataset_id, restruct_dir, other_file)

        # Meta values
        for key in meta_dict.keys():
            metadata_id = db.query('SELECT id FROM metadata where name = ?', key)

            if metadata_id:
                metadata_id = metadata_id[0][0]
                db.query('INSERT INTO meta_values (metadata_id, dataset_id, value) VALUES '
                         '(?, ?, ?)',
                         metadata_id, dataset_id, meta_dict[key])

        # Commit all changes.
        db.commit()

        print('Metadata from {0} loaded!!'.format(restruct_dir))
    except Exception, e:
        print('METADATA FROM {0} FAILED TO LOAD'.format(restruct_dir))
        raise e
    finally:
        db.close()

if __name__ == '__main__':
    for root, subdirs, files in os.walk('/media/sf_tmp/restruct/'):
        if 'Metadata.csv' in files:
            load_metadata(root, '/tmp/MetaDatadb.db')


    #load_metadata('/media/sf_tmp/restruct_test/CSP02/20070809/', '/tmp/MetaDatadb.db')