"""
This is a one shot script used by @vermeer on Dec 2017
to extract and update the latest OGR ROME mapping.

This script is not fully industrialized since it is not sure it will be
used again, as maybe next time the incoming data format might be different.

References:
https://trello.com/c/hkiXLqrx/985-mise-%C3%A0-jour-mapping-ogr-rome
https://www.data.gouv.fr/fr/datasets/repertoire-operationnel-des-metiers-et-des-emplois-rome/#_
https://docs.google.com/spreadsheets/d/1lXm0f_TSLy-QhvdMSqCd5sI7ud6ybIRIBZAe0xF-IF8/edit#gid=296398022
"""
import csv


def write_csv_for_rome_labels(rome_labels):
    with open('rome_labels.csv', 'wb') as f:
        f.write("rome_id|rome_label\n")
        for rome_id in sorted(rome_labels.keys()):
            f.write("%s|%s\n" % (rome_id, rome_labels[rome_id]))


def write_csv_for_ogr_labels(ogr_labels):
    with open('ogr_labels.csv', 'wb') as f:
        f.write("ogr_id|ogr_label\r\n")
        for ogr_id in sorted(ogr_labels.keys()):
            f.write("%s|%s\r\n" % (ogr_id, ogr_labels[ogr_id]))


def write_csv_for_ogr_rome_mapping(ogr_rome_mapping):
    with open('ogr_rome_mapping.csv', 'wb') as f:
        f.write("ogr_id|rome_id\n")
        for ogr_id in sorted(ogr_rome_mapping.keys()):
            f.write("%s|%s\n" % (ogr_id, ogr_rome_mapping[ogr_id]))


def extract_ogr_rome_data():
    rome_labels = {}
    ogr_labels = {}
    ogr_rome_mapping = {}
    with open('ogr_rome_mapping_raw.csv', 'rb') as f:
        rows = csv.reader(f, delimiter=',', quotechar='"')
        for row in rows:
            if len(row) != 5:
                raise ValueError('this row does not have 5 fields')
            rome_id = row[0] + row[1] + row[2]
            ogr_id = row[4]
            if len(rome_id) == 5:
                if ogr_id == '':
                    # this line defines a rome label
                    rome_label = row[3]
                    if rome_id in rome_labels:
                        raise ValueError('unexpected duplicate rome label')
                    rome_labels[rome_id] = rome_label
                else:
                    # this line defines an ogr plus its mapping to a rome
                    ogr_label = row[3]
                    if ogr_id in ogr_labels:
                        raise ValueError('unexpected duplicate ogr label')
                    ogr_labels[ogr_id] = ogr_label
                    if ogr_id in ogr_rome_mapping:
                        raise ValueError('unexpected duplicate ogr rome mapping')
                    else:
                        ogr_rome_mapping[ogr_id] = rome_id
    
    write_csv_for_rome_labels(rome_labels)
    write_csv_for_ogr_labels(ogr_labels)
    write_csv_for_ogr_rome_mapping(ogr_rome_mapping)


if __name__ == '__main__':
    extract_ogr_rome_data()
