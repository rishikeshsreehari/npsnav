import subprocess

def run_script(script_path):
    try:
        subprocess.run(['python', script_path], check=True)
        print(f"Successfully ran {script_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_path}: {e}")
        raise

if __name__ == "__main__":
    scripts = [
        'scripts/calculate.py',
        'scripts/main.py',
        'scripts/api.py',
        'scripts/funds.py',
        'scripts/minify.py',
        'scripts/robots-sitemap.py'
    ]
    
    for script in scripts:
        run_script(script)
