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
		
		conn = httplib.HTTPConnection(televisionIP, televisionPort)
		conn.connect()
		
		print "Attempting to register with CERS API... GUID device ID"
		conn.request("GET", "/cers/api/register?name=indigoRemote&registrationType=new&deviceId=34c43339-af3d-40e7-b1b2-743331375368c")
		responseToGUID = conn.getresponse()
		print "CERS GUID Headers: " + str(responseToGUID.getheaders())
		print "CERS GUID Response: [" + str(responseToGUID.status) + "] " + responseToGUID.read()
		
		
		print "Attempting to register with CERS API... GUID device ID AND Auth Cookie"
		conn.request("GET", "/cers/api/register?name=indigoRemote&registrationType=new&deviceId=34c43339-af3d-40e7-b1b2-743331375368c")
		conn.putheader("Cookie", "auth=3d76f00d8c7e4473fbc8c3d952a33756f863427596fc76c4395367bea25b3288")
		conn.endheaders()
		responseToGUIDCookie = conn.getresponse()
		print "CERS GUID/Cookie Headers: " + str(responseToGUIDCookie.getheaders())
		print "CERS GUID/Cookie Response: [" + str(responseToGUIDCookie.status) + "] " + responseToGUIDCookie.read()

		#print "Sending IR Code With X-CERS-DEVICE Headers"
		#conn.putrequest('POST', "/sony/IRCC")
		#conn.putheader("Host", televisionIP + ":" + str(televisionPort))
		#conn.putheader("Content-type", "text/xml; charset=\"UTF-8\"")
		#conn.putheader("X-CERS-DEVICE-INFO", "Duncanware (IndigoPlugin)")
		#conn.putheader("X-CERS-DEVICE-ID", "DuncanwareRemote:34c43339-af3d-40e7-b1b2-743331375368c")
		#conn.putheader("Cookie", "auth=3d76f00d8c7e4473fbc8c3d952a33756f863427596fc76c4395367bea25b3288")
		#conn.putheader("SOAPAction", "\"urn:schemas-sony-com:service:IRCC:1#X_SendIRCC\"")
		#conn.putheader("Content-Length", "%d" % len(soapTemplate))
		#conn.endheaders()
		#conn.send(soapTemplate)
		#responseToREST = conn.getresponse()
		#print "Response: [" + str(responseToREST.status) + "] " + responseToREST.read()
		#print ""
		
		#print "Sending IR Code With SideView User Agent Header"
		#conn2 = httplib.HTTPConnection(televisionIP, televisionPort)
		#conn2.connect()
		#conn2.putrequest('POST', "/sony/IRCC")
		#conn2.putheader("Host", televisionIP + ":" + str(televisionPort))
		#conn2.putheader("Content-type", "text/xml; charset=\"UTF-8\"")
		#conn2.putheader("User-Agent", "TVSideView/2.0.1 CFNetwork/672.0.8 Darwin/14.0.0")
		#conn2.putheader("Cookie", "auth=3d76f00d8c7e4473fbc8c3d952a33756f863427596fc76c4395367bea25b3288")
		#conn2.putheader("SOAPAction", "\"urn:schemas-sony-com:service:IRCC:1#X_SendIRCC\"")
		#conn2.putheader("Content-Length", "%d" % len(soapTemplate))
		#conn2.endheaders()
		#conn2.send(soapTemplate)
		#responseToREST = conn2.getresponse()
		#print "Response: [" + str(responseToREST.status) + "] " + responseToREST.read()
		#print ""
		
		#print "Attempting to read System Information..."
		#payload = '{"id":20,"method":"getSystemInformation","version":"1.0","params":[]}'
		#sysInfoConn = httplib.HTTPConnection(televisionIP, televisionPort)
		#sysInfoConn.connect()
		#sysInfoConn.putrequest('POST', "/sony/system")
		#sysInfoConn.putheader("Content-type", "application/json")
		#sysInfoConn.putheader("Cookie", "auth=3d76f00d8c7e4473fbc8c3d952a33756f863427596fc76c4395367bea25b3288")
		#sysInfoConn.putheader("Content-Length", "%d" % len(payload))
		#sysInfoConn.endheaders()
		#sysInfoConn.send(payload)
		#responseToSysInfo = sysInfoConn.getresponse()
		#print "Response: [" + str(responseToSysInfo.status) + "] " + responseToSysInfo.read()
		#print ""
		
		#print "Attempting to read Remote Control Information..."
		#payload = '{"id":20,"method":"getRemoteControllerInfo","version":"1.0","params":[]}'
		#remoteInfoConn = httplib.HTTPConnection(televisionIP, televisionPort)
		#remoteInfoConn.connect()
		#remoteInfoConn.putrequest('POST', "/sony/system")
		#remoteInfoConn.putheader("Content-type", "application/json")
		#remoteInfoConn.putheader("Content-Length", "%d" % len(payload))
		#remoteInfoConn.endheaders()
		#remoteInfoConn.send(payload)
		#responseToRemoteInfo = remoteInfoConn.getresponse()
		#print "Response: [" + str(responseToRemoteInfo.status) + "] " + responseToRemoteInfo.read()
		#print ""
		
		#regconn = httplib.HTTPConnection(televisionIP, televisionPort)
		#regconn.connect()
		#regconn.request("GET", "/cers/api/register?name=indigoRemote&registrationType=new&deviceId=MediaRemote%3A" + fakeMAC)
		#responseToReg = regconn.getresponse()
		#print "Response to Registration: [" + str(responseToReg.status) + "] " + responseToReg.read()

	except Exception as e:
		print "Exception: " + str(e)
	