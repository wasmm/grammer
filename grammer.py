#from random import random, randrange, randint
from random import randint
import random
import time
import sqlite3
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

def get_likes():
    liked_feed = api.feed_liked()
    mid = liked_feed['next_max_id']
    like_posts = []
    while mid:
        try:
            liked_feed = api.feed_liked(max_id = mid)
            for like in liked_feed['items']:
                like_posts.append({'pk' : like['user']['pk'],
                                   'username' : like['user']['username'],
                                   'id_like' : like['id'],
                                   'taken_at' : like['taken_at']
                                       })
            mid = liked_feed['next_max_id']

            tt = randint(10, 20)
            time.sleep(tt)
        except KeyError:
            break


    return like_posts


def gen_mas_for_likes(mas_likes):
    #в массиве followings будут попадать те, кого пользователь еще не лайкал
    #сверка проводится с массивом пролайканых постов
    #так же в массив попадут те, кому лайк был поставлен
    #позднее параметра TIME_LAST_ACTIVITY_LIKE

    followings = []
    peoples_for_likes = 0
    for follower in users_following:
        rand_user = random.choice(users_following)
        i=0
        buffer_likes = []
        for like in mas_likes:
            if rand_user['pk'] == like['pk']:
                #print(str(like['pk']) + '-------' + str(like['taken_at']))
                buffer_likes.append(like['taken_at'])
                i += 1
        if i == 0:
            followings.append({'pk' : rand_user['pk'],
                               'username' : rand_user['username'],
                               'following' : '',})
        else:
            #сортируем массив по возрастанию дат
            maxdate_ar = sorted(buffer_likes)
            cur_time = int(time.time())
            res_time = cur_time - maxdate_ar[len(maxdate_ar)-1]
            if config.TIME_LAST_ACTIVITY_LIKE < res_time:
                followings.append({'pk' : rand_user['pk'],
                                   'username' : rand_user['username'],
                                   'following' : '',})

    #как только массив заполняется, набор прекращаем
    #количество подписчиков хранится в переменной MAX_USERS_LIKE
        if len(followings) == config.MAX_USERS_LIKE:
            break

    return(followings)


if __name__ == '__main__':

    logging.basicConfig()
    logger = logging.getLogger('instagram_private_api')
    logger.setLevel(logging.WARNING)
    print('Версия клиента: {0!s}'.format(client_version))
    device_id = None
    try:
        settings_file = config.COOKIE_FILE
        if not os.path.isfile(settings_file):
            # settings file does not exist
            print('Невозможно найти файл: {0!s}'.format(settings_file))
            # login new
            api = Client(
                config.INSTAGRAM_LOGIN, config.INSTAGRAM_PASSWORD,
                on_login=lambda x: onlogin_callback(x, config.COOKIE_FILE))
        else:
            with open(settings_file) as file_data:
                cached_settings = json.load(file_data, object_hook=from_json)
            print('Повторное использование настроек: {0!s}'.format(settings_file))
            device_id = cached_settings.get('device_id')
            # reuse auth settings
            api = Client(
                config.INSTAGRAM_LOGIN, config.INSTAGRAM_PASSWORD,
                settings=cached_settings)

    except (ClientCookieExpiredError, ClientLoginRequiredError) as e:
        print('ClientCookieExpiredError/ClientLoginRequiredError: {0!s}'.format(e))

            # Login expired
            # Do relogin but use default ua, keys and such
        api = Client(
            config.INSTAGRAM_LOGIN, config.INSTAGRAM_PASSWORD,
            device_id=device_id,
            on_login=lambda x: onlogin_callback(x, config.COOKIE_FILE))

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
    print('Добро пожаловать, ' + config.INSTAGRAM_LOGIN)
    print()




#####################Лайкинг####################################
    my_id = api.authenticated_user_id
    rank_tok = api.generate_uuid()
    print('ID: ' + my_id)
    print('RANK_TOKEN: ' + rank_tok)

    mas_following = api.user_following(my_id, rank_tok)
    users_following = mas_following['users']
    cnt_following = len(users_following)
    print('Количество подписок: ' +str(cnt_following))

    #Сбор всех лайков с данного аккаунта
    mas_likes = get_likes()
    #генерация массива юзеров для постановки лайков
    users_for_likes = gen_mas_for_likes(mas_likes)

    for user in users_for_likes:
        pk = user['pk']
        username = user['username']
        data_follow = api.friendships_show(pk)
        print('Пользователь: ' + username)
        print('Ссылка на профиль: https://www.instagram.com/' + username)

        count_like_posts = randint(config.START_COUNT_POSTS, config.FINISH_COUNT_POSTS)
        print('Будет пролайкано: ' + str(count_like_posts) + ' постов')

        feed_user = api.user_feed(pk)

        schet_likes = 1
        #идем по ленте, чтобы лайкать посты
        mas_likes = []
        for feed in feed_user['items']:
            id_media = feed['id']
            print('Пролайканый пост : https://www.instagram.com/p/' + feed['code'])

            cur_time_like = int(time.time())
            like = api.post_like(id_media)
            if like['status'] == 'ok':
                mas_likes.append([pk, username, id_media, feed['code'], cur_time_like])

            if schet_likes == count_like_posts:
                break
            schet_likes += 1
            #рандомное количество сна между лайками
            tl = randint(config.START_SLEEP_TIME_LIKE, config.FINISH_SLEEP_TIME_LIKE)
            print('До следующего лайка ' + str(tl) + ' сек')
            time.sleep(tl)



        conn = sqlite3.connect('instagram.db')
        cursor = conn.cursor()
        sql = "INSERT INTO stat('id_account', 'link_account', 'id_post',"\
                               "'link_post', 'time_like') VALUES (?, ?, ?, ?, ?)"

        cursor.executemany(sql, mas_likes)
        conn.commit()
        conn.close()

        #рандомное количество сна между подписчиками
        t = randint(config.START_SLEEP_TIME_FOLLOWER, config.FINISH_SLEEP_TIME_FOLLOWER)
        print('Жди ' + str(t) + ' сек, выбирается очередная жертва')
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
