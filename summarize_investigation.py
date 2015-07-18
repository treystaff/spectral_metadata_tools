# Imports
import os
execfile('/home/trey/CODE/mySqlite.py')

# Setup db connection
db = mySqlite('/home/trey/CODE/investigate.db')


# PROJECTS/REPS SUMMARY FILE:

# Remove the project reps summary file if it exists.
try:
    os.remove('/home/trey/CODE/results/project_reps.txt')
except:
    pass

projects = db.query('SELECT id, name FROM projects;')

# Setup a dictionary. The structure is dict[project name][rep name][location name] = [list of dates]
dict = {}

# Loop thru every project
for proj_id, proj_name in projects:
    # Set up a dictionary to keep track of everything.
    if proj_name not in dict.keys():
        dict[proj_name] = {}

    # Get the reps for every project
    reps = db.query('SELECT id, name, location, locations FROM reps WHERE project_id = ?', proj_id)

    # Get the dates from each rep.
    for rep_id, rep_name, location, locations in reps:
        if rep_name not in dict[proj_name].keys():
            dict[proj_name][rep_name] = {}

        # Add the rep's location.
        # location = location + ' / ' + locations
        if location not in dict[proj_name][rep_name].keys():
            dict[proj_name][rep_name][location] = []  # A list for dates

        # Get the dates associated with each rep.
        dates = db.query('SELECT date FROM dates WHERE rep_id = ?', rep_id)
        for date in dates:
            dict[proj_name][rep_name][location].append(date)


showdate = True
with open('/home/trey/CODE/results/project_reps.txt','w+') as f:
    for project in dict.keys():
        f.write('\n\n PROJECT: ' + project + '\n')
        for rep in dict[project].keys():
            f.write('\n\t REP: ' + rep + '\n')
            for loc in dict[project][rep].keys():
                f.write('\t\t LOCATION: ' + loc + '\n')
                if showdate:
                    datesStr = 'DATES: '
                    for date in dict[project][rep][loc]:

                        datesStr += str(date[0]) + '; '
                    f.write('\t\t\t' + datesStr + '\n')


# Now create the unique records files (documents unique combinations of records and subdirectories)
dict2 = {}
paths = db.query('SELECT id, path FROM datasets;')

count = 0
# Look thru each dataset and get the records and subdirs associated w/ them.
for dataset_id,path in paths:
    records = db.query('SELECT filename FROM records WHERE dataset_id = ?', dataset_id)
    subdirs = db.query('SELECT name FROM subdirs WHERE dataset_id = ?', dataset_id)

    # Index the dictionary by unique combinations of 'elements' aka subdirs and records
    elements = []
    for record in records: elements.append(str(record[0]))
    for subdir in subdirs: elements.append(str(subdir[0]))

    #print(elements)

    # Create dict entry:
    if tuple(elements) not in dict2.keys():
        dict2[tuple(elements)] = []
        count += 1
        print(count)
    else:
        print('WHOOOOOP')

    # Add the path to the dict
    dict2[tuple(elements)].append(str(path))

    #print(count)
    #print(len(dict.keys()))

# Remove the records/subdirs summary file if it exists.
try:
    os.remove('/home/trey/CODE/results/records_subdirs.txt')
except:
    pass


# Create the file and save the results.
with open('/home/trey/CODE/results/records_subdirs.txt', 'w+') as f:
    '''
    for paths in dict.keys():
        for path in paths:
            f.write(str(path[0]) + '\n')
        for element in dict[paths]:
            f.write('\t' + element + '\n')
    '''

    for elements in dict2.keys():
        for path in dict2[elements]:
            f.write(path + '\n')
        for element in set(elements):
            if element.endswith('.txt'):
                f.write('\t' + element + '\n')
            else:
                f.write('\t' + element + '/' + '\n')


