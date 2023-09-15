from argparse import ArgumentParser

parser = ArgumentParser()

parser.add_argument('--num_samples', '-n', required=False, help='The number of samples from the CSV file')
parser.add_argument('--input', '-i', required=True, help='The input CSV file')
parser.add_argument('--output', '-o', required=False, help='The output CSV file')

args = parser.parse_args()

