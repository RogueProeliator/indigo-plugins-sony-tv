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
	
		# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		# INPUT YOUR CONFIGURATION HERE
		# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		televisionIP = "192.168.178.32"
		televisionPort = 80
		hostname = ""
		
		jsontosend = '{"id":13, "method":"actRegister", "version":"1.0", "params": [{"clientid":"' + hostname + ':34c43339-af3d-40e7-b1b2-743331375368c", "nickname":"' + hostname + ' (IndigoPlugin)"}, [{"clientid":"' + hostname + ':34c43339-af3d-40e7-b1b2-743331375368c", "value":"yes", "nickname":"' + hostname + ' (IndigoPlugin)", "function":"WOL"}]]}'
		conn = httplib.HTTPConnection(televisionIP, televisionPort)
		conn.connect()
		
		conn.putrequest('POST', "/sony/webauth/auth_default")
		conn.putheader("Content-type", "application/json")
		conn.putheader("Content-Length", "%d" % len(jsontosend))
		conn.endheaders()
		
		conn.send(jsontosend)
		responseToREST = conn.getresponse()
		print "Response: [" + str(responseToREST.status) + "] " + responseToREST.read()
		print "Headers: " + str(responseToREST.getheaders())
	
	except Exception as e:
		print "Exception: " + str(e)
	