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

def write_to_csv(outputFileName, dataList, header_row = []):
    with open(outputFileName, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if (len(header_row) > 0):
            writer.writerow(header_row)

        for d in dataList:
            writer.writerow(d)
    print(f"Data written to {outputFileName}")

# --------------------------------------------------------------------------------------------------------------------------------------------------------------

# includeFileExtensions: can contain multiple extensions, ex: "shader,hlsl"
def run_grep(input_dir, pattern, include_file_extensions):

    # -Hrn with line numbers
    proc = subprocess.run(["grep", "-Hrn", pattern, input_dir, "--include=*.{" + include_file_extensions + "}"], capture_output=True, text=True)

    grep_result = proc.stdout
    return grep_result.splitlines()

# --------------------------------------------------------------------------------------------------------------------------------------------------------------

# file_path: ex: <input_dir>/Shaders/2D/Light2D.shader:20:
# returns (path, line:number, remaining)
def split_path_and_line(input_dir, path_and_line):
    tokens = path_and_line.replace(input_dir,"")[1:].split(':') # use local_path relative to input_dir
    return (tokens[0], tokens[1], " ".join(tokens[2:]))

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
        self.shader_usages = {}
        self.cs_usages = {}

    def add_declaration(self, pragma_type, shader_file_path, line_number, desc):
        # Declarations
        # _SHADOWS_SOFT -> multi_compile -> A.hlsl -> [(line 10, actual_line), (line 20, actual_line)]
        if not pragma_type in self.declarations:
            self.declarations[pragma_type] = {}

        if not shader_file_path in self.declarations[pragma_type]:
            self.declarations[pragma_type][shader_file_path] = list()

        self.declarations[pragma_type][shader_file_path].append((line_number, desc))

    def get_or_add_shader_usage(self, shader_file_path):
        if not shader_file_path in self.shader_usages:
            cur_shader_keyword.shader_usages[shader_file_path] = list()
        return cur_shader_keyword.shader_usages[shader_file_path]

    def get_or_add_cs_usage(self, shader_file_path):
        if not shader_file_path in self.cs_usages:
            cur_shader_keyword.cs_usages[shader_file_path] = list()
        return cur_shader_keyword.cs_usages[shader_file_path]

    def validate(self):

        # Declarations
        if len(self.declarations) <= 0:
            raise Exception(f"No declarations for keyword: {self.keyword}")

        for j, pragma_type in enumerate(self.declarations):
            cur_dict = self.declarations[pragma_type]

            if len(cur_dict) <= 0:
                raise Exception(f"Declarations error for keyword: {self.keyword}. Pragma is empty: {pragma_type}")

            for k, shader_file_path in enumerate(cur_dict):
                if (len(cur_dict[shader_file_path])) <= 0:
                    raise Exception(f"Declarations error for keyword: {self.keyword}. No usages in shader file: {shader_file_path}")

        # Usages
        if len(self.shader_usages) <=0:
            raise Exception(f"No usages for keyword: {self.keyword}")

        for j, shader_file_path in enumerate(self.shader_usages):

            if (len(self.shader_usages[shader_file_path])) <= 0:
                raise Exception(f"Usages error for keyword: {self.keyword}. No usages in shader file: {shader_file_path}")


    def to_string_list(self, start_col, source_url_root):
        ret = []

        # Declarations
        l = self.__create_empty_string_list(start_col)
        l[start_col] = "Decl."
        for j, pragma_type in enumerate(self.declarations):
            cur_dict = self.declarations[pragma_type]
            l[start_col + 1] = pragma_type

            for k, shader_file_path in enumerate(cur_dict):
                l[start_col + 2] = shader_file_path

                self.__extend_list_on_usage_dict(cur_dict[shader_file_path], start_col + 3, source_url_root, shader_file_path, l, ret)

        # Shader Usages
        l = self.__create_empty_string_list(start_col)
        l[start_col] = "Sh Usages"
        for j, shader_file_path in enumerate(self.shader_usages):
            l[start_col + 2] = shader_file_path
            self.__extend_list_on_usage_dict(self.shader_usages[shader_file_path], start_col + 3, source_url_root, shader_file_path, l, ret)

        l = self.__create_empty_string_list(start_col)
        l[start_col] = "C# Usages"
        for j, cs_file_path in enumerate(self.cs_usages):
            l[start_col + 2] = cs_file_path
            self.__extend_list_on_usage_dict(self.cs_usages[cs_file_path], start_col + 3, source_url_root, cs_file_path, l, ret)

        return ret

    def __extend_list_on_usage_dict(self, dictionary, start_col, source_url_root, file_path, out_col_list, out_line_list):
        for (usage_line, line_content) in dictionary:
            out_col_list[start_col] = usage_line
            out_col_list[start_col + 1] = line_content
            if len(source_url_root) > 0:
                out_col_list[start_col + 2] = f"{source_url_root}/{file_path}#L{usage_line}"

            out_line_list.append(out_col_list)
            out_col_list = self.__create_empty_string_list(start_col)

        pass

    def __create_empty_string_list(self, num_empty_elements):
        return [""] * (num_empty_elements + 6)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------

shader_file_extensions = "shader,hlsl,cg,cginc"

parser = ArgumentParser()

parser.add_argument('--directory', '-d', required=True, help='The directory of the shader files')
parser.add_argument('--output', '-o',required=False, default="shader.csv", help='The output file (default: shader.csv)')
parser.add_argument('--source-url-root', '-r',required=False, default="", help='The URL root of the source code (default: "")')

args = parser.parse_args()

input_dir = args.directory

# Error checking
isError = False
if not os.path.isdir(input_dir):
    print(f"Invalid input dir: {input_dir}")
    isError = True


if isError:
    exit()



lines = run_grep(input_dir, "'#pragma\smulti_compile\|#pragma\sshader_feature'", shader_file_extensions)

special_pragma_types = set()

# Definition:
# _SHADOWS_SOFT -> multi_compile -> A.hlsl -> [(line 10, actual_line), (line 20, actual_line)]
#                                   B.hlsl -> [(line 90, actual_line), (line 80, actual_line)]
# Usage:
# _SHADOWS_SOFT -> A.hlsl -> [(line 10, actual_line), (line 20, actual_line)]
#                  B.hlsl -> [(line 90, actual_line), (line 80, actual_line)]

keywords_dict = {}
keywords_grepped = set()

for declaration_line_index, line in enumerate(lines):
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

    (shader_file_path, declaration_line_number, rem_token_0) = split_path_and_line(input_dir, tokens[0])

    # Empty strings are false
    if rem_token_0:
        print("Error: this program needs to be upgraded to handle the remaining of token 0: ", rem_token_0)
        exit()

    # loop all keywords in this declaration line
    for index, keyword in enumerate(tokens[keyword_start_index:], keyword_start_index):
        if keyword == "_" or keyword == "__":
            continue

        #print(keyword, index, keyword_tokens_in_line)
        if not keyword in keywords_dict:
            keywords_dict[keyword] = ShaderKeyword(keyword)

        cur_shader_keyword = keywords_dict[keyword]

        # Declarations
        cur_shader_keyword.add_declaration(pragma_type, shader_file_path,declaration_line_number, keyword_tokens_in_line)

        #break early for debugging
        # if declaration_line_index >= 10:
        #     break

        # Usages. Skip if already processed before
        if keyword in keywords_grepped:
            continue

        keywords_grepped.add(keyword)

        #shader
        shader_usage_lines = run_grep(input_dir, keyword, shader_file_extensions)
        for usage_line in shader_usage_lines:
            if "#pragma" in usage_line:
                continue

            usage_tokens = usage_line.rsplit(',', 1)

            (usage_path, usage_line_number, rem_token_0) = split_path_and_line(input_dir, usage_tokens[0])

            usage_line_content = rem_token_0 + " " + " ".join(usage_tokens[1:])
            # print(usage_path, " " * 4, usage_line_content)

            keyword_usage = cur_shader_keyword.get_or_add_shader_usage(usage_path)
            keyword_usage.append( (usage_line_number, usage_line_content) )

        #cs
        cs_usage_lines = run_grep(input_dir, keyword, "cs")
        for usage_line in cs_usage_lines:
            usage_tokens = usage_line.rsplit(',', 1)
            (usage_path, usage_line_number, rem_token_0) = split_path_and_line(input_dir, usage_tokens[0])

            usage_line_content = rem_token_0 + " " + " ".join(usage_tokens[1:])
            # print(usage_path, " " * 4, usage_line_content)

            keyword_usage = cur_shader_keyword.get_or_add_cs_usage(usage_path)
            keyword_usage.append( (usage_line_number, usage_line_content) )



# convert to list
list = []
for i, keyword in enumerate(keywords_dict):
    list.append([keyword])

    try:
        keywords_dict[keyword].validate()
    except Exception as e:
        print('Exception:', e)
        continue

    list.extend(keywords_dict[keyword].to_string_list(start_col=1, source_url_root= args.source_url_root))

header_row = ["Keyword","","Type","FilePath", "LineNumber", "LineContents", "URL"]
write_to_csv(args.output, list, header_row)

# print
for line in list:
    print(line)

