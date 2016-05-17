import logging
import os
import traceback
from reorganize_data import *


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
                    shutil.rmtree(del_out_dir)

                # Remove the cal dir
                del_cal_dir = cal_meta['out_dir']
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
        if err_list:
            # We'll re-write this file each time, to ensure that it contains the most recent errors.
            with open(os.path.join(processing_dir, year, 'error_list.txt'), 'w') as error_file:
                error_file.write(data_dir + '\n')

    logging.shutdown()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action="store_true")
    parser.add_argument('--years', nargs='+', type=int, 
                        default=range(2001, 2010))

    args = parser.parse_args()
    if args.test:
        test_split()

    else:
       process_years(args.years) 
