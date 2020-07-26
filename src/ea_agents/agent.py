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
Generic tool class
Used on plugins
"""

from ea_agents.libs.NetLayerLib import ClientAgent as NetLayerLib
from ea_agents.libs.NetLayerLib import Messages

from ea_agents.libs import FifoQueue
from ea_agents.libs import settings as Settings

import logging
import os
import threading
import time
import sys
import shutil
import json
import base64
import requests

class TestThread(threading.Thread):
    """
    Test Thread
    """
    def __init__(self, parent, testUuid, scriptId, 
                    adapterId, interval=40, shared=False):
        """
        """
        threading.Thread.__init__(self)
        self.parent = parent
        self.stopEvent = threading.Event()
        self.event = threading.Event()
        self.scriptId = scriptId
        self.testUuid = testUuid
        self.adapterId = adapterId
        self.shared = shared
        self.timestamp = time.time()
        
        self.__fifo_incoming_events_thread = FifoQueue.FifoCallbackThread()
        self.__fifo_incoming_events_thread.start()
        
        self.ctx_plugin = None
        self.interval = interval
    
    def ctx(self):
        """
        Return the context
        """
        return self.ctx_plugin
        
    def updateTimestamp(self):
        """
        Update the timestamp
        """
        self.timestamp = time.time()
        
    def run(self):
        """
        On run
        """
        while not self.stopEvent.isSet():
            if (time.time() - self.timestamp) > self.interval:
                logging.debug("timeout raised, no more keepalive received from test server" )
                break
            time.sleep(1)
        self.onTerminated(testUuid=self.testUuid, 
                          scriptId=self.scriptId, 
                          adapterId=self.adapterId)
    
    def putItem(self, item):
        """
        Add item in the queue
        """
        self.__fifo_incoming_events_thread.putItem(item)
        
    def stop(self):
        """
        Stop the thread
        """

        self.__fifo_incoming_events_thread.removeAll()
        
        self.__fifo_incoming_events_thread.stop()
        self.__fifo_incoming_events_thread.join()
        
        if self.ctx_plugin is not None:
            self.ctx_plugin.onReset()
            
        self.stopEvent.set()
        
    def onTerminated(self, testUuid, scriptId, adapterId):
        """
        On terminated event
        """
        pass
        
class Tool(NetLayerLib.ClientAgent):
    """
    Tool client agent
    """
    def __init__(self, controllerIp, controllerPort, toolName, toolDesc, defaultTool, 
                    supportProxy=False, proxyIp=None, proxyPort=None, sslSupport=True,
                    toolType = NetLayerLib.TYPE_AGENT_AGENT, fromCmd=False, name=None):
        """Constructor"""
        self.login = "anonymous"
        self.password = "anonymous"
        self.toolType = toolType
 
        # init ssl
        self.sslSupportFinal=sslSupport
        if not Settings.getBool( 'Server', 'ssl-support' ): self.sslSupportFinal=False 

        # init websocket
        wsSupport=False  
        if Settings.getBool( 'Server', 'websocket-support' ): wsSupport=True 

        NetLayerLib.ClientAgent.__init__(self, typeAgent = toolType, startAuto = True,
                                        keepAliveInterval=Settings.getInt( 'Network', 'keepalive-interval' ),
                                        inactivityTimeout=Settings.getInt( 'Network', 'inactivity-timeout' ),
                                        timeoutTcpConnect=Settings.getInt( 'Network', 'tcp-connect-timeout' ),
                                        responseTimeout=Settings.getInt( 'Network', 'response-timeout' ),
                                        selectTimeout=Settings.get( 'Network', 'select-timeout' ),
                                        sslSupport=self.sslSupportFinal,
                                        wsSupport=wsSupport,
                                        pickleVer=Settings.getInt( 'Network', 'pickle-version' ),
                                        tcpKeepAlive=Settings.getBool( 'Network', 'tcp-keepalive' ), 
                                        tcpKeepIdle=Settings.getInt( 'Network', 'tcp-keepidle' ),
                                        tcpKeepCnt=Settings.getInt( 'Network', 'tcp-keepcnt' ), 
                                        tcpKeepIntvl=Settings.getInt( 'Network', 'tcp-keepintvl' )
                                        )
        serverPort = Settings.getInt( 'Server', 'port' )
        if controllerPort is not None:
            serverPort = int(controllerPort)
        
        self.setServerAddress( ip = controllerIp, port = serverPort)
        if supportProxy:
            self.setProxyAddress(ip = proxyIp, port = int(proxyPort) )
        self.setAgentName( name = toolName )
        toolMore = {'details': toolDesc, 'default': False}
        if name is not None:
            self.setDetails( name = name, desc = toolMore, ver = Settings.getVersion() )
        else:
            self.setDetails( name = self.__class__.__name__, 
                             desc = toolMore, 
                             ver = Settings.getVersion() )
        
        self.controllerIp = controllerIp
        self.controllerPort = serverPort

        self.__mutex__ = threading.RLock()
        self.regThread = None
        self.regRequest =  None

        self.testsContext = {}

    def getTemp(self):
        """
        Return the path of the temp area
        """
        return "%s/%s/" % (Settings.getDirExec(), Settings.get( 'Paths', 'tmp' ))

    def checkPrerequisites(self):
        """
        Function must be reimplement
        """
        pass
        
    def context(self):
        """
        Get the tests context
        """
        return self.testsContext

    def onRequest(self, client, tid, request):
        """Reimplemented from ClientAgent"""
        try:
            if request['cmd'] == Messages.RSQ_CMD:
                _body_ = request['body']
                if 'cmd' in _body_:
                    logging.debug( 'On request, receiving <-- CMD: %s' % _body_['cmd'] )
                    
                    logging.error( 'Cmd unknown %s' % _body_['cmd'])
                    rsp = {'cmd': _body_['cmd'], 'res': Messages.CMD_ERROR }
                    NetLayerLib.ClientAgent.failed(self, tid, body = rsp )
                else:
                    logging.error( 'Cmd is missing')
                    
            elif request['cmd'] == Messages.RSQ_NOTIFY:
                self.onNotify(client, tid, request=request['body'])
                
            else:
                logging.error( '[onRequest] request unknown %s' % request['cmd'])
        except Exception as e:
            logging.error( "[onRequest] %s" % str(e) )

    def onNotify(self, client, tid, request):
        """Called on incoming request from server"""
        if request['event'] == 'agent-notify':
            try:
                self.__onAgentNotify(client, tid, request)
            except Exception as e:
                logging.error( "__onAgentNotify %s" % str(e) ) 
        elif request['event'] == 'agent-ready':
            try:
                self.__onAgentReady(client, tid, request)
            except Exception as e:
                logging.error( "__onAgentReady %s" % str(e) ) 
        elif request['event'] == 'agent-init':
            try:
                self.__onAgentInit(client, tid, request)
            except Exception as e:
                logging.error( "__onAgentInit %s" % str(e) ) 
        elif request['event'] == 'agent-reset':
            try:
                self.__onAgentReset(client, tid, request)
            except Exception as e:
                logging.error( "__onAgentReset %s" % str(e) ) 
        elif request['event'] == 'agent-alive':
            try:
                self.__onAgentAlive(client, tid, request)
            except Exception as e:
                logging.error( "__onAgentAlive %s" % str(e) ) 
        else:
            logging.error( "unknown event request received: %s" % str(request['event']) )
        
    def __onAgentReady(self, client, tid, request):
        """
        Function to reimplement on plugin
        """
        logging.debug("Init agent testUuid=%s ScriptId=%s AdapterId=%s" % (request['uuid'], 
                                                                        request['script_id'], 
                                                                        request['source-adapter'])  )
        logging.debug("Tests context before init: %s" % self.testsContext)
        test_ctx = TestThread(parent=self, testUuid=request['uuid'], 
                              scriptId=request['script_id'], 
                              adapterId=request['source-adapter'] )
        if 'shared' in request['data']: 
            test_ctx.shared = request['data']['shared']
        if request['uuid'] in self.testsContext:
            self.testsContext[request['uuid']][request['source-adapter']] = test_ctx
        else:
            self.testsContext[request['uuid']] = {request['source-adapter']: test_ctx }
        test_ctx.onTerminated = self.onResetTestContext
        test_ctx.start()

        self.sendNotify(request, data={ 'cmd': "AGENT_INITIALIZED", 'ready': True } )                         
        logging.debug("Agent initialized testUuid=%s ScriptId=%s AdapterId=%s" % (request['uuid'], 
                                                                               request['script_id'], 
                                                                               request['source-adapter']) )
        
        self.onAgentReady(client, tid, request)
 
    def __onAgentNotify(self, client, tid, request):
        """
        Function to reimplement on plugin
        """
        self.onAgentNotify(client, tid, request)
 
    def __onAgentInit(self, client, tid, request):
        """
        Function to reimplement on plugin
        """
        self.onAgentInit(client, tid, request)

    def __onAgentReset(self, client, tid, request):
        """
        Function to reimplement on plugin
        """
        logging.debug("Resetting agent testUuid=%s ScriptId=%s AdapterId=%s" % (request['uuid'], 
                                                                             request['script_id'], 
                                                                             request['source-adapter']) )
        logging.debug("Tests context before reset: %s" % self.testsContext)

        if request['uuid'] in self.testsContext:
            try:
                if request['source-adapter'] in self.testsContext[request['uuid']]:
                    test_ctx = self.testsContext[request['uuid']][request['source-adapter']]
                    if test_ctx.shared:
                        logging.debug("Shared adapter detected, ignore reset")
                    else:   
                        test_ctx.stop()
                        test_ctx.join()
                        
                        test_ctx = self.testsContext[request['uuid']].pop(request['source-adapter'])
                        del test_ctx
                        if not len(self.testsContext[request['uuid']]):
                            test_ctx  = self.testsContext.pop(request['uuid'])
                            del test_ctx
                        logging.debug("Agent resetted testUuid=%s ScriptId=%s AdapterId=%s" % (request['uuid'], 
                                                                                            request['script_id'], 
                                                                                            request['source-adapter']) ) 
                        self.onAgentReset(client, tid, request)
                else:
                    logging.debug("AdapterId=%s does not exists in test context" % request['source-adapter'] )
            except Exception as e:
                pass # not really nice to bypass exception here...
        else:
            logging.debug("TestUuid=%s does not exists in test context" % request['uuid'] )

    def __onAgentAlive(self, client, tid, request):
        """
        Function to reimplement on plugin
        """
        logging.debug("Updating keepalive testUuid=%s ScriptId=%s AdapterId=%s" % (request['uuid'], 
                                                                                request['script_id'], 
                                                                                request['source-adapter']) )
        if request['uuid'] in self.testsContext:
            if request['source-adapter'] in self.testsContext[request['uuid']]:
                test_ctx = self.testsContext[request['uuid']][request['source-adapter']]
                test_ctx.updateTimestamp()
                logging.debug("Agent alive testUuid=%s ScriptId=%s AdapterId=%s" % (request['uuid'], 
                                                                                 request['script_id'], 
                                                                                 request['source-adapter']) )                 
                self.onAgentAlive(client, tid, request)
    
    def onAgentReady(self, client, tid, request):
        """
        Function to reimplement on plugin
        """
        pass
 
    def onAgentNotify(self, client, tid, request):
        """
        Function to reimplement on plugin
        """
        pass
 
    def onAgentInit(self, client, tid, request):
        """
        Function to reimplement on plugin
        """
        pass

    def onAgentReset(self, client, tid, request):
        """
        Function to reimplement on plugin
        """
        pass
 
    def onAgentAlive(self, client, tid, request):
        """
        Function to reimplement on plugin
        """
        pass
        
    def onResetTestContext(self, testUuid, scriptId, adapterId):
        """
        Function to reimplement on plugin
        """
        pass

    def onDisconnection(self, byServer=False, inactivityServer=False):
        """
        On disconnection
        """
        logging.debug( "disconnection by-server=%s inactivity=%s" % (byServer, inactivityServer) )
        NetLayerLib.ClientAgent.onDisconnection(self)
        self.onToolDisconnection(byServer=byServer, inactivityServer=inactivityServer)
        logging.debug( "[onDisconnection] terminated" )
        
    def onToolDisconnection(self, byServer=False, inactivityServer=False):
        """
        On tool disconnection
        """
        logging.debug("Disconnnection")
    
    def onProxyConnectionSuccess(self):
        """
        On proxy connection success
        """
        logging.debug("Connection successful")
        if self.wsSupport:
            logging.debug("Do ws handshake")
            wspath = Settings.get( 'Server', 'websocket-path' )
            if self.sslSupport:
                wspath = Settings.get( 'Server', 'websocket-secure-path' )
            self.handshakeWebSocket(resource=wspath, hostport=self.controllerIp)
        else:
            self.doRegistration()
            
    def onConnectionSuccessful(self):
        """
        On connection successful
        """
        logging.debug("Connection successful")
        if self.wsSupport:
            logging.debug("Do ws handshake")
            wspath = Settings.get( 'Server', 'websocket-path' )
            if self.sslSupport:
                wspath = Settings.get( 'Server', 'websocket-secure-path' )
            self.handshakeWebSocket(resource=wspath, hostport=self.controllerIp)
        else:
            self.doRegistration()

    def onWsHanshakeSuccess(self):
        """
        On websocket hanshake success
        """
        self.regRequest = threading.Event()
        logging.debug("Handshake OK")
        self.regThread = threading.Thread(target=self.doRegistration, 
                                          args=(self.regRequest,))
        self.regThread.start()

    def onPreCleanup(self):
        """
        Called on program stop
        """
        logging.debug("pre cleanup called")
        try:
            # reset all tests
            logging.debug("Tests context before cleanup: %s" % self.testsContext)
            for scriptId, s  in self.testsContext.items():
                for adapterId, a in s.items():
                    try:
                        if a.ctx() is not None:
                            a.ctx().stop()
                            a.ctx().join()
                    except Exception as e:
                        pass
                    a.stop()
                    a.join()
        except Exception as e:
            pass
        logging.debug("Tests context after cleanup: %s" % self.testsContext)    
        self.onCleanup()
        
    def cleanupTestContext(self, testUuid, scriptId, adapterId):
        """
        Try to clean up the test context in all
        """
        logging.debug("cleanup test context called")        
        # remove the adapter thead from the test context
        logging.debug('removing adapterId=%s thread from test context' % adapterId)
        try:
            adapterThread = self.context()[testUuid].pop(adapterId)
        except Exception as e:
            pass # by pass exception, sometime adapterID is already removed from the context
            
        try:
            adapterThread.stop()
            adapterThread.join()
        except Exception as e:
            pass # by pass exception and ignore errors
        del adapterThread
        
        # current test uuid is empty ?
        if not len(self.context()[testUuid]):
            logging.debug('removing testUuid=%s from test context' % testUuid)
            try:
                test = self.context().pop(testUuid)
                del test
            except Exception as e:
                pass # by pass exception, sometime testUuid is already removed from the context
                
        logging.debug("Tests context: %s" % self.testsContext)
        
    def onCleanup(self):
        """
        Called on program stop
        """
        pass
        
    def sendError(self, request, data):
        """send error"""
        logging.error( "send error: %s"  % str(data) )
        req =  request
        req['event'] = "agent-error"
        req['data'] = data
        self.notify( data=req )

    def sendNotify(self, request, data):
        """send notify"""
        logging.debug( "send notify: %s"  % len(data) )
        req =  request
        req['event'] = "agent-notify"
        req['data'] = data
        self.notify( data=req )

    def sendData(self, request, data):
        """send data"""
        logging.debug( "send notify: %s"  % len(data) )
        req =  request
        req['event'] = "agent-data"
        req['data'] = data
        self.notify( data=req )

    def requestNotify (self, resultPath, fileName):
        """send notify"""
        logging.info( 'Notify the server'  )
        try:
            tpl =  { 'cmd': Messages.CMD_NEW_FILE, 
                     'result-path': resultPath, 
                     'filename': fileName } 
            NetLayerLib.ClientAgent.notify( self, data = tpl )
        except Exception as e:
            logging.error( "unable to send notify: %s"  % str(e) )

    def uploadData(self, fileName, resultPath, data=None, filePath=None, callId=None):
        """Upload data"""
        logging.debug("Upload binary data")
                      
        if data is not None:
            fileContent = base64.b64encode(data)
            
        if filePath is not None:
            fd = open(filePath, 'rb')
            fileContent = base64.b64encode(fd.read())
            fd.close()

        t = threading.Thread(target=self.__callRest, args=(resultPath, fileName, 
                                                           fileContent, callId)  )
        t.start()
        
    def onUploadError(self, callId=None):
        """On upload error"""
        logging.error('upload error, cleanup temp folder')

    def __callRest(self, resultPath, fileName, fileContent, callId=None):
        """
        Rest call
        """
        # set proxy is activated
        proxyDict = {}
        if eval( Settings.get( 'Server', 'proxy-active' ) ):
            proxyAddr = Settings.get( 'Server', 'addr-proxy-http' )
            proxyPort = Settings.get( 'Server', 'port-proxy-http' )
            logging.debug("Proxy activated for rest Ip=%s Port=%s" % (proxyAddr, proxyPort) )
            
            https_proxy = "https://%s:%s" % (proxyAddr, proxyPort)
            proxyDict = { "https" : https_proxy}

        # for support server on python3, not nice ...
        resultPath = resultPath.replace('\\', '\\\\')
        
        req = '{"result-path": "%s", "file-name": "%s", "file-content": "%s"}' % ( resultPath,
                                                                                   fileName,
                                                                                   fileContent.decode("utf8") )
        api_scheme = "https"
        if not eval( Settings.get( 'Server', 'rest-api-ssl' ) ):
            api_scheme = "http"
        api_url = "%s://%s:%s%sresults/upload/file" % ( api_scheme,
                                                        self.controllerIp, 
                                                        Settings.get( 'Server', 'rest-api-port' ),
                                                        Settings.get( 'Server', 'rest-api-path' ))
        logging.debug("API URL=%s" % (api_url) )
        r = requests.post(api_url,
                        headers = {'Content-Type': 'application/json;charset=utf-8'},
                        data = req.encode("utf8"),
                        proxies=proxyDict, verify=False)
        if r.status_code != 200:
            logging.error('Unable to reach the rest api: %s - %s' % (r.status_code, r.text) )
            self.onUploadError(callId=callId)