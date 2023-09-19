from argparse import ArgumentParser
import csv
import os
import random

parser = ArgumentParser()

parser.add_argument('--num_rows', '-n', required=False, default=5, help='The number of rows from the CSV file (default: 5)')
parser.add_argument('--input', '-i', required=True, help='The input CSV file')
parser.add_argument('--output', '-o', required=False, default="output.csv", help='The output CSV file (default: output.csv)')
parser.add_argument('--include_header_row', '-r', required=False, default=False, help='Include the top header row (default: False)')

args = parser.parse_args()

num_rows = args.num_rows
input_filename = args.input

# print(os.getcwd())

# Error checking
isError = False
if not os.path.isfile(input_filename):
    print(f"Invalid input file: {input_filename}")
    isError = True
    exit()

if num_rows <= 0:
    print(f"Invalid number of rows: {num_rows}")
    isError = True

if isError:
    exit()

# First read to know the number of lines
header = ""
num_lines = 0
with open(input_filename) as f:
    for line in f:
        if line.strip() != "":
            num_lines +=1
        if (num_lines == 1 & args.include_header_row):
            header = line

num_lines = num_lines - 1 if not args.include_header_row else num_lines
num_rows = min(num_lines, num_rows)

# Calculate random numbers
chosen_rows = set()
start_line = 1 if args.include_header_row else 0
while (len(chosen_rows) < num_rows):
    candidate_row = random.randrange(num_lines) + start_line
    chosen_rows.add(candidate_row)

# Second read to get the rows
output = list()
with open(input_filename) as f:
    reader = csv.reader(f)
    for row_number, row in enumerate(reader):
        if row_number in chosen_rows:
            output.append(row)


with open('output.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    for estate in desiredRealEstates:
        writer.writerow([estate['place name'], estate['postal code'], estate['latitude'], estate['longitude']])


print(output)
print(len(output))

#with open(input_filename,'r') as f:
#    reader = csv.reader(f, delimiter='\t')
#    print(type(reader))
#    next(reader)
#    for row in reader:
#        print(row)


