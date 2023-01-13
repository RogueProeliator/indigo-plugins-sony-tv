#! /usr/bin/env python
# -*- coding: utf-8 -*-
import functools
import httplib
import Queue
import os
import re
import string
import socket
import sys
import threading
import telnetlib
import time
import urllib

if __name__ == '__main__':
	try:
		#payload = "{\"id\":2,\"method\":\"getVersions\",\"version\":\"1.0\",\"params\":[]}"
		payload = '{"id":20,"method":"getRemoteControllerInfo","version":"1.0","params":[]}'
		#payload = '{"id":20,"method":"getSystemSupportedFunction","version":"1.0","params":[]}'
		#payload = '{"id":20,"method":"getSystemInformation","version":"1.0","params":[]}'
		#payload = '{"id":9,"method":"getMethodTypes","version":"1.0","params":["1.0"]}'
		
		conn = httplib.HTTPConnection("172.16.1.80", 80)
		conn.connect()
		conn.putrequest('POST', "/sony/system")
		#conn.putrequest('POST', "/sony/irCommandProxy")
		conn.putheader("Content-type", "application/json")
		conn.putheader("User-Agent", "TVSideView/2.0.1 CFNetwork/672.0.8 Darwin/14.0.0")
		#conn.putheader("Cookie", "auth=37549a06c7c54f1790665a7ebccd4a36")
		conn.putheader("Content-Length", "%d" % len(payload))
		conn.endheaders()
		conn.send(payload)

		responseToREST = conn.getresponse()
		print "Response: [" + str(responseToREST.status) + "] " + responseToREST.read()

	except Exception as e:
		print "Exception: " + str(e)
	