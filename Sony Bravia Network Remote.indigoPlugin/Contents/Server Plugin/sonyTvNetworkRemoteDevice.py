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

CMD_AUTHENTICATE_TO_DEVICE = u'AuthenticateCommand'
CMD_PAIR_TO_DEVICE = u'PairDeviceCommand'
AUTH_REQUEST_RESULT_DONE = 1
AUTH_REQUEST_RESULT_PAIRREQUIRED = 2
AUTH_REQUEST_RESULT_ERROR = 3

PLUGIN_PAIRING_AUTH_CODE = u'34c43339-af3d-40e7-b1b2-743331375368c'

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
		self.upgradedDeviceProperties.append((u'authCookie', u''))
		self.upgradedDeviceProperties.append((u'httpPort', u'80'))
		self.upgradedDeviceProperties.append((u'authMethod', u'accessControl'))
		self.upgradedDeviceProperties.append((u'queryPath', u'/sony/IRCC'))
		
		
	#/////////////////////////////////////////////////////////////////////////////////////
	# RESTful device overloads
	#/////////////////////////////////////////////////////////////////////////////////////
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	# This routine should return the HTTP address that will be used to connect to the
	# RESTful device. It may connect via IP address or a host name
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	def getRESTfulDeviceAddress(self):
		return (self.indigoDevice.pluginProps.get(u'httpAddress', u''), int(self.indigoDevice.pluginProps.get(u'httpPort', u'80')))
		
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	# This routine will be called prior to any network operation to allow the addition
	# of custom headers to the request (does not include file download)
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	def addCustomHTTPHeaders(self, headers):
		headers["Host"] = self.getRESTfulDeviceAddress()[0]
		headers["User-Agent"] = "DuncanwareRemote (IndigoPlugin)"
		
		authCookie = self.indigoDevice.pluginProps.get("authCookie", "")
		if authCookie != "":
			headers["Cookie"] =  authCookie
		
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	# This routine should be overridden in individual device classes whenever they must
	# handle custom commands that are not already defined
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	def handleUnmanagedCommandInQueue(self, deviceHTTPAddress, rpCommand):
		if rpCommand.commandName == CMD_AUTHENTICATE_TO_DEVICE or rpCommand.commandName == CMD_PAIR_TO_DEVICE:
			self.hostPlugin.logDebugMessage(u'Received an authentication command, attempting connection', RPFramework.RPFrameworkPlugin.DEBUGLEVEL_HIGH)
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
				
				conn.putrequest("POST", "/sony/accessControl")
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
				self.hostPlugin.logDebugMessage(u'Response to Auth Request: [' + RPFramework.RPFrameworkUtils.to_unicode(responseToRegister.status) + u'] ' + RPFramework.RPFrameworkUtils.to_unicode(responseToRegister.getheaders()) + u'\n\n' + responseToRegister.read(), RPFramework.RPFrameworkPlugin.DEBUGLEVEL_HIGH)
				if responseToRegister.status == 200:
					# retrieve the authentication cookie from the headers
					cookieParser = re.compile(ur'(auth=[a-zA-Z\d]+);', re.MULTILINE | re.IGNORECASE)
					authCookie = re.search(cookieParser, responseToRegister.getheader("set-cookie")).group(1)
					self.hostPlugin.logDebugMessage(u'Obtained Auth Cookie: ' + authCookie, RPFramework.RPFrameworkPlugin.DEBUGLEVEL_MED)
					
					# update the device property with the auth cookie
					deviceProps = self.indigoDevice.pluginProps
					deviceProps[u'authCookie'] = authCookie
					self.indigoDevice.replacePluginPropsOnServer(deviceProps)
					
					# if a payload is set on the command, this is a SOAP request that must be
					# re-queued... otherwise return success
					if rpCommand.commandName == CMD_PAIR_TO_DEVICE or rpCommand == None or rpCommand.commandPayload == None or rpCommand.commandPayload == u'':
						return AUTH_REQUEST_RESULT_DONE
					elif rpCommand.commandPayload != None and rpCommand.commandPayload != u'':
						self.commandQueue.put(RPFramework.RPFrameworkCommand.RPFrameworkCommand(RPFramework.RPFrameworkRESTfulDevice.CMD_SOAP_REQUEST, commandPayload=rpCommand.commandPayload))
					
				elif responseToRegister.status == 401:
					# the user must pair the plugin to the Sony device before it will allow us to
					# register for an auth cookie
					indigo.server.log(u'This device (' + RPFramework.RPFrameworkUtils.to_unicode(self.indigoDevice.id) + u') must be paired in order for the plugin to act as a remote.', isError=True)
					return AUTH_REQUEST_RESULT_PAIRREQUIRED
				else:
					# this is an unknown error (no registration service exists??) throw an error in the log
					# and disregard the previous commandName
					indigo.server.log(u'Error authenticating device: ' + RPFramework.RPFrameworkUtils.to_unicode(self.indigoDevice.id) + u' - the plugin is not able to act as a remote until this is corrected; turn on debug for more details.', isError=True)
					return AUTH_REQUEST_RESULT_ERROR
			except:
				# this is an unknown error (no registration service exists??) throw an error in the log
				# and disregard the previous commandName
				indigo.server.log(u'Error authenticating device: ' + RPFramework.RPFrameworkUtils.to_unicode(self.indigoDevice.id) + u' - the plugin is not able to act as a remote until this is corrected; turn on debug for more details.', isError=True)
				if self.hostPlugin.debug == True:
					self.hostPlugin.exceptionLog()
				return AUTH_REQUEST_RESULT_ERROR
				
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	# This routine will handle an error as thrown by the SOAP call... it allows 
	# us to attempt to re-pair the device if we can detect an unauthorized condition
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-		
	def handleRESTfulError(self, rpCommand, err, response=None):
		if response is None:
			super(SonyTvNetworkRemoteDevice, self).handleRESTfulError(rpCommand, err, response)
		elif response.status_code == 401 or response.status_code == 403 or (response.status_code == 500 and response.text.find(u'<errorDescription>Action not authorized</errorDescription>') > 0):
			self.hostPlugin.logDebugMessage(u'Received an authentication request, attempting now...', RPFramework.RPFrameworkPlugin.DEBUGLEVEL_LOW)
			self.commandQueue.put(RPFrameworkCommand.RPFrameworkCommand(CMD_AUTHENTICATE_TO_DEVICE, commandPayload=rpCommand.commandPayload))
		elif response.status_code == 404:
			indigo.server.log(u'Error executing command: Page Not Found on Device', isError=True)
		else:
			super(SonyTvNetworkRemoteDevice, self).handleRESTfulError(rpCommand, err, response)
			
	
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
			self.hostPlugin.logDebugMessage(u'Received IR Commands List: ' + RPFramework.RPFrameworkUtils.to_unicode(responseObj), RPFramework.RPFrameworkPlugin.DEBUGLEVEL_HIGH)
			remoteCommands = simplejson.loads(responseObj)
			
			# create the header for the report...
			reportDate = time.time()
			reportHeaders = list()
			reportHeaders.append((u'Device: ', self.indigoDevice.name + u'[' + RPFramework.RPFrameworkUtils.to_unicode(self.indigoDevice.id) + u']'))
			reportHeaders.append((u'Date Run: ', RPFramework.RPFrameworkUtils.to_unicode(reportDate)))

			# the IR commands themselves will be displayed in a table format; create the table header
			irCodesHtml = u"<table style='border: solid #404040 1px; border-collapse: collapse; margin: 15px;'>"
			irCodesHtml += u"<tr><td style='padding: 3px; font-weight: bold; font-size: 1.05em;'>Command Name</td><td style='padding: 3px; font-weight: bold; font-size: 1.05em;'>IR Code</td></tr>"
			
			# format should be a dictionary , we are looking for the "result" value, which will be an array whose
			# second element is an array of the commands
			irCommandsArray = remoteCommands[u'result'][1]
			for commandDict in irCommandsArray:
				# each command definition is a dictionary of name/value
				irCodesHtml += u"<tr><td style='padding: 2px; border: solid #404040 1px;'>" + commandDict[u'name'] + u"</td><td style='padding: 2px; font-size: 0.9em; border: solid #404040 1px;'>" + commandDict[u'value'] + u"</td></tr>"
				
			# complete the report table and footer
			irCodesHtml += u'</table>'
			
			# write out the file...
			self.hostPlugin.logDebugMessage(u'Writing IR Command List HTML to file', RPFramework.RPFrameworkPlugin.DEBUGLEVEL_MED)
			outputFilename = self.hostPlugin.writePluginReport("Sony Device IR Commands Report", reportHeaders, irCodesHtml, "tmpIRCodeDownloadResults.html")
			
			# launch the file in a browser window via the command line
			call(["open", outputFilename])
			indigo.server.log(u'Created IR codes download results temporary file at ' + outputFilename);
		except:
			indigo.server.log(u'IR Command List Failed:', isError=True)
			self.hostPlugin.exceptionLog()
			