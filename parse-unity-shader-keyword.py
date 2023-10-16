from argparse import ArgumentParser
import csv
import os
import random

from shinmodule import write_to_csv


# --------------------------------------------------------------------------------------------------------------------------------------------------------------

parser = ArgumentParser()

# parser.add_argument('--percentage', '-p', required=False, default=0.2, help='The percentage of rows for test data (default: 0.2)')
parser.add_argument('--input', '-i', required=True, help='The input CSV file')
# parser.add_argument('--has_header_row', '-r', required=False, default=True, help='Specifies if the CSV has a header row or not (default: True)')
# parser.add_argument('--output_train', required=False, default="train.csv", help='The output train CSV file (default: train.csv)')
# parser.add_argument('--output_test', required=False, default="test.csv", help='The output test CSV file (default: test.csv)')

args = parser.parse_args()

input_filename = args.input

# print(os.getcwd())

# Error checking
isError = False
if not os.path.isfile(input_filename):
    print(f"Invalid input file: {input_filename}")
    isError = True


if isError:
    exit()

with open(input_filename, encoding='utf-8') as f:
    for line in f:
        print(line)
