from requests import post
from json import load
import sys
#from similarity import lev_dis

'''
    Запуск тестового файла:
    >>> python3 unittest.py [команда марусе] [количество повторений запросов]
'''

def post_test(message = None):
    with open('/usr/bin/assol/request.json', 'r') as f:
        request = load(f)

        request['request']['command'] = message
        request['request']['original_utterance'] = message
        request['request']['nlu']['tokens'] = message.split(' ')

        url = 'http://localhost:8080'
        res = post(url, json=request)
        answer = res.json()
        edit_answer = answer['response']
        #print(json.dumps(edit_answer.values(), ensure_ascii=False))
        print(' | '.join([str(elem) for elem in edit_answer.values()]))

text = 'включи навык ассоль стандартная команда после включающей'
if len(sys.argv) > 1:
    text = sys.argv[1]
count_post = 3
if len(sys.argv) > 2:
    count_post = int(sys.argv[2])

if __name__ == "__main__":

    #print(lev_dis('Старт! Режим отладки.', 'старт режим отладки'))
    #print(lev_dis('Стоп. Режим отладки.', 'стоп режим отладки'))
    #print(lev_dis('Старт! Режим отладки.', 'старт режим отладки'))

    print('end_session | text | tts')
    for i in range(count_post):
        post_test(text)
