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
		soapTemplate = """<?xml version="1.0" encoding="UTF-8"?>
		<SOAP-ENV:Envelope 
		SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"  
		xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
		<SOAP-ENV:Body>
		<m:X_SendIRCC xmlns:m="urn:schemas-sony-com:service:IRCC:1">
		<IRCCCode>AAAAAQAAAAEAAAASAw==</IRCCCode>
		</m:X_SendIRCC>
		</SOAP-ENV:Body>
		</SOAP-ENV:Envelope>
		"""
		
		# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		# INPUT YOUR CONFIGURATION HERE
		# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		televisionIP = "192.168.178.32"
		televisionPort = 80
		authCode = "34c43339-af3d-40e7-b1b2-743331375368c"
		registerJSONTemplate = '{"id":13, "method":"actRegister", "version":"1.0", "params": [{"clientid":"DuncanwareRemote:' + authCode +'", "nickname":"DuncanwareRemote (IndigoPlugin)"}, [{"clientid":"DuncanwareRemote:' + authCode + '", "value":"yes", "nickname":"DuncanwareRemote (IndigoPlugin)", "function":"WOL"}]]}'
		
		
		conn = httplib.HTTPConnection(televisionIP, televisionPort)
		conn.connect()
		
		print "Sending JSON Registration Request:"
		conn = httplib.HTTPConnection(televisionIP, televisionPort)
		conn.connect()
		conn.putrequest('POST', "/sony/accessControl")
		conn.putheader("content-type", "application/json")
		conn.putheader("Connection", "close")
		conn.putheader("User-Agent", "DuncanwareRemote (IndigoPlugin)")
		conn.putheader("Host", televisionIP)
		conn.putheader("Content-Length", "%d" % len(registerJSONTemplate))
		conn.endheaders()
		conn.send(registerJSONTemplate)
		responseToREST = conn.getresponse()
		print "Response: [" + str(responseToREST.status) + "] " + str(responseToREST.getheaders()) + "\n\n" + responseToREST.read()
		print ""
		
		if responseToREST.status == 401:
			print "************************************************"
			print "************************************************"
			accessCode = str(input('Enter Access Code from TV:'))
			
			print "Sending JSON Registration Request With PIN:"
			conn.putrequest('POST', "/sony/accessControl")
			conn.putheader("content-type", "application/json")
			conn.putheader("Connection", "close")
			conn.putheader("Authorization", "Basic " + base64.b64encode(":" + accessCode))
			conn.putheader("User-Agent", "DuncanwareRemote (IndigoPlugin)")
			conn.putheader("Host", televisionIP)
			conn.putheader("Content-Length", "%d" % len(registerJSONTemplate))
			conn.endheaders()
			conn.send(registerJSONTemplate)
			responseToREST = conn.getresponse()
			print "Response: [" + str(responseToREST.status) + "] " + str(responseToREST.getheaders()) + "\n\n" + responseToREST.read()
			print ""
			
		# the last reponseToREST (however it came back) should have the authorization cookie...
		cookieParser = re.compile(ur'(auth=[a-zA-Z\d]+);', re.MULTILINE | re.IGNORECASE)
		authCookie = re.search(cookieParser, responseToREST.getheader("set-cookie")).group(1)
		print "Found authorization cookie: " + authCookie
		
		# attempting to control tv with auth cookie...
		print "Sending IR code to TV..."
		conn.putrequest('POST', "/sony/IRCC")
		conn.putheader("soapaction", "urn:schemas-sony-com:service:IRCC:1#X_SendIRCC")
		conn.putheader("content-type", "text/xml; charset=utf-8")
		conn.putheader("Cookie", authCookie)
		conn.putheader("User-Agent", "DuncanwareRemote (IndigoPlugin)")
		conn.putheader("Host", televisionIP)
		conn.putheader("Content-Length", "%d" % len(soapTemplate))
		conn.endheaders()
		conn.send(soapTemplate)
		responseToREST = conn.getresponse()
		print "Response: [" + str(responseToREST.status) + "] " + str(responseToREST.getheaders()) + "\n\n" + responseToREST.read()
		print ""

	except Exception as e:
		print "Exception: " + str(e)
	