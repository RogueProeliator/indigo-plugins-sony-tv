#! /usr/bin/env python
# -*- coding: utf-8 -*-

import RPFrameworkNetworkingUPnP

if __name__ == "__main__":
    print "Issuing discover command..."
    deviceList = RPFrameworkNetworkingUPnP.uPnPDiscover("ssdp:all", timeout=8)
    for device in deviceList:
		print "Device Found:"
		print "   Location: " + device.location
		print "   USN: " + device.usn
		print "   ST: " + device.st
		print "   Cache: " + device.cache