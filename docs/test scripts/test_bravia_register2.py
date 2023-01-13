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
import base64

if __name__ == '__main__':
	try:
	
		# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		# INPUT YOUR CONFIGURATION HERE
		# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		televisionIP = "192.168.178.32"
		televisionPort = 80
		hostname = "DuncanwareRemote"
		
		jsontosend = '{"id":13, "method":"actRegister", "version":"1.0", "params": [{"clientid":"' + hostname + ':34c43339-af3d-40e7-b1b2-743331375368c", "nickname":"' + hostname + ' (IndigoPlugin)"}, [{"clientid":"' + hostname + ':34c43339-af3d-40e7-b1b2-743331375368c", "value":"yes", "nickname":"' + hostname + ' (IndigoPlugin)", "function":"WOL"}]]}'
		conn = httplib.HTTPConnection(televisionIP, televisionPort)
		conn.connect()
		
		conn.putrequest('POST', "/sony/accessControl")
		conn.putheader("Content-type", "application/json")
		conn.putheader("Content-Length", "%d" % len(jsontosend))
		conn.endheaders()
		
		conn.send(jsontosend)
		responseToREST = conn.getresponse()
		print "PRE Auth Headers: " + str(responseToREST.getheaders())
		print "PRE Auth Response: [" + str(responseToREST.status) + "] " + responseToREST.read()
		
		print "************************************************"
		print "************************************************"
		accessCode = str(input('Enter Access Code from TV:'))
		
		conn2 = httplib.HTTPConnection(televisionIP, televisionPort)
		conn2.connect()
		
		conn2.putrequest('POST', "/sony/accessControl")
		conn2.putheader("Content-type", "application/json")
		conn2.putheader("Authorization", "Basic " + base64.b64encode(":" + accessCode))
		conn2.putheader("Content-Length", "%d" % len(jsontosend))
		conn2.endheaders()
		
		conn2.send(jsontosend)
		responseToAuth = conn2.getresponse()
		print "POST Auth Headers: " + str(responseToAuth.getheaders())
		print "POST Auth Response: [" + str(responseToAuth.status) + "] " + responseToAuth.read()
		
	
	except Exception as e:
		print "Exception: " + str(e)
	