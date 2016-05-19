import logging
import re
import os
import traceback
from reorganize_data import *


def find_datafiles(years, processing_dir='/media/sf_tmp/processing_lists/', base_dir = '/media/sf_Field-Data/'):
    """
    Need to just find and save filenames/paths of files we want.
    """
    # Define some ~constants~ (server changes may result in 'outdated' constants.
    if not os.path.exists(base_dir):
        raise RuntimeError('Base data directory not found!')

    # First make sure the save directory exists and create it if not.
    if not os.path.exists(processing_dir):
        os.mkdir(processing_dir)

    # Define some regex
    upPattern = re.compile('.*Upwelling.*\.txt')
    outPattern = re.compile('.*Outgoing.*\.txt')

    # We'll process each year individually since some years represent significant breaks in file structure
    for year in years:
        year = str(year)

        # Ensure the year exists in the base directory
        search_dir = os.path.join(base_dir, year)
        if not os.path.exists(search_dir):
            warnings.warn('A data directory for year {0} was not found!'.format(year))
            continue  # Move on to the next year if a directory doesn't exist for this one

        # Construct the path to the output master list.
        processing_year_dir = os.path.join(processing_dir, year)
        if not os.path.exists(processing_year_dir):
            os.mkdir(processing_year_dir)
        filename = os.path.join(processing_year_dir, 'master_list.txt')

        # We are going to create or overwrite the <processing_dir>/year/master_list.txt
        with open(filename, 'w') as savefile:
            for root, dirs, files in os.walk(search_dir):
                # Ensure it's a CSP related directory, that it's not a renamed one, or a duplicate dir.
                # (below basically just ensures the exclusion of directories we do not want to process.)
                if '/'+str(year)+'/'+str(year) + '/' not in root and 'renamed' not in root.lower() and\
                'combined' not in root.lower() and 'lab' not in root.lower() and 'test' not in root.lower()\
                    and 'smallplots' not in root.lower() and 'bad' not in root.lower() and 'old process' not in root.lower()\
                        and ('csp' in root.lower() or 'mead' in root.lower() or 'BLMV' in root):
                    # Only save directories if it contains upwelling data.
                    if [f for f in files if upPattern.match(f) or outPattern.match(f)]:
                        savefile.write(root + '\n')

def test_split():
    import shutil
    data_dir = '/media/sf_tmp/exdata/'
    out_dir = '/media/sf_tmp/restruct_test/'
    shutil.rmtree(out_dir)

    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    logging.basicConfig(filename='/media/sf_tmp/restruct_test/app_log.txt',
                        format='%(levelname)s: %(message)s', level=logging.DEBUG)

    logging.basicConfig(filename='/media/sf_tmp/restruct_test/error_log.txt',
                        format='%(levelname)s: %(message)s', level=logging.ERROR)

    try:
        cal_idxs, loc_idxs, loc_meta, cal_meta, key_dict, standard_project_names = process_upwelling(data_dir, out_dir)
        process_otherfiles(data_dir, cal_meta, loc_meta)
        process_downwelling(data_dir, cal_idxs, loc_idxs, loc_meta, cal_meta, key_dict, standard_project_names)
        process_reflectance(data_dir, cal_idxs, loc_idxs, loc_meta, cal_meta, key_dict, standard_project_names)
    finally:
        logging.shutdown()


def process_years(years, processing_dir='/media/sf_tmp/processing_lists/', process_errors=False):
    out_dir = '/media/sf_tmp/restruct2/'
    if not os.path.exists(processing_dir):
        raise RuntimeError('Processing directory {0} not found!'.format(processing_dir))
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    logging.basicConfig(filename=os.path.join(out_dir,'app_log.txt'),
                        format='%(levelname)s: %(message)s',level=logging.DEBUG)
    logging.basicConfig(filename=os.path.join(out_dir,'error_log.txt'),
                        format='%(levelname)s: %(message)s',level=logging.ERROR)

    for year in years:
        year = str(year)
        logging.info('Processing year {0}. Started {1}'.format(year, time.strftime('%d/%m/%Y at %H:%M:%S')))

        if process_errors:
            master_list_file = os.path.join(processing_dir, year, 'error_list.txt')
        else:
            master_list_file = os.path.join(processing_dir, year, 'master_list.txt')
        if not os.path.exists(master_list_file):
            warnings.warn('A filepaths file was not found for {0}'.format(year))
            continue
        with open(master_list_file, 'r') as datadirs_file:
            # Process each dir for that year.
            data_dirs = datadirs_file.readlines()

        err_list = []  # maintain a list of directories that failed processing.
        for data_dir in data_dirs:
            data_dir = data_dir.strip('\n')
            # Now process the data
            if not os.path.isdir(data_dir):
                continue
            try:
                cal_idxs, loc_idxs, loc_meta, cal_meta, key_dict, standard_project_names = process_upwelling(
                    data_dir, out_dir)
                process_otherfiles(data_dir, cal_meta, loc_meta)
                if cal_idxs is None:
                    print('Problem with {0} !'.format(data_dir))
                else:
                    process_downwelling(data_dir, cal_idxs, loc_idxs, loc_meta, cal_meta, key_dict,
                                        standard_project_names)
                    process_reflectance(data_dir, cal_idxs, loc_idxs, loc_meta, cal_meta, key_dict,
                                        standard_project_names)

                # Save completed files to a 'completed files list'
                with open(os.path.join(processing_dir, year, 'completed.txt'), 'a') as completed_file:
                    completed_file.write(data_dir + '\n')

            except Exception, e:
                # Log that the error occured
                problem_str = 'PROBLEM PROCESSING {0}! Exception:\n {1} \n'\
                              '-------------------------------------------------------------'\
                              '\n'.format(data_dir, traceback.format_exc())

                logging.error(problem_str)
                warnings.warn(problem_str)

                err_list.append(data_dir)

                # Cleanup
                # Remove all the location directories
                for loc in loc_meta.keys():
                    del_out_dir = loc_meta[loc]['out_dir']
                    print('Cleaning up {0}'.format(del_out_dir))
                    if os.path.isdir(del_out_dir):
                        shutil.rmtree(del_out_dir)

                # Remove the cal dir
                del_cal_dir = cal_meta['out_dir']
                if os.path.isdir(del_cal_dir):
                    shutil.rmtree(del_cal_dir)

                # Now back up to the 'base' directory.
                cal_dir_list = split_path(del_cal_dir)
                del_dir = '/'
                for i in range(len(cal_dir_list) - 1):
                    del_dir = os.path.join(del_dir, cal_dir_list[i])

                # If there's nothing left in the 'base' directory, remove it.
                if os.path.isdir(del_dir) and not os.listdir(del_dir):
                    shutil.rmtree(del_dir)

        # Save the offending directory to a file
        error_file_path = os.path.join(processing_dir, year, 'error_list.txt')
        if err_list:
            # We'll re-write this file each time, to ensure that it contains the most recent errors.
            with open(os.path.join(error_file_path, year, 'error_list.txt'), 'w') as error_file:
                for err_dir in err_list:
                    error_file.write(err_dir + '\n')
        elif os.path.isfile(error_file_path):
            os.remove(error_file_path)

    logging.shutdown()

if __name__ == '__main__':
    """j
    find_datafiles([2001], base_dir='/media/sf_O_DRIVE/reprocess_2001/')
    """
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action="store_true")
    parser.add_argument('--years', nargs='+', type=int, 
                        default=range(2002, 2010))
    parser.add_argument('--errors', action="store_true", default=False)

    args = parser.parse_args()
    if args.test:
        test_split()

    else:
        process_years(args.years, process_errors=args.errors)
