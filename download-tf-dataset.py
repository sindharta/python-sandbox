#Usage example: python download-tf-dataset.py --dataset_name imdb_reviews --output_info imdb_info.json

from argparse import ArgumentParser
import csv
import numpy as np

import tensorflow as tf
import tensorflow_datasets as tfds

# [Note-sin: 2023-9-28]
# if the programs fails to load "resource" when importing tensorflow_datasets on Windows, then we may have to apply this patch
# https://github.com/tensorflow/datasets/commit/82215c7cf4b3e6df706a72c9b7ad8cede09f4d84

def write_to_csv(outputFileName, dataList, header = ""):
    with open(outputFileName, 'w', newline='', encoding='utf-8') as f:
        if (len(header) > 0):
            f.write(f'{header}')

        writer = csv.writer(f)
        for d in dataList:
            writer.writerow(d)
    print(f"Data written to {outputFileName}")

def convert_tf_data_to_nparray(tf_data):
    sentences = []
    labels = []

    for sentence, label in tf_data:
        sentences.append(str(sentence.numpy().decode('utf8')))
        labels.append(label.numpy())

    return (sentences, labels)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------


parser = ArgumentParser()
parser.add_argument('--dataset_name', '-d', required=True, help='The name of the dataset')
parser.add_argument('--output_prefix', '-p' , required=False, default="output_", help='The prefix of the CSV outputs (default: output_)')
parser.add_argument('--output_info', '-i' , required=False, default="info.json", help='The path of the dataset info (default: info.json)')

args = parser.parse_args()


# load dataset
dataset_name = args.dataset_name
data, info = tfds.load(dataset_name, with_info=True, as_supervised=True)

for k,v in data.items():
    (sentences, labels) = convert_tf_data_to_nparray(v)

    # Combine with label into 2D array
    csv_data = np.vstack((sentences, labels)).T

    #write data
    output_file_name = args.output_prefix + k + ".csv"
    write_to_csv(output_file_name, csv_data)

#write info
with open(args.output_info, 'w', newline='', encoding='utf-8') as f:
    f.write(info.as_json)
    print(f"Info written to {args.output_info}")


