# -*- coding: utf-8 -*-
import re


def generate_row_data(html_file, android_version, project_name, class_name, chipset, test_report_prefix, build_job_url, build_number):
    # url = 'http://10.18.19.2/AutoTest/AllureReport/dvb_t/2023.07.02_14.16/report'
    regex = r'^(http:\/\/aut\.amlogic\.com\/AutoTest\/AllureReport\/\w+)'
    matches = re.match(regex, test_report_prefix)
    extracted_url = matches.group(1) if matches else None
    # if "index.html" in html_file:
    row_data = f"""
    <tr class="{android_version}-{class_name}">
        {f'<td rowspan="16">{android_version}</td>' if ((project_name == "IPTV Basic Play Control") and (android_version == "Android_S")) else ''}
        {f'<td rowspan="9">{android_version}</td>' if ((project_name == "Sanity Test") and (android_version == "Android_U") and ("index.html" in html_file)) else ''}
        {f'<td rowspan="4">Basic Function</td>' if ((project_name == "Sanity Test") and (android_version == "Android_U") and ("index.html" in html_file)) else ''}
        {f'<td rowspan="2">{android_version}</td>' if ((project_name == "Sanity Test") and (android_version == "Android_U") and ("shenzhen.html" in html_file)) else ''}
        {f'<td rowspan="2">Basic Function</td>' if ((project_name == "Sanity Test") and (android_version == "Android_U") and ("shenzhen.html" in html_file)) else ''}
        {f'<td rowspan="8">Basic Function</td>' if project_name == "IPTV Basic Play Control" else ''}
        {f'<td rowspan="2">Stress</td>' if project_name == "Stress" else ''}
        {f'<td rowspan="1">Performance</td>' if project_name == "KPI" else ''}
        {f'<td rowspan="1">Android_P</td>' if project_name == "Android P IPTV YUV" else ''}
        {f'<td rowspan="1">Android_R</td>' if project_name == "Android R IPTV YUV" else ''}
        <td rowspan="1">{project_name}</td>
        <td rowspan="1">{chipset}</td>
        <td class="jenkins_status"><img src="jenkins_png">jenkins_text</td>
        <td id="{android_version}-{class_name}" class="{android_version}-{class_name}"></td>
        <script>
        fetchData('{test_report_prefix}/widgets/summary.json', '{android_version}-{class_name}');
        </script>

        <td id="{android_version}-{class_name}-start-time" class="data-cell" data-url="{test_report_prefix}/widgets/summary.json"></td>
        <td id="{android_version}-{class_name}-duration-time" class="data-cell" data-url="{test_report_prefix}/widgets/summary.json"></td>

        <script>
         fetchSummaryData('{test_report_prefix}/widgets/summary.json', '{android_version}-{class_name}-start-time', '{android_version}-{class_name}-duration-time');
        </script>

        <td><a target='_blank' href='{test_report_prefix}'>Report</a></td>
        <td title="header=[Client Computer Information] body=[Name: Autotest124_BJ<br><br>IP Address:10.68.9.144]">
            <ul id="jenkins_list">
              <li class='jenkins_log'><a target='_blank' href='{build_job_url}/console'>Log</a></li>
              <li class="jenkins_id"><a target='_blank' href="{build_job_url}">#{build_number}</a></li>
            </ul>
        </td>
        <td><a target='_blank' href='{extracted_url}'>History</a></td>
        <td title="header=[Comments] body=[]" class="comments_more">N/A</td>
    </tr>
    """

    return row_data


def generate_html_file(android_version, html_file, project_name, class_name, chipset, test_report_prefix, build_job_url, build_number):
    try:
        # 读取现有的 HTML 模板
        with open(html_file, "r") as file:
            html_template = file.read()

        # 生成每个项目的行数据并插入到模板中
        # for project_name in project_names:
        row_data = generate_row_data(html_file, android_version, project_name, class_name, chipset, test_report_prefix, build_job_url, build_number)
        print(row_data)

        # 构建正则表达式的模式
        escaped_android_version = re.escape(android_version)
        escaped_class_name = re.escape(class_name)
        print(escaped_class_name)
        pattern = fr'<tr\s+class="{escaped_android_version}-{escaped_class_name}"[^>]*>.*?</tr>'
        # 使用正则表达式匹配并替换整个 <tr> 标签
        new_html = re.sub(pattern, row_data, html_template, flags=re.DOTALL)
        #print(new_html)

        # 将修改后的内容写回原始文件
        with open(html_file, 'w') as file:
            file.write(new_html)

        with open("project_data_row" + "/" + "data_row.txt", "a") as f:
            f.write(row_data)
    finally:
        print("ok")


if __name__ == '__main__':
    generate_html_file("/home/poppy/AUT/AutoTestRes/scripts/python/report_bck.html", "IPTV Basic Play Control", "IPTV Basic Play Control", "111", "111", "111", "111", "111", "111")




