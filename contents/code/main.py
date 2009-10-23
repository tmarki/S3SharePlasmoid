# -*- coding: utf-8 -*-
# myPlasmoid/contents/code/main.py
 
#import kde and qt specific stuff
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyKDE4.plasma import Plasma
from PyKDE4 import plasmascript
from os import path
botofound = True
try:
    from boto.s3 import *
except:
    botofound = False

#import commands for executing shell commands
import commands

expiry_mult = {
        0 : 365 * 24 * 60 * 60, # years
        1 : 30 * 24 * 60 * 60, # months
        2 : 24 * 60 * 60, # days
        3 : 60 * 60, # hours
        4 : 60 # minutes
        }

class S3Uploader (QThread):
    def __init__ (self, uris, bucketname, conn, exp):
        QThread.__init__ (self)
        self.uris = uris
        self.conn = conn
        self.bucketname = bucketname
        self.bucketerror = False
        self.expiry = exp
        print 'uploader ctor'
    def run (self):
        self.urls = [ ]
        for uri in self.uris:
            if uri.indexOf ('file:///') != 0:
#                print 'Skipping non-file: ' + uri
                continue
            uri = uri.replace ('file://', '')
#            print "uploading to s3: " + uri
            bucket = None
            try:
                bucket = self.conn.get_bucket (self.bucketname, validate = True)
            except:
                try:
                    bucket = self.conn.create_bucket (self.bucketname)
                except:
                    bucket = None
            if not bucket:
#                print 'bucket error'
                self.bucketerror = True
                return False
            k = Key (bucket)
            #awqk = Key (self.conn.get_bucket (self.bucketname))
            try:
                fname = path.basename (str (uri))
                k.key = fname
                k.set_contents_from_filename (str (uri))
                k.make_public ()
                print 'Expiry time: %s ' % self.expiry
                self.urls.append (k.generate_url (self.expiry))
            except Exception, e:
                print 'Exception: %s' % e        

#Plasmoid gained by inheritance
class myPlasmoid(plasmascript.Applet):
 
    #constructor
    def __init__(self,parent,args=None):
        plasmascript.Applet.__init__(self,parent)
        print dir (self)
 
    #done once when initiating
    def init(self):
 
        #disable settings dialog
        self.uploader = None
        self.setHasConfigurationInterface (True)
        self.setAcceptDrops(True)
        self.setAspectRatioMode(Plasma.Square)
        self.theme = Plasma.Svg(self)
        self.layout = QGraphicsLinearLayout(Qt.Vertical, self.applet)
        self.layout.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        #set size of Plasmoid
        self.resize(100, 40)
        #set aspect ratio mode
        self.setAspectRatioMode(Plasma.IgnoreAspectRatio)
        #set timer interval in ms (1000=1s)
        self.startTimer(1000)
        self.connect(self.configScheme (), SIGNAL('configChanged()'), self.readConfig)

    #def configChanged (self):
        #print 'changed'
        #print dir (self)

    def readConfig (self):
#        print 'CONFIG CHANGED'
        key = str (self.config('s3share').readEntry('AWSKey'))
        secret = str (self.config('s3share').readEntry('AWSSecret'))
        self.bucketname = str (self.config('s3share').readEntry('BucketName'))
        self.expirynum = int (self.config('s3share').readEntry('ExpireNum') or '1')
        self.expirytype = int (self.config('s3share').readEntry('ExpireType') or '0')
        print 'Expiry: %s @ %s' % (self.expirynum, self.expirytype)
        try:
            self.conn = Connection (key, secret)
            print 'S3Connection OK: %s' % self.conn.get_canonical_user_id ()
        except:
            self.setConfigurationRequired (True, '')
        else:
            self.setConfigurationRequired (self.bucketname == '', '')

    def dropEvent(self, e):
        uris = e.mimeData().text().replace(QRegExp("\n+$"), "").split("\n")
        self.uploader = S3Uploader (uris, self.bucketname, self.conn, self.expirynum * expiry_mult[self.expirytype])
        self.connect (self.uploader, SIGNAL ("finished ()"), self.uploadDone)
        self.update ()
        self.uploader.start ()

    def uploadDone (self):
#        print 'urls: %s' % self.uploader.urls
        if not self.uploader.bucketerror:
            QMessageBox.information (None,  ("S3 Share Plasmoid"), '\n'.join (self.uploader.urls), QMessageBox.AcceptRole)
        else:
            QMessageBox.warning (None,  ("Bucket error: please check your settings and if the bucket name is available!"))
            
        self.uploader = None
        self.update ()
    
    def timerEvent(self, event):
 
        self.update()
    
    def paintInterface(self, painter, option, rect):
 
        painter.save()
        if not botofound:
            painter.drawText(rect,Qt.AlignLeft,  ("BOTO not installed"))
        elif not self.uploader:
            painter.drawText(rect,Qt.AlignLeft,  ("S3 Share"))
        else:
            painter.drawText(rect,Qt.AlignLeft,  ("Uploading..."))
        painter.restore()
 
def CreateApplet(parent):
    return myPlasmoid(parent)
