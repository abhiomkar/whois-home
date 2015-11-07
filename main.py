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

def ip_scan():
	_output = subprocess.Popen("nmap -sP 192.168.1.0/28 | grep report | awk '{print $5}'", shell=True, stdout=subprocess.PIPE).stdout.read()
	if _output:
		_list = _output.split()
		_list = map(lambda x: x.replace('.Home', ''), _list)
		_excluded = map(lambda x: x.replace('.Home', ''), config.excluded_hosts)
		return filter(lambda x: x not in _excluded, _list)
	else:
		return []

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
	return subprocess.Popen("mail -s '%s' %s < /dev/null" % (msg, config.send_to), shell=True, stdout=subprocess.PIPE).stdout.read()

def run():
	prev_scan_list = []
	while True:
		scan_list = ip_scan()

		if scan_list:
			if (scan_list != prev_scan_list):
				offline_devices = list(set(prev_scan_list).difference(set(scan_list)))
				online_devices = list(set(scan_list).difference(set(prev_scan_list)))

				if offline_devices:
					if len(offline_devices) > 1:
						who_left = ', '.join(offline_devices[:-1])
						who_left += ' and ' + offline_devices[-1]
					elif len(offline_devices) == 1:
						who_left = offline_devices[0]

					send_mail_s(who_left + ' appears to be left your home.')

				if online_devices:
					if len(online_devices) > 1:
						who_isin = ', '.join(online_devices[:-1])
						who_isin += ' and ' + online_devices[-1]
						send_mail_s(who_isin + ' are in the house.')
					elif len(online_devices) == 1:
						who_isin = online_devices[0]
						send_mail_s(who_isin + ' is in the house.')

		prev_scan_list = scan_list
		time.sleep(60)

if __name__ == "__main__":
	run()
