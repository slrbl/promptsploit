# Promptsploit v1 02/08/2025
# Author: walid.daboubi@gmail.com


import configparser
import requests
import yaml
import argparse
import sys
import logging
import random
import subprocess


def query_llm(config,llm,prompt):
    # Make a prompt and get a response

    data = {
        "model": llm,
        "prompt": (
            prompt
        ),
        "stream": False,
    }
    try:
        url=config[llm]['url']
    except: 
        logging.info(f"URL not found for {llm}. Make sure that this LLM has been added to yout config file.")
        sys.exit(1)

    try:
        response = requests.post(config[llm]['url'], json=data, timeout=600)
        response.raise_for_status()
        response = response.json().get('response', '')
    except (requests.RequestException, ValueError) as e:
        logging.info(f"Error querying LLM: {e}")
        sys.exit(1)
    return response



def scan(rules,config,tested_llm,checker_llm,owasp_category):
    # Scan an LLM using the rules defined in rules.yaml
    print('> Your model is being tested for OWASP LLM vulnerabilities, please wait..')

    result={'model':tested_llm}

    general_count=0
    general_passes=0.

    # Filter rules if a specific category is selected by user 
    active_rules=rules
    if owasp_category!='All':
        active_rules=[]
        for rule in rules:
            if rule['OWASP']==owasp_category:
                active_rules.append(rule)
                break
    
    for rule in active_rules:

        count=0
        passes=0
        result[rule['OWASP']+'-'+rule['name']]={
            'checks':[]
        }

        logging.info('\n\n\n************************ {} - {} ************************\n\n\n'.format(rule['OWASP'],rule['name']))
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

    report_file_path="./REPORTS/report_{}_{}.html".format(data['model'],report_id)
    with open(report_file_path, "w") as f:
        f.write(report)

    return report_file_path



def get_compare_report(multiple_result_data):
    # Generates a HTML report 
    with open("TEMPLATES/report_template.html", "r") as f:
        report_template=f.read()

    tables=""
    for data in multiple_result_data:
        tables+="<h3>General score for {}: {}</h3>".format(data['model'],round(data['general_score'],2))
    


    for key in multiple_result_data[0]:
        if key in ['model','general_score']:
            continue
        tables+="<h3>{}</h3>".format(key)
        tables+="""<table><thead><tr>
                <th width="30%">Prompt</th>
                <th width="30%">{} Response</th>
                <th width="10%">Verdict</th>
                <th width="30%">{} Response</th>
                <th width="10%">Verdict</th>
                </tr>
                </thead>
                <tbody>""".format(multiple_result_data[0]['model'],multiple_result_data[1]['model'])
        details_llm_1=multiple_result_data[0][key]
        details_llm_2=multiple_result_data[1][key]

        checks_llm_1=details_llm_1['checks']
        checks_llm_2=details_llm_2['checks']

        for check1,check2 in zip(checks_llm_1,checks_llm_2):
            tables+="<tr>"
            tables+="<td>{}</td>".format(check1['prompt'])
            tables+="<td>{}</td>".format(check1['response'])
            tables+="<td class='result-{}'>{}</td>".format(check1['verdict'],check1['verdict'])
            tables+="<td>{}</td>".format(check2['response'])
            tables+="<td class='result-{}'>{}</td>".format(check2['verdict'],check2['verdict'])
            tables+="</tr>"
        tables+="</tbody></table>"
        tables+="<h4>Score:{}</h4>".format(details_llm_1['score'])
        tables+="<h4>Score:{}</h4>".format(details_llm_2['score'])
        tables+="<br><br>"

    report=report_template
    for key,value in [["[TABLE]",tables],["[MODEL]",'{} v/s {}'.format(multiple_result_data[0]['model'],multiple_result_data[1]['model'])]]:
        report=report.replace(key,value)

    # Creating a random report id
    characters = 'abcdefghijklmnopqrstuvwxyz'
    report_id = ''.join(random.choices(characters, k=12))

    report_file_path="./REPORTS/report_{}_vs_{}_{}.html".format(multiple_result_data[0]['model'],multiple_result_data[1]['model'],report_id)
    with open(report_file_path, "w") as f:
        f.write(report)

    return report_file_path


def get_args():
    # Get the script args
    parser = argparse.ArgumentParser(description="Promptsploit help you check your LLM")
    parser.add_argument('-m', '--tested_llm', help = 'The LLM you want to assess for security vulnerabilities', required = True)
    parser.add_argument('-c', '--checker_llm', help = 'The LLM which will assess the responses of the tested LLM (llama3.2 by default)', default='llama3.2')
    parser.add_argument('-o', '--owasp__llm_category', help = 'Scan for a specific OWASP for LLM category', default='All')
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


    data=[]

    # Launching the scan 
    for tested_llm in args.tested_llm.split(','):
        print("==========")
        print(tested_llm)
        print("==========")
        if tested_llm!='':
            result = scan(rules,config,tested_llm,args.checker_llm,args.owasp__llm_category)
            data.append(result)

    if len(data)==1:
        # Generating a HTML report for a single model 
        report_file_path=get_report(data[0])
    else:
        # Generating a report that compare 2 or more LLMs
        report_file_path=get_compare_report(data)

    # open the report 
    subprocess.run(["open", report_file_path])


if __name__ == '__main__':
    main()
