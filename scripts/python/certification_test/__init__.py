import os
import subprocess

from tools.yamlTool import yamlTool

base_path = os.path.dirname(os.path.realpath(__file__))
parent_path = os.path.dirname(base_path)
config_certification_file = yamlTool(parent_path + '/config/config_certification.yaml')
image_url = os.environ.get("TEST_IMAGE_URL")
workspace = os.environ.get("WORKSPACE", subprocess.getoutput("pwd"))
if image_url:
    if "Android_U" in image_url:
        if "_SH" in workspace:
            config_certification = config_certification_file.get_note("android_u_sh")
            server_site = "SH"
        if "_XA" in workspace:
            config_certification = config_certification_file.get_note("android_u_xa")
            server_site = "XA"
        android_type = "Android_U"
    if "Android_S" in image_url:
        config_certification = config_certification_file.get_note("android_s")
        android_type = "Android_S"
        server_site = "SH"
else:
    if "Android_S_" in workspace:
        config_certification = config_certification_file.get_note("android_s")
        android_type = "Android_S"
        server_site = "SH"
    if "Android_U_" in workspace:
        if "_SH" in workspace:
            config_certification = config_certification_file.get_note("android_u_sh")
            server_site = "SH"
        if "_XA" in workspace:
            config_certification = config_certification_file.get_note("android_u_xa")
            server_site = "XA"
        android_type = "Android_U"
