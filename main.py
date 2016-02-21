#!/usr/bin/python

import time
import sys
import subprocess
import smtplib
import getpass
import socket
import requests

from email.mime.text import MIMEText

import config

def whatismyip():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("gmail.com",80))
	ip = s.getsockname()[0]
	s.close()
	return ip

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

def login(login_url, payload):
	s = requests.Session()
	s.post(login_url, data=payload)
	return s

def get_mapinfo():
	'http://192.168.1.1/pages/connectionStatus/GetNetworkMapInfo.html'

def run():
	prev_mapinfo = []

	myip = whatismyip()
	router_ip = '.'.join(myip.split('.')[:-1]) + '.1'
	base_router_url = "http://" + router_ip

	login_url = base_router_url + "/login/login-page.cgi"
	payload = {
	    'AuthName': 'admin',
	    'Display': config.password,
	    'AuthPassword': config.password
	}

	s = login(login_url, payload)

	while True:
		mapinfo_raw = s.get(base_router_url + "/pages/connectionStatus/GetNetworkMapInfo.html").text

		if (mapinfo_raw.find("/login/login.html") >= 0):
			print "Trying to login..."
			s = login(login_url, payload)
			continue

		# [u'192.168.1.3 Abhinays-iMac', u'192.168.1.2 unknown', u'192.168.1.4 iPh', u'192.168.1.7 Abhinays-iPhone', u'192.168.1.8 AbhinaypleWatch', u'192.168.1.9 PJ', u'192.168.1.10 iPhone', u'192.168.1.13 raspberrypi', u'192.168.1.14 abhiomkar-macbookair', u'192.168.1.16 unknown']
		mapinfo = map(lambda x: x.split('/')[5] + " " + x.split('/')[1], mapinfo_raw.split("\n")[2].split('|'))

		mapinfo = filter(lambda x: x.split()[1] not in config.excluded_hosts, mapinfo)

		# print "Found " + ', '.join(map(lambda x: x.split()[1], mapinfo))

		if (mapinfo != prev_mapinfo):

			offline_devices = list(set(prev_mapinfo).difference(mapinfo))
			online_devices = list(set(mapinfo).difference(prev_mapinfo))

			print " online_devices: ", online_devices
			print "offline_devices: ", offline_devices

			if offline_devices:
				if len(offline_devices) > 1:
					who_left = ', '.join(map(lambda x: x.split()[1], offline_devices[:-1]))
					who_left += ' and ' + offline_devices[-1].split()[1]
				elif len(offline_devices) == 1:
					who_left = offline_devices[0].split()[1]

				if len(offline_devices) > 0:
					send_mail_s(who_left + ' appears to be left your home.')

			if online_devices:
				if len(online_devices) > 1:
					who_isin = ', '.join(map(lambda x: x.split()[1], online_devices[:-1]))
					who_isin += ' and ' + online_devices[-1].split()[1]
					send_mail_s(who_isin + ' are in the house.')
				elif len(online_devices) == 1:
					who_isin = online_devices[0].split()[1]
					send_mail_s(who_isin + ' is in the house.')

		prev_mapinfo = mapinfo
		time.sleep(15)

if __name__ == "__main__":
	run()
