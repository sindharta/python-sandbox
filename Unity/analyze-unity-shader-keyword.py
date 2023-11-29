# Example of how to use:
# py analyze-unity-shader-keyword.py -d <package_path>/com.unity.render-pipelines.universal@15.0.6 -s 2 -r https://github.com/Unity-Technologies/Graphics/blob/2023.1/staging/Packages/com.unity.render-pipelines.universal

from argparse import ArgumentParser
import csv
import os
import subprocess
import re

from shin_unity import is_special_pragma_type

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

class ShaderKeyword:
    def __init__(self, kw):
        self.keyword = kw
        self.declarations = {}
        self.shader_usages = {}
        self.cs_usages = {}

    def add_declaration(self, pragma_type, shader_file_path, line_number, line_contents):
        # Declarations
        # _SHADOWS_SOFT -> A.hlsl -> [(line 10, [line_contents] ), (line 20, [line_contents] )]
        if pragma_type not in self.declarations:
            self.declarations[pragma_type] = {}

        if shader_file_path not in self.declarations[pragma_type]:
            self.declarations[pragma_type][shader_file_path] = list()

        self.declarations[pragma_type][shader_file_path].append((line_number, line_contents))

    def add_shader_usage(self, shader_file_path, line_number, line_contents):
        if shader_file_path not in self.shader_usages:
            self.shader_usages[shader_file_path] = list()
        self.shader_usages[shader_file_path].append((line_number, line_contents))

    def add_cs_usage(self, shader_file_path, line_number, line_contents):
        if shader_file_path not in self.cs_usages:
            self.cs_usages[shader_file_path] = list()
        self.cs_usages[shader_file_path].append((line_number, line_contents))

    def validate(self):

        # Declarations
        if len(self.declarations) <= 0:
            return f"No declarations for keyword: {self.keyword}"

        for j, pragma_type in enumerate(self.declarations):
            cur_dict = self.declarations[pragma_type]

            if len(cur_dict) <= 0:
                return f"Declarations error for keyword: {self.keyword}. Pragma is empty: {pragma_type}"

            for k, shader_file_path in enumerate(cur_dict):
                if (len(cur_dict[shader_file_path])) <= 0:
                    return f"Declarations error for keyword: {self.keyword}. No usages in shader file: {shader_file_path}"

        # Usages
        if len(self.shader_usages) <=0:
            return f"No usages for keyword: {self.keyword}"

        for j, shader_file_path in enumerate(self.shader_usages):

            if (len(self.shader_usages[shader_file_path])) <= 0:
                return f"Usages error for keyword: {self.keyword}. No usages in shader file: {shader_file_path}"

        return ""

    def to_string_list(self, start_col, source_url_root):
        ret = []

        # Declarations
        usages_type_item = "Decl."
        for j, pragma_type in enumerate(self.declarations):
            cur_dict = self.declarations[pragma_type]
            pragma_type_item = pragma_type

            for k, shader_file_path in enumerate(cur_dict):
                shader_file_path_item = shader_file_path

                usage_list = self.__create_usage_list(cur_dict[shader_file_path], start_col + 3, source_url_root, shader_file_path)
                for usage in usage_list:
                    usage[start_col] = usages_type_item
                    usage[start_col+1] = pragma_type_item
                    usage[start_col+2] = shader_file_path_item
                    ret.append(usage)
                    usages_type_item = pragma_type_item = shader_file_path_item = ""

        # Shader Usages
        usages_type_item = "Sh Usages"
        for j, shader_file_path in enumerate(self.shader_usages):
            shader_file_path_item = shader_file_path

            usage_list = self.__create_usage_list(self.shader_usages[shader_file_path], start_col + 3, source_url_root, shader_file_path)
            for usage in usage_list:
                usage[start_col] = usages_type_item
                usage[start_col + 2] = shader_file_path_item
                ret.append(usage)
                usages_type_item = shader_file_path_item = ""

        usages_type_item = "C# Usages"
        for j, cs_file_path in enumerate(self.cs_usages):
            cs_file_path_item = cs_file_path

            usage_list = self.__create_usage_list(self.cs_usages[cs_file_path], start_col + 3, source_url_root, cs_file_path)
            for usage in usage_list:
                usage[start_col] = usages_type_item
                usage[start_col + 2] = cs_file_path_item
                ret.append(usage)
                usages_type_item = cs_file_path_item = ""

        return ret


    def to_usage_list_summary(self, start_col, source_url_root):
        ret = []

        usage_start_col = start_col + 1

        # Declarations
        for j, pragma_type in enumerate(self.declarations):
            cur_dict = self.declarations[pragma_type]
            ret.extend(self.__create_file_dictionary_summary(cur_dict, usage_start_col, "Decl.", source_url_root))

        ret.extend(self.__create_file_dictionary_summary(self.shader_usages, usage_start_col, "Sh Usages", source_url_root))
        ret.extend(self.__create_file_dictionary_summary(self.cs_usages, usage_start_col, "C# Usages", source_url_root))


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


lines = run_grep(input_dir, "'#pragma\smulti_compile\|#pragma\sshader_feature'", shader_file_extensions)

special_pragma_types = set()

# Declarations:
# _SHADOWS_SOFT -> multi_compile -> A.hlsl -> [(line 10, actual_line), (line 20, actual_line)]
#                                   B.hlsl -> [(line 90, actual_line), (line 80, actual_line)]
# Usage:
# _SHADOWS_SOFT -> A.hlsl -> [(line 10, actual_line), (line 20, actual_line)]
#                  B.hlsl -> [(line 90, actual_line), (line 80, actual_line)]

keywords_dict = {}
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

    if is_special_pragma_type(pragma_type):
        special_pragma_types.add(pragma_type)
        continue

    numTokens = len(tokens)

    keyword_start_index = 2
    keyword_tokens_in_line = " ".join(tokens[keyword_start_index:])

    # loop all keywords in this declaration line
    for index, keyword in enumerate(tokens[keyword_start_index:], keyword_start_index):
        if keyword == "_" or keyword == "__":
            continue

        # break out of comments
        if keyword.startswith("//"):
            break

        #print(keyword, index, keyword_tokens_in_line)
        if not keyword in keywords_dict:
            keywords_dict[keyword] = ShaderKeyword(keyword)

        cur_shader_keyword = keywords_dict[keyword]

        # Declarations
        cur_shader_keyword.add_declaration(pragma_type, shader_file_path,declaration_line_number, usage_line_content)

        #break early for debugging
        # if declaration_line_index >= 10:
        #     break

        # Usages. Skip if already processed before
        if keyword in keywords_grepped:
            continue

        keywords_grepped.add(keyword)

        temp_path = ""
        temp_contents = []

        #shader
        shader_usage_lines = run_grep([input_dir, *additional_usage_dirs], keyword, shader_file_extensions, True)
        for usage_line in shader_usage_lines:

            if "#pragma" in usage_line:
                continue

            usage_tokens = usage_line.rsplit(',', 1)

            (rel_usage_path, usage_line_number, rem_token_0) = split_path_and_line(input_dir, usage_tokens[0])

            if temp_path != rel_usage_path:
                temp_contents = read_file_all_lines(f"{input_dir}/{rel_usage_path}")
                temp_path = rel_usage_path

            start_line_no = usage_line_number - num_surrounding_usage_lines - 1
            end_line_no   = usage_line_number + num_surrounding_usage_lines

            cur_shader_keyword.add_shader_usage(rel_usage_path, usage_line_number, temp_contents[start_line_no: end_line_no])

        #cs
        cs_usage_lines = run_grep([input_dir, *additional_usage_dirs], keyword, "cs", True)
        for usage_line in cs_usage_lines:
            usage_tokens = usage_line.rsplit(',', 1)
            (rel_usage_path, usage_line_number, rem_token_0) = split_path_and_line(input_dir, usage_tokens[0])

            if temp_path != rel_usage_path:
                temp_contents = read_file_all_lines(f"{input_dir}/{rel_usage_path}")
                temp_path = rel_usage_path

            start_line_no = usage_line_number - num_surrounding_usage_lines - 1
            end_line_no   = usage_line_number + num_surrounding_usage_lines
            cur_shader_keyword.add_cs_usage(rel_usage_path, usage_line_number, temp_contents[start_line_no: end_line_no])

# convert to list
csv_list = []
error_keywords = set()
sorted_keywords = sorted(keywords_dict.keys())
for keyword in sorted_keywords:
    csv_list.append([keyword])

    validation_message = keywords_dict[keyword].validate()
    if len(validation_message) > 0:
        csv_list.append(["", "Error", validation_message])
        error_keywords.add(keyword)

    csv_list.extend(keywords_dict[keyword].to_string_list(start_col=1, source_url_root= args.source_url_root))

# combine errors
if len(error_keywords) > 0:
    csv_list.append([])
    csv_list.append([])
    csv_list.append([])
    csv_list.append(["Error Keywords"])
    for keyword in sorted(error_keywords):
        csv_list.append(["", keyword])

# add summary at the end
csv_list.append([])
csv_list.append([])
csv_list.append([])
csv_list.append(["Usage Summary"])
for keyword in sorted_keywords:
    if keyword in error_keywords:
        continue

    csv_list.append([keyword])
    csv_list.extend(keywords_dict[keyword].to_usage_list_summary(start_col=1, source_url_root= args.source_url_root))


header_row = [[f"Keywords (Total: {len(keywords_dict)})","","Type","Path", "LineNo", "LineContents"]]
write_to_csv(args.output, csv_list, header_row)

# print
for line in csv_list:
    print(line)

