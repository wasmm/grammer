###############################################################################
#
#
#Скрипт постановки лайков,
#для начала запусти collect_likes.py, он соберет проставленые лайки
#если не собрать лайки то скрипт может работать некорректно
#
#
###############################################################################

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





    #получаем свой идентификатор и токен
    my_id = api.authenticated_user_id
    rank_tok = api.generate_uuid()
    print('ID: ' + my_id)
    print('RANK_TOKEN: ' + rank_tok)
    #получаем массив подписок
    mas_following = api.user_following(my_id, rank_tok)
    users_following = mas_following['users']
    cnt_following = len(users_following)
    print('Количество подписок: ' +str(cnt_following))

    #рандомно определяем количество постов, которое будет пролайкано
    count_like_posts = randint(config.START_COUNT_POSTS, config.FINISH_COUNT_POSTS)
    print('Будет пролайкано: ' + str(count_like_posts) + ' постов')




    conn = psycopg2.connect(dbname='grammer', user='insta',
                        password='123456789', host='localhost')
    cursor = conn.cursor()


    #счетчик подписок
    ss = 1
    #счетчик новостей
    sf = 1
    #сквозной счет поставленных лайков, их количество должно быть меньше ограничения
    sl = 1

    #идем по каждой подписке
    for user in users_following:
        pk = user['pk']
        #получаем список ленту пользователя
        feed_user = api.user_feed(pk)
        #идем по каждому посту пользователя
        like_posts = []
        for feed in feed_user['items']:
            #если лимит достигнут, то записываем массив поставленных лайков
            #и заканчиваем выполнение скрипта
            if sl == config.MAX_LIKE_PER_DAY:
                print('Было проставлено '+ str(config.MAX_LIKE_PER_DAY) + ' лайков')
                cursor.executemany("""INSERT INTO likes(account ,id_account, link_account, id_post, link_post, time_stamp)
                                VALUES (%(login)s, %(pk)s, %(username)s, %(id_like)s, %(code)s, %(taken_at)s)""", like_posts)
                conn.commit()
                exit(1)



            id_post = feed['id']
            #получаем самую большую(т.е. самую ближайшую к текушей) дату лайка
            cursor.execute("""SELECT MAX(time_stamp) FROM public.likes WHERE account = %s AND id_account = %s""", (id, str(pk)))
            res_last_date = cursor.fetchone()
            last_date = int(res_last_date[0])
            #текущая дата
            cur_time = int(time.time())

            #в результате получаем разницу в секундах,
            #если разница меньше ограничения значит пропускаем этого пользюка
            #если разница больше то ставим ему лайк
            res_time = cur_time - last_date
            print('Последняя активность на странице пользователя была ' + str(res_time) + ' секунд назад( ~' + str(res_time // 86400) + 'дней )')
            if res_time < config.TIME_LAST_ACTIVITY_LIKE:
                print('Прошло мало времени, этого пользователя полайкаем позже')
                continue
            else:


                print('Этого пользователя будем лайкать')
                #like = api.post_like(id_media)
                like_posts.append({'login' : id,
                                   'pk' : user['pk'],
                                   'username' : user['username'],
                                   'id_like' : id_post,
                                   'code' : feed['code'],
                                   'taken_at' : feed['taken_at']})
                #ведем счет лайкам
                sl += 1
            #пересчет всех новостей пользователя
            if sf == 3:
                break
            sf += 1

        #после того как пользователя отработали то производим запись ланных по лайкам в базу
        #print(like_posts)
        cursor.executemany("""INSERT INTO likes(account ,id_account, link_account, id_post, link_post, time_stamp)
                        VALUES (%(login)s, %(pk)s, %(username)s, %(id_like)s, %(code)s, %(taken_at)s)""", like_posts)
        conn.commit()






        #пересчет всех пользователей
        if ss == 1:
            break
        ss += 1

    cursor.close()
    conn.close()

















'''

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


        #рандомное количество сна между подписчиками
        t = randint(config.START_SLEEP_TIME_FOLLOWER, config.FINISH_SLEEP_TIME_FOLLOWER)
        print('Жди ' + str(t) + ' сек, выбирается очередная жертва')
        print()

        time.sleep(t)



'''









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
