# Example of how to use:
# py analyze-unity-shader-builtin-pragma.py -d <package_path>/com.unity.render-pipelines.universal@15.0.6 -s 2 -r https://github.com/Unity-Technologies/Graphics/blob/2023.1/staging/Packages/com.unity.render-pipelines.universal

from argparse import ArgumentParser
import csv
import os
import subprocess
import re

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

def write_to_csv(outputFileName, dataList, header_rows = []):
    with open(outputFileName, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for h in header_rows:
            writer.writerow(h)

        for d in dataList:
            writer.writerow(d)
    print(f"Data written to {outputFileName}")

# --------------------------------------------------------------------------------------------------------------------------------------------------------------

# input_dir: can be a string or a list of strings
# include_file_extensions: can contain multiple extensions, ex: "shader,hlsl"
# An example of the called grep:
#   grep -Hrn DEBUG_DISPLAY <package_path>/com.unity.render-pipelines.universal@15.0.6/Shaders/2D <package_path>/com.unity.render-pipelines.core@15.0.6 --include=*.{shader,hlsl,cginc,cg}

def run_grep(input_dir, pattern, include_file_extensions, is_exact_match = False):

    grep_options = "-Hrn"
    if is_exact_match:
        grep_options += "w"

    # -Hrn with line numbers
    if type(input_dir) == list:
        proc = subprocess.run(["grep", grep_options, pattern, *input_dir, "--include=*.{" + include_file_extensions + "}"], capture_output=True, text=True)
    else:
        proc = subprocess.run(["grep", grep_options, pattern, input_dir, "--include=*.{" + include_file_extensions + "}"], capture_output=True, text=True)

    grep_result = proc.stdout
    if (grep_result):
        return grep_result.splitlines()
    else:
        return []


def read_file_all_lines(filePath):
    ret = []
    with open(filePath, encoding='utf-8') as f:
        ret = f.readlines()

    return ret

# --------------------------------------------------------------------------------------------------------------------------------------------------------------

# file_path: ex: <input_dir>/Shaders/2D/Light2D.shader:20:
# returns (relative path, line:number, remaining)
def split_path_and_line(input_dir, path_and_line):

    common_path = input_dir
    find_rel_path = not path_and_line.startswith(input_dir)
    if find_rel_path:
        common_path = os.path.commonpath([input_dir, path_and_line]).replace("\\","/")

    tokens = path_and_line.replace(common_path,"")[1:].split(':') # use local_path relative to input_dir
    rel_path = tokens[0]

    #tokens[0] is not located under input_dir. Find its relative path
    if (find_rel_path):
        rel_path = os.path.relpath(common_path + "/" + tokens[0], input_dir).replace("\\","/")

    return (rel_path, int(tokens[1]), " ".join(tokens[2:]))

# --------------------------------------------------------------------------------------------------------------------------------------------------------------

# Definition:
# _SHADOWS_SOFT -> multi_compile -> A.hlsl -> [(line 10, [line_contents] ), (line 20, [line_contents])]
#                                   B.hlsl -> [(line 90, [line_contents] ), (line 80, [line_contents])]
# Shader Usage / CS Usage:
# _SHADOWS_SOFT -> A.hlsl -> [(line 10, [line_contents] ), (line 20, [line_contents] )]
#                  B.hlsl -> [(line 90, [line_contents] ), (line 80, [line_contents] )]

class ShaderPragmaShortcut:
    def __init__(self, shortcut):
        self.pragma_shortcut = shortcut
        self.usages = {}

    def add_usage(self, shader_file_path, line_number, line_contents):
        if shader_file_path not in self.usages:
            cur_shader_keyword.usages[shader_file_path] = list()
        cur_shader_keyword.usages[shader_file_path].append((line_number, line_contents))


    def to_string_list(self, start_col, source_url_root):
        ret = []

        # Shader Usages
        for j, shader_file_path in enumerate(self.usages):
            shader_file_path_item = shader_file_path

            usage_list = self.__create_usage_list(self.usages[shader_file_path], start_col + 1, source_url_root, shader_file_path)
            for usage in usage_list:
                usage[start_col] = shader_file_path_item
                ret.append(usage)
                usages_type_item = shader_file_path_item = ""

        return ret


    def __create_usage_list(self, dictionary, start_col, source_url_root, file_path):
        ret = []
        for (line_no, line_contents) in dictionary:
            l = self.__create_empty_string_list(start_col)

            l[start_col + 1] = "".join(line_contents) # convert a list to a multiline string
            
            if len(source_url_root) > 0:
                l[start_col] = self.__convert_path_to_hyperlink(line_no, source_url_root, file_path, line_no)
            else:
                l[start_col] = line_no

            ret.append(l)
        return ret

    def __create_file_dictionary_summary(self, dic, start_col, start_col_content, source_url_root):
        ret = []
        
        usage_type_item = start_col_content
        empty_cols = [""] * (start_col - 1) if start_col > 0 else []

        for j, file_path in enumerate(dic):
            ret.append([*empty_cols, usage_type_item, self.__convert_path_to_hyperlink(file_path, source_url_root, file_path)])
            usage_type_item = ""

        return ret

    def __convert_path_to_hyperlink(self, link_text, url_root, path, line_no = -1):

        rel_url = re.sub('@\d+\.\d+\.\d+', '', path)  # ../com.unity.render-pipelines.core@15.0.6/ -> ../com.unity.render-pipelines.core/
        ret = f"{url_root}/{rel_url}"


        if (line_no >=0):
            ret+= f"#L{line_no}"

        # put inside hyperlink formula
        ret = ret.replace('"','""')
        ret = f'=HYPERLINK("{ret}","{link_text}")'

        return ret

    def __create_empty_string_list(self, num_empty_elements):
        return [""] * (num_empty_elements + 6)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------

shader_file_extensions = "shader,hlsl,cg,cginc,template"

parser = ArgumentParser()

parser.add_argument('--directory', '-d', required=True, help='<Required> The directory of the shader files')
parser.add_argument('--output', '-o',required=False, default="shader.csv", help='The output file (default: shader.csv)')
parser.add_argument('--source-url-root', '-r',required=False, default="", help='The URL root of the source code (default: "")')
parser.add_argument('--num-surrounding-usage-lines', '-s',required=False, default=2, help='The number of surrounding usage lines (default: 2)')
parser.add_argument('--add-usage-directory','-u', nargs='+', required=False, help='Additional usage directories')


args = parser.parse_args()

input_dir = args.directory
num_surrounding_usage_lines = int(args.num_surrounding_usage_lines)

# Error checking
isError = False
if not os.path.isdir(input_dir):
    print(f"Invalid input dir: {input_dir}")
    isError = True


if isError:
    exit()

additional_usage_dirs = []
if type(args.add_usage_directory) == list:
    for dir in args.add_usage_directory:
        if not os.path.isdir(dir):
            print(f"Invalid additional usage dir: {dir}")
            continue

        additional_usage_dirs.append(dir)


# TODO need to search all dirs
lines = run_grep(input_dir, "'#pragma\smulti_compile\|#pragma\sshader_feature'", shader_file_extensions)

special_pragma_types = set()

# Declarations:
# multi_compile_fog -> A.hlsl -> [(line 10, actual_line), (line 20, actual_line)]
#                      B.hlsl -> [(line 90, actual_line), (line 80, actual_line)]

pragma_dict = {}
keywords_grepped = set()

for declaration_line_index, line in enumerate(lines):

    grep_tokens = line.split()
    (shader_file_path, declaration_line_number, rem_token_0) = split_path_and_line(input_dir, grep_tokens[0])

    usage_line_content = (rem_token_0 + " " + " ".join(grep_tokens[1:])).strip()

    tokens = usage_line_content.split()

    pragma_token = tokens[0]
    if pragma_token.startswith('//'):
        continue

    pragma_type = tokens[1]

    if not is_special_pragma_type(pragma_type):
        continue

    #print(keyword, index, keyword_tokens_in_line)
    if not pragma_type in pragma_dict:
        pragma_dict[pragma_type] = ShaderPragmaShortcut(pragma_type)

    cur_shader_keyword = pragma_dict[pragma_type]



    cur_shader_keyword.add_usage(shader_file_path, declaration_line_number, usage_line_content)

    print(shader_file_path, usage_line_content)

    continue






# convert to list
csv_list = []
error_keywords = set()
sorted_keywords = sorted(pragma_dict.keys())
for pragma_type in sorted_keywords:
    csv_list.append([pragma_type])
    csv_list.extend(pragma_dict[pragma_type].to_string_list(start_col=1, source_url_root= args.source_url_root))

header_row = [[f"Keywords (Total: {len(pragma_dict)})","","Type","Path", "LineNo", "LineContents"]]
write_to_csv(args.output, csv_list, header_row)

# print
for line in csv_list:
    print(line)

