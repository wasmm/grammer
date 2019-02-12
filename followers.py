#from random import random, randrange, randint
from random import randint
import random
import time
import psycopg2
import config


import json
import codecs
import datetime
import os.path
import logging
import argparse
try:
    from instagram_private_api import (
        Client, ClientCompatPatch, ClientError, ClientLoginError,
        ClientCookieExpiredError, ClientLoginRequiredError,
        __version__ as client_version)
except ImportError:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from instagram_private_api import (
        Client, ClientCompatPatch, ClientError, ClientLoginError,
        ClientCookieExpiredError, ClientLoginRequiredError,
        __version__ as client_version)

def to_json(python_object):
    if isinstance(python_object, bytes):
        return {'__class__': 'bytes',
                '__value__': codecs.encode(python_object, 'base64').decode()}
    raise TypeError(repr(python_object) + ' is not JSON serializable')


def from_json(json_object):
    if '__class__' in json_object and json_object['__class__'] == 'bytes':
        return codecs.decode(json_object['__value__'].encode(), 'base64')
    return json_object

def onlogin_callback(api, new_settings_file):
    cache_settings = api.settings
    with open(new_settings_file, 'w') as outfile:
        json.dump(cache_settings, outfile, default=to_json)
        print('SAVED: {0!s}'.format(new_settings_file))

#обработка подписок
def get_followings(my_id, rank_tok):
    mas_followings = api.user_following(my_id, rank_tok)
    users_followings = mas_followings['users']
    return users_followings

#обработка подписчиков
def get_followers(my_id, rank_tok):
    mas_followers = api.user_followers(my_id, rank_tok)
    users_followers = mas_followers['users']
    return users_followers


def get_auth_data(id_user):

    conn = psycopg2.connect(dbname='grammer', user='insta',
                        password='123456789', host='localhost')
    cursor = conn.cursor()
    cursor.execute('SELECT login_acc, passwd_acc FROM inst_acc WHERE id = %s', (id_user, ))
    u = cursor.fetchone()
    cursor.close()
    conn.close()
    cnt = len(u)
    if u == None:
        return False
    else:
        return ({'login' : u[0], 'passwd' : u[1], 'cookie': u[0]+'.json'})



if __name__ == '__main__':

    #id - 1   kabluchki_shop
    #id - 2   Selentaori.art
    #id - 3   kava_cafe_od
    id = '1'
    data_auth = get_auth_data(id)
    instalogin = data_auth['login']
    instapwd = data_auth['passwd']
    instacookie = data_auth['cookie']

    logging.basicConfig()
    logger = logging.getLogger('instagram_private_api')
    logger.setLevel(logging.WARNING)
    print('Версия клиента: {0!s}'.format(client_version))
    device_id = None
    try:
        settings_file = instacookie
        if not os.path.isfile(settings_file):
            # settings file does not exist
            print('Невозможно найти файл: {0!s}'.format(settings_file))
            # login new
            api = Client(
                instalogin, instapwd,
                on_login=lambda x: onlogin_callback(x, instacookie))
        else:
            with open(settings_file) as file_data:
                cached_settings = json.load(file_data, object_hook=from_json)
            print('Повторное использование настроек: {0!s}'.format(settings_file))
            device_id = cached_settings.get('device_id')
            # reuse auth settings
            api = Client(
                instalogin, instapwd,
                settings=cached_settings)

    except (ClientCookieExpiredError, ClientLoginRequiredError) as e:
        print('ClientCookieExpiredError/ClientLoginRequiredError: {0!s}'.format(e))

            # Login expired
            # Do relogin but use default ua, keys and such
        api = Client(
            instalogin, instapwd,
            device_id=device_id,
            on_login=lambda x: onlogin_callback(x, instacookie))

    except ClientLoginError as e:
        print('ClientLoginError {0!s}'.format(e))
        exit(9)
    except ClientError as e:
        print('ClientError {0!s} (Code: {1:d}, Response: {2!s})'.format(e.msg, e.code, e.error_response))
        exit(9)
    except Exception as e:
        print('Unexpected Exception: {0!s}'.format(e))
        exit(99)



        # Show when login expires
    cookie_expiry = api.cookie_jar.auth_expires
    print('Срок действия cookie: {0!s}'.format(datetime.datetime.fromtimestamp(cookie_expiry).strftime('%Y-%m-%dT%H:%M:%SZ')))
    print('Добро пожаловать, ' + instalogin)
    print()




#####################Лайкинг####################################
    #Создаю массив подписок
    #Беру каждого пользователя и получаю его статус
    #Если я на него подписан, а он на меня нет, то отписка от страницы
    #Если он на меня подписан, а я на него нет, то подписка на страницу

    #following - я подписан на эту страницу
    #followed_by - эта страница подписана на меня

    #user_following(my_id, rank_tok) - список подписок
    #user_followers(user_id, rank_token) - список подписчиков


    #friendships_create(user_id) - ф-ция добавлления в друзья
    #friendships_destroy(user_id) - ф-ция удаления из подписчиков


    #нужна таблица со списком пользоватлей
    #поля:
    #ID - идентификатор
    #current_user - имя аккаунта, под которым работает скрипт(или ссылка ключ)
    #id_user - ид юзера
    #date_add - временной штамп доавления в таблицу
    #type_act - тип действия, добавление в друзья, удаление из друзей(follow, unfollow)
    #result - результат действия, если оно было то True, если нет то False
    #date_act - временной штамп даты действия
    ####




    my_id = api.authenticated_user_id
    rank_tok = api.generate_uuid()
    print('ID: ' + my_id)
    print('RANK_TOKEN: ' + rank_tok)

    mas_followings = get_followings(my_id, rank_tok)
    mas_followers = get_followers(my_id, rank_tok)

    follovers_followings = []

    follovers_followings.extend(mas_followers)
    follovers_followings.extend(mas_followings)

    print('Генерация массива пользователей')

    #users_f = []

    i=1 #сквозной счетчик итераций
    s_podpiska = 1 #счетчик подписок
    s_otpiska = 1 #счетчик отписок

    for following in follovers_followings:
        pk = following['pk']
        data_follow = api.friendships_show(pk)

        #Я подписан, а на меня не подписаны
        if data_follow['following'] == True and data_follow['followed_by'] == False:
            print('Пользователь: ' + following['username'])
            print('Подписка невзаимная с его строны - отписка от пользователя(' + str(s_otpiska) + ')')
            try:
                api.friendships_destroy(pk)
                s_otpiska += 1
                t = randint(config.START_SLEEP_TIME_TO_UNFOLLOW, config.FINISH_SLEEP_TIME_TO_UNFOLLOW)
                print('Жди ' + str(t) + ' сек')
                print()
                time.sleep(t)
            except ClientError as e:
                print('Лимит подписок исчерпан')


        #Я не подписан, а на меня подписаны
        elif data_follow['following'] == False and data_follow['followed_by'] == True:
            print('Пользователь: ' + following['username'])
            print('Подписка невзаимная с моей строны - подписка на пользователя(' + str(s_podpiska) + ')')

            try:
                api.friendships_create(pk)
                s_podpiska += 1
                t = randint(config.START_SLEEP_TIME_TO_FOLLOW, config.FINISH_SLEEP_TIME_TO_FOLLOW)
                print('Жди ' + str(t) + ' сек')
                print()
                time.sleep(t)
            except ClientError as e:
                print('Лимит отписок исчерпан')


        else:
            print('Пользователь: ' + following['username'])
            print('Пользователь взаимен, пропускаем его')

            t = randint(1, 2)
            print('Жди ' + str(t) + ' сек')
            print()
            time.sleep(t)




















        #Поля таблицы статистики лайков
        #
        #логин аккаунта для которого делаются лайки
        #идентификатор
        #ид аккаунта
        #имя пользователя
        #ид поста
        #ссылка на пост
        #время поста
        #
        ############
        #Поля таблицы статистики запусков скриптов
        #ид
        #тип скрипта(mas_like, mas_follow, и пр.)
        #время запуска скрипта
        #######################
