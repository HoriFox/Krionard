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
            is_end_dialog = True
            text_answer, voice_answer = self.switch_command(user_id, token_instruction, unknown_tokens)

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

    def switch_command(self, user_id, token_instruction, unknown_tokens):
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
            self.log.info('ВЫВОД: не нашла соотвествий')
            text_answer = voice_answer = random.choice(self.vocabulary['output']['dontunderstand'])
            
        return text_answer, voice_answer

    def debug_param(self, user_id, token_instruction, unknown_tokens):
        stage = token_instruction[0]
        valueDebug = 'true' if stage == 'turnon' else 'false'
        result = self.session.edit_session(user_id, 'debug', valueDebug)
        self.log.info('ВЫВОД: Режим отладки: %s, SessionOK: %s' % (valueDebug, result))
        text_answer = voice_answer = '%s режим отладки' % (valueDebug)
        return text_answer, voice_answer

    def what_can(self, user_id, token_instruction, unknown_tokens):
        self.log.info('ВЫВОД: Отвечает, что Ассоль умеет')
        text_answer, voice_answer = self.output_conf(theme='whatican')
        return text_answer, voice_answer

    def relay(self, user_id, token_instruction, unknown_tokens):
        stage = token_instruction[0]
        mayby_relay_name = ' '.join(unknown_tokens)
        text_answer, voice_answer = '', ''

        # Узнаем по кусочку дополнительного после тэга текста ip устройства из базы данных
        res = requests.post('http://127.0.0.1:4050/data', json={'function': 'get_ip_by_name', 'relayname': mayby_relay_name}) 
        responseText = res.json()
        
        # Если устройство найдено в единичном варианте, значит он нашёл более-менее похожее (не 0 и не много, а 1)
        if len(responseText) == 1:
            ip_module = responseText[0]['ModuleIp']
            self.log.info('LOGIC: Полученное по токену [%s] IP устройства [%s]' % (mayby_relay_name, ip_module))
            valueRelay = '1' if stage == 'turnon' else '0'
            res = requests.post('http://127.0.0.1:4050', json={'type': 'relay', 'ip': ip_module, 'value': valueRelay})
            if res.text == 'good':
                self.log.info('ВЫВОД: %s реле' % (stage))
            elif res.text == 'error-connection-ip':
                self.log.info('ВЫВОД: не смогла обратиться по IP адресу')
                text_answer = voice_answer = 'Не смогла обратиться по адресу устройства'
        else:
            text_answer = voice_answer = 'Я не смогла определить нужное устройство'
        return text_answer, voice_answer

