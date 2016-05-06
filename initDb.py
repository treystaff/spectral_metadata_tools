from mySqlite import mySqlite
import csv
import os
import uuid

# Define the path to the metadata descriptions file (this is the master file
# used to control what is considered metadata, metadata descriptions, etc.)
meta_list_path = '/code/spectral_metadata_tools/METADATA_DESCRIPTIONS.csv'

# Define the user-id we'll be using.
user_id = '7367a141-eaf0-4aee-8f9a-ca059150acca'

# Define the path to the database. Remove it if it already exists.
db_path = '/tmp/MetaDataDb.db'
if os.path.isfile(db_path):
    os.remove(db_path)

# Initiate connection to the db
db = mySqlite(db_path)

# Lets make some tables!
# User table & An entry for myself.
db.query('''CREATE TABLE user (
            user_id char(16) not null primary key,
            f_name text,
            l_name text,
            organization text,
            profession text,
            experience text,
            psswrd text,
            email text,
            consent boolean,
            lastLogin datetime,
            lastSync datetime,
            lastLogout datetime);''')

user_uuid = uuid.uuid4()
db.query('''INSERT INTO user (user_id, f_name, l_name, organization, profession, psswrd, email) VALUES
    (?, 'admin', 'admin', 'admin', 'admin', 'admin', 'admin@admin.com');''', str(user_uuid))

# Categories table and entries
db.query('''CREATE TABLE categories (
            id char(16) not null primary key,
            name text,
            description text,
            last_updated datetime);''')

categories_entries = [
            "INSERT INTO categories (id, name, description, last_updated) VALUES ('cc6aa3e5-918c-4c33-84ab-94c1a0ddd703','Other','Other', datetime());",
            "INSERT INTO categories (id, name, description, last_updated) VALUES ('1b16b1db-c9a9-4181-9bfd-2efe933f401c','Illumination Geometry','Solar angles', datetime());",
            "INSERT INTO categories (id, name, description, last_updated) VALUES ('720d5bf0-a6ad-40a7-8037-eafb45985aec','Viewing Geometry','Sensor angles and FOV', datetime());",
            "INSERT INTO categories (id, name, description, last_updated) VALUES ('9cd960c2-c620-4563-9314-303c4a2c044a','Instruments','Information about instruments used', datetime());",
            "INSERT INTO categories (id, name, description, last_updated) VALUES ('946ee4a0-d893-4089-84ea-5145560884f2','Scan Data','Information about instruments used', datetime());",
            "INSERT INTO categories (id, name, description, last_updated) VALUES ('0316ac68-b6cb-43ea-9e51-d59a4d4be6ab','Calibration','Information on how calibration was performed', datetime());",
            "INSERT INTO categories (id, name, description, last_updated) VALUES ('9c17a7f4-5774-4d35-8e00-0717a08c054b','Location','Location information (lat, lon, area, etc.)', datetime());",
            "INSERT INTO categories (id, name, description, last_updated) VALUES ('73e05abe-8b54-4c9f-8b87-c9406808249d','Target','Target information (vegetation, etc)', datetime());",
            "INSERT INTO categories (id, name, description, last_updated) VALUES ('7f1343bf-0bbf-46e4-8f8a-86fda688c170','Auxiliary','Metadata related to auxilliary sensors/data', datetime());",
            ]

for entry in categories_entries:
    db.query(entry)


# Keywords
db.query('''CREATE TABLE keywords (
            id char(16) not null primary key,
            user_id char(16) REFERENCES user(user_id),
            category_id char(15) REFERENCES categories(id),
            name text,
            description text,
            compulsory boolean,
            last_updated datetime);
        ''')

keywords_entries = [
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, 'cc6aa3e5-918c-4c33-84ab-94c1a0ddd703', 'Other', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '9cd960c2-c620-4563-9314-303c4a2c044a','Upwelling Instrument Name', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '9cd960c2-c620-4563-9314-303c4a2c044a','Upwelling Instrument Serial Number', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '9cd960c2-c620-4563-9314-303c4a2c044a','Upwelling Instrument FOV', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '9cd960c2-c620-4563-9314-303c4a2c044a','Upwelling Instrument Max Wavelength', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '9cd960c2-c620-4563-9314-303c4a2c044a', 'Upwelling Instrument Min Wavelength', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '9cd960c2-c620-4563-9314-303c4a2c044a', 'Downwelling Instrument Name', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '9cd960c2-c620-4563-9314-303c4a2c044a', 'Downwelling Instrument Serial Number', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '9cd960c2-c620-4563-9314-303c4a2c044a', 'Downwelling Instrument FOV', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '9cd960c2-c620-4563-9314-303c4a2c044a', 'Downwelling Instrument Max Wavelength', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '9cd960c2-c620-4563-9314-303c4a2c044a', 'Downwelling Instrument Min Wavelength', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '9cd960c2-c620-4563-9314-303c4a2c044a', 'Acquisition Software', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '9cd960c2-c620-4563-9314-303c4a2c044a', 'Software Version', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '0316ac68-b6cb-43ea-9e51-d59a4d4be6ab', 'Calibration Panel', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '0316ac68-b6cb-43ea-9e51-d59a4d4be6ab', 'Calibration Mode', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '9cd960c2-c620-4563-9314-303c4a2c044a', 'Upwelling Instrument Channels', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '9cd960c2-c620-4563-9314-303c4a2c044a', 'Downwelling Instrument Channels', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '946ee4a0-d893-4089-84ea-5145560884f2', 'Scans Count', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '9c17a7f4-5774-4d35-8e00-0717a08c054b', 'Minimum Latitude', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '9c17a7f4-5774-4d35-8e00-0717a08c054b', 'Maximum Longitude', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '9c17a7f4-5774-4d35-8e00-0717a08c054b', 'Minimum Longitude', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '9c17a7f4-5774-4d35-8e00-0717a08c054b', 'Average Longitude', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '9c17a7f4-5774-4d35-8e00-0717a08c054b', 'Average Latitude', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '1b16b1db-c9a9-4181-9bfd-2efe933f401c', 'Illumination Source', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '1b16b1db-c9a9-4181-9bfd-2efe933f401c', 'Minimum Solar Azimuth', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '1b16b1db-c9a9-4181-9bfd-2efe933f401c', 'Maximum Solar Azimuth', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '1b16b1db-c9a9-4181-9bfd-2efe933f401c', 'Minimum Solar Elevation', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '1b16b1db-c9a9-4181-9bfd-2efe933f401c', 'Maximum Solar Elevation', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '1b16b1db-c9a9-4181-9bfd-2efe933f401c', 'Minimum Solar Zenith', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '1b16b1db-c9a9-4181-9bfd-2efe933f401c', 'Maximum Solar Zenith', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '9c17a7f4-5774-4d35-8e00-0717a08c054b', 'Minimum Altitude', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '9c17a7f4-5774-4d35-8e00-0717a08c054b', 'Maximum Altitude', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '9c17a7f4-5774-4d35-8e00-0717a08c054b', 'Maximum Latitude', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '73e05abe-8b54-4c9f-8b87-c9406808249d', 'Target', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '9c17a7f4-5774-4d35-8e00-0717a08c054b', 'State', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '9c17a7f4-5774-4d35-8e00-0717a08c054b', 'Place Name', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '9c17a7f4-5774-4d35-8e00-0717a08c054b', 'County', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '9c17a7f4-5774-4d35-8e00-0717a08c054b', 'Country', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '7f1343bf-0bbf-46e4-8f8a-86fda688c170', 'Minimum Canopy Temperature', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '7f1343bf-0bbf-46e4-8f8a-86fda688c170', 'Maximum Canopy Temperature', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '7f1343bf-0bbf-46e4-8f8a-86fda688c170', 'Minimum Wheel Temperature', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '7f1343bf-0bbf-46e4-8f8a-86fda688c170', 'Maximum Wheel Temperature', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '7f1343bf-0bbf-46e4-8f8a-86fda688c170', 'Minimum Pyranometer', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '7f1343bf-0bbf-46e4-8f8a-86fda688c170', 'Maximum Pyranometer', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '7f1343bf-0bbf-46e4-8f8a-86fda688c170', 'Minimum Quantum Sensor', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());",
            "INSERT INTO keywords (id, category_id, name, compulsory,user_id, last_updated) VALUES (?, '7f1343bf-0bbf-46e4-8f8a-86fda688c170', 'Maximum Quantum Sensor', 0, '7367a141-eaf0-4aee-8f9a-ca059150acca' ,datetime());"
            ]

for entry in keywords_entries:
    db.query(entry, str(uuid.uuid4()))

# Projects
db.query('''CREATE TABLE projects (
            id char(16) not null primary key,
            user_id char(16) REFERENCES user(user_id),
            name text,
            abstract text,
            sponsor text,
            organization text,
            contact text,
            flag boolean,
            created_date datetime);
        ''')

# Datasets
db.query('''CREATE TABLE datasets (
            id char(16) not null primary key,
            user_id char(16) REFERENCES user(user_id),
            project_id char(16) REFERENCES projects(id),
            date text,
            start_time text,
            stop_time text,
            lat text,
            lon text,
            country text,
            location text,
            State text,
            county text,
            created_date datetime);''')

# Records
db.query('''CREATE TABLE records (
            id char(16) not null primary key,
            user_id char(16) REFERENCES user(user_id),
            dataset_id char(16) REFERENCES datasets(id),
            path text,
            filename text,
            last_updated datetime);''')

# Metadata & Entries
db.query('''CREATE TABLE metadata (
            id char(16) NOT NULL primary key,
            keyword_id char(16) REFERENCES keywords(id),
            user_id char(16) REFERENCES user(user_id),
            name text,
            version text,
            description text,
            units text,
            reserved text,
            last_updated datetime);''')

# Read metadata elements from the meta list file.
elements = []
with open(meta_list_path, 'r') as meta_list_file:
    reader = csv.reader(meta_list_file, delimiter=',')
    for row in reader:
        elements.append(row)

# Add each metadata element to the medtadata table
for element in elements:
    # Each element is [meta_name, units, description, keyword_name]
    meta_name, units, desc, keyword_name = element
    if 'null' in units.lower():
        units = None

    # First, find the keyword id associated with this metadata entry. 
    keyword_id = db.query("SELECT id FROM keywords WHERE name = ?",
                          keyword_name)

    if keyword_id:
        keyword_id = keyword_id[0][0]
    else:
        print("WARNING: KEYWORD {0} WAS NOT FOUND IN THE \
              KEYWORD TABLE!".format(keyword_name))
        continue

    query_str = "INSERT INTO metadata (id, keyword_id, name, version, \
            last_updated, units, description, user_id) VALUES \
            (?, ?, ?, 'Restructured Data', datetime(), ?, ?, ?)"

    db.query(query_str, str(uuid.uuid4()), keyword_id, meta_name, units, desc,
             user_id)

# meta_values table
db.query('''CREATE TABLE meta_values (
    id char(16) not null primary key,
    user_id char(16) REFERENCES user(user_id),
    metadata_id char(16) REFERENCES metadata(id),
    record_id char(16) REFERENCES records(id),
    dataset_id char(16) REFERENCES datasets(id),
    value text,
    last_updated datetime);''')

# logs table
db.query('''CREATE TABLE logs (
    id char(16) NOT NULL PRIMARY KEY,
    user_id char(16),
    project_id char(16),
    dataset_id char(16),
    category_name text,
    page_name text,
    before_value text,
    after_value text,
    event_name text,
    control_type text,
    control_name text,
    last_updated datetime,
	FOREIGN KEY(user_id) REFERENCES user(user_id),
    FOREIGN KEY(project_id) REFERENCES project(id),
	FOREIGN KEY(dataset_id) REFERENCES datasets(id));''')

# commit the changes
print('yay closing!')
db.commit()
db.close()
print('closed, mofo!')
