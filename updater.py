import subprocess

def execute_shell_script(script_path):
    try:
        subprocess.run(['bash', script_path], check=True)
        print("Script executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing script: {e}")

execute_shell_script('update_script.sh')
print("version updated !")
