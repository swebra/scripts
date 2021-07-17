#/bin/sh

ip=$(ip -o -f inet addr show | awk '/scope global/ {print $4}')
nmap -sn $ip
