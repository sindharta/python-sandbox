from argparse import ArgumentParser
import csv
import os
import subprocess

# --------------------------------------------------------------------------------------------------------------------------------------------------------------

def is_special_pragma_type(token):
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

def run_grep(input_dir, pattern):

    # -Hrn with line numbers
    proc = subprocess.run(["grep", "-Hrn", pattern, input_dir, "--include", "'*.shader'"], capture_output=True, text=True)
    grep_result = proc.stdout
    return grep_result.splitlines()


# --------------------------------------------------------------------------------------------------------------------------------------------------------------

# Definition:
# _SHADOWS_SOFT -> multi_compile -> A.hlsl -> [(line 10, actual_line), (line 20, actual_line)]
#                                   B.hlsl -> [(line 90, actual_line), (line 80, actual_line)]
# Usage:
# _SHADOWS_SOFT -> A.hlsl -> [(line 10, actual_line), (line 20, actual_line)]
#                  B.hlsl -> [(line 90, actual_line), (line 80, actual_line)]

class ShaderKeyword:
    def __init__(self, kw):
        self.keyword = kw
        self.declarations = {}
        self.usages = {}

    def add_declaration(self, pragma_type, shader_file_path, line_number, desc):
        # Declarations
        # _SHADOWS_SOFT -> multi_compile -> A.hlsl -> [(line 10, actual_line), (line 20, actual_line)]
        if not pragma_type in self.declarations:
            self.declarations[pragma_type] = {}

        if not shader_file_path in self.declarations[pragma_type]:
            self.declarations[pragma_type][shader_file_path] = list()

        self.declarations[pragma_type][shader_file_path].append((line_number, desc))

    def get_or_add_usage(self, shader_file_path):

        if not shader_file_path in self.usages:
            cur_shader_keyword.usages[shader_file_path] = list()

        return cur_shader_keyword.usages[shader_file_path]

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



lines = run_grep(input_dir, "'#pragma\smulti_compile\|#pragma\sshader_feature'")

special_pragma_types = set()

# Definition:
# _SHADOWS_SOFT -> multi_compile -> A.hlsl -> [(line 10, actual_line), (line 20, actual_line)]
#                                   B.hlsl -> [(line 90, actual_line), (line 80, actual_line)]
# Usage:
# _SHADOWS_SOFT -> A.hlsl -> [(line 10, actual_line), (line 20, actual_line)]
#                  B.hlsl -> [(line 90, actual_line), (line 80, actual_line)]

keywords_dict = {}

for line in lines:
    tokens = line.split()

    pragma_token = tokens[1]
    if pragma_token.startswith('//'):
        continue

    pragma_type = tokens[2]

    if is_special_pragma_type(pragma_type):
        special_pragma_types.add(pragma_type)
        continue

    numTokens = len(tokens)

    keyword_start_index = 3
    keyword_tokens_in_line = " ".join(tokens[keyword_start_index:])
    shader_file_path_tokens = tokens[0].replace(input_dir,"")[1:].split(':') # use local_path relative to input_dir
    shader_file_path = shader_file_path_tokens[0]
    declaration_line_number = shader_file_path_tokens[1]

    for index, keyword in enumerate(tokens[keyword_start_index:], keyword_start_index):
        if keyword == "_" or keyword == "__":
            continue

        #            print(keyword, index, keyword_tokens_in_line)

#        if not pragma_type in keywords_dict:
#            keywords_dict[pragma_type] = dict()


        if not keyword in keywords_dict:
            keywords_dict[keyword] = ShaderKeyword(keyword)

        cur_shader_keyword = keywords_dict[keyword]

        # Declarations
        cur_shader_keyword.add_declaration(pragma_type, shader_file_path,declaration_line_number, keyword_tokens_in_line)


        # Usages
        keyword_usage = cur_shader_keyword.get_or_add_usage(shader_file_path)

        # do another grep here
        line_number = 10
        keyword_usage.append((line_number, "test"))


for i, keyword in enumerate(keywords_dict):
    print(keyword)

    for j, pragma_type in enumerate(keywords_dict[keyword].declarations):
        cur_dict = keywords_dict[keyword].declarations[pragma_type]
        for k, shader_file_path in enumerate(cur_dict):
            print("    ",shader_file_path)
            for (usage_line, line_content) in cur_dict[shader_file_path]:
                print("         ", usage_line, line_content)

#    for j, shader_file_path in enumerate(keywords_dict[keyword].usages):
#        print("    ",shader_file_path)
#        for (usage_line, line_content) in keywords_dict[keyword].usages[shader_file_path]:
#            print("         ", usage_line, line_content)


