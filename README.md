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
    * [Generate token](#generate-token)
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
    --token=TOKEN      Token agent
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
| [ssh](https://github.com/ExtensiveAutomation/extensiveautomation-agent-plugin-ssh) | communicate with remote server through SSH | plugin-cli |
| [selenium3](https://github.com/ExtensiveAutomation/extensiveautomation-agent-plugin-selenium) | interact with a selenium server | plugin-gui |
| [sikulix](https://github.com/ExtensiveAutomation/extensiveautomation-agent-plugin-sikulix) | run sikulix commands | plugin-gui |

### Agent Deployment

### Generate token

A token is mandatory to connect a remote agent to your automation server.

1. Connect on your automation server 

2. Executes the following command

```bash
extensiveautomation --generate-token agent01.curl
agent01.curl 0bb2705c-9860-445b-b0fc-44b552476cb3
```

3. Save the token generated and reload the server

```bash
extensiveautomation --reload
```

### Running agent

Running agent is easy but before 
- you must install the good plugin according to your needs 
- generate a token for your agent
- register then on the server

After that you can execute the following command:

```bash
extensiveautomation_agent --remote=10.0.0.100 --token=13ae34f7-e2f6-40b6-9c87-6c275423127e --curl
2020-07-26 10:28:09,513 starting agent curl ...
2020-07-26 10:28:09,877 agent registration successful
```
