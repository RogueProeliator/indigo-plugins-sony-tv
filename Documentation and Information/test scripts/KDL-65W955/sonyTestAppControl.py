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
		soapTemplate = """<?xml version="1.0" encoding="UTF-8"?>
		<SOAP-ENV:Envelope 
		SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"  
		xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
		<SOAP-ENV:Body>
		<m:X_SendIRCC xmlns:m="urn:schemas-sony-com:service:IRCC:1">
		<IRCCCode>AAAAAQAAAAEAAAAkAw==</IRCCCode>
		</m:X_SendIRCC>
		</SOAP-ENV:Body>
		</SOAP-ENV:Envelope>
		"""
		
		# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		# INPUT YOUR CONFIGURATION HERE
		# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		televisionIP = "192.168.178.32"
		televisionPort = 80
		authCode = "34c43339af3d40e7b1b2743331375368c"
		
		conn = httplib.HTTPConnection(televisionIP, televisionPort)
		conn.connect()
		
		print "Sending IR Code User-Agent Nickname:"
		conn = httplib.HTTPConnection(televisionIP, televisionPort)
		conn.connect()
		conn.putrequest('POST', "/sony/IRCC")
		conn.putheader("soapaction", "\"urn:schemas-sony-com:service:IRCC:1#X_SendIRCC\"")
		conn.putheader("content-type", "text/xml; charset=utf-8")
		conn.putheader("Cookie", "auth=" + authCode)
		conn.putheader("User-Agent", "DuncanwareRemote (IndigoPlugin)")
		conn.putheader("Host", televisionIP)
		conn.putheader("Cookie", "auth=" + authCode)
		conn.putheader("Content-Length", "%d" % len(soapTemplate))
		conn.endheaders()
		conn.send(soapTemplate)
		responseToREST = conn.getresponse()
		print "Response: [" + str(responseToREST.status) + "] " + str(responseToREST.getheaders()) + "\n\n" + responseToREST.read()
		print ""


	except Exception as e:
		print "Exception: " + str(e)
	