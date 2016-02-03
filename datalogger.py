"""Functions related to dealing w/ datalogger entries"""
from utility import mean


def split_datalogger_entry(datalogger_str):
    """
    Splits a datalogger entry into its constituent parts.

    Parameters:
        datalogger_str - String. A datalogger entry

    Returns:
        split_entries - A list of individual datalogger values
    """
    return [s[2:] for s in datalogger_str.split(',')]


def split_datalogger_entries(datalogger_strs):
    """
    Splits a list of datalogger entries into their constituent parts.
    Covinience function for splitting many datalogger entries.

    Parameters:
        datalogger_strs - List of strings.

    Returns:
        split_entries - A list of lists containing datalogger values.
    """
    # TODO: maybe just remove split_datalogger_entry and replace with this.

    return map(split_datalogger_entry, datalogger_strs)


def unzip_dlogger_entries(split_entries, num_entries):
    '''

    Unzips split datalogger entries. Replaces zip(*split_datalogger_entries(data_datlogger))
    to support missing datalogger entries (e.g., '')
    '''
    for idx, entry in enumerate(split_entries):
        if entry == ['']:
            split_entries[idx] = ['-9999'] * num_entries

    return zip(*split_entries)


def datalogger_to_dict(data_dict, key_dict, data_dir):
    """
    Removes the datalogger entry from cal and data dicts, replacing with new fields for each logged value.

    Parameters:
        cal_dict - Dictionary of CALMIT calibration data
        data_dict - Dicitonary of CALMIT scandata (not cal)
        key_dict - A key dictionary created via create_key_dict()

    Returns:
        data_dict, key_dict - Modified dictionaries.
    """
    data_datalogger = data_dict[key_dict['Data Logger']]
    num_entries = None
    for data_str in data_datalogger:
        split_entry = split_datalogger_entry(data_str)
        if data_str != '':
            num_entries = len(split_entry)
            break

    # If no entries were found, just remove the datalogger field alltogether and move on
    if num_entries is None:
        del data_dict[key_dict['Data Logger']]
        return data_dict

    # Split out all of the data from the datalogger strings. Each var is it's own list.
    data_entries = unzip_dlogger_entries(split_datalogger_entries(data_datalogger), num_entries=num_entries)

    # TODO rename temperature 1 and 2.
    entry_names = ['Battery Voltage', 'Temperature 1', 'Temperature 2']
    if num_entries == 4:
        entry_names.append('Pyronometer')
    elif num_entries == 5:
        # Either Pyronometer then Quantum Sensor or None then Pyronometer.
        if all(float(val) < 0 for val in data_entries[3]) and all(float(val) < 0 for val in data_entries[4]):
            entry_names.extend([None, 'Pyronometer'])
            entry_names[2] = None  # Temperature 2 also becomes None.
        else:
            if mean(data_entries[3]) > mean(data_entries[4]):
                err_str = "\n WARNING: PYRONOMETER VALUES FOUND HIGHER THAN QUANTUM SENSOR. MAYBE " \
                          "UNKNOWN DATALOGGER TYPE {0}. Proceeding anyway. \n".format(data_dir)
                print(err_str)

            entry_names.extend(['Pyronometer', 'Quantum Sensor'])

    elif num_entries == 6 and all(float(val) < 0 for val in data_entries[5]):  # Last value is -99999
        # battery volt, temp1, temp2, Pyronometer, Quantum Sensor, None.
        entry_names.extend(['Pyronometer', 'Quantum Sensor', None])

    elif num_entries == 3:
        # Just battery voltage, temp1, temp2.
        pass

    else:
        # TODO Implement other datalogger types (if there are any others...)
        import pdb
        pdb.set_trace()
        raise NotImplementedError('Unrecognized Datalogger string. Sorry!')

    # Create an entry in the data and cal dicts for the split datalogger data.
    for name in entry_names:
        if name is not None:
            key_dict[name] = name  # Add this to the key dict, for consistency (other functs rely on it).
            data_dict[name] = []

    # Add the data to the data dict
    for name, values in zip(entry_names, data_entries):
        if name is not None:
            # Check for a list of nodata.
            unique_vals = [val for val in values if val != '']
            unique_vals = set(values)
            # Datalogger should not have negative values.
            if all(float(val) < 0 for val in unique_vals):
                # Don't add to the data_dict.
                pass
            else:
                data_dict[name] = []
                for value in values:
                    # We assume DL values less than 0 are bad/nodata values.
                    if value == '':
                        data_dict[name].append('-9999')
                    elif float(value) < 0:
                        # TODO standardize nodata value. For now, use -9999
                        data_dict[name].append('-9999')
                    elif name in {'Temperature 1', 'Temperature 2'} and float(value) > 250:
                        data_dict[name].append('-9999')
                    else:
                        data_dict[name].append(value)

    del data_dict[key_dict['Data Logger']]
    return data_dict

