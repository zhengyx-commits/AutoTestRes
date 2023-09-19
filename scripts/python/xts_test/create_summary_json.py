import json
import os.path
import re
import sys

data = {}
test_data = {}
html_file_path = "./last_report/index.html"
if not os.path.isfile(html_file_path):
    print("ERROR: Can't find index.html!")
    sys.exit()
with open(html_file_path, "r") as html_file:
    html_content = html_file.read()
test_data["passed"] = re.findall(r"Passed</td><td>(.*?)</td>", html_content)[0]
test_data["failed"] = re.findall(r"Failed</td><td>(.*?)</td>", html_content)[0]
test_data["module_done"] = re.findall(r"Modules Done</td><td>(.*?)</td>", html_content)[0]
test_data["module_total"] = re.findall(r"Modules Total</td><td>(.*?)</td>", html_content)[0]
xts_project = sys.argv[1]
start = int(sys.argv[2])
stop = int(sys.argv[3])
duration = int(sys.argv[4])

data["reportName"] = xts_project
data["statistic"] = test_data
data["time"] = {
    "start": start,
    "stop": stop,
    "duration": duration
}
file_path = "./last_report/summary.json"
with open(file_path, "w") as json_file:
    json.dump(data, json_file, indent=4)
print(f"Summary.json of {xts_project} create successfully!")
