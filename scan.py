import configparser
import requests
import yaml


def scan(rules,config):
    result={}
    url=config['LLM']['url']

    for rule in rules:
        score=0
        count=0
        successes=0
        result[rule['OWASP']+'-'+rule['name']]={
            'checks':[]
        }

        print('\n\n\n\n\n\n************************ {} - {} ************************'.format(rule['OWASP'],rule['name']))
        for prompt in rule['prompt'].split(';'):
            count+=1
            print('\n\nTEST {}'.format(count))
            #prompt=rule['prompt']
            checker=rule['test_prompt']
            print('\nprompt:')
            print(prompt)
            # Prompt 
            data = {
                    "model": config['LLM']['model'],
                    "prompt": (
                        "{}".format(prompt+' .Your response must be a short paragraph of a maximum 20 words.')
                    ),
                    "stream": False,
            }
            response = requests.post(url, json=data)
            answer=(response.json()['response'])
            print('\nanswer:')
            print(answer)
            # Checker
            print('\nchecker:')
            checker=checker.replace('[PROMPT]',prompt)
            checker=checker.replace('[ANSWER]',answer)
            print(checker.format(answer,prompt))
            data = {
                    "model": config['CHECKER_LLM']['model'],
                    "prompt": (
                        "{}".format(checker+' your answer must be "yes" or "no" without punctuation and do not add any explications.')
                    ),
                    "stream": False,
            }
            response = requests.post(url, json=data)
            checker_answer=(response.json()['response'])
            print(checker_answer)
            if rule['pass_answer'] in checker_answer.lower():
                verdict='SUCCESS'
            else:
                verdict='FAILED'
            if verdict=='SUCCESS':
                successes+=1
            print(verdict)

            result[rule['OWASP']+'-'+rule['name']]['checks'].append({
                'prompt':prompt,
                'response':answer,
                'verdict':verdict
                
            })
        result[rule['OWASP']+'-'+rule['name']]['score']= successes/count
        print('<<<<<<<<<<<<<<<<<< Score:')
        print(successes/count)
        print(result)
    return result


def main():
    # Load settings 
    config = configparser.ConfigParser()
    config.sections()
    config.read('settings.conf')
    
    # Load rules from YAML
    with open('rules.yaml', 'r') as f:
        rules = yaml.safe_load(f)
    scan(rules,config)
    

if __name__ == '__main__':
    main()