import os
import csv


def get_root_path():
    root_path = os.path.dirname(os.path.abspath(__file__)).replace('/physicians/physicians/spiders', '')
    return root_path

def result_path(spider_type, name):

    out_path = None
    if spider_type == 'half1':
        out_path = get_root_path() + '/OUTPUT/' + name + '/'
    elif spider_type == 'half2':
        out_path = get_root_path() + '/half2/OUTPUT/' + name + '/'

    if not os.path.exists(out_path):
        os.makedirs(out_path)

    return out_path


def get_chrome_driver_path():
    path = get_root_path() + '/chromedriver'
    return path


def get_firefox_driver_path():
    path = get_root_path() + '/geckodriver'
    return path


def get_phantomjs_path():
    path = get_root_path() + '/phantomjs'
    return path


def csv_to_dict():
    file_path = get_root_path() + '/csv_json/postalcode.csv'
    reader = csv.reader(open(file_path))

    result = {}
    for row in reader:
        key = row[0]
        if key in result:
            # implement your duplicate row handling here
            pass
        result[key] = row[1:]
    return result


def clean_csv(path):
    old_physician_csv = path + 'temp_physicians.csv'
    physician_csv = path + 'physicians.csv'

    with open(old_physician_csv) as old_file, open(physician_csv, 'w') as new_file:
        writer = csv.writer(new_file)
        for row in csv.reader(old_file):
            if any(field.strip() for field in row):
                writer.writerow(row)

    old_specialities_csv = path + 'temp_specialities.csv'
    specialities_csv = path + 'specialities.csv'

    with open(old_specialities_csv) as old_file, open(specialities_csv, 'w') as new_file:
        writer = csv.writer(new_file)
        for row in csv.reader(old_file):
            if any(field.strip() for field in row):
                writer.writerow(row)

    old_locations_csv = path + 'temp_locations.csv'
    locations_csv = path + 'locations.csv'

    with open(old_locations_csv) as old_file, open(locations_csv, 'w') as new_file:
        writer = csv.writer(new_file)
        for row in csv.reader(old_file):
            if any(field.strip() for field in row):
                writer.writerow(row)

    os.remove(old_physician_csv)
    os.remove(old_specialities_csv)
    os.remove(old_locations_csv)
    