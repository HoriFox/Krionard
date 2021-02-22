from flask import Flask
from utils import *
from plugins import Skill
import logging
from flask.logging import default_handler

class FlaskServer (Flask):
	def __init__(self, import_name, config_file, vocabulary_file):
		super(FlaskServer, self).__init__(import_name)
		self.skill_config = self.load_config(config_file)
		self.vocabulary = self.load_vocabulary(vocabulary_file)
		self.handler = logging.StreamHandler(sys.stderr)
		self.logger.removeHandler(default_handler)
		self.logger.addHandler(self.handler)
		self.logger.setLevel(logging.DEBUG)
		self.skill = Skill(self.skill_config, self.vocabulary, self.logger)

	def load_config(self, input_path=None):
		skill_config = {
				'host_redis':'127.0.0.1',
				'port_redis':'6379',
				'user_mysql':'marusyatech',
				'password_mysql':'password',
				'host_mysql':'127.0.0.1',
				'port_mysql':'3306',
				'database_mysql':'marusyatech',
				'skillname':'ассоль'}
		path = input_path or '/etc/assol/skill.config.json'
		try:
			with open(path) as file:
				data = load_json(path)
				skill_config.update(data)
		except:
			eprint('[!]Cant load config from %s' % path)
		self.show_load_log('config', skill_config)
		return skill_config

	def load_vocabulary(self, input_path=None):
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

		path = input_path or '/etc/assol/skill.vocabulary.json'
		try:
			with open(path) as file:
				data = load_json(path)
				vocabulary.update(data)
		except:
			eprint('[!]Cant load vocabulary from %s' % path)
		self.show_load_log('vocabulary', vocabulary)
		return vocabulary

	def show_load_log(self, name, config):
		eprint('[!]Load %s file' % name)
		for key in config:
			eprint('%s - %s' % (key, config[key]))

	def setup_route(self):
		self.add_url_rule('/', "run_skill", self.skill.run_skill, methods=['POST'])
		self.add_url_rule('/', "get_info", self.skill.get_info, methods=['GET'])

def create_app(config_file, vocabulary_file):
	app = FlaskServer('FlaskServer', config_file, vocabulary_file)
	app.setup_route()
	return app
