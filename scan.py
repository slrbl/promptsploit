import configparser
import requests
import yaml


def scan(rules,config):
    result=[]
    url=config['LLM']['url']
    for rule in rules:
        print('\n\n************************ {} - {} ************************'.format(rule['OWASP'],rule['name']))
        prompt=rule['prompt']
        checker=rule['test_prompt']
        print('\nprompt:')
        print(prompt)
        # Prompt 
        data = {
                "model": config['LLM']['model'],
                "prompt": (
                    "{}".format(rule['prompt']+' Respond by a paragraph of a maximum of 2 phrases')
                ),
                "stream": False,
        }
        response = requests.post(url, json=data)
        answer=(response.json()['response'])
        print('\nanswer:')
        print(answer)
        # Checker
        #print('\nchecker:')
        #print(checker.format(answer,prompt))
        data = {
                "model": config['CHECKER_LLM']['model'],
                "prompt": (
                    "{}".format(checker.format(answer,prompt)+'? I want a "yes" or "no" answer without punctuation. Do not add any explications.')
                ),
                "stream": False,
        }
        response = requests.post(url, json=data)
        checker_answer=(response.json()['response'])
        #print('\nchecker_answer:')
        #print(checker_answer)
        if checker_answer.lower() == rule['pass_answer']:
            verdict='SUCCESS'
        else:
            verdict='FAILED'
        print(verdict)
        result.append(
            {
                'OWASP':rule['OWASP'],
                'name':rule['name'],
                'result':verdict
            }
        )
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
    print("\n\n\n\n")
    



if __name__ == '__main__':
    main()