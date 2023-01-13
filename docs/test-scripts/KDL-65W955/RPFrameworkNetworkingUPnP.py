#! /usr/bin/env python
# -*- coding: utf-8 -*-
#/////////////////////////////////////////////////////////////////////////////////////////
#/////////////////////////////////////////////////////////////////////////////////////////
# RPFrameworkNetworkingUPnP by RogueProeliator <rp@rogueproeliator.com>
# 	Classes that handle various aspects of Universal Plug and Play protocols such as
#	discovery of devices.
#	
#	Version 1.0.0 [10-18-2013]:
#		Initial release of the plugin framework
#
#/////////////////////////////////////////////////////////////////////////////////////////
#/////////////////////////////////////////////////////////////////////////////////////////

#/////////////////////////////////////////////////////////////////////////////////////////
# Python imports
#/////////////////////////////////////////////////////////////////////////////////////////
import socket
import httplib
import StringIO

#/////////////////////////////////////////////////////////////////////////////////////////
#/////////////////////////////////////////////////////////////////////////////////////////
# SSDPResponse
#	Handles the request (and response) to SSDP queries initiated in order to find Network
#	devices such as Roku boxes
#/////////////////////////////////////////////////////////////////////////////////////////
#/////////////////////////////////////////////////////////////////////////////////////////
class SSDPResponse(object):
	######################################################################################
	# Internal class for creating the socket necessary to send the request
	######################################################################################
	class _FakeSocket(StringIO.StringIO):
		def makefile(self, *args, **kw):
			return self
		
	def __init__(self, response):
		r = httplib.HTTPResponse(self._FakeSocket(response))
		r.begin()
		self.location = r.getheader("location")
		self.usn = r.getheader("usn")
		self.st = r.getheader("st")
		self.server = r.getheader("server")
		self.cache = r.getheader("cache-control").split("=")[1]
		self.allHeaders = r.getheaders()
		
	def __repr__(self):
		return "<SSDPResponse(%(location)s, %(st)s, %(usn)s, %(server)s)>" % (self.__dict__) + str(self.allHeaders) + "</SSDPResonse>"


#/////////////////////////////////////////////////////////////////////////////////////////
#/////////////////////////////////////////////////////////////////////////////////////////
# uPnPDiscover
#	Module-level function that executes a uPNP MSEARCH operation to find devices matching
#	a given service
#/////////////////////////////////////////////////////////////////////////////////////////
#/////////////////////////////////////////////////////////////////////////////////////////
def uPnPDiscover(service, timeout=2, retries=1):
    group = ("239.255.255.250", 1900)
    message = "\r\n".join([
        'M-SEARCH * HTTP/1.1',
        'HOST: ' + group[0] + ':' + str(group[1]),
        'MAN: "ssdp:discover"',
        'ST: ' + service,'MX: 3','',''])
    socket.setdefaulttimeout(timeout)
    responses = {}
    for _ in range(retries):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.sendto(message, group)
        while True:
            try:
                response = SSDPResponse(sock.recv(1024))
                responses[response.location] = response
            except socket.timeout:
                break
    return responses.values()
 