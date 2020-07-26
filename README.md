# ExtensiveAutomation Agent

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/extensiveautomation-agent)
![](https://github.com/ExtensiveAutomation/extensiveautomation-agent/workflows/Python%20Package/badge.svg)

**agent** for the extensive automation server. 

## Table of contents
* [Agent Installation](#agent-installation)
	* [PyPI package](#pypi-package)
	* [Source code](#source-code)
	* [Install plugins](#install-plugins)
* [Agent Deployment](#agent-deployment)   
    * [Running agent](#running-agent)

### Agent Installation

### About agents

Agents enable  to execute remotely your workflow. It's can be useful on some cases
to run them from different machine that your extensive automation server.

### PyPI package

1. Run the following command

    ```bash
    python3 -m pip install extensiveautomation_agent
    ```
    
2. Type the following command on your shell to start the server

    ```bash
    extensiveautomation_agent --help
    Usage: extensiveautomation_agent.py [options]

    Options:
    -h, --help         show this help message and exit
    --verbose          Verbose mode
    --remote=REMOTE    Server host address (default=127.0.0.1)
    --port=PORT        Server port (optional default=8083)
    --name=AGENT_NAME  Agent name (example: agent.win.curl01)
    --proxy=PROXY      Proxy address:port (optional)
    ```
    
3. The next step is to install one or more [plugins](#install-plugins)

### Source code
 
1. Clone this repository on your linux server

    ```bash
    git clone https://github.com/ExtensiveAutomation/extensiveautomation-agent.git
    cd extensiveautomation-agent/
    ```

2. Show usage documentation.

    ```bash
    cd src/
    python3 extensiveautomation_agent.py --help
    ```
    
3. The next step is to install one or more [plugins](#install-plugins)


### Install plugins

By default the agent binary comes without plugins so you need 
to install them one by one according to your needs. 
The installation can be done with the `pip` command. 

Take a look to the table below to see the correspondence
between the agents plugins you want to use and the plugin to deploy on server side too.

| Agent Plugins | Description | Server Plugins (must have) |
| ------------- | ------------- | ------------- |
| [curl](https://github.com/ExtensiveAutomation/extensiveautomation-agent-plugin-curl) | send http requests and analyze http responses | plugin-web |
| [ssh](https://github.com/ExtensiveAutomation/extensiveautomation-agent-plugin-ssh) | execute shh commands | plugin-cli |
| [selenium3](https://github.com/ExtensiveAutomation/extensiveautomation-agent-plugin-selenium3) | execute selenium3 commands | plugin-gui |
| [sikuli](https://github.com/ExtensiveAutomation/extensiveautomation-agent-plugin-sikulix) | execute sikulix commands | plugin-gui |
| [adb](https://github.com/ExtensiveAutomation/extensiveautomation-agent-plugin-adb) | execute adb commands | plugin-gui |
| [socket](https://github.com/ExtensiveAutomation/extensiveautomation-agent-plugin-socket) | send and receive network packet |  |
| [database](https://github.com/ExtensiveAutomation/extensiveautomation-agent-plugin-database) | query database | |
| [ftp](https://github.com/ExtensiveAutomation/extensiveautomation-agent-plugin-ftp) | execute ftp commands |  |


### Agent Deployment

### Running agent

Running agent is easy but before you must install the good plugin according to your needs and 
register then on the server, after that you can execute the following command:

```bash
extensiveautomation_agent --remote=10.0.0.100 --name=curl01 --curl
2020-07-26 10:28:09,513 starting agent curl ...
2020-07-26 10:28:09,877 agent registration successful
```
