from argparse import ArgumentParser
import csv
import os
import random

from shinmodule import write_to_csv


# --------------------------------------------------------------------------------------------------------------------------------------------------------------

parser = ArgumentParser()

parser.add_argument('--percentage', '-p', required=False, default=0.2, help='The percentage of rows for test data (default: 0.2)')
parser.add_argument('--input', '-i', required=True, help='The input CSV file')
parser.add_argument('--has_header_row', '-r', required=False, default=True, help='Specifies if the CSV has a header row or not (default: True)')
parser.add_argument('--output_train', required=False, default="train.csv", help='The output train CSV file (default: train.csv)')
parser.add_argument('--output_test', required=False, default="test.csv", help='The output test CSV file (default: test.csv)')

args = parser.parse_args()

input_filename = args.input

# print(os.getcwd())

# Error checking
isError = False
if not os.path.isfile(input_filename):
    print(f"Invalid input file: {input_filename}")
    isError = True

test_percentage = 0
try:
    test_percentage = float(args.percentage)
    if test_percentage < 0 or test_percentage > 1:
       print(f"Percentage must be between 0 and 1: {test_percentage}")
       isError = True
except Exception as e:
    print(f"Exception {e} for the percentage: {args.percentage}")
    isError = True


if isError:
    exit()

has_header_row = args.has_header_row

# First read to know the number of lines
header = ""
num_lines = 0
with open(input_filename, encoding='utf-8') as f:
    for line in f:
        if line.strip() != "":
            num_lines +=1
        if (num_lines == 1 and args.has_header_row):
            header = line

num_lines = num_lines - 1 if not has_header_row else num_lines
num_test_data = min(num_lines, int(test_percentage * num_lines))

# Calculate random numbers
test_data_rows = set()
start_line = 1 if has_header_row else 0
while (len(test_data_rows) < num_test_data):
    candidate_row = random.randrange(num_lines) + start_line
    test_data_rows.add(candidate_row)

# Second read to get the rows
train_data = list()
test_data = list()
with open(input_filename, encoding='utf-8') as f:
    reader = csv.reader(f)
    if has_header_row:
        next(reader)
    for row_number, row in enumerate(reader):
        if row_number in test_data_rows:
            test_data.append(row)
        else:
            train_data.append(row)

# Write to train test file
write_to_csv(args.output_train, train_data, header)
write_to_csv(args.output_test, test_data, header)

