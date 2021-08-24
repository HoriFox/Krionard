import time
from redishelper import RedisConnection
from mysqlhelper import DBConnection
import random
import redis
from similarity import preparer_instruction, lev_dis
from utils import *
from plugins import *
from flask import request, jsonify
import requests

class Skill():
	def __init__(self, config, vocabulary, logger):
		self.config = config
		self.vocabulary = vocabulary
		self.log = logger

	def run_skill(self):
		self.log.info('\n--> REQUEST CAME')
		start_time = time.time()
		json_request = request.json
		text_answer, text_answer_tts, is_end_session = self.compute_module(json_request)
		answer = {
			"response": {
				"text": text_answer,
				"tts": text_answer_tts,
				"end_session": is_end_session},
			"session": {
				"session_id": json_request['session']['session_id'],
				"message_id": json_request['session']['message_id'],
				"user_id": json_request['session']['user_id']},
			"version": json_request['version']}
		delta_time = time.time() - start_time
		self.log.info('ОТЧЁТ: DELTA TIME WORK: %s s', delta_time)
		self.log.info('<-- SEND RESPONSE')
		return jsonify(answer)

	def get_info(self):
		return jsonify({'endpoints': [{'POST /': 'Marusya\'s skill API'}, {'GET /': 'Info'}]})

	def compute_module(self, request_data):
		text_answer = ''
		voice_answer = ''
		is_end_dialog = False

		#[Абсолютный вызод]End word: "Стоп", "выход" and e.t.c
		if request_data['request']['command'] == 'on_interrupt':
			self.log.info('ВЫВОД: выход из навыка Ассоль')
			text_answer, voice_answer = self.output_conf(theme='bye')
			return text_answer, voice_answer, True

		#Получаем данные пользователя
		user_id = request_data['session']['user_id']
		profile = self.get_profile(user_id)
		#Without words of activation "Включи", "навык", "ассоль"
		token_instruction = self.slice_instruction(request_data['request']['nlu']['tokens'])
		#Подготовка текста
		self.log.info('АНАЛИЗ: COMMAND (before): %s', token_instruction)
		token_instruction, unknown_tokens = preparer_instruction(token_instruction, self.vocabulary['input'])
		self.log.info('АНАЛИЗ: COMMAND (after): %s', token_instruction)
		self.log.info('АНАЛИЗ: COMMAND (unknown): %s', unknown_tokens)
		instruction = ' '.join(token_instruction) if token_instruction else str()

		#Получаем контекст
		#self.session = RedisConnection(host=self.config['host_redis'], port=self.config['port_redis'], db=0)
		#self.log.debug('REDIS CONNECTION INITED')

		#Если инструкции пустые, то спросить, что пользователь хочет
		if len(token_instruction) == 0:
			if len(unknown_tokens) == 0 or len(unknown_tokens) == 1 and unknown_tokens[0] == '':
				text_answer, voice_answer = self.output_conf(theme='canihelp', prof=profile)
			else:
				self.log.info('ВЫВОД: не поняла команду, странная комбинация')
				text_answer = voice_answer = random.choice(self.vocabulary['output']['dontunderstand'])

			#self.session.new_session(user_id)
		else:
			is_end_dialog = True
			text_answer, voice_answer = self.switch_command(user_id, token_instruction, unknown_tokens)

			#Добавочная информация режима отладки
			#session_profile = self.session.get_session(user_id)
			#debug = session_profile['debug']
			#if debug == 'true':
			#	history = session_profile['history']
			#	self.log.info('DEBUG')
			#	text_answer, voice_answer = self.output_conf(theme='debug', prof=profile, history=history,
			#				ins=instruction,text=text_answer, voice=voice_answer)
			#	self.session.edit_session(user_id, 'history', instruction)

		self.log.debug('COMPUTE MODULE FINISHED')
		return text_answer, voice_answer, is_end_dialog

	def output_conf(self, **data):
		"""
		Конфигурируемый вывод. Отвечает за вывод информации по указанной
		теме по заданному алгоритму, в основном, по стучайному выбору из
		списка заранее указанных ответов.
		"""
		random.seed()
		text_answer, voice_answer = None, None

		if data['theme'] == 'canihelp':
			name = data['prof'][1] if data['prof'] != None else str()
			name_start, name_end = (name + ' ', str()) if random.randint(0, 1) else (str(), ' ' + name)
			text_answer = voice_answer = name_start + random.choice(self.vocabulary['output']['canihelp']) + name_end + '?'

		if data['theme'] == 'whatican':
			text_answer = voice_answer = self.vocabulary['output']['whatican']

		if data['theme'] == 'bye':
			text_answer = voice_answer = random.choice(self.vocabulary['output']['bye'])

		if data['theme'] == 'debug':
			answer = '. \nDEBUG \nCOMMAND: {}.'.format(data['ins'])
			if data['prof']:
				answer += '\nYOU: {} LOCATED: {}.'.format(data['prof'][1], data['prof'][2])
			if data['history']:
				answer += '\nLAST COMMAND: ' + data['history']
			text_answer = data['text'] + answer if data['text'] is not None else answer
			voice_answer = data['voice'] + answer if data['voice'] is not None else answer

		return text_answer, voice_answer

	def get_profile(self, user_id):
		"""
		Получаем всю информацию о пользователе, что производит запрос.
		Для расширения возможностей по уникальному ответу тому или иному
		пользователю.
		"""
		link = DBConnection(user=self.config['user_mysql'],
							password=self.config['password_mysql'],
							host=self.config['host_mysql'],
							port=self.config['port_mysql'],
				database=self.config['database_mysql'])
		user_row = link.select('users', dict(UserId=user_id))
		if len(user_row) > 0:
			return user_row[0]
		else:
			return None

	def slice_instruction(self, tokens):
		"""
		Отсекатор технических команд от команды запуска.
		[Включи навык Ассоль] включи свет
		Будет удалено то, что находится в квадратных скобках по слову активации.
		"""
		main_instruction = []
		nameskill = self.config['skillname']
		if nameskill in tokens:
			main_instruction = tokens[tokens.index(nameskill)+1:]
		else:
			main_instruction = tokens
		return main_instruction

	def switch_command(self, user_id, token_instruction, unknown_tokens):
		"""
		Метод переключения между командами.
		Пытается выполнить команду из заранее указанного списка.
		"""
		instruction = ' '.join(token_instruction)
		function = {'turnon debug' : self.debug_param,
				'turnoff debug' : self.debug_param,
				'what can' : self.what_can,
				'turnon' : self.relay,
				'turnoff' : self.relay,
				}

		text_answer, voice_answer = '', ''
		command_worked = False
		try:
			text_answer, voice_answer = function[instruction](user_id, token_instruction, unknown_tokens)
		except KeyError:
			# default block switch
			pass
		else:
			command_worked = True
		if command_worked == False:
			self.log.info('ВЫВОД: не поняла команду, странная комбинация')
			text_answer = voice_answer = random.choice(self.vocabulary['output']['dontunderstand'])

		return text_answer, voice_answer

	def debug_param(self, user_id, token_instruction, unknown_tokens):
		stage = token_instruction[0]
		valueDebug = 'true' if stage == 'turnon' else 'false'
		# result = self.session.edit_session(user_id, 'debug', valueDebug)
		# self.log.info('ВЫВОД: Режим отладки: %s, SessionOK: %s' % (valueDebug, result))
		text_answer = voice_answer = '%s режим отладки' % (valueDebug)
		return text_answer, voice_answer

	def what_can(self, user_id, token_instruction, unknown_tokens):
		self.log.info('ВЫВОД: Отвечает, что Ассоль умеет')
		text_answer, voice_answer = self.output_conf(theme='whatican')
		return text_answer, voice_answer

	def relay(self, user_id, token_instruction, unknown_tokens):
		"""
		Отдаём команду и по ответу от dacrover производим голосовую часть
		выполнения команды.
		"""
		self.log.debug('ДЕЙСТВИЕ: RELAY FUNCTION ENTRY POINT')
		stage = token_instruction[0]
		relay_name = ' '.join(unknown_tokens)
		# TODO(m.kucherenko): create authentication method with multiple options
		if self.config['dacrover_auth'] == 'basic_auth':
			auth = '{}:{}@'.format(self.config['dacrover_user'], self.config['dacrover_pass'])
		else:
			auth = ''
		smart_home_baseurl = '{}://{}{}:{}'.format(self.config['dacrover_schema'], auth, self.config['dacrover_addr'], self.config['dacrover_port'])
		value_relay = '1' if stage == 'turnon' else '0'
		text_answer = voice_answer = ''
		try:
			res = requests.post(smart_home_baseurl, json={'type': 'relay', 'name': relay_name, 'value': value_relay})
			res.raise_for_status() # To catch bad requests (not 2xx codes) in except block
			if res.text == 'good':
				self.log.info('ВЫВОД: %s реле' % (stage))
				text_answer, voice_answer = 'готово', 'готово'
			elif res.text == 'error-connection-ip':
				self.log.info('ВЫВОД: dacrover не смогл обратиться по найденному IP адресу')
				text_answer = voice_answer = random.choice(self.vocabulary['output']['couldnotapply'])
			elif res.text == 'didnt-find-unique-device':
				self.log.info('ВЫВОД: dacrover не смог найти уникальное устройство')
				text_answer = voice_answer = random.choice(self.vocabulary['output']['didnotfind'])
		except Exception as err:
			self.log.error('ОШИБКА: Failed to update device state: {}', err)
			text_answer = voice_answer = 'Ошибка запроса к API'

		self.log.debug('ДЕЙСТВИЕ: RELAY FUNCTION FINISHED')
		return text_answer, voice_answer

