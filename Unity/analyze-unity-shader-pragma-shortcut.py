# Example of how to use:
# py analyze-unity-shader-pragma-shortcut.py -d <package_path>/com.unity.render-pipelines.universal@15.0.6 -s 2 -r https://github.com/Unity-Technologies/Graphics/blob/2023.1/staging/Packages/com.unity.render-pipelines.universal

from argparse import ArgumentParser
import os
import re
from shin_unity import is_pragma_shortcut, write_to_csv, read_file_all_lines, split_path_and_line, run_grep


# --------------------------------------------------------------------------------------------------------------------------------------------------------------

pragma_shortcut_to_keywords_dict = {

    "multi_compile_fwdbase": [
        "DIRECTIONAL", "LIGHTMAP_ON", "DIRLIGHTMAP_COMBINED",
        "DYNAMICLIGHTMAP_ON", "SHADOWS_SCREEN", "SHADOWS_SHADOWMASK",
        "LIGHTMAP_SHADOW_MIXING", "LIGHTPROBE_SH"
    ],
    "multi_compile_fwdbasealpha": [
        "DIRECTIONAL", "LIGHTMAP_ON", "DIRLIGHTMAP_COMBINED",
        "DYNAMICLIGHTMAP_ON", "LIGHTMAP_SHADOW_MIXING", "VERTEXLIGHT_ON",
        "LIGHTPROBE_SH"
    ],
    "multi_compile_fwdadd": [
        "POINT", "DIRECTIONAL", "SPOT", "POINT_COOKIE", "DIRECTIONAL_COOKIE"
    ],
    "multi_compile_fwdadd_fullshadows": [
        "POINT", "DIRECTIONAL", "SPOT", "POINT_COOKIE", "DIRECTIONAL_COOKIE",
        "SHADOWS_DEPTH", "SHADOWS_SCREEN", "SHADOWS_CUBE", "SHADOWS_SOFT",
        "SHADOWS_SHADOWMASK", "LIGHTMAP_SHADOW_MIXING"
    ],
    "multi_compile_lightpass": [
        "POINT", "DIRECTIONAL", "SPOT", "POINT_COOKIE", "DIRECTIONAL_COOKIE",
        "SHADOWS_DEPTH", "SHADOWS_SCREEN", "SHADOWS_CUBE", "SHADOWS_SOFT",
        "SHADOWS_SHADOWMASK", "LIGHTMAP_SHADOW_MIXING"
    ],
    "multi_compile_shadowcaster": ["SHADOWS_DEPTH", "SHADOWS_CUBE"],
    "multi_compile_shadowcollector": [
        "SHADOWS_SPLIT_SPHERES", "SHADOWS_SINGLE_CASCADE"
    ],
    "multi_compile_prepassfinal": [
        "LIGHTMAP_ON", "DIRLIGHTMAP_COMBINED", "DYNAMICLIGHTMAP_ON",
        "UNITY_HDR_ON", "SHADOWS_SHADOWMASK", "LIGHTPROBE_SH"
    ],
    "multi_compile_particles": ["SOFTPARTICLES_ON"],
    "multi_compile_fog": ["FOG_LINEAR", "FOG_EXP", "FOG_EXP2"],
    "multi_compile_instancing": ["INSTANCING_ON", "PROCEDURAL_ON"]
}

# --------------------------------------------------------------------------------------------------------------------------------------------------------------

# Usage:
# multi_compile_fog -> A.hlsl -> [(line 10, actual_line), (line 20, actual_line)]
#                      B.hlsl -> [(line 90, actual_line), (line 80, actual_line)]

class ShaderPragmaShortcut:
    def __init__(self, shortcut):
        self.pragma_shortcut = shortcut
        self.declarations = {}
        self.usages = {}


    def add_declaration(self, shader_file_path, line_number, line_contents):
        if shader_file_path not in self.declarations:
            self.declarations[shader_file_path] = list()
        self.declarations[shader_file_path].append((line_number, line_contents))

    def add_usage(self, keyword, shader_file_path, line_number, line_contents):

        if keyword not in self.usages:
            self.usages[keyword] = {}

        if shader_file_path not in self.usages[keyword]:
            self.usages[keyword][shader_file_path] = list()

        self.usages[keyword][shader_file_path].append((line_number, line_contents))

        pass


    def to_string_list(self, start_col, source_url_root):
        ret = []

        # Shader Declarations
        usages_type_item = "Decl."
        for j, shader_file_path in enumerate(self.declarations):
            shader_file_path_item = shader_file_path

            usage_list = self.__create_usage_list(self.declarations[shader_file_path], start_col + 3, source_url_root, shader_file_path)
            for usage in usage_list:
                usage[start_col] = usages_type_item
                usage[start_col+2] = shader_file_path_item
                ret.append(usage)
                usages_type_item = shader_file_path_item = ""


        # Declarations
        usages_type_item = "Usages."
        for j, keyword in enumerate(self.usages):
            cur_dict = self.usages[keyword]
            keyword_item = keyword

            for k, shader_file_path in enumerate(cur_dict):
                shader_file_path_item = shader_file_path

                usage_list = self.__create_usage_list(cur_dict[shader_file_path], start_col + 3, source_url_root, shader_file_path)
                for usage in usage_list:
                    usage[start_col] = usages_type_item
                    usage[start_col+1] = keyword_item
                    usage[start_col+2] = shader_file_path_item
                    ret.append(usage)
                    usages_type_item = keyword_item = shader_file_path_item = ""

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
parser.add_argument('--output', '-o',required=False, default="pragma_shortcut.csv", help='The output file (default: pragma_shortcut.csv)')
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


lines = run_grep([input_dir, *additional_usage_dirs], "'#pragma\smulti_compile\|#pragma\sshader_feature'", shader_file_extensions)

special_pragma_types = set()

# Declarations:
# multi_compile_fog -> A.hlsl -> [(line 10, actual_line), (line 20, actual_line)]
#                      B.hlsl -> [(line 90, actual_line), (line 80, actual_line)]

# Usage:
# multi_compile_fog -> FOG_LINEAR -> A.hlsl -> [(line 10, actual_line), (line 20, actual_line)]
#                      FOG_EXP -> B.hlsl -> [(line 90, actual_line), (line 100, actual_line)]
#                      FOG_EXP2 -> B.hlsl -> [(line 500, actual_line), (line 400, actual_line)]

pragma_shortcut_dict = {}

# Find declarations
for declaration_line_index, line in enumerate(lines):

    grep_tokens = line.split()
    (shader_file_path, declaration_line_number, rem_token_0) = split_path_and_line(input_dir, grep_tokens[0])

    usage_line_content = (rem_token_0 + " " + " ".join(grep_tokens[1:])).strip()

    tokens = usage_line_content.split()

    pragma_token = tokens[0]
    if pragma_token.startswith('//'):
        continue

    pragma_type = tokens[1]

    if not is_pragma_shortcut(pragma_type):
        continue

    #print(keyword, index, keyword_tokens_in_line)
    if not pragma_type in pragma_shortcut_dict:
        pragma_shortcut_dict[pragma_type] = ShaderPragmaShortcut(pragma_type)

    cur_shortcut = pragma_shortcut_dict[pragma_type]
    cur_shortcut.add_declaration(shader_file_path, declaration_line_number, usage_line_content)

temp_path = ""
temp_contents = []

# Find Usages
for shortcut in pragma_shortcut_dict:
    if not shortcut in pragma_shortcut_to_keywords_dict:
        print(f"Invalid pragma shortcut found: {shortcut}")
        exit()


    for keyword in pragma_shortcut_to_keywords_dict[shortcut]:

        shader_usage_lines = run_grep([input_dir, *additional_usage_dirs], keyword, shader_file_extensions, True)

        for usage_line in shader_usage_lines:

            usage_tokens = usage_line.rsplit(',', 1)

            (rel_usage_path, usage_line_number, rem_token_0) = split_path_and_line(input_dir, usage_tokens[0])

            if temp_path != rel_usage_path:
                temp_contents = read_file_all_lines(f"{input_dir}/{rel_usage_path}")
                temp_path = rel_usage_path

            start_line_no = usage_line_number - num_surrounding_usage_lines - 1
            end_line_no   = usage_line_number + num_surrounding_usage_lines

            pragma_shortcut_dict[shortcut].add_usage(keyword, rel_usage_path, usage_line_number, temp_contents[start_line_no: end_line_no])




# convert to list
csv_list = []
sorted_shortcuts = sorted(pragma_shortcut_dict.keys())
for shortcut in sorted_shortcuts:
    csv_list.append([shortcut])
    csv_list.extend(pragma_shortcut_dict[shortcut].to_string_list(start_col=1, source_url_root= args.source_url_root))

header_row = [['=HYPERLINK("https://docs.unity3d.com/2023.3/Documentation/Manual/SL-MultipleProgramVariants.html","Pragma Shortcut")', "Type", "Keyword", "Path", "LineNo", "LineContents"]]
write_to_csv(args.output, csv_list, header_row)


# print
for line in csv_list:
    print(line)

