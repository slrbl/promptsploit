# promptsploit
promptsploit is a tool for assessing the security and quality of LLM applications. It uses a combination of preset rules and a checker LLM to evaluate your applications. Based on the OWASP Top 10 for LLMs, promptsploit generates easy-to-read reports highlighting potential risks and issues.

<img src='IMAGES/flowchart.png' width="80%"/>

## Setup

### Using a Python virtual env

```shell
python -m venv promptsploit_env
source promptsploit_env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
