import time
from redishelper import RedisConnection
from mysqlhelper import DBConnection
import random
import redis
#import logging
from similarity import preparer_instruction, lev_dis
from utils import *
from plugins import *
from flask import request, jsonify

class Skill():    
    def __init__(self, config, vocabulary):
        self.config = config
        self.vocabulary = vocabulary

    def run_skill(self, _request = None):
        eprint('NEW REQUEST -->')
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
        eprint('DELTA TIME WORK:', delta_time, 's')
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
            eprint('ВЫВОД: выход из навыка Ассоль')
            text_answer, voice_answer = self.output_conf(theme='bye')
            return text_answer, voice_answer, True

        #Получаем данные пользователя
        user_id = request_data['session']['user_id']
        profile = self.get_profile(user_id)
        #Without words of activation "Включи", "навык", "ассоль"
        token_instruction = self.slice_instruction(request_data['request']['nlu']['tokens'])
        #Подготовка текста
        eprint('COMMAND (before):', token_instruction)
        token_instruction, unknown_tokens = preparer_instruction(token_instruction, self.vocabulary['input'])
        eprint('COMMAND (after):', token_instruction)
        eprint('COMMAND (unknown):', unknown_tokens)
        instruction = ' '.join(token_instruction) if token_instruction else str()

        #Получаем контекст
        session = RedisConnection(host=self.config['host_redis'], port=self.config['port_redis'], db=0)

        #Если инструкции пустые, то спросить, что пользователь хочет
        if len(token_instruction) == 0:
            text_answer, voice_answer = self.output_conf(theme='canihelp', prof=profile)
            session.new_session(user_id)
        else:
            #Временно TODO
            text_answer, voice_answer, is_end_dialog = self.switch_command(instruction, is_end_dialog)

            #Добавочная информация режима отладки
            debug = session.get_session(user_id, 'debug')
            if debug == 'true':
                history = session.get_session(user_id, 'history')
                eprint('DEBUG')
                text_answer, voice_answer = self.output_conf(theme='debug', prof=profile, history=history,
                            ins=instruction,text=text_answer, voice=voice_answer, session=session)
                session.edit_session(user_id, 'history', instruction)

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

    def switch_command(self, instruction, is_end_dialog):
        if instruction == 'turnon debug':
            result = session.edit_session(user_id, 'debug', 'true')
            eprint('ВЫВОД: Режим отладки: True, SessionOK:', result)
            text_answer = voice_answer = 'включаю режим отладки'
        if instruction == 'turnoff debug':
            result = session.edit_session(user_id, 'debug', 'false')
            eprint('ВЫВОД: Режим отладки: False, SessionOK:', result)
            text_answer = voice_answer = 'выключила режим отладки'
        if instruction == 'what can':
            eprint('ВЫВОД: Отвечает, что Ассоль умеет')
            text_answer, voice_answer = self.output_conf(theme='whatican')
        if instruction == 'turnon light':
            eprint('ВЫВОД: включает свет')
            text_answer = voice_answer = '{} свет'.format(random.choice(self.vocabulary['output']['turnon']))
        if instruction == 'turnoff light':
            eprint('ВЫВОД: выключает свет')
            text_answer = voice_answer = '{} свет'.format(random.choice(self.vocabulary['output']['turnoff']))
        if instruction == 'turnon powersocket':
            eprint('ВЫВОД: включает розетку')
            text_answer = voice_answer = '{} розетку'.format(random.choice(self.vocabulary['output']['turnon']))
        if instruction == 'turnoff powersocket':
            eprint('ВЫВОД: выключает свет')
            text_answer = voice_answer = '{} розетку'.format(random.choice(self.vocabulary['output']['turnoff']))
        if instruction == 'itsall':
            eprint('ВЫВОД: Ассоль уходит в сон')
            text_answer = voice_answer = random.choice(self.vocabulary['output']['yes'])
            is_end_dialog = True
        if text_answer == str() and voice_answer == str():
            eprint('ВЫВОД: не нашла соотвествий')
            text_answer = voice_answer = random.choice(self.vocabulary['output']['dontunderstand'])
        return text_answer, voice_answer, is_end_dialog