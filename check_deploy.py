import urllib.request, json
url = 'https://korean-biz-coach.scm.azurewebsites.net/api/deployments/latest'
try:
    r = urllib.request.urlopen(url, timeout=30)
    d = json.loads(r.read())
    for k in ['status', 'complete', 'message', 'end_time', 'start_time']:
        print(f'{k}: {d.get(k)}')
except Exception as e:
    print(f'Error: {e}')
