import subprocess

def run_script(script_path):
    try:
        subprocess.run(['python3', script_path], check=True)
        print(f"Successfully ran {script_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_path}: {e}")
        raise

if __name__ == "__main__":
    scripts = [
        'scripts/fetch.py',        # gera data/data.json
        'scripts/calculate.py',
        'scripts/main.py',
        'scripts/api.py',          # gera public/api/*
        'scripts/funds.py',
        'scripts/compare_page.py', # gera public/compare.html
        'scripts/minify.py',
        'scripts/robots-sitemap.py'
    ]
    for script in scripts:
        run_script(script)