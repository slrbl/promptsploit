# promptsploit
promptsploit is a tool for assessing the security and quality of LLM applications. It uses a combination of preset rules and a checker LLM to evaluate your applications against the OWASP Top 10 for LLMs vulnerabilities. promptsploit generates and easy-to-read reports highlighting potential risks and issues.

## How does it work

<center><img src='IMAGES/flowchart.png'/></center>

## Setup

### Ollama
You need to install Ollama on your local machines. More details can be found at https://ollama.com.


### Using a Python virtual env
```shell
python -m venv promptsploit_env
source promptsploit_env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Settings file
Copy settings.template to settings.conf and adjust it according to your needs.
You can also create a new settings file as in the following example:
```shell
[mistral]
name:mistral
url:http://localhost:11434/api/generate
token:

[llama3.2]
name:llama3.2
url:http://localhost:11434/api/generate
token:
```

## Usage

```shell
python promptsploit.py -h       
usage: promptsploit.py [-h] -m TESTED_LLM [-c CHECKER_LLM] [-l LOGGING_LEVEL]

Promptsploit help you check your LLM

options:
  -h, --help            show this help message and exit
  -m, --tested_llm TESTED_LLM
                        The LLM you want to assess for security vulnerabilities
  -c, --checker_llm CHECKER_LLM
                        The LLM which will assess the responses of the tested LLM (llama3.2 by default)
  -l, --logging_level LOGGING_LEVEL
                        The level of log: OFF, INFO or DEBUG
```

This is an example of testing mistral model
```shell
python promptsploit.py -m mistral -l OFF 
```
Note that the model you want to test and the checker model have to be declared in sessting.conf, here is an example:
```shell
[mistral]
name:mistral
url:http://localhost:11434/api/generate

[llama3.2]
name:llama3.2
url:http://localhost:11434/api/generate
```

## Report 
The following is an example of a prompsploit report for nuextract model

<center><img src='IMAGES/promptsploit_report_example.png' width="50%"/></center>
