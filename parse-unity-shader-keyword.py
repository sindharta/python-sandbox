from argparse import ArgumentParser
import csv
import os
import random

# This script assumes the input contains lines obtained by a grep script such as:
# grep - r '#pragma\smulti_compile\|#pragma\sshader_feature'. > text.txt --include '*.shader'

from shinmodule import write_to_csv

def isSpecialPragmaType(token):
    if (token == "multi_compile"):
        return False

    if (token == "multi_compile_fragment"):
        return False

    if (token == "multi_compile_local_fragment"):
        return False

    if (token == "multi_compile_local"):
        return False

    if (token == "multi_compile_vertex"):
        return False

    if (token == "shader_feature"):
        return False

    if (token == "shader_feature_local"):
        return False

    if (token == "shader_feature_local_fragment"):
        return False

    return True


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

special_pragma_types = set()

# type  => keyword => (context)
keywords_dict = {}


with open(input_filename, encoding='utf-8') as f:
    for line in f:
        tokens = line.split()

        pragma_token = tokens[1]
        if pragma_token.startswith('//'):
            continue

        pragma_type = tokens[2]

        if isSpecialPragmaType(pragma_type):
            special_pragma_types.add(pragma_type)
            continue

        numTokens = len(tokens)

        keyword_start_index = 3
        keyword_tokens_in_line = " ".join(tokens[keyword_start_index:])
        for index, keyword in enumerate(tokens[keyword_start_index:], keyword_start_index):
            if keyword == "_" or keyword == "__" :
                continue

#            print(keyword, index, keyword_tokens_in_line)

            if not pragma_type in keywords_dict:
                keywords_dict[pragma_type] = dict()

            if not keyword in keywords_dict[pragma_type]:
                keywords_dict[pragma_type][keyword] = set()

            keywords_dict[pragma_type][keyword].add(keyword_tokens_in_line)

print(keywords_dict)

#for c in special_pragma_types:
#    print(c)



