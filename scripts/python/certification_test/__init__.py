import os
import re
from pathlib import Path

from tools.yamlTool import yamlTool

base_path = os.path.dirname(os.path.realpath(__file__))
parent_path = os.path.dirname(base_path)
config_path = Path(parent_path) / "config" / "config_certification.yaml"
config_certification_file = yamlTool(config_path)
keywords = ["ohm", "planck", "oppen", "boreal", "adt4", "unknown"]
image_url = os.environ.get("TEST_IMAGE_URL")
workspace = re.findall(r"(.*?)/AutoTestRes", parent_path)[0]
test_board = os.environ.get("TEST_BOARD", "unknown")
board = next((keyword for keyword in keywords if keyword in test_board))
test_site = os.environ.get("TEST_SITE")
test_android_type = os.environ.get("TEST_SERIES")

if image_url:
    if test_site and test_android_type and board != "unknown":
        yaml_key = test_android_type + "_" + test_site + "_" + board
        yaml_key = yaml_key.lower()
        print(f"Test project info :{yaml_key}")
        config_certification = config_certification_file.get_note(yaml_key)
        android_type = test_android_type
        server_site = test_site
    else:
        raise Exception("Configuration file parsing error, exit test")
else:
    job_name = re.findall(r"OTT/(.*?)/AutoTestRes", parent_path)
    if job_name:
        job_info = job_name[0].split("_")
        android_type = job_info[0] + "_" + job_info[1]
        server_site = job_info[-1]
        board = job_info[2].lower()
        if board == "kt":
            board = "ohm"
        yaml_key = android_type + "_" + server_site + "_" + board
        yaml_key = yaml_key.lower()
        print(f"Test project info :{yaml_key}")
        config_certification = config_certification_file.get_note(yaml_key)
    else:
        raise Exception("AutoTestRes framework file path error, exit local test")
