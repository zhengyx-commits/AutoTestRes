import datetime
import json
import sys

import requests

file_path = "/home/amlogic/FAE/AutoTest/jenkins_status.json"
data = {}
status_list = []
ott_url = sys.argv[1]
iptv_url = sys.argv[2]
print(iptv_url)
print(ott_url)
ott_jobs = []
iptv_jobs = []
iptv_job_list = []
ott_job_list = []
project_name = ""
android_version = ""
android_s = "Android_S"
android_u = "Android_U"
xts_keyword = ["CTS", "STS", "VTS", "GTS", "TVTS"]


iptv_all_jobs_status = requests.get(url=iptv_url + "api/json").json()
for iptv_job_status in iptv_all_jobs_status["jobs"]:
    if ("name" in iptv_job_status) and ("color" in iptv_job_status):
        # if iptv_job_status["color"] != "disabled":
            # print(iptv_job_status["name"], iptv_job_status["color"])
        iptv_jobs.append(iptv_job_status["name"])
# iptv_all_jobs = requests.get(url=iptv_url + "api/json?tree=jobs[name]").json()
# iptv_jobs = iptv_all_jobs['jobs']
# ott_all_jobs = requests.get(url=ott_url + "api/json?tree=jobs[name]").json()
# ott_jobs = ott_all_jobs['jobs']

ott_all_jobs_status = requests.get(url=ott_url + "api/json").json()
for ott_job_status in ott_all_jobs_status["jobs"]:
    if ("name" in ott_job_status) and ("color" in ott_job_status):
        # if ott_job_status["color"] != "disabled":
            # print(iptv_job_status["name"], iptv_job_status["color"])
        if ("Android_S_Hybrid_Openlinux_Autotest_DVB_C_Stress_Player_Switch" not in ott_job_status["name"]) and\
                ("Android_U_Google_Boreal_Autotest_Sanity" not in ott_job_status["name"]):
            ott_jobs.append(ott_job_status["name"])

print(iptv_jobs)
print(ott_jobs)

for iptv_job in iptv_jobs:
    if "IPTV_Product_Line" in iptv_job:
        iptv_job_list.append(iptv_job)
for ott_job in ott_jobs:
    if "Autotest" in ott_job:
        ott_job_list.append(ott_job)
        # if ("_Hybrid_" in ott_job) and ("XTS" not in ott_job):
        # if ("_Hybrid_" in ott_job) and ("XTS" not in ott_job):
        #     ott_job_list.append(ott_job)
        # if any(keyword in ott_job for keyword in xts_keyword):
        #     ott_job_list.append(ott_job)
        # if "Autotest_KPI" in ott_job:
        #     ott_job_list.append(ott_job)
print("iptv_job_list", iptv_job_list)
print("ott_job_list", ott_job_list)

for iptv in iptv_job_list:
    job_data = {}
    res = requests.get(url=f"{iptv_url}job/{iptv}/lastBuild/api/json")
    if "Android_P_IPTV" in iptv and "YuvCheck" in iptv:
        project_name = "Android P IPTV YUV"
    elif "Android_R_IPTV" in iptv and "YuvCheck" in iptv:
        project_name = "Android R IPTV YUV"
    if res.status_code == 200:
        result = res.json()["result"]
        job_data["name"] = project_name
        job_data["status"] = result
        status_list.append(job_data)
    else:
        print(f"Can't get {iptv} job status!")

for ott in ott_job_list:
    job_data = {}
    res = requests.get(url=f"{ott_url}job/{ott}/lastBuild/api/json")
    # res = requests.get(url=f"{ott_url}job/{ott}/api/json")
    if "Android_S" in ott:
        android_version = android_s
    if "Android_U" in ott:
        android_version = android_u
    # if ott == "Android_S_Hybrid_Openlinux_Autotest":
    #     project_name = "IPTV Basic Play Control"
    if "Basic" in ott:
        project_name = "IPTV Basic Play Control"
    # elif ott == "Android_S_Hybrid_Openlinux_Autotest_Compatibility":
    #     project_name = "IPTV Compatibility"
    elif ("Compatibility" in ott) and ("Format_Compatibility" not in ott):
        project_name = "IPTV Compatibility"
    elif "Format_Compatibility" in ott:
        project_name = "Format Compatibility"
    elif "CAS" in ott:
        project_name = "CAS"
    elif "Sanity" in ott:
        project_name = "Sanity Test"
    elif "Autotest_KPI" in ott:
        project_name = "KPI"
    elif "Autotest_Multi_Stress" in ott:
        project_name = "Stress"
    elif "DVB_C" in ott and "Stress" in ott:
        project_name = "DVB-Stress"
    elif "DVB_C" in ott and ("Stress" not in ott):
        project_name = "DVB-C"
    elif "DVB_S" in ott and ("Stress" not in ott):
        project_name = "DVB-S"
    elif "DVB_T" in ott and ("Stress" not in ott):
        project_name = "DVB-T"
    elif "YuvCheck" in ott:
        project_name = "Decoder Check(YUV)"
    elif "CTS_Autotest" in ott:
        project_name = "CTS"
    elif "_VTS_Autotest" in ott:
        project_name = "VTS"
    elif "STS_Autotest" in ott:
        project_name = "STS"
    elif "GTS_Autotest" in ott:
        project_name = "GTS"
    elif "_TVTS_Autotest" in ott:
        project_name = "TVTS"
    else:
        project_name = ott
    if res.status_code == 200:
        result = res.json()["result"]
        job_data["name"] = f"{android_version}-{project_name}"
        job_data["status"] = result
        if ott.endswith("SZ"):
            job_data["location"] = "ShenZhen"
        elif ott.endswith("XA"):
            job_data["location"] = "XiAn"
        else:
            job_data["location"] = "ShangHai"
        status_list.append(job_data)
    else:
        print(f"Can't get {ott} job status!")

data["job_status"] = status_list
data["update_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
# print("data", data)
with open(file_path, "w") as json_file:
    json.dump(data, json_file)


