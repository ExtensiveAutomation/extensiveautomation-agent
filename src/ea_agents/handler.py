#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -------------------------------------------------------------------
# Copyright (c) 2010-2020 Denis Machard
# This file is part of the extensive automation project
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301 USA
# -------------------------------------------------------------------

"""
Agent handler
"""

from ea_agents.libs import settings as Settings

import sys
import time
import inspect
import sys
import os
import threading
import logging

# adding missing folders
if not os.path.exists( "%s/plugins" % Settings.getDirExec() ):
    os.mkdir( "%s/plugins" % Settings.getDirExec() )
if not os.path.exists( "%s/var" % Settings.getDirExec() ):
    os.mkdir( "%s/var" % Settings.getDirExec() )
if not os.path.exists( "%s/var/logs/" % Settings.getDirExec() ):
    os.mkdir( "%s/var/logs" % Settings.getDirExec() )
if not os.path.exists( "%s/var/data/" % Settings.getDirExec() ):
    os.mkdir( "%s/var/data" % Settings.getDirExec() )

# loading all plugins
installed = []
for f in os.listdir( "%s/plugins/" % Settings.getDirExec() ):
    if f == "__pycache__": continue
    if os.path.isdir( "%s/plugins/%s" % (Settings.getDirExec(),f) ):
        installed.append('"%s"' % f)

# update the init
f = open( '%s/plugins/__init__.py' % Settings.getDirExec(), 'w')
f.write( "__all__ = [%s]" % ",".join(installed) )
f.close()

# finally import all plugins
from ea_agents.plugins import *

def get_plugins():
    """plugins"""
    plugins = {} 
    pkg =  __import__( "ea_agents" )
    obj = getattr(pkg, "plugins")
    for listing in dir(obj):
        obj2 = getattr(obj, listing)
        if inspect.ismodule(obj2):
            plugins[listing] = obj2
    return plugins

class AgentHandler(object):
    """agent handler"""
    def __init__(self): 
        """class constructor"""
        self.maxReconnect = int(Settings.get('Server','max-reconnect'))
        self.currentReconnect = 0
        self.timersList = []
        self.tool = None
        self.running = False
        self.disconnected = False
    def initialize (self, ip, port, agent_type, agent_name, supportProxy=False,
                    proxyIp=None, proxyPort=None, sslSupport=True, isAgent=0, fromCmd=False):
        """initialize agent"""
        try:
            logging.info("starting agent %s ..." % agent_type)

            self.tool = get_plugins()[agent_type].initialize( 
                                                    controllerIp=str(ip), 
                                                    toolName=agent_name, 
                                                    toolDesc="", 
                                                    defaultTool=False, 
                                                    controllerPort=int(port), 
                                                    supportProxy=supportProxy,
                                                    proxyIp=str(proxyIp), 
                                                    proxyPort=proxyPort, 
                                                    sslSupport=sslSupport
                                                )

            self.tool.onRegistrationSuccessful = self.onRegSuccess
            self.tool.onRegistrationFailed = self.onRegError
            self.tool.onRegistrationRefused = self.onRegError
            self.tool.onToolDisconnection = self.onDisconnection
            self.tool.onConnectionRefused = self.onConnError
            self.tool.onConnectionTimeout = self.onConnError
            self.tool.onProxyConnectionTimeout = self.onProxyError
            self.tool.onProxyConnectionRefused = self.onProxyError
            self.tool.onProxyConnectionError = self.onProxyError
            self.tool.checkPrerequisites()
            self.tool.startCA()
  
        except Exception as e:
            logging.error("unable to start agent: " + str(e))
        else:
            # run in loop
            self.running = True
            self.run()
        
    def onDisconnection(self, byServer=False, inactivityServer=False):
        """on agent disconnection"""
        if self.disconnected:
            return
            
        logging.error( "agent disconnected")
        self.disconnected = True
        self.restart_on_error()

    def restart_on_error(self):
        """restart on error"""
        if self.currentReconnect > 0:
            if self.currentReconnect <= self.maxReconnect:
                self.currentReconnect += 1
                logging.info( 'connection retry #%s' % self.currentReconnect )
                self.restartTool()
            else:
                logging.info( 'max connection retries reached' )
                self.running = False
        else:
            self.running = False
            
    def restartTool(self):
        """restart agent"""
        if self.running:
            # stop the plugin before to restart
            self.tool.onPreCleanup()
            
            # init the interval, exponential restart
            # 0       1         2           3           4
            # 0 ----> 5s -----> 15s ------> 30s ------> 50s 
            # max: 5s x 10 = 50s
            interval = int(Settings.get('Server','initial-retry'))
            interval = interval * self.currentReconnect
            
            logging.info("sleeping %s sec before to restart" % interval )
            
            # start timer
            t = threading.Timer(interval, self.tool.startConnection)
            self.timersList.append( t )
            t.start()

    def onRegError(self, err):
        """on registration error"""
        logging.error( "agent registration error: %s" % err)
        self.running = False
        
    def onRegSuccess(self):
        """on registration successful"""
        self.currentReconnect = 0
        self.disconnected = False
        logging.info( "agent registration successful")
        self.tool.initAfterRegistration()

    def onConnError(self, err):
        """on connection error"""
        logging.error( "tcp connection error: %s" % err)
        self.restart_on_error()

    def onProxyError(self, err):
        """on proxy connection refused"""
        logging.error( "proxy connection error: %s" % err)
        self.restart_on_error()

    def finalize(self):
        """Stops all modules"""
        try:
            self.running = False
            if self.tool is not None:
                self.tool.onPreCleanup()
                self.tool.stopCA()
        except Exception as e:
            pass
        sys.exit(1)

    def run(self):
        """On run"""
        try:
            while self.running:
                time.sleep(0.01)
            self.finalize()
        except KeyboardInterrupt:
            logging.info('stopping agent...')
            # reset timers
            for timer in self.timersList:
                timer.cancel()
            # and finalize
            self.finalize()