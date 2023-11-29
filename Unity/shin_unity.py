
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

    if (token == "shader_feature_local_vertex"):
        return False

    if (token == "shader_feature_local_fragment"):
        return False

    return True

#---------------------------------------------------------------------------------------------------------------------------------------------------------------

import csv
def write_to_csv(outputFileName, dataList, header_rows = []):
    with open(outputFileName, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for h in header_rows:
            writer.writerow(h)

        for d in dataList:
            writer.writerow(d)
    print(f"Data written to {outputFileName}")

def read_file_all_lines(filePath):
    ret = []
    with open(filePath, encoding='utf-8') as f:
        ret = f.readlines()

    return ret

#---------------------------------------------------------------------------------------------------------------------------------------------------------------

import subprocess

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

