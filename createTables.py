execfile('/home/trey/CODE/mySqlite.py')

import os

dbpath = '/home/trey/CODE/investigate.db'

# Remove the db if it already exists
try:
    os.remove(dbpath)
except:
    pass

db = mySqlite(dbpath)

db.query('''CREATE TABLE datasets 
                (id INTEGER primary key,
                path text,
                year int);''')

db.query('''CREATE TABLE records
                (id INTEGER primary key,
                dataset_id REFERENCES datasets(id),
                filename text);''')

db.query('''CREATE TABLE meta 
                (id INTEGER primary key,
                dataset_id REFERENCES datasets(id),
                software text,
                instrument text,
                datalogger text);''')

db.query('''CREATE TABLE fields
                (id INTEGER primary key,
                dataset_id REFERENCES datasets(id),
                name text);''')

db.query('''CREATE TABLE projects
                (id INTEGER primary key,
                dataset_id REFERENCES datasets(id),
                name text);''')

db.query('''CREATE TABLE reps
                (id INTEGER primary key,
                project_id REFERENCES projects(id),
                name text,
                location text,
                locations text);''')

db.query('''CREATE TABLE dates
                (id INTEGER primary key,
                rep_id REFERENCES reps(id),
                date text);''')

db.query('''CREATE TABLE odirs
                (id INTEGER primary key,
                dataset_id REFERENCES datasets(id),
                name text);''')

db.query('''CREATE TABLE subdirs
                (id INTEGER primary key,
                dataset_id REFERENCES datasets(id),
                name text);''')

db.commit()
db.close()
