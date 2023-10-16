from argparse import ArgumentParser
import csv
import os
import random

# This script assumes the input contains lines obtained by a grep script such as:
# grep - r '#pragma\smulti_compile\|#pragma\sshader_feature'. > text.txt --include '*.shader'

from shinmodule import write_to_csv

# --------------------------------------------------------------------------------------------------------------------------------------------------------------

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

def write_keywords_dict_to_csv(outputFileName, keywords_dict):
    with open(outputFileName, 'w', newline='', encoding='utf-8') as f:

        writer = csv.writer(f)
        for i, key in enumerate(keywords_dict):
            
            writer.writerow([key])

    print(f"Data written to {outputFileName}")


# --------------------------------------------------------------------------------------------------------------------------------------------------------------

parser = ArgumentParser()

parser.add_argument('--directory', '-d', required=True, help='The directory of the shader files')
parser.add_argument('--output', '-o',required=False, default="shader.csv", help='The output file (default: shader.csv)')

args = parser.parse_args()

input_dir = args.directory

# Error checking
isError = False
if not os.path.isdir(input_dir):
    print(f"Invalid input dir: {input_dir}")
    isError = True


if isError:
    exit()


import os
import subprocess

proc = subprocess.run(["grep", "-r", "'#pragma\smulti_compile\|#pragma\sshader_feature'", input_dir, "--include", "'*.shader'"],
                      capture_output=True, text=True)
grep_result=proc.stdout
lines = grep_result.splitlines()
for line in lines:
    print(line)


