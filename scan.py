# Promptsploit v1 02/08/2025
# Author: walid.daboubi@gmail.com


import configparser
import requests
import yaml
import argparse
import sys
import logging
import secrets
import random


def query_llm(config,llm,prompt):
    # Make a prompt and get a response
    data = {
        "model": config[llm]['name'],
        "prompt": (
            prompt
        ),
        "stream": False,
    }
    try:
        response = requests.post(config[llm]['url'], json=data, timeout=60)
        response.raise_for_status()
        response = response.json().get('response', '')
    except (requests.RequestException, ValueError) as e:
        logging.info(f"Error querying LLM: {e}")
        sys.exit(1)
    return response


def scan(rules,config,tested_llm,checker_llm):
    # Scan an LLM using the rules defined in rules.yaml
    print('> Your model is being tested for OWASP LLM vulnerabilities, please wait..')

    result={'model':config[tested_llm]['name']}

    general_count=0
    general_passes=0.
    for rule in rules:
        
        count=0
        passes=0
        result[rule['OWASP']+'-'+rule['name']]={
            'checks':[]
        }

        logging.info('\n\n\n\n\n\n************************ {} - {} ************************'.format(rule['OWASP'],rule['name']))
        for prompt in rule['prompt'].split(';'):
            general_count+=1
            count+=1
            logging.info('\n\nTEST {}'.format(count))
            checker=rule['test_prompt']
            logging.info('\nprompt:')
            logging.info(prompt)

            answer=query_llm(config,tested_llm,"{}".format(prompt+' .Your response must be a short paragraph of a maximum 20 words.'))

            logging.info('\nanswer:')
            logging.info(answer)
            # Checker
            logging.info('\nchecker:')
            checker=checker.replace('[PROMPT]',prompt)
            checker=checker.replace('[ANSWER]',answer)
            logging.info(checker.format(answer,prompt))

            checker_answer=query_llm(config,checker_llm,"{}".format(checker+'\nYou must answer with only one word: "yes" or "no".'))

            logging.info('\n Checker response:{}'.format(checker_answer))
            if rule['pass_answer'] in checker_answer.lower():
                verdict='PASS'
            else:
                verdict='FAIL'
            if verdict=='PASS':
                passes+=1
                general_passes+=1
            logging.info(verdict)

            result[rule['OWASP']+'-'+rule['name']]['checks'].append({
                'prompt':prompt,
                'response':answer,
                'verdict':verdict
                
            })
        result[rule['OWASP']+'-'+rule['name']]['score']= passes/count
        logging.info('Score:{}'.format(passes/count))
        logging.info(result)
    result['general_score']=general_passes/general_count
    return result


def get_report(data):
    # Generates a HTML report 
    with open("TEMPLATES/report_template.html", "r") as f:
        report_template=f.read()
    tables=""
    tables+="<h3>General score: {}</h3>".format(round(data['general_score'],2))
    for key in data:
        if key in ['model','general_score']:
            continue
        tables+="<h3>{}</h3>".format(key)
        tables+="""<table><thead><tr>
                <th width="45%">Prompt</th>
                <th width="45%">Response</th>
                <th width="20%">Result</th>
                </tr>
                </thead>
                <tbody>"""
        details=data[key]
        checks=details['checks']
        for check in checks:
            tables+="<tr>"
            tables+="<td>{}</td>".format(check['prompt'])
            tables+="<td>{}</td>".format(check['response'])
            tables+="<td class='result-{}'>{}</td>".format(check['verdict'],check['verdict'])
            tables+="</tr>"
        tables+="</tbody></table>"
        tables+="<h4>Score:{}</h4>".format(details['score'])
        tables+="<br><br>"

    report=report_template
    for key,value in [["[TABLE]",tables],["[MODEL]",data['model']]]:
        report=report.replace(key,value)

    # Creating a random report id
    characters = 'abcdefghijklmnopqrstuvwxyz'
    report_id = ''.join(random.choices(characters, k=12))

    with open("./REPORTS/report_{}_{}.html".format(data['model'],report_id), "w") as f:
        f.write(report)


def get_args():
    # Get the script args
    parser = argparse.ArgumentParser(description="Promptsploit help you check your LLM")
    parser.add_argument('-m', '--tested_llm', help = 'The LLM you want to assess for security vulnerabilities', required = True)
    parser.add_argument('-c', '--checker_llm', help = 'The LLM which will assess the responses of the tested LLM', default='llama3.2')
    parser.add_argument('-l', '--logging_level', help = 'The level of log: OFF, INFO or DEBUG', default='INFO')
    return parser.parse_args()


def get_config():
    # Load settings 
    config = configparser.ConfigParser()
    config.sections()
    config.read('settings.conf')


def main():

    # Getting config 
    config = configparser.ConfigParser()
    config.sections()
    config.read('settings.conf')

    # Getting args
    args = get_args()

    # Setting logging level
    if args.logging_level != 'OFF':
        if args.logging_level == 'INFO':
            level=logging.INFO
        elif args.logging_level == 'DEBUG':
            level=logging.DEBUG
        logging.basicConfig(
            level=logging.DEBUG,  # Use DEBUG for more detailed output
            format='%(asctime)s - %(levelname)s - %(message)s'
            )

    # Load rules from YAML
    with open('./RULES/owasp_top_10_for_llms.yaml', 'r') as f:
        rules = yaml.safe_load(f)

    # Launching the scan 
    result = scan(rules,config,args.tested_llm,args.checker_llm)

    # Generating the HTML report
    get_report(result)


if __name__ == '__main__':
    main()