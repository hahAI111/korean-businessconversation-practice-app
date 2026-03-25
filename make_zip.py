import zipfile, os

excluded = {'.venv', '__pycache__', '.git', '.azure', '_bmad', 'bmad-docs', 'applogs', 'app_logs', 'logs2', '{output_folder}', 'scripts', '.github', 'docs', '.pytest_cache', 'webapp_logs.zip'}
excluded_files = {'docker_log_today.txt', 'docker-compose.yml', 'Dockerfile', '.env.local', '.zipignore', 'deploy.zip', 'deploy2.zip', 'check_deploy.py', 'make_zip.py'}
excluded_ext = {'.pyc', '.zip'}

zf = zipfile.ZipFile('deploy2.zip', 'w', zipfile.ZIP_DEFLATED)
count = 0
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in excluded]
    for f in files:
        if f in excluded_files:
            continue
        if any(f.endswith(e) for e in excluded_ext):
            continue
        fp = os.path.join(root, f)
        zf.write(fp, os.path.relpath(fp, '.'))
        count += 1
zf.close()
size = os.path.getsize('deploy2.zip')
print(f'{count} files, {size/1024:.0f} KB')
