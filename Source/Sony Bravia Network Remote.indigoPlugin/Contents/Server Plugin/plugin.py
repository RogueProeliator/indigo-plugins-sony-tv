#! /usr/bin/env python
# -*- coding: utf-8 -*-
#/////////////////////////////////////////////////////////////////////////////////////////
#/////////////////////////////////////////////////////////////////////////////////////////
# Sony TV Network Remote Control by RogueProeliator <rp@rogueproeliator.com>
# 	Indigo plugin designed to allow full control of a Sony Bravia TV via the IP control
#	protocol (wired or wireless network connection); this should control nearly any
#	Sony device (e.g. Bluray players)
#
#	Version 1.0.3:
#		Initial release of the plugin to Indigo users
#	Version 1.0.9:
#		Updated to v.9 of the framework
#		Fixed update check URL to duncanware.com address
#		Changed support forum to new IndigoDomo URL
#	Version 1.2.14:
#		Added UPnP Search debug routine
#		Added ability to pair to v3 (/sony/accessControl) devices
#		Added support for authentication token
#		Added ability to download remote IR codes from devices
#		Added the authentication type device property
#		Upgraded framework to 1.0.14
#		Switched MenuItems.xml to use DEBUGOPTIONS template from framework
#		Changed enumeration to look for all devices instead of just IRCC
#		Added device dialog check to see if we can pull the IRCC service
#		Added support for sending an arbitrary IR code from the menu
#	Version 1.4.14:
#		Added queryPath property and support pulling it from the device UPnP description
#	Version 2.0.14:
#		Added event for update available
#
#/////////////////////////////////////////////////////////////////////////////////////////
#/////////////////////////////////////////////////////////////////////////////////////////


#/////////////////////////////////////////////////////////////////////////////////////////
# Python imports
#/////////////////////////////////////////////////////////////////////////////////////////
import httplib
import re
import subprocess
import urllib2
import RPFramework
import sonyTvNetworkRemoteDevice
import xml.etree.ElementTree


#/////////////////////////////////////////////////////////////////////////////////////////
# Constants and configuration variables
#/////////////////////////////////////////////////////////////////////////////////////////


#/////////////////////////////////////////////////////////////////////////////////////////
#/////////////////////////////////////////////////////////////////////////////////////////
# Plugin
#	Primary Indigo plugin class that is universal for all devices (TV instances) to be
#	controlled
#/////////////////////////////////////////////////////////////////////////////////////////
#/////////////////////////////////////////////////////////////////////////////////////////
class Plugin(RPFramework.RPFrameworkPlugin.RPFrameworkPlugin):

	#/////////////////////////////////////////////////////////////////////////////////////
	# Class construction and destruction methods
	#/////////////////////////////////////////////////////////////////////////////////////
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	# Constructor called once upon plugin class creation; setup the device tracking
	# variables for later use
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
		# RP framework base class's init method
		super(Plugin, self).__init__(pluginId, pluginDisplayName, pluginVersion, pluginPrefs, "http://www.duncanware.com/Downloads/IndigoHomeAutomation/Plugins/SonyBraviaNetworkRemote/SonyBraviaNetworkRemoteVersionInfo.html", managedDeviceClassModule=sonyTvNetworkRemoteDevice)
		
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	# This routine is called to parse out a uPNP search results list in order to createDeviceObject
	# an indigo-friendly menu; usually will be overridden in plugin descendants
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-	
	def parseUPNPDeviceList(self, deviceList):
		try:
			menuItems = []
			deviceIdx = 0
			for networkDevice in deviceList:
				try:
					self.logDebugMessage("Found uPnP Device: " + str(networkDevice), RPFramework.RPFrameworkPlugin.DEBUGLEVEL_MED)
				
					locationREMatch = re.match(r'http://([\d\.]*)\:{0,1}(\d+)', networkDevice.location, re.I)
					ipAddress = locationREMatch.group(1) + ":" + locationREMatch.group(2)
					try:
						nameIndex = [x[0] for x in networkDevice.allHeaders].index("x-av-physical-unit-info")
						displayName = re.match(r'^pa=\"(BRAVIA KDL\-[\w]+)\";$', networkDevice.allHeaders[nameIndex][1], re.I).group(1)
					except ValueError:
						# this is not a Bravia device as the list index was
						displayName = ""
						pass
					except:	
						if self.debugLevel == RPFramework.RPFrameworkPlugin.DEBUGLEVEL_HIGH:
							self.exceptionLog()
						displayName = ipAddress
				
					# only add to the menu items if a display name is set
					if displayName != "":
						menuItems.append(("IDX" + str(deviceIdx), displayName))
					
					deviceIdx += 1
				except:
					self.logDebugMessage("Skipped previous UPnP device due to parsing error" + str(networkDevice), RPFramework.RPFrameworkPlugin.DEBUGLEVEL_MED)
				
			return menuItems
		except:
			self.exceptionLog()
			return []
			
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	# This routine is called whenever the user clicks the "Select" button on a device
	# dialog that asks for selecting from an list of enumerated devices
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-	
	def selectUPNPEnumeratedDeviceForUse(self, valuesDict, typeId, devId):
		# for our purposes, the value of the selection will be the index into the UPnP list
		# cached for the plugin
		try:
			self.logDebugMessage("Selected Device Index: " + valuesDict[self.getGUIConfigValue(typeId, RPFramework.RPFrameworkPlugin.GUI_CONFIG_UPNP_ENUMDEVICESFIELDID, "upnpEnumeratedDevices")][3:], RPFramework.RPFrameworkPlugin.DEBUGLEVEL_HIGH)
			deviceSelected = self.enumeratedDevices[int(valuesDict[self.getGUIConfigValue(typeId, RPFramework.RPFrameworkPlugin.GUI_CONFIG_UPNP_ENUMDEVICESFIELDID, "upnpEnumeratedDevices")][3:])]
			self.logDebugMessage("Found UPnP Device: " + str(deviceSelected), RPFramework.RPFrameworkPlugin.DEBUGLEVEL_HIGH)
			
			# we need to pull down the XML descriptor and see if we can find the IRCC service
			# to which we will send commands... because this is not directly the service!
			self.logDebugMessage("Downloading XML Descriptor: " + deviceSelected.location, RPFramework.RPFrameworkPlugin.DEBUGLEVEL_MED)
			response = urllib2.urlopen(deviceSelected.location)
			html = response.read()
			html = re.sub("\<root xmlns=\"[^\"]+\"", "<root", html)
			
			try:
				self.logDebugMessage("Downloaded XML Descriptor: " + html, RPFramework.RPFrameworkPlugin.DEBUGLEVEL_HIGH)
			
				# parse the descriptor as an XML document
				upnpInfoXml = xml.etree.ElementTree.fromstring(html)
				self.logDebugMessage("Successfully parsed XML descriptor", RPFramework.RPFrameworkPlugin.DEBUGLEVEL_HIGH)
				self.logDebugMessage("Root Node: " + upnpInfoXml.tag, RPFramework.RPFrameworkPlugin.DEBUGLEVEL_HIGH)
			
				# search the XML document to see if we can find the IRCC command service
				deviceNode = upnpInfoXml.find("device")
				if deviceNode == None:
					self.logDebugMessage("No 'device' node found in UPnP XML service descriptor", RPFramework.RPFrameworkPlugin.DEBUGLEVEL_HIGH)
				else:
					serviceList = deviceNode.find("serviceList")
					if serviceList == None:
						self.logDebugMessage("No 'serviceList' node found in UPnP XML service descriptor", RPFramework.RPFrameworkPlugin.DEBUGLEVEL_HIGH)
					else:
						allServices = serviceList.findall("service")
						for serviceNode in allServices:
							serviceType = serviceNode.find("serviceType").text
							if serviceType == "urn:schemas-sony-com:service:IRCC:1":
								# found the service... pull the URL required so that we can determine the Port
								controlURLMatch = re.match(r'http://([\d\.]*)(\:(\d*)){0,1}(/.*)$', serviceNode.find("controlURL").text, re.I)
								valuesDict["httpAddress"] = controlURLMatch.group(1)
								if controlURLMatch.group(3) != None:
									valuesDict["httpPort"] = controlURLMatch.group(3)
								else:
									valuesDict["httpPort"] = "80"
								valuesDict["queryPath"] = controlURLMatch.group(4)
								valuesDict["validationMsgControl"] = "99"
								return valuesDict
			except:
				self.exceptionLog()
			
			# if we made it this far we need to set the device via the location (only) and ignore the service...
			valuesDict["validationMsgControl"] = "2"
			locationURLMatch = re.match(r'http://([\d\.]*)(\:(\d*)){0,1}', deviceSelected.location, re.I)
			valuesDict["httpAddress"] = locationURLMatch.group(1)
			if locationURLMatch.group(3) == None:
				valuesDict["httpPort"] = "80"
			else:
				valuesDict["httpPort"] = locationURLMatch.group(3)
			return valuesDict
		except:
			self.exceptionLog()
		
		# an error occurred if we made it here... 
		valuesDict["validationMsgControl"] = "1"
		valuesDict["httpAddress"] = ""
		valuesDict["httpPort"] = ""
		return valuesDict
			
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	# This routine is called to attempt to read the MAC address of a device on the
	# network (based on its IP address)
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-	
	def readMACAddress(self, valuesDict, typeId, devId):
		self.logDebugMessage("User requested an attempt to read MAC address of device", RPFramework.RPFrameworkPlugin.DEBUGLEVEL_MED)
		ipAddress = valuesDict["httpAddress"]
		if ipAddress is None or ipAddress == "":
			valuesDict["macAddress"] = ":: invalid IP ::"
			return valuesDict
		else:
			try:
				# the device must be pinged in order to get its IP address into the ARP cache table
				output = subprocess.Popen(["/sbin/ping", "-c2", "-t2", ipAddress],stdout = subprocess.PIPE).communicate()[0]
				self.logDebugMessage("Ping output: " + output, RPFramework.RPFrameworkPlugin.DEBUGLEVEL_HIGH)

				# attempt to read the arp cache...
				arpResults = subprocess.Popen(["/usr/sbin/arp", "-n", ipAddress], stdout=subprocess.PIPE).communicate()[0]
				self.logDebugMessage("ARP cache output: " + arpResults, RPFramework.RPFrameworkPlugin.DEBUGLEVEL_HIGH)
				deviceMacParser = re.search(r'(([a-f\d]{1,2}\:){5}[a-f\d]{1,2})', arpResults, re.I)
				if deviceMacParser is None:
					valuesDict["macAddress"] = ":: device not found ::"
					return valuesDict
				else:
					self.logDebugMessage("ARP parse: " + str(deviceMacParser.groups()), RPFramework.RPFrameworkPlugin.DEBUGLEVEL_HIGH)
					valuesDict["macAddress"] = deviceMacParser.group(0)
					self.logDebugMessage("MAC value found: " + valuesDict["macAddress"], RPFramework.RPFrameworkPlugin.DEBUGLEVEL_MED)
					return valuesDict
			except:
				valuesDict["macAddress"] = ":: error ::"
				return valuesDict
	
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-	
	# This routine will be called whenever the user has clicked to pair one of their
	# Indigo devices to their physical device
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-	
	def pairToDevice(self, valuesDict, typeId):
		# we need to be sure that a device was selected from the list
		deviceId = int(valuesDict.get("targetDevice", "0"))
		if deviceId == 0:
			# no device was selected
			return valuesDict
		else:
			# we have the ID of the device and hopefully it is setup...
			rpDevice = self.managedDevices[deviceId]
			pinCode = valuesDict.get("devicePIN", "")
			
			# if no PIN has been entered then we attempt a direct authentication w/o PIN (it may already be
			# associated, if so then this should tell us... won't hurt anything
			if pinCode == "":
				authCommand = RPFramework.RPFrameworkCommand.RPFrameworkCommand(sonyTvNetworkRemoteDevice.CMD_AUTHENTICATE_TO_DEVICE, commandPayload=None)
				authorizeResults = rpDevice.handleUnmanagedCommandInQueue("", authCommand)
				
				# next processing depends upon the results... we must 
				if authorizeResults == sonyTvNetworkRemoteDevice.AUTH_REQUEST_RESULT_DONE:
					# things are already registered or don't need to be paired...
					valuesDict["registrationMsgControl"] = "99"
					return valuesDict
				elif authorizeResults == sonyTvNetworkRemoteDevice.AUTH_REQUEST_RESULT_PAIRREQUIRED:
					# the service was hit but a pairing is required to complete the process (pairing
					# via PIN entry)
					valuesDict["registrationMsgControl"] = "5"
					return valuesDict
				else:
					# an unknown error occurred... show a different error depending upon the debug
					# status
					if self.debug == True:
						valuesDict["registrationMsgControl"] = "1"
					else:
						valuesDict["registrationMsgControl"] = "2"
					return valuesDict
					
			else:
				# the user has entered a PIN number... attempt to register with the device now!
				authCommand = RPFramework.RPFrameworkCommand.RPFrameworkCommand(sonyTvNetworkRemoteDevice.CMD_PAIR_TO_DEVICE, commandPayload=pinCode)
				authorizeResults = rpDevice.handleUnmanagedCommandInQueue("", authCommand)
				
				# next processing depends upon the results...
				if authorizeResults == sonyTvNetworkRemoteDevice.AUTH_REQUEST_RESULT_DONE:
					# we paired up successfully!
					valuesDict["registrationMsgControl"] = "99"
					return valuesDict
				elif authorizeResults == sonyTvNetworkRemoteDevice.AUTH_REQUEST_RESULT_PAIRREQUIRED:
					# the service was hit but the pairing not accepted... maybe bad PIN number or
					# something else went wrong...
					valuesDict["registrationMsgControl"] = "6"
					return valuesDict
				else:
					# an unknown error occurred... show a different error depending upon the debug
					# status
					if self.debug == True:
						valuesDict["registrationMsgControl"] = "1"
					else:
						valuesDict["registrationMsgControl"] = "2"
					return valuesDict
					
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-	
	# This routine will be called from the menu item that allows retrieval of the IR
	# codes supported by this device
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-	
	def retrieveIRCodesFromDevice(self, valuesDict, typeId):
		try:
			# we need to be sure that a device was selected from the list
			deviceId = valuesDict.get("targetDevice", "0")
			if deviceId == "" or deviceId == "0":
				# no device was selected
				errorDict = indigo.Dict()
				errorDict["targetDevice"] = "Please select a device"
				return (False, valuesDict, errorDict)
			else:
				# we have the ID of the device and hopefully it is setup...
				# queue the command up as a RESTful post to the specified location
				self.executeAction(None, indigoActionId="downloadRemoteCommands", indigoDeviceId=int(deviceId), paramValues=indigo.Dict())
		except:
			self.exceptionLog()
			return (False, valuesDict)
		return (True, valuesDict)
		
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-	
	# This routine will be called from the user executing the menu item action to send
	# an arbitrary IR code to the Sony device
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-	
	def sendArbitraryIRCode(self, valuesDict, typeId):
		try:
			# validate that the IR code entered was valid
			deviceId = valuesDict.get("targetDevice", "0")
			irPattern = re.compile("^[a-zA-Z\d/+]{18}==$")
			irCode = valuesDict.get("irCodeToSend", "").strip()
		
			if deviceId == "" or deviceId == "0":
				# no device was selected
				errorDict = indigo.Dict()
				errorDict["targetDevice"] = "Please select a device"
				return (False, valuesDict, errorDict)
			elif irPattern.match(irCode) == None:
				errorDict = indigo.Dict()
				errorDict["irCodeToSend"] = "Invalid IR Code Format"
				return (False, valuesDict, errorDict)
			else:
				# send the code using the normal action processing...
				actionParams = indigo.Dict()
				actionParams["buttonSelect"] = irCode.strip()
				self.executeAction(None, indigoActionId="sendRemoteButton", indigoDeviceId=int(deviceId), paramValues=actionParams)
				return (True, valuesDict)
		except:
			self.exceptionLog()
			return (False, valuesDict)	