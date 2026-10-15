import os
import glob
import sys
import requests
import urllib3
from sigma.collection import SigmaCollection
from sigma.backends.splunk import SplunkBackend

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SPLUNK_HOST = "https://137.184.102.241:8089"
SPLUNK_USER = os.environ["SPLUNK_USER"]
SPLUNK_PASS = os.environ["SPLUNK_PASS"]
RULES_DIR = "splunk_rules"

auth = (SPLUNK_USER, SPLUNK_PASS)
backend = SplunkBackend()

base_url = f"{SPLUNK_HOST}/servicesNS/nobody/search/saved/searches"

success = 0
failed = 0

for path in sorted(glob.glob(f"{RULES_DIR}/*.yml")):
    name = os.path.splitext(os.path.basename(path))[0]
    try:
        collection = SigmaCollection.load_ruleset([path])
        spl_list = backend.convert(collection)
        spl = spl_list[0]
        search = f"search {spl}"

        upd = requests.post(f"{base_url}/{name}", auth=auth,
                            data={"search": search}, verify=False)

        if upd.status_code in (200, 201):
            print(f"[UPDATED] {name}")
            success += 1
        else:
            r = requests.post(base_url, auth=auth,
                              data={"name": name, "search": search}, verify=False)
            if r.status_code in (200, 201):
                print(f"[CREATED] {name}")
                success += 1
            else:
                print(f"[FAILED]  {name} -> {r.status_code} {r.text}")
                failed += 1
    except Exception as e:
        print(f"[ERROR]   {name} -> {e}")
        failed += 1

print(f"\nDone: {success}/{success + failed} success")
if failed > 0:
    sys.exit(1)
