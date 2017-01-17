#Introduction
This Indigo 6.0+ plugin allows Indigo to act as a remote control for select network-connected Sony devices. All commands/buttons found on the standard, included remote can be sent to the device as well as a multitude of additional commands generally available only through network or advanced universal remotes. The protocol exposed by Sony devices, and utilized by this plugin, does not allow for state information about the device to be obtained (such as what current application/channel is active or what input the television is currently showing). If the protocol is changed or a device comes out that does provide feedback then it may be possible to enhance the plugin at that time.

Currently this plugin is loaded with the necessary remote commands to control Sony televisions; however, if anyone has alternate Sony devices supporting IP control (e.g. some recent Blu-Ray players) then it should be trivial to add support for those device types.

_**INDIGO 6 IMPORTANT NOTE:**_ The Indigo 6 version of this plugin is end-of-life with respect to new development, however the latest stable version on Indigo 6 is [still available](https://github.com/RogueProeliator/IndigoPlugins-Sony-Network-Remote/archive/v2.3.1.zip) and is working as expected at the moment. Please consider an upgrade to Indigo 7 to support further development of our favorite HA platform!

#Hardware Requirements
This plugin should work with any supported Sony device type as the remote commands do not change much between individual device models; some models may not support all commands provided by the plugin (e.g. Netflix & Picture-in-Picture commands). Also note that turning ON the device is only supported on those Sony models that support Wake-On-LAN (WOL). This includes many/most 2013 models supporting IP commands and some limited previous year models.

The auto-discovery feature requires that the Sony device and Indigo server be on the same subnet, though manual IP entry should allow remote control via a WAN interfaces (such as over a VPN connection).

*IMPORTANT* NOTE: If you wish to allow the plugin to remotely power on the device, you must turn on "Remote Start" on your Sony device. This is found in different menus depending upon your device, but is often found in the "Home Network Setup" section of the settings menu. Note that you must also configure the MAC address on the Device Configuration screen (see below).

#Installation and Configuration
###Obtaining the Plugin
The latest released version of the plugin is available for download in the Releases section... those versions in beta will be marked as a Pre-Release and will not appear in update notifications.

###Configuring the Plugin
Upon first installation you will be asked to configure the plugin; please see the instructions on the configuration screen for more information. Most users will be fine with the defaults unless an email is desired when a new version is released.<br />
![](<Documentation/Doc-Images/PluginConfigDialog.png>)

#Plugin Devices
When creating a device, in the Device Settings you will need to select from the list of supported devices found on the network or else manually enter your devices's IP address. Note that if you ever lose connection with your device, you may need to return here to find/enter the IP Address again if it has picked up a new address on the network. Please read the additional instructions on the configuration dialog as you may need to fill out additional information to get full control of your device:<br />
![](<Documentation/Doc-Images/DeviceConfigDialog.png>)

#Available Actions
###Send Button Press
This action will send a network command that is equivalent to pressing the button on the remote (some buttons included are not found on the physical remote). Not all models will support all commands available in the plugin... non-supported commands will generally just be ignored by the device. If there are any commands that you believe your TV supports but which are not included here, please let me know and I can attempt to add it to the action.

###Power ON
When a device is powered off it will not respond to network commands; however, many Sony devices now include the ability for the plugin to "wake up" the device over the network. This action attempts to do just that.

###Power OFF
This command will power off the device.
