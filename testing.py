# https://codeberg.org/alexhkurz/testing-python-programs/src/branch/main/testing4b.py
import os
import subprocess
import re
import glob

TIMEOUT = 0.2  # Timeout duration in seconds

def load_tests(file_path):
    tests = []
    with open(file_path, 'r') as file:
        for line in file:
            name, input, expected_output = line.strip().split(', ')
            tests.append((name, input, expected_output))
    return tests

def run_test(program, input):
    try:
        result = subprocess.run(['python3', program, input], capture_output=True, text=True, timeout=TIMEOUT)
        return result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return "TIMEOUT", ""

def remove_ansi_escape_sequences(text):
    ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)

def remove_old_py_txt_files():
    # Find all files with the .py.txt extension in the current directory
    for file_path in glob.glob("*.py.txt"):
        try:
            os.remove(file_path)
            print(f"Removed old file: {file_path}")
        except OSError as e:
            print(f"Error removing file {file_path}: {e}")

# Generate fresh variable names in the form Var1, Var2, Var3, ...
class FreshNameRenamer:
    def __init__(self):
        self.name_mapping = {}
        self.counter = 0

    def get_fresh_name(self, old_name):
        if old_name not in self.name_mapping:
            self.counter += 1
            self.name_mapping[old_name] = f"Var{self.counter}"
        return self.name_mapping[old_name]

# Function to rename variables in the output
def rename_variables_in_output(output):
    renamer = FreshNameRenamer()
    tokens = re.split(r'(\W+)', output)  # Split by non-word characters (to keep variable names)
    renamed_tokens = [renamer.get_fresh_name(token) if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', token) else token for token in tokens]
    return ''.join(renamed_tokens)

def main():
    remove_old_py_txt_files()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tests_path = os.path.join(script_dir, "testing-data-M1.txt")
    tests = load_tests(tests_path)
    for program in os.listdir(script_dir):
        if program.endswith(f".py"):  # only test Python files
            for (name, input, expected_output) in tests:
                if program.endswith(f"{name}.py"):  # only apply tests that match the name
                    print(f"Processing \033[95m{program}\033[0m on \033[95m{input}\033[0m")
                    output, error = run_test(program, input)
                    clean_output = remove_ansi_escape_sequences(output)
                    result_file_path = os.path.join(script_dir, f"{program}.txt")
                    with open(result_file_path, 'a') as result_file:
                        # rename bound variables in lambda calculus terms
                        renamed_clean_output = rename_variables_in_output(clean_output)
                        renamed_expected_output = rename_variables_in_output(expected_output)
                        if renamed_clean_output == renamed_expected_output:
                            result_file.write(f"True | {name} | Input: {input} | Expected: {expected_output} | Output: {clean_output} \n")
                        elif output == "TIMEOUT":
                            result_file.write(f"TIMEOUT | {name} | Input: {input} | Expected: {expected_output} | Output: {output}\n")
                        else:
                            try:
                                result_file.write(f"{float(output) == float(expected_output)} | {name} | Input: {input} | Expected: {expected_output} | Output: {output}\n")
                            except ValueError:
                                result_file.write(f"False | {name} | Input: {input} | Expected: {expected_output} | Output: {clean_output}\n")
                        if error:
                            result_file.write(f"Error: {error}\n")
    
if __name__ == "__main__":
    main()