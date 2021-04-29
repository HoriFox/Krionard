from requests import post
import argparse
import json
import sys

'''
    Запуск тестового файла:
    >>> python3 call.py [-t 'команда марусе'] [-c 'количество повторений запросов']
'''

parser = argparse.ArgumentParser(description='Marusya skill unittest executor')
parser.add_argument('-t', '--text', metavar='TEXT', type=str,
                    default='включи навык ассоль включи',
                    help='Command string from Marusya')
parser.add_argument('-d', '--device', metavar='DEVICE', type=str,
                    default='свет',
                    help='Command string from Marusya')
parser.add_argument('-c', '--count', metavar='N', type=int,
                    default=1,
                    help='Request repeat count')
parser.add_argument('-H', '--host', type=str,
                    default='127.0.0.1',
                    help='Server hostname or IP')
parser.add_argument('-p', '--port', type=int,
                    default=5000,
                    help='Server port')
parser.add_argument('-r', '--request', type=str,
                    default='test/request.json',
                    help='Path to request JSON file')
args = parser.parse_args()


def post_test(message = None):
	with open(args.request, 'r') as f:
		request = json.load(f)

		request['request']['command'] = message
		request['request']['original_utterance'] = message
		request['request']['nlu']['tokens'] = message.split(' ')

		url = 'http://{}:{}/'.format(args.host, args.port)
		print(	'<-- Send request\n' +
			'URL: %s\n' % url +
			'Message: %s\n' % message +
			'Tokens: %s' % message.split(' '))
		res = post(url, json=request)
		answer = res.json()
		edit_answer = answer['response']
		print(	'--> Get responce\n' +
			' | '.join([str(elem) for elem in edit_answer.values()]), '\n')


if __name__ == "__main__":
    for i in range(args.count):
        post_test(args.text + ' ' + args.device)
