#!/bin/bash
# Define your report and log URLs
REPORT_URL=$(jq -r '.report_url' last_report/summary.json) # Assuming you're fetching it from the JSON
LOG_URL=$1 # Replace with your actual log URL
input_file="last_report/index.html"
start_tag="<table"
end_tag="</table>"
content=""
is_target_table=false
while IFS= read -r line; do
    if [[ $line == *"$start_tag"* ]]; then
        if [[ $line =~ "summary" ]];then
            is_target_table=true
#            content+="$line"
        fi
    fi
    if $is_target_table; then
        content+="$line"
    fi
    if [[ $line == *"$end_tag"* ]] && [[ ! -z $content ]]; then
        is_target_table=false
        break
    fi
done < "$input_file"
# Create or overwrite report.html from the here document
cat <<EOF > mail_report.html
<!DOCTYPE html>
<html>
<head>
    <title>Test Report</title>
    <style>
        body {
            color: #333;
            font-family: "Microsoft YaHei",arial,sans-serif;
            font-size: 13px;
            margin: 10;
            padding: 10;
        }
        table.summary {
            background-color: #d4e9a9;
            border: 0 solid #a5c639;
            border-collapse: collapse;
            margin-left: auto;
            margin-right: auto;
        }
        table.summary th {
            background-color: #a5c639;
            font-size: 1.2em;
            padding: .5em;
        }
        table.summary td {
            border: 0 inset #808080;
            font-size: 1em;
            padding: .5em;
            vertical-align: top;
        }
        p {
            font-size: 18px;
            font-weight: bold;
            text-align: center;
        }
        hr {
            border: 1px solid #a5c639;
            /* margin: 20px 0; */
        }
    </style>
</head>
<body>
    <p>Test Results</p>
    <div>
        $content
    </div>
    <br>
    <p>Test Report: <a href="$REPORT_URL">View Full Report</a></p>
    <p>Test Logs: <a href="$LOG_URL">View Full Logs</a></p>
    <hr>
    <p>Test Regression</p>
</body>
</html>
EOF

