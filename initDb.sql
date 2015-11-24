BEGIN;

--Users table
/*
CREATE TABLE user (
	user_id integer primary key,
	f_name text,
	l_name text,
	organization text,
	profession text,
	psswrd text,
	email text);
*/


/*
--Categories of metadata keywords.
CREATE TABLE categories (
    id INTEGER primary key, 
    name text,
    description text);
*/

INSERT INTO categories (id, name, description) VALUES (1,'Other','Other');
INSERT INTO categories (id, name, description) VALUES (2,'Illumination Geometry','Solar angles');
INSERT INTO categories (id, name, description) VALUES (3,'Viewing Geometry','Sensor angles and FOV');
INSERT INTO categories (id, name, description) VALUES (4,'Instruments','Information about instruments used');
INSERT INTO categories (id, name, description) VALUES (5,'Scan Data','Information about instruments used');
INSERT INTO categories (id, name, description) VALUES (6,'Calibration','Information on how calibration was performed');
INSERT INTO categories (id, name, description) VALUES (7,'Location','Location information (lat, lon, area, etc.)');
INSERT INTO categories (id, name, description) VALUES (8,'Target','Target information (vegetation, etc)');
INSERT INTO categories (id, name, description) VALUES (9,'Auxiliary','Metadata related to auxilliary sensors/data');

--Keywords used by the Metadata Manager Application for searching/organizing/etc.
-- critical metadata.
/*
CREATE TABLE keywords (
    id INTEGER primary key, 
    category_id REFERENCES categories(id),
    name text,
    compulsory boolean);
*/

INSERT INTO keywords (category_id, name, compulsory) VALUES (1, 'Other', 0); 
INSERT INTO keywords (category_id, name, compulsory) VALUES (4, 'Upwelling Instrument Name', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (4, 'Upwelling Instrument Serial Number', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (4, 'Upwelling Instrument FOV', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (4, 'Upwelling Instrument Max Wavelength', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (4, 'Upwelling Instrument Min Wavelength', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (4, 'Downwelling Instrument Name', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (4, 'Downwelling Instrument Serial Number', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (4, 'Downwelling Instrument FOV', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (4, 'Downwelling Instrument Max Wavelength', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (4, 'Downwelling Instrument Min Wavelength', 0);
--INSERT INTO keywords (category_id, name, compulsory) VALUES (4, 'Scans Averaged', 0); --Number of scans averaged
INSERT INTO keywords (category_id, name, compulsory) VALUES (4, 'Acquisition Software', 0); --Software used to acquire the data
INSERT INTO keywords (category_id, name, compulsory) VALUES (4, 'Software Version', 0);
--INSERT INTO keywords (category_id, name, compulsory) VALUES (4, 'Averaging', 0); --The type of averaging (mean or median)
INSERT INTO keywords (category_id, name, compulsory) VALUES (6, 'Calibration Panel', 0); --Name of panel used for calibration
INSERT INTO keywords (category_id, name, compulsory) VALUES (6, 'Calibration Mode', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (4, 'Upwelling Instrument Channels', 0); --# of pixels/bands for the instrument
INSERT INTO keywords (category_id, name, compulsory) VALUES (4, 'Downwelling Instrument Channels', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (5, 'Cal Scans Count', 0); --Number of spectra
INSERT INTO keywords (category_id, name, compulsory) VALUES (5, 'Data Scans Count', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (7, 'Minimum Latitude', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (7, 'Maximum Longitude', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (7, 'Minimum Longitude', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (2, 'Illumination Source', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (2, 'Minimum Solar Azimuth', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (2, 'Maximum Solar Azimuth', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (2, 'Minimum Solar Elevation', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (2, 'Maximum Solar Elevation', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (2, 'Minimum Solar Zenith', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (2, 'Maximum Solar Zenith', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (7, 'Minimum Altitude', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (7, 'Maximum Altitude', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (7, 'Maximum Latitude', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (8, 'Vegetation', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (7, 'State', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (7, 'Place Name', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (7, 'County', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (7, 'Country', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (9, 'Minimum Temperature 1', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (9, 'Maximum Temperature 1', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (9, 'Minimum Temperature 2', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (9, 'Maximum Temperature 2', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (9, 'Minimum Pyranometer', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (9, 'Maximum Pyranometer', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (9, 'Minimum Quantum Sensor', 0);
INSERT INTO keywords (category_id, name, compulsory) VALUES (9, 'Maximum Quantum Sensor', 0);

--Project information. Every dataset belongs to a project.
/*
CREATE TABLE projects (
    id integer primary key,
    user_id REFERENCES user(user_id),
    name text,
    abstract text,
    sponsor text,
    organization text,
    contact text);

--Defines a set of related data. Data taken at the same time and day at the same location. 
-- Every dataset contains record(s) (upwelling,downwelling, reflectance,etc.). 
CREATE TABLE datasets (
    id integer primary key, 
    project_id REFERENCES projects(id),
    date text,
    start_time text,
    stop_time text,
    lat text, 
    lon text);

--Every dataset is composed of records (data files; e.g., reflectance.txt)
CREATE TABLE records (
    id INTEGER primary key,
    dataset_id REFERENCES datasets(id),
    path text, 
    filename text);

--Metadata table links keywords to data file attributes. 
CREATE TABLE metadata (
    id integer primary key, 
    keyword_id REFERENCES keywords(id),
    name text,
    version text,
    reserved text);
*/
--Restructured Data metadata entries
INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Illumination Source'),'Illumination Source','Restructured Data'); --Illumination Source

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Other'),'Legacy Path','Restructured Data'); --Legacy path

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Other'),'Dataset ID','Restructured Data'); --Dataset ID

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Maximum Latitude'),'Max Latitude','Restructured Data'); --Max lat entry

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Minimum Latitude'),'Min Latitude','Restructured Data'); --Min lat entry

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Maximum Longitude'),'Max Longitude','Restructured Data'); --Max lon entry

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Minimum Longitude'),'Min Longitude','Restructured Data'); --Min lon entry

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Acquisition Software'), 'Acquisition Software', 'Restructured Data');

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Software Version'), 'Software Version', 'Restructured Data');

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Minimum Solar Azimuth'), 'Min Solar Azimuth', 'Restructured Data'); --Entry for minimum solar azimuth.

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Maximum Solar Azimuth'), 'Max Solar Azimuth', 'Restructured Data'); --Max solar azimuth

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Minimum Solar Elevation'), 'Min Solar Elevation', 'Restructured Data'); --Min solar elevation

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Maximum Solar Elevation'), 'Max Solar Elevation', 'Restructured Data'); --Max solar elevation

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Minimum Solar Zenith'), 'Min Solar Zenith', 'Restructured Data'); --Min solar zenith

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Maximum Solar Zenith'), 'Max Solar Zenith', 'Restructured Data'); --Max solar zenith

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Upwelling Instrument Name'),'Upwelling Instrument Name','Restructured Data'); -- Upwelling Instrument's name

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Upwelling Instrument Serial Number'),'Upwelling Instrument Serial Number','Restructured Data');

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Upwelling Instrument FOV'),'Upwelling Instrument FOV','Restructured Data');

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Upwelling Instrument Maximum Wavelength'),'Upwelling Instrument Max Wavelength','Restructured Data');

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Upwelling Instrument Minimum Wavelength'),'Upwelling Instrument Min Wavelength','Restructured Data');

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Downwelling Instrument Name'),'Downwelling Instrument Name','Restructured Data'); -- Upwelling Instrument's name

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Downwelling Instrument Serial Number'),'Downwelling Instrument Serial Number','Restructured Data');

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Downwelling Instrument FOV'),'Downwelling Instrument FOV','Restructured Data');

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Downwelling Instrument Maximum Wavelength'),'Downwelling Instrument Max Wavelength','Restructured Data');

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Downwelling Instrument Minimum Wavelength'),'Downwelling Instrument Min Wavelength','Restructured Data');

--INSERT INTO metadata (keyword_id, name, version) VALUES (13,4,'Averaged Scans','Restructured Data'); --The number of scans averaged per one output result

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Minimum Altitude'),'Min Altitude','Restructured Data'); --Min Altitude

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Maximum Altitude'),'Max Altitude','Restructured Data'); --Max Altitude

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Calibration Mode'),'Calibration Mode','Restructured Data'); --Scan averaging (mean or median)

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Calibration Panel'),'Calibration Panel','Restructured Data'); --Processing panel

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Calibration Scans Count'),'Cal Scans Count','Restructured Data'); --Number of scans that are in the dataset.

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Data Scans Count'),'Data Scans Count','Restructured Data');

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Upwelling Instrument Channels'),'Upwelling Instrument Channels','Restructured Data'); --Number of channels/pixels/bands

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Downwelling Instrument Channels'),'Downwelling Instrument Channels','Restructured Data');

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Vegetation'),'Target','Restructured Data'); --vegetation

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'State'),'State','Restructured Data'); --state

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Place Name'),'Location','Restructured Data'); --place name

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'County'),'County','Restructured Data'); --County

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Country'),'Country','Restructured Data'); --Country

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Minimum Temperature 1'),'Min Temperature 1','Restructured Data'); --Min Temp 1

INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Maximum Temperature 1'),'Max Temperature 1','Restructured Data'); -- Max Temp 1
INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Minimum Temperature 2'),'Min Temperature 2','Restructured Data'); --Min Temp 2
INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Maximum Temperature 2'),'Max Temperature 2','Restructured Data'); --Max Temp 2
INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Minimum Pyronometer'),'Min Pyronometer','Restructured Data'); --min pyro
INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Maximum Pyronometer'),'Max Pyronometer','Restructured Data'); --max pyro
INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Minimum Quantum Sensor'),'Min Quantum Sensor','Restructured Data'); --min qs
INSERT INTO metadata (keyword_id, name, version) VALUES
    ((SELECT id FROM keywords WHERE name = 'Maximum Quantum Sensor'),'Max Quantum Sensor' ,'Restructured Data'); --max qs

--Contains the actual data file attribute values that are linked to keywords.
/*
CREATE TABLE meta_values (
    id integer primary key, 
    metadata_id REFERENCES metadata(id),
    record_id REFERENCES records(id),
    dataset_id REFERENCES datasets(id),
    value text);
*/


COMMIT;  


    
    
    