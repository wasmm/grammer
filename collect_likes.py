###############################################################################
#
#
#Скрипт сбора лайков,
#запускать один раз после добавления инстаграм аккаунта
#
#
#
###############################################################################

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
    id = '2'
    data_auth = get_auth_data(id)

    if data_auth == False:
        print('Пользователь не опознан')
        #break

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
    my_id = api.authenticated_user_id
    rank_tok = api.generate_uuid()
    print('ID: ' + my_id)
    print('RANK_TOKEN: ' + rank_tok)

    print()

    conn = psycopg2.connect(dbname='grammer', user='insta',
                        password='123456789', host='localhost')
    cursor = conn.cursor()

    liked_feed = api.feed_liked()
    mid = liked_feed['next_max_id']
    print('максимальный ID: ' + str(mid))

    ss = 1#сквозной счетчик
    sp = 0#Счетчик постов
    while mid:

        try:
            print()
            print('Проход #' + str(ss))
            like_posts = []
            liked_feed = api.feed_liked(max_id = mid)

            for like in liked_feed['items']:
                sp += 1
                print('Пост #' + str(sp))
                cursor.execute('SELECT id FROM likes WHERE account = %s AND id_account = %s AND id_post = %s', (id, str(like['user']['pk']), str(like['id'])))
                u = cursor.fetchone()
                #cursor.close()
                #если запись не найдена то она будет добавлена
                if u == None:
                    print('------Пост будет добавлен, ид пользователя, под которым работаем: '+ str(id))

                    like_posts.append({'login' : id,
                                       'pk' : like['user']['pk'],
                                       'username' : like['user']['username'],
                                       'id_like' : like['id'],
                                       'code' : like['code'],
                                       'taken_at' : like['taken_at']})
                #если запись найдена то
                else:
                    print('------Пост не будет добавлен, ид пользователя, под которым работаем: '+ str(id))
                    print('Переход к следующей итерации')
                    continue


            print('Проход окончен, запись даннных')
            cursor.executemany("""INSERT INTO likes(account ,id_account, link_account, id_post, link_post, time_stamp)
                            VALUES (%(login)s, %(pk)s, %(username)s, %(id_like)s, %(code)s, %(taken_at)s)""", like_posts)
            conn.commit()

            mid = liked_feed['next_max_id']
            tt = randint(30, 40)
            time.sleep(tt)

        except KeyError:
            result = True
            print('Сбор лайков завершен успешно')

            cursor.execute('SELECT id FROM stat WHERE account = %s', (id))
            line = cursor.fetchone()
            #cursor.close()

            if line == None:
                print('Добавляем данные в stat, ид пользователя, под которым работаем: '+ str(id))
                cursor.execute("""INSERT INTO stat(account, inst_likes, max_id, t_likes, t_followers)
                     VALUES (%s, %s, %s, %s, %s)""", (int(id), result, mid, 0, 0))
                conn.commit()
                #cursor.close()
            else:
                print('Обновляем данные в stat, ид пользователя, под которым работаем: '+ str(id))
                cursor.execute("""UPDATE stat SET inst_likes = %s WHERE account = %s """, (result, id))
                conn.commit()
                #cursor.close()

            #conn.close()
            break
        except ConnectionResetError:
            result = False
            print('Произошла ошибка при сборе лайков с аккаунта ')

            cursor.execute('SELECT id FROM stat WHERE account = %s', (id))
            line = cursor.fetchone()
            #cursor.close()

            if line == None:
                print('Добавляем данные в stat, ид пользователя, под которым работаем: '+ str(id))
                cursor.execute("""INSERT INTO stat(account, inst_likes, max_id, t_likes, t_followers)
                     VALUES (%s, %s, %s, %s, %s)""", (id, result, mid, 0, 0))
                conn.commit()
                #cursor.close()
            else:
                print('Обновляем данные в stat, ид пользователя, под которым работаем: '+ str(id))
                cursor.execute("""UPDATE stat SET inst_likes = %s WHERE account = %s """, (result, id))
                conn.commit()
                #cursor.close()

            #conn.close()

        #conn.commit()
        ss += 1
    cursor.close()
    conn.close()
    print('Сбор лайков завершен')





















        #######################
