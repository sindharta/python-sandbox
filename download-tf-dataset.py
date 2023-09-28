#Usage example: python download-tf-dataset.py --dataset_name imdb_reviews

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

    for sent, label in tf_data:
        sentences.append(str(sent.numpy().decode('utf8')))
        labels.append(label.numpy())

    return (sentences, labels)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------


parser = ArgumentParser()
parser.add_argument('--dataset_name', '-d', required=True, help='The name of the dataset')
args = parser.parse_args()


dataset_name = args.dataset_name
data, info = tfds.load(dataset_name, with_info=True, as_supervised=True)



(train_sentences, train_labels) = convert_tf_data_to_nparray(data['train'])

#print(train_sentences[0:1])
#print(train_labels[0:1])

train_data = np.vstack((train_sentences, train_labels)).T

print(train_data[0:1])

#print(np.concatenate([train_sentences, train_labels]))

#write
with open("info.json", 'w', newline='', encoding='utf-8') as f:
    f.write(info.as_json)

write_to_csv("train.csv",train_data)
