#!/usr/bin/python

# $ nmap -sP 192.168.1.0/28 | grep report | awk '{print $5}'
# D-Link123.Home
# Abhinays-iMac.Home
# Abhinays-iPhone.Home
# raspberrypi.Home
# android-4b5451e9e51fd693.Home

import time
import sys
import subprocess
import smtplib
import getpass
import socket

from email.mime.text import MIMEText

import config

def ip_scan(ip, retry=0):
	subprocess.Popen("arp -a", shell=True, stdout=subprocess.PIPE).stdout.read()

	scan_result = []

	while True:
		print "nmap -sP %s 2> /dev/null | grep report | grep '(' | awk '{print $5, $6}'" % (ip)
		_output = subprocess.Popen("nmap -sP %s 2> /dev/null | grep report | grep '(' | awk '{print $5, $6}'" % (ip), shell=True, stdout=subprocess.PIPE).stdout.read()
		# _output = subprocess.Popen("nmap -sP 192.168.1.1-20 && arp -a | grep -v -e '^?' | awk '{print $1}'", shell=True, stdout=subprocess.PIPE).stdout.read()
		if _output:
			_list = _output.strip().split("\n")
			_list = map(lambda x: {"hostname": x.split()[0], "ip": x.split()[1].lstrip('(').rstrip(')')}, _list)
			_list = filter(lambda x: x["hostname"] not in config.excluded_hosts, _list)

			scan_result.extend([entry for entry in _list if entry not in scan_result])

		else:
			scan_result.extend([])

		if retry == 0:
			break

		retry = retry - 1
		time.sleep(4)

	return scan_result

def whatismyip():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("gmail.com",80))
	ip = s.getsockname()[0]
	s.close()
	return ip

def get_hostname_byips(ip_list, scan_list):
	return map(lambda x: x["hostname"].replace('.Home', ''), filter(lambda x: True if x["ip"] in ip_list else False, scan_list))

def send_mail(msg):
	sender = getpass.getuser() + '@' + socket.gethostname()

	m = MIMEText("")
	m["Subject"] = msg
	m["From"] = sender
	m["To"] = config.send_to

	s = smtplib.SMTP('localhost')

	s.sendmail(sender, [config.send_to], m.as_string())
	s.quit()
	return s

def send_mail_s(msg):
	print "mail -s '%s' %s < /dev/null" % (msg, config.send_to)
	return subprocess.Popen("mail -s '%s' %s < /dev/null" % (msg, config.send_to), shell=True, stdout=subprocess.PIPE).stdout.read()

def run():
	prev_scan_list = []
	while True:
		myip = whatismyip()
		# 192.168.1.2-20
		ip_range = ".".join(myip.split('.')[:-1]) + ".2-25"
		scan_list = ip_scan(ip_range)

		print scan_list

		if (scan_list != prev_scan_list):
			offline_devices = set([x["ip"] for x in prev_scan_list]).difference(set([x["ip"] for x in scan_list]))
			online_devices = set([x["ip"] for x in scan_list]).difference(set([x["ip"] for x in prev_scan_list]))

			all_scan_list = []
			for entry in (prev_scan_list + scan_list):
				if entry not in all_scan_list:
					all_scan_list.append(entry)

			# offline_devices_list = [entry for entry in all_scan_list if entry["ip"] in offline_devices]
			# online_devices_list = [entry for entry in all_scan_list if entry["ip"] in online_devices]

			print " online_devices: ", online_devices
			print "offline_devices: ", offline_devices

			if offline_devices:
				# retry for 5 times to check if they really left?
				results_after_retry = ip_scan(" ".join(offline_devices), retry=10)

				# update the scan_result accordingly
				scan_list.extend([entry for entry in results_after_retry if entry not in scan_list])

				# if any of them found online again remove it from offline_devices and add them back to online_devices
				offline_devices.difference_update(map(lambda x: x["ip"], results_after_retry))

				offline_devices_names = get_hostname_byips(offline_devices, all_scan_list)

				if len(offline_devices) > 1:
					who_left = ', '.join(offline_devices_names[:-1])
					who_left += ' and ' + offline_devices_names[-1]
				elif len(offline_devices) == 1:
					who_left = offline_devices_names[0]

				if len(offline_devices) > 0:
					send_mail_s(who_left + ' appears to be left your home.')

			online_devices_names = get_hostname_byips(online_devices, scan_list)

			if online_devices:
				if len(online_devices) > 1:
					who_isin = ', '.join(online_devices_names[:-1])
					who_isin += ' and ' + online_devices_names[-1]
					send_mail_s(who_isin + ' are in the house.')
				elif len(online_devices) == 1:
					who_isin = online_devices_names[0]
					send_mail_s(who_isin + ' is in the house.')

		prev_scan_list = scan_list
		time.sleep(15)

if __name__ == "__main__":
	run()
