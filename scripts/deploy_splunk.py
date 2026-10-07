import os
import glob
import sys
import requests
import urllib3
from sigma.collection import SigmaCollection
from sigma.backends.splunk import SplunkBackend

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SPLUNK_HOST = "https://134.122.116.125:8089"
SPLUNK_TOKEN = os.environ["SPLUNK_TOKEN"]
RULES_DIR = "splunk_rules"

headers = {"Authorization": f"Bearer {SPLUNK_TOKEN}"}
backend = SplunkBackend()

success = 0
failed = 0

for path in sorted(glob.glob(f"{RULES_DIR}/*.yml")):
    name = os.path.splitext(os.path.basename(path))[0]
    try:
        collection = SigmaCollection.load_ruleset([path])
        spl_list = backend.convert(collection)
        spl = spl_list[0]
        search = f"search {spl}"

        url = f"{SPLUNK_HOST}/servicesNS/admin/search/saved/searches"
        data = {"name": name, "search": search}

        r = requests.post(url, headers=headers, data=data, verify=False)

        if r.status_code in (200, 201):
            print(f"[CREATED] {name}")
            success += 1
        elif r.status_code == 409:
            upd = requests.post(f"{url}/{name}", headers=headers,
                                data={"search": search}, verify=False)
            if upd.status_code in (200, 201):
                print(f"[UPDATED] {name}")
                success += 1
            else:
                print(f"[FAILED]  {name} -> {upd.status_code} {upd.text}")
                failed += 1
        else:
            print(f"[FAILED]  {name} -> {r.status_code} {r.text}")
            failed += 1
    except Exception as e:
        print(f"[ERROR]   {name} -> {e}")
        failed += 1

print(f"\nDone: {success}/{success + failed} success")
if failed > 0:
    sys.exit(1)
