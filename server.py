from flask import Flask
from utils import *
from plugins import Skill
import logging
from flask.logging import default_handler

class FlaskServer (Flask):
	"""
	Класс сервера с загрузкой конфигураций, словарей и
	созданием экземляра Skill
	"""
	def __init__(self, import_name, config_file, vocabulary_file):
		super(FlaskServer, self).__init__(import_name)
		self.skill_config = self.load_config(config_file)
		self.vocabulary = self.load_vocabulary(vocabulary_file)
		self.handler = logging.StreamHandler(sys.stderr)
		self.logger.removeHandler(default_handler)
		self.logger.addHandler(self.handler)
		self.logger.setLevel(logging.DEBUG)
		self.skill = Skill(self.skill_config, self.vocabulary, self.logger)

	def load_config(self, path):
		"""
		Загрузка файла конфигураций для подключений к redis, базе данных и т.д.
		"""
		skill_config = {
				'host_redis': '127.0.0.1',
				'port_redis': 6379,
				'user_mysql': 'marusyatech',
				'password_mysql': 'password',
				'host_mysql': '127.0.0.1',
				'port_mysql': 3306,
				'database_mysql': 'marusyatech',
				'skillname': 'ассоль',
				'smarthome_addr': '127.0.0.1',
				'smarthome_port': 4050,
		}
		load_status = True
		try:
			with open(path) as file:
				data = load_json(path)
				skill_config.update(data)
		except Exception as err:
			eprint('\n[!]Cant load config from %s: %s' % (path, err))
			eprint('[!]Load default config\n')
			load_status = False
		if load_status:
			eprint('\n[!]Load config from %s\n' % path)
		self.show_load_log('config', skill_config)
		return skill_config

	def load_vocabulary(self, path):
		"""
		Загрузка словаря "разнообразия". Словарь, который содержит не только
		слова ввода и вывода Маруси, но и их разные вариации для достижения
		разнообразия ответов и ввода.
		"""
		vocabulary = {
				'input':{'turnon debug':['включить дебаг'],
					'turnoff  debug':['выключить дебаг'],
					'what can':['что ты умеешь'],
					'turnon':['включи'],
					'turnoff':['выключи']},
				'output':{'canihelp':['могу я помочь'],
					'whatican':'я навык умного дома ассоль',
					'bye':['пока'],
					'dontunderstand':['я не понимаю']}}
		load_status = True
		try:
			with open(path) as file:
				data = load_json(path)
				vocabulary.update(data)
		except Exception as err:
			eprint('\n[!]Cant load vocabulary from %s: %s' % (path, err))
			eprint('[!]Load default vocabulary\n')
			load_status = False
		if load_status:
			eprint('\n[!]Load vocabulary from %s\n' % path)
		return vocabulary

	def show_load_log(self, name, config):
		"""
		Вывод списка загруженных конфигураций.
		Password выводится после предварительного hash()
		"""
		for key in config:
			value = hash(config[key]) if ('password' in key) else config[key]
			eprint('[C]%s - %s' % (key, value))

	def setup_route(self):
		"""
		Устанавливаем маршрутизацию обращений на сервер.
		"""
		self.add_url_rule('/', "run_skill", self.skill.run_skill, methods=['POST'])
		self.add_url_rule('/', "get_info", self.skill.get_info, methods=['GET'])

def create_app(config_file, vocabulary_file):
	"""
	Вызываемая функция создания экземпляра Flask и установки маршрутизации.
	"""
	app = FlaskServer('FlaskServer', config_file, vocabulary_file)
	app.setup_route()
	return app
