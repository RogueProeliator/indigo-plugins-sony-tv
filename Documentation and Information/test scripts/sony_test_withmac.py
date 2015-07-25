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
		<IRCCCode>AAAAAgAAADAAAAAuAw==</IRCCCode>
		</m:X_SendIRCC>
		</SOAP-ENV:Body>
		</SOAP-ENV:Envelope>
		"""
	
		# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		# INPUT YOUR CONFIGURATION HERE
		# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		fakeMAC = "90-b2-1f-bb-07-53"
		televisionIP = "192.168.178.32"
		televisionPort = 80
		
		conn = httplib.HTTPConnection(televisionIP, televisionPort)
		conn.connect()

		print "Sending IR Code as iPhone MAC..."
		conn.putrequest('POST', "/sony/IRCC")
		conn.putheader("Content-type", "text/xml; charset=\"UTF-8\"")
		conn.putheader("Host", televisionIP + ":" + str(televisionPort))
		conn.putheader("User-Agent", "MediaRemote/3.0.1 CFNetwork/548.0.4 Darwin/11.0.0")
		conn.putheader("X-CERS-DEVICE-INFO", "iPhone OS5.0.1/3.0.1/iPhone3,3")
		conn.putheader("X-CERS-DEVICE-ID", "MediaRemote:" + fakeMAC)
		conn.putheader("SOAPAction", "\"urn:schemas-sony-com:service:IRCC:1#X_SendIRCC\"")
		conn.putheader("Content-Length", "%d" % len(soapTemplate))
		conn.endheaders()
		conn.send(soapTemplate)
		responseToREST = conn.getresponse()
		print "Response to iPhone MAC: [" + str(responseToREST.status) + "] " + responseToREST.read()
		print ""
		
		#regconn = httplib.HTTPConnection(televisionIP, televisionPort)
		#regconn.connect()
		#regconn.request("GET", "/cers/api/register?name=indigoRemote&registrationType=new&deviceId=MediaRemote%3A" + fakeMAC)
		#responseToReg = regconn.getresponse()
		#print "Response to Registration: [" + str(responseToReg.status) + "] " + responseToReg.read()

	except Exception as e:
		print "Exception: " + str(e)
	