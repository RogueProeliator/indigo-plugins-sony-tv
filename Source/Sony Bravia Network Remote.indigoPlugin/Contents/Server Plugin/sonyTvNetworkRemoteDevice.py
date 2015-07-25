#! /usr/bin/env python
# -*- coding: utf-8 -*-
#/////////////////////////////////////////////////////////////////////////////////////////
#/////////////////////////////////////////////////////////////////////////////////////////
# Sony TV Network Remote Control by RogueProeliator <rp@rogueproeliator.com>
# 	See plugin.py for more plugin details and information
#/////////////////////////////////////////////////////////////////////////////////////////
#/////////////////////////////////////////////////////////////////////////////////////////

#/////////////////////////////////////////////////////////////////////////////////////////
# Python imports
#/////////////////////////////////////////////////////////////////////////////////////////
import base64
import httplib
import re
import simplejson
from subprocess import call
import time
import urllib2
import indigo
import RPFramework

CMD_AUTHENTICATE_TO_DEVICE = "AuthenticateCommand"
CMD_PAIR_TO_DEVICE = "PairDeviceCommand"
AUTH_REQUEST_RESULT_DONE = 1
AUTH_REQUEST_RESULT_PAIRREQUIRED = 2
AUTH_REQUEST_RESULT_ERROR = 3

PLUGIN_PAIRING_AUTH_CODE = "34c43339-af3d-40e7-b1b2-743331375368c"

#/////////////////////////////////////////////////////////////////////////////////////////
#/////////////////////////////////////////////////////////////////////////////////////////
# SonyTvNetworkRemoteDevice
#	Handles the configuration of a single Sony device that is connected to this plugin;
#	this class does all the 'grunt work' of communications with the device
#/////////////////////////////////////////////////////////////////////////////////////////
#/////////////////////////////////////////////////////////////////////////////////////////
class SonyTvNetworkRemoteDevice(RPFramework.RPFrameworkRESTfulDevice.RPFrameworkRESTfulDevice):
	
	#/////////////////////////////////////////////////////////////////////////////////////
	# Class construction and destruction methods
	#/////////////////////////////////////////////////////////////////////////////////////
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	# Constructor called once upon plugin class receiving a command to start device
	# communication. The plugin will call other commands when needed, simply zero out the
	# member variables
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	def __init__(self, plugin, device):
		super(SonyTvNetworkRemoteDevice, self).__init__(plugin, device)
		
		# record the new property that was added so that the device will properly upgrade
		# to one that supports authentication
		self.upgradedDeviceProperties.append(("authCookie", ""))
		self.upgradedDeviceProperties.append(("httpPort", "80"))
		self.upgradedDeviceProperties.append(("authMethod", "accessControl"))
		self.upgradedDeviceProperties.append(("queryPath", "/sony/IRCC"))
		
		
	#/////////////////////////////////////////////////////////////////////////////////////
	# RESTful device overloads
	#/////////////////////////////////////////////////////////////////////////////////////
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	# This routine should return the HTTP address that will be used to connect to the
	# RESTful device. It may connect via IP address or a host name
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	def getRESTfulDeviceAddress(self):
		return (self.indigoDevice.pluginProps.get("httpAddress", ""), int(self.indigoDevice.pluginProps.get("httpPort", "80")))
		
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	# This routine will be called prior to any network operation to allow the addition
	# of custom headers to the request (does not include file download)
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	def addCustomHTTPHeaders(self, httpRequest):
		httpRequest.putheader("Host", self.getRESTfulDeviceAddress()[0])
		httpRequest.putheader("User-Agent", "DuncanwareRemote (IndigoPlugin)")
		
		authCookie = self.indigoDevice.pluginProps.get("authCookie", "")
		if authCookie != "":
			httpRequest.putheader("Cookie", authCookie)
		
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	# This routine should be overridden in individual device classes whenever they must
	# handle custom commands that are not already defined
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	def handleUnmanagedCommandInQueue(self, deviceHTTPAddress, rpCommand):
		if rpCommand.commandName == CMD_AUTHENTICATE_TO_DEVICE or rpCommand.commandName == CMD_PAIR_TO_DEVICE:
			self.hostPlugin.logDebugMessage("Received an authentication command, attempting connection", RPFramework.RPFrameworkPlugin.DEBUGLEVEL_HIGH)
			try:
				# this command requires that we formulate a registration request and send it
				# to the device, trapping the cookie returned (if successful)
				registerAddress = self.getRESTfulDeviceAddress()
				conn = httplib.HTTPConnection(registerAddress[0], registerAddress[1])
				conn.connect()
				
				registerJSONTemplate = '{"id":13, "method":"actRegister", "version":"1.0", "params": [{"clientid":"DuncanwareRemote:' + PLUGIN_PAIRING_AUTH_CODE +'", "nickname":"DuncanwareRemote (IndigoPlugin)"}, [{"clientid":"DuncanwareRemote:' + PLUGIN_PAIRING_AUTH_CODE + '", "value":"yes", "nickname":"DuncanwareRemote (IndigoPlugin)", "function":"WOL"}]]}'
				self.hostPlugin.logDebugMessage("Sending Auth Request: " + registerJSONTemplate, RPFramework.RPFrameworkPlugin.DEBUGLEVEL_HIGH)
				if rpCommand.commandName == CMD_PAIR_TO_DEVICE:
					self.hostPlugin.logDebugMessage("Including Pair PIN: " + rpCommand.commandPayload, RPFramework.RPFrameworkPlugin.DEBUGLEVEL_HIGH)
				
				conn.putrequest('POST', "/sony/accessControl")
				conn.putheader("content-type", "application/json")
				conn.putheader("Connection", "close")
				conn.putheader("User-Agent", "DuncanwareRemote (IndigoPlugin)")
				conn.putheader("Host", registerAddress[0])
				if rpCommand.commandName == CMD_PAIR_TO_DEVICE:
					conn.putheader("Authorization", "Basic " + base64.b64encode(":" + rpCommand.commandPayload))
				conn.putheader("Content-Length", "%d" % len(registerJSONTemplate))
				conn.endheaders()
				conn.send(registerJSONTemplate)
				responseToRegister = conn.getresponse()
				
				# if the response is 200 then we are paired or not required to pair... we should have a cookie
				# returned; if not then throw an error as it must be paired for use
				self.hostPlugin.logDebugMessage("Response to Auth Request: [" + str(responseToRegister.status) + "] " + str(responseToRegister.getheaders()) + "\n\n" + responseToRegister.read(), RPFramework.RPFrameworkPlugin.DEBUGLEVEL_HIGH)
				if responseToRegister.status == 200:
					# retrieve the authentication cookie from the headers
					cookieParser = re.compile(ur'(auth=[a-zA-Z\d]+);', re.MULTILINE | re.IGNORECASE)
					authCookie = re.search(cookieParser, responseToRegister.getheader("set-cookie")).group(1)
					self.hostPlugin.logDebugMessage("Obtained Auth Cookie: " + authCookie, RPFramework.RPFrameworkPlugin.DEBUGLEVEL_MED)
					
					# update the device property with the auth cookie
					deviceProps = self.indigoDevice.pluginProps
					deviceProps["authCookie"] = authCookie
					self.indigoDevice.replacePluginPropsOnServer(deviceProps)
					
					# if a payload is set on the command, this is a SOAP request that must be
					# re-queued... otherwise return success
					if rpCommand.commandName == CMD_PAIR_TO_DEVICE or rpCommand == None or rpCommand.commandPayload == None or rpCommand.commandPayload == "":
						return AUTH_REQUEST_RESULT_DONE
					elif rpCommand.commandPayload != None and rpCommand.commandPayload != "":
						self.commandQueue.put(RPFramework.RPFrameworkCommand.RPFrameworkCommand(RPFramework.RPFrameworkRESTfulDevice.CMD_SOAP_REQUEST, commandPayload=rpCommand.commandPayload))
					
				elif responseToRegister.status == 401:
					# the user must pair the plugin to the Sony device before it will allow us to
					# register for an auth cookie
					indigo.server.log("This device (" + str(self.indigoDevice.id) + ") must be paired in order for the plugin to act as a remote.", isError=True)
					return AUTH_REQUEST_RESULT_PAIRREQUIRED
				else:
					# this is an unknown error (no registration service exists??) throw an error in the log
					# and disregard the previous commandName
					indigo.server.log("Error authenticating device: " + str(self.indigoDevice.id) + " - the plugin is not able to act as a remote until this is corrected; turn on debug for more details.", isError=True)
					return AUTH_REQUEST_RESULT_ERROR
			except:
				# this is an unknown error (no registration service exists??) throw an error in the log
				# and disregard the previous commandName
				indigo.server.log("Error authenticating device: " + str(self.indigoDevice.id) + " - the plugin is not able to act as a remote until this is corrected; turn on debug for more details.", isError=True)
				if self.hostPlugin.debug == True:
					self.hostPlugin.exceptionLog()
				return AUTH_REQUEST_RESULT_ERROR
		
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	# This override allows us to handle the response prior to normal processing; if this
	# response is that we are not authenticated, attempt that now (unless previous
	# command was an authorization attempt!)
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-	
	def handleDeviceResponse(self, responseObj, responseText, rpCommand):
		# if we receive a response indicating that authentication is required, we may attempt to authenticate
		# to the service, storing the previous command so that it may be re-executed
		if responseObj.status == 401:
			self.hostPlugin.logDebugMessage("Received an authentication request, attempting now...", RPFramework.RPFrameworkPlugin.DEBUGLEVEL_LOW)
			self.commandQueue.put(RPFrameworkCommand.RPFrameworkCommand(CMD_AUTHENTICATE_TO_DEVICE, commandPayload=rpCommand.commandPayload))
		elif responseObj.status == 404:
			indigo.server.log("Error executing command: Page Not Found on Device", isError=True)
		else:
			super(SonyTvNetworkRemoteDevice, self).handleDeviceResponse(responseObj, responseText, rpCommand)
			
	
	#/////////////////////////////////////////////////////////////////////////////////////
	# Custom Response Handlers
	#/////////////////////////////////////////////////////////////////////////////////////
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	# This callback is made whenever the plugin has received the response to a request
	# to download remote IR commands
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	def remoteDeviceIRCommandListReceived(self, responseObj, rpCommand):
		try:
			# the response should be a JSON-formatted page; if not then the request was
			# definitely unsuccessful
			self.hostPlugin.logDebugMessage("Received IR Commands List: " + responseObj, RPFramework.RPFrameworkPlugin.DEBUGLEVEL_HIGH)
			remoteCommands = simplejson.loads(responseObj)
			
			# create the header for the report...
			reportDate = time.time()
			reportHeaders = list()
			reportHeaders.append(("Device: ", self.indigoDevice.name + "[" + str(self.indigoDevice.id) + "]"))
			reportHeaders.append(("Date Run: ", str(reportDate)))

			# the IR commands themselves will be displayed in a table format; create the table header
			irCodesHtml = "<table style='border: solid #404040 1px; border-collapse: collapse; margin: 15px;'>"
			irCodesHtml += "<tr><td style='padding: 3px; font-weight: bold; font-size: 1.05em;'>Command Name</td><td style='padding: 3px; font-weight: bold; font-size: 1.05em;'>IR Code</td></tr>"
			
			# format should be a dictionary , we are looking for the "result" value, which will be an array whose
			# second element is an array of the commands
			irCommandsArray = remoteCommands["result"][1]
			for commandDict in irCommandsArray:
				# each command definition is a dictionary of name/value
				irCodesHtml += "<tr><td style='padding: 2px; border: solid #404040 1px;'>" + commandDict["name"] + "</td><td style='padding: 2px; font-size: 0.9em; border: solid #404040 1px;'>" + commandDict["value"] + "</td></tr>"
				
			# complete the report table and footer
			irCodesHtml += "</table>"
			
			# write out the file...
			self.hostPlugin.logDebugMessage("Writing IR Command List HTML to file", RPFramework.RPFrameworkPlugin.DEBUGLEVEL_MED)
			outputFilename = self.hostPlugin.writePluginReport("Sony Device IR Commands Report", reportHeaders, irCodesHtml, "tmpIRCodeDownloadResults.html")
			
			# launch the file in a browser window via the command line
			call(["open", outputFilename])
			indigo.server.log("Created IR codes download results temporary file at " + outputFilename);
		except:
			indigo.server.log("IR Command List Failed:", isError=True)
			self.hostPlugin.exceptionLog()
			