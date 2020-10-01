import time
from redishelper import RedisConnection
from mysqlhelper import DBConnection
import random
import redis
from similarity import preparer_instruction, lev_dis
from utils import *
from plugins import *
from flask import request, jsonify

class Skill():    
    def __init__(self, config, vocabulary, logger):
        self.config = config
        self.vocabulary = vocabulary
        self.log = logger

    def run_skill(self, _request = None):
        self.log.info('NEW REQUEST -->')
        start_time = time.time()
        if _request is None:
            _request = request.json
        json_request = _request
        text_answer, text_answer_tts, is_end_session = self.compute_module(json_request)
        answer = {
        "response": {
                "text": text_answer,
                "tts": text_answer_tts,
                "end_session": is_end_session
        },
        "session": {
                "session_id": json_request['session']['session_id'],
                "message_id": json_request['session']['message_id'],
                "user_id": json_request['session']['user_id']
            },
            "version": json_request['version']
        }
        delta_time = time.time() - start_time
        self.log.info('DELTA TIME WORK: %s s', delta_time)
        return jsonify(answer)

    def get_info(self):
        return jsonify({'endpoints': [{'POST /': 'Marusya\'s skill API'}, {'GET /': 'Info'}]})

    #Compute
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
        self.log.info('COMMAND (before): %s', token_instruction)
        token_instruction, unknown_tokens = preparer_instruction(token_instruction, self.vocabulary['input'])
        self.log.info('COMMAND (after): %s', token_instruction)
        self.log.info('COMMAND (unknown): %s', unknown_tokens)
        instruction = ' '.join(token_instruction) if token_instruction else str()

        #Получаем контекст
        self.session = RedisConnection(host=self.config['host_redis'], port=self.config['port_redis'], db=0)

        #Если инструкции пустые, то спросить, что пользователь хочет
        if len(token_instruction) == 0:
            text_answer, voice_answer = self.output_conf(theme='canihelp', prof=profile)
            self.session.new_session(user_id)
        else:
            text_answer, voice_answer = self.switch_command(user_id, token_instruction)

            #Добавочная информация режима отладки
            session_profile = self.session.get_session(user_id)
            debug = session_profile['debug']
            if debug == 'true':
                history = session_profile['history']
                self.log.info('DEBUG')
                text_answer, voice_answer = self.output_conf(theme='debug', prof=profile, history=history,
                            ins=instruction,text=text_answer, voice=voice_answer)
                self.session.edit_session(user_id, 'history', instruction)

        return text_answer, voice_answer, is_end_dialog

    #Randomazer
    def output_conf(self, **data):
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

    #Получаем всю информацию о пользователе, что производит запрос
    def get_profile(self, user_id):
        link = DBConnection(user=self.config['user_mysql'], password=self.config['password_mysql'],
                            host=self.config['host_mysql'], database=self.config['database_mysql'])
        user_row = link.select('users', dict(UserId=user_id))
        if len(user_row) > 0:
            return user_row[0]
        else:
            return None

    #Отсекатор технических команд от команды запуска
    def slice_instruction(self, tokens):
        main_instruction = []
        nameskill = self.config['nameskill']
        if nameskill in tokens:
            main_instruction = tokens[tokens.index(nameskill)+1:]
        else:
            main_instruction = tokens
        return main_instruction

    def switch_command(self, user_id, token_instruction):
        instruction = ' '.join(token_instruction)
        function = {'turnon debug' : self.debug_param, 
                    'turnoff debug' : self.debug_param, 
                    'what can' : self.what_can, 
                    'turnon light' : self.relay, 
                    'turnoff light' : self.relay, 
                    'turnon powersocket' : self.relay, 
                    'turnoff powersocket' : self.relay
                    }
        # 'itsall' : its_all TO DO
        text_answer, voice_answer = function[instruction](user_id, token_instruction)

        if text_answer == str() and voice_answer == str():
            self.log.info('ВЫВОД: не нашла соотвествий')
            text_answer = voice_answer = random.choice(self.vocabulary['output']['dontunderstand'])
            
        return text_answer, voice_answer

    def debug_param(self, user_id, token_instruction):
        stage = token_instruction[0]
        if stage == 'turnon':
            result = self.session.edit_session(user_id, 'debug', 'true')
            self.log.info('ВЫВОД: Режим отладки: True, SessionOK: %s', result)
            text_answer = voice_answer = 'включаю режим отладки'
        if stage == 'turnoff':
            result = self.session.edit_session(user_id, 'debug', 'false')
            self.log.info('ВЫВОД: Режим отладки: False, SessionOK: %s', result)
            text_answer = voice_answer = 'выключила режим отладки'
        return text_answer, voice_answer

    def what_can(self, user_id, token_instruction):
        self.log.info('ВЫВОД: Отвечает, что Ассоль умеет')
        text_answer, voice_answer = self.output_conf(theme='whatican')
        return text_answer, voice_answer

    def relay(self, user_id, token_instruction):
        stage = token_instruction[0]
        relay_type = token_instruction[1]
        # relay_name = token_instruction[2]
        if stage == 'turnon':
            self.log.info('ВЫВОД: включает %s', relay_type)
            text_answer = voice_answer = '{} {}'.format(random.choice(self.vocabulary['output']['turnon']), relay_type)
        if stage == 'turnoff':
            self.log.info('ВЫВОД: выключает %s', relay_type)
            text_answer = voice_answer = '{} {}'.format(random.choice(self.vocabulary['output']['turnoff']), relay_type)
        return text_answer, voice_answer

