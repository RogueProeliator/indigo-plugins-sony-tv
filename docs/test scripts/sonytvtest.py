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
		<IRCCCode xmlns:dt="urn:schemas-microsoft-com:datatypes" dt:dt="string">AAAAAgAAAKQAAAA7Aw==</IRCCCode>
		</m:X_SendIRCC>
		</SOAP-ENV:Body>
		</SOAP-ENV:Envelope>
		"""
	
		conn = httplib.HTTPConnection("172.16.1.113", 80)
		conn.connect()
		conn.putrequest('POST', "/sony/IRCC")
		conn.putheader("Content-type", "text/xml; charset=\"UTF-8\"")
		#conn.putheader("User-Agent", "Microsoft-Windows/6.1 UPnP/1.0")
		conn.putheader("SOAPAction", "\"urn:schemas-sony-com:service:IRCC:1#X_SendIRCC\"")
		conn.putheader("Content-Length", "%d" % len(soapTemplate))
		#conn.putheader("Host", "172.16.113")
		conn.endheaders()
		conn.send(soapTemplate)

		responseToREST = conn.getresponse()
		print "Response: [" + str(responseToREST.status) + "] " + responseToREST.read()

	except Exception as e:
		print "Exception: " + str(e)
	