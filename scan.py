import configparser
import requests
import yaml
import argparse

def scan(rules,config,tested_llm,checker_llm):

    result={'model':config[tested_llm]['name']}

    general_count=0
    general_passes=0.
    for rule in rules:
        
        count=0
        passes=0
        result[rule['OWASP']+'-'+rule['name']]={
            'checks':[]
        }

        print('\n\n\n\n\n\n************************ {} - {} ************************'.format(rule['OWASP'],rule['name']))
        for prompt in rule['prompt'].split(';'):
            general_count+=1
            count+=1
            print('\n\nTEST {}'.format(count))
            #prompt=rule['prompt']
            checker=rule['test_prompt']
            print('\nprompt:')
            print(prompt)
            # Prompt 
            data = {
                    "model": config[tested_llm]['name'],
                    "prompt": (
                        "{}".format(prompt+' .Your response must be a short paragraph of a maximum 20 words.')
                    ),
                    "stream": False,
            }
            response = requests.post(config[tested_llm]['url'], json=data)
            answer=(response.json()['response'])
            print('\nanswer:')
            print(answer)
            # Checker
            print('\nchecker:')
            checker=checker.replace('[PROMPT]',prompt)
            checker=checker.replace('[ANSWER]',answer)
            print(checker.format(answer,prompt))
            data = {
                    "model": config[checker_llm]['name'],
                    "prompt": (
                        "{}".format(checker+'\nYou must answer with only one word: "yes" or "no".')
                    ),
                    "stream": False,
            }
            response = requests.post(config[checker_llm]['url'], json=data)
            checker_answer=(response.json()['response'])
            print('\n Checker response:{}'.format(checker_answer))
            if rule['pass_answer'] in checker_answer.lower():
                verdict='PASS'
            else:
                verdict='FAIL'
            if verdict=='PASS':
                passes+=1
                general_passes+=1
            print(verdict)

            result[rule['OWASP']+'-'+rule['name']]['checks'].append({
                'prompt':prompt,
                'response':answer,
                'verdict':verdict
                
            })
        result[rule['OWASP']+'-'+rule['name']]['score']= passes/count
        print('<<<<<<<<<<<<<<<<<< Score:')
        print(passes/count)
        print(result)
    result['general_score']=general_passes/general_count
    return result


def get_report(data):
    with open("template.html", "r") as f:
        report_template=f.read()
    tables=""
    tables+="<h3>Genral score: {}</h3>".format(round(data['general_score'],2))
    for key in data:
        if key in ['model','general_score']:
            continue
        owasp=key
        tables+="<h3>{}</h3>".format(owasp)
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

    with open("report_{}.html".format(data['model']), "w") as f:
        f.write(report)



def get_args():
    parser = argparse.ArgumentParser(description="Promptsploit help you check your LLM")
    parser.add_argument('-m', '--tested_llm', help = 'The LLM you want to assess for security vulnerabilities', required = True)
    parser.add_argument('-c', '--checker_llm', help = 'The LLM which will assess the responses of the tested LLM', default='llama3.2')
    return parser.parse_args()





def main():
    # Load settings 
    config = configparser.ConfigParser()
    config.sections()
    config.read('settings.conf')

    args = get_args()

    # Load rules from YAML
    with open('rules.yaml', 'r') as f:
        rules = yaml.safe_load(f)

    result = scan(rules,config,args.tested_llm,args.checker_llm)
    get_report(result)


if __name__ == '__main__':
    main()