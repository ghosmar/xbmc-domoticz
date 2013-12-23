import xbmc, xbmcgui,xbmcaddon
import time

import urllib2
if sys.version_info < (2, 7):
	import simplejson
else:
	import json as simplejson
	

### get addon info and set globals
__addon__        = xbmcaddon.Addon()
__addonid__      = __addon__.getAddonInfo('id')
__addonname__    = __addon__.getAddonInfo('name')
__author__       = __addon__.getAddonInfo('author')
__version__      = __addon__.getAddonInfo('version')
__addonpath__    = __addon__.getAddonInfo('path')
__localize__     = __addon__.getLocalizedString
__user__=__addon__.getSetting('login')
__password__=__addon__.getSetting('password')
__rooturl__=__addon__.getSetting('url')
__favonly__=__addon__.getSetting('favonly')

while __rooturl__=='': 
	__addon__.openSettings()
	__user__=__addon__.getSetting('login')
	__password__=__addon__.getSetting('password')
	__rooturl__=__addon__.getSetting('url')
	__favonly__=__addon__.getSetting('favonly')



def log( text, severity=xbmc.LOGNOTICE ):
	if type( text).__name__=='unicode':
		text = text.encode('utf-8')
	message = ('[%s] - %s' % ( __addonname__ ,text.__str__() ) )
	xbmc.log( msg=message, level=severity)


# Maange authentication
if __user__!='': 		# Authentication optional
	passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
	passman.add_password(None, __rooturl__, __user__, __password__)
	authhandler = urllib2.HTTPBasicAuthHandler(passman)
	opener = urllib2.build_opener(authhandler)
	urllib2.install_opener(opener)

#get actioncodes from https://github.com/xbmc/xbmc/blob/master/xbmc/guilib/Key.h
ACTION_PREVIOUS_MENU = 10
ACTION_BACK = 92

# Dict used for internalization
__labels__ = {	'off':30040,
			'on' : 30041,
			'open' : 30042,
			'closed' : 30043,
			'panic': 30044,
			'normal' : 30045 }

# When a switch is XX, we can switch it to YY
__opposite_status__ = {'Off':'On',
					'On':'Off',
					'Closed':'Open',
					'Open':'Closed',
					'Panic':'Normal',
					'Normal':'Panic'}
					
 
__customimages__ = { 'lightbulb': ['lightbulb','wallsocket','tv','harddisk','printer','amplifier','computer','fan','speaker','generic','push'],
						'smoke': ['smoke'],
						'contact': ['contact'],
						'blinds': ['blinds'],
						'temperature':['temperature'],
						'siren': ['siren'],
						'dimmer':['dimmer'],
						'motion': ['motion'],
						'door': ['door'],
						'dusk': ['dusk']
						}
 
class DomoticzWindow(xbmcgui.WindowXMLDialog):

	def __init__(self, *args, **kwargs):
		#and define it as self
		log('running __init__ from DomoticzWindow class', xbmc.LOGNOTICE)
        

	def sendcmd(self,switchid,cmd,itemtype):
		log("Sending "+cmd+" to Switch "+switchid, xbmc.LOGNOTICE)
		thisurl=__rooturl__+"/json.htm?type=command&param="+itemtype+"&idx="+switchid+"&switchcmd="+cmd+"&level=0"
		log ("URL is "+thisurl , xbmc.LOGNOTICE)
		log('You selected : ' + switchid+"-"+cmd, xbmc.LOGNOTICE)
		xbmc.executebuiltin( "ActivateWindow(busydialog)" )
		try:
			pagehandle = urllib2.urlopen(thisurl)
			html = pagehandle.read()
			pagehandle.close()
		except:
			html="Error !!"
		xbmc.executebuiltin( "Dialog.Close(busydialog)" )
		log(html, xbmc.LOGNOTICE)
		time.sleep(2)
		#self.message("Done")
		self.populateFromDomo()
        
        
# INIT Function       
	def onInit(self):
		#tell the object to go read the log file, parse it, and put it into listitems for the XML
		log('running inInit from DomoticzWindow class', xbmc.LOGNOTICE)
		self.populateFromDomo()
        
	def message(self, message):
		dialog = xbmcgui.Dialog()
		dialog.ok(" My message title", message)
     
	def onClick(self, control):
		item = self.getControl(control).getSelectedItem()
		log("Click  "+item.getProperty('isswitch'),xbmc.LOGNOTICE)
		if item.getProperty('type') == 'switchscene' or item.getProperty('type') == 'switchlight':
			self.sendcmd(item.getProperty('idx'),__opposite_status__[item.getProperty('data')],item.getProperty('type') )
     
	def onAction(self, action):
		#~ captures user input and acts as needed
		log('running onAction from DomoticzWindow class', xbmc.LOGNOTICE)
		if(action == ACTION_PREVIOUS_MENU or action == ACTION_BACK):
			#if the user hits back or exit, close the window
			log('user initiated previous menu or back', xbmc.LOGNOTICE)
			global __windowopen__
			#set this to false so the worker thread knows the window is being closed
			__windowopen__ = False
			log('set windowopen to false', xbmc.LOGNOTICE)
			#tell the window to close
			log('tell the window to close', xbmc.LOGNOTICE)
			self.close()

	def populateFromDomo(self):
		results=self.getData()
		self.getControl(120).reset()
		#time.sleep(5)
		item = xbmcgui.ListItem(label="XBMC Domoticz")
		item.setProperty('istitle','true')
		self.getControl(120).addItem(item)
		odd=True
		for myitem in results[u'result']:
			if __favonly__=="true" and  myitem[u'Favorite']==0:  
				continue

			if myitem[u'Type'] == 'Group' or myitem[u'Type'] == 'Scene':
				myitem[u'Data'] = myitem[u'Status']
				myitem[u'CustomImage'] = 10
				
			log("Adding"+myitem[u'Name'],xbmc.LOGNOTICE)
			# Ulgy thing because Domoticz does not handle Dusk sensors like the others
			if u'SwitchType' in myitem and myitem[u'SwitchType'] == "Dusk Sensor":
				myitem[u'TypeImg']='dusk'
				
			if myitem[u'TypeImg']  in ['lightbulb','blinds','contact','smoke','siren','dimmer','motion','door','dusk']:
				log(myitem[u'CustomImage'])
				mytype=__customimages__[myitem[u'TypeImg']][myitem[u'CustomImage']]+"-"+myitem[u'Status'].lower()+".png"
			elif myitem[u'TypeImg'] == "temperature":
				mini=int(float(myitem[u'Data'].split(',')[0].split(' ')[0])/5)*5
				maxi=mini+5
				mytype="temp-"+str(mini)+"-"+str(maxi)+".png"
			else:
				mytype=myitem[u'TypeImg'].lower()+".png"
				
			if myitem[u'Data'].lower() in __labels__:
				myitem[u'Data']=__localize__(__labels__[myitem[u'Data'].lower()])
              
			item = xbmcgui.ListItem(label=myitem[u'Name'],label2=myitem[u'Data'])
			item.setProperty('idx',myitem[u'idx'])
			odd= not odd
			if odd:
				item.setProperty('isodd','true')
			else:
				item.setProperty('isodd','false')

			log("Type :"+myitem[u'Type'],xbmc.LOGNOTICE)
			if myitem[u'Type'] in ['Lighting 2','Lighting 1','Lighting 4','Security']:
				item.setProperty('type','switchlight')
			else:
				item.setProperty('type','none')
			
			if myitem[u'Type'] in ['Scene','Group']:
				item.setProperty('type','switchscene')
			
			if u'Status' in myitem:
				item.setProperty('data',myitem[u'Status'])

			item.setProperty(mytype.lower(),'true')
			item.setIconImage(mytype)
			self.getControl(120).addItem(item)
			

	def getData(self):
		xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        
		url=__rooturl__+u'/json.htm?type=devices&filter=all&used=true&order=Name'

		log('URL is '+url,xbmc.LOGNOTICE)
        
        
		try:
			pagehandle = urllib2.urlopen(url)
			#~ pagehandle = open('/home/fpege/json.html', 'r')
			html = pagehandle.read()
			pagehandle.close()
		except urllib2.HTTPError, e:
			log('HTTPError = ' + str(e.code))
			self.message('HTTPError = ' + __localize__(int("30"+str(e.code))))
			xbmc.executebuiltin( "Dialog.Close(busydialog)" )
			self.onAction(ACTION_BACK)
			return ""
		except urllib2.URLError, e:
			log('URLError = ' + str(e.reason))
			self.message('URLError = ' +  __localize__(30404))
			xbmc.executebuiltin( "Dialog.Close(busydialog)" )
			self.onAction(ACTION_BACK)
			return ""
		except httplib.HTTPException, e:
			log('HTTPException')
			self.message('HTTPException')
			xbmc.executebuiltin( "Dialog.Close(busydialog)" )
			self.onAction(ACTION_BACK)
			return ""
		except Exception:
			import traceback
			log('generic exception: ' + traceback.format_exc())
			self.message('generic exception: ' + traceback.format_exc())
			xbmc.executebuiltin( "Dialog.Close(busydialog)" )
			self.onAction(ACTION_BACK)
			return ""

			

		xbmc.executebuiltin( "Dialog.Close(busydialog)" )
		return simplejson.loads(html)
 
 


w = DomoticzWindow("domoticz.xml", __addonpath__, "Default")
w.doModal()
del w
