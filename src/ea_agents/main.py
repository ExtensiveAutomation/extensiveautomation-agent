#!/usr/bin/python

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

from ea_agents import handler
from ea_agents.libs import settings

import optparse
import sys
import logging

    
settings.initialize()
        
if not settings.cfgFileIsPresent():
    logging.error( "config file missing" )
    sys.exit(1)

# prepare the command line with all options	
parser = optparse.OptionParser()

parser.add_option('--verbose', dest='verbose', action="store_true", default=False,
                    help="Verbose mode")
      
parser.add_option('--remote', dest='remote', default='127.0.0.1',
                    help="Server host address (default=127.0.0.1)")
                    
parser.add_option('--port', dest='port', default=8083,
                    help="Server port (optional default=8083)")
                    
parser.add_option('--name', dest='agent_name',  
                    help="Agent name (example: agent.win.curl01)")

parser.add_option('--proxy', dest='proxy', default=None, 
                    help="Proxy address:port (optional)")
                    
for p in handler.get_plugins().keys():
    parser.add_option('--%s' % p, dest='%s' % p, action="store_true", default=False)


(options, args) = parser.parse_args()

logging_level = logging.INFO
if options.verbose:
    logging_level = logging.DEBUG
    
logging.basicConfig(format='%(asctime)s %(message)s', level=logging_level)


def cli():
    if not options.agent_name:
        parser.print_help()
        sys.exit(2)

    mgnr = handler.AgentHandler()

    support_proxy = False
    proxy_host = None
    proxy_port = None
    if options.proxy is not None:
        if ":" not in options.proxy:
            parser.print_help()
            sys.exit(2)
        else:
            proxy_host, proxy_port = options.proxy.split(":", 1)
            support_proxy = True

    agent_type = None
    for p in handler.get_plugins().keys():
        if getattr(options, p) == True:
            agent_type = p
        
    if agent_type is None:
        parser.print_help()
        sys.exit(2)
        
    mgnr.initialize(ip=options.remote, 
                    port=options.port, 
                    agent_type=agent_type, 
                    agent_name=options.agent_name,
                    sslSupport=True, 
                    isAgent=0, 
                    fromCmd=True,
                    supportProxy=support_proxy,
                    proxyIp=proxy_host, 
                    proxyPort=proxy_port)

    sys.exit(0)    