#!/bin/bash

timeout=3600  # Timeout duration of 1 hour (in seconds)
counter=0     # Counter

while [ $counter -lt $timeout ]; do
    ping -c 1 www.google.com > /dev/null  # Perform a single ICMP request to ping www.google.com and redirect the output to /dev/null
    if [ $? -eq 0 ]; then  # If the ping is successful, the exit code will be 0
        echo "Network connection is active, successfully pinged."
        exit 0
    fi

    echo "Network connection is not available, continuing to ping..."
    sleep 5  # Pause for 5 seconds in each iteration, adjust as needed
    counter=$((counter + 5))
done

echo "Network connection is not available, exceeded the 1-hour timeout."
exit 1

