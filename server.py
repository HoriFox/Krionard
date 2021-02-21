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

    def load_config(self, path):
        if not path:
            path='/etc/assol/skill.config.json'
        return load_json(path)

    def load_vocabulary(self, path):
        if not path:
            path='/etc/assol/skill.vocabulary.json'
        return load_json(path)

    def setup_route(self):
        self.add_url_rule('/', "run_skill", self.skill.run_skill, methods=['POST'])
        self.add_url_rule('/', "get_info", self.skill.get_info, methods=['GET'])

def create_app(config_file, vocabulary_file):
    app = FlaskServer('FlaskServer', config_file, vocabulary_file)
    app.setup_route()
    return app
