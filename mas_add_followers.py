import psycopg2
import config
from random import randint
import random
import time


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


#following - я подписан на эту страницу
#followed_by - эта страница подписана на меня

#user_following(my_id, rank_tok) - список подписок
#user_followers(user_id, rank_token) - список подписчиков


#friendships_create(user_id) - ф-ция добавлления в друзья
#friendships_destroy(user_id) - ф-ция удаления из подписчиков



    my_id = api.authenticated_user_id
    rank_tok = api.generate_uuid()
    print('ID: ' + my_id)
    print('RANK_TOKEN: ' + rank_tok)


    my_followers = api.user_followers(my_id, rank_tok)
    my_following = my_followers['users']

    target_list = ['casual_rare_stuff', 'bulvar_shop21']



#получаем массив пользователей, на которых я подписан и сверяю со списком
#в котором хранятся логины конкурентов
#если есть совпадение то беру у найденного пользователя его подписчиков
#каждого подписчика проверяю,

#если я не подписан на человека, а он на меня подписан, то подписываюсь на него и ставлю ему лайк
#если я не подписан на человека и он не подписа на меня то подписываюсь на него и ставлю ему лайк
#если я подписан на человека и он на меня подписан, то пропускаю его
#если я подписан на человека, а человек на меня не подписан, то пропускаю его

###
    #сквозной счетчик добавлений в друзья
    sf = 1
    for user in my_following:
        if user['username'] in target_list:
            print('****************************************************************')
            print('Пользователь ' + user['username'] + ' найден')
            pk = user['pk']
            target_followers = api.user_followers(pk, rank_tok)
            i=1
            like_posts = []
            #идем по каждому фолловеру
            for tg_follower in target_followers['users']:
                print('\tБерем его друга: ' + tg_follower['username'])
                if tg_follower['is_private'] == False:
                    #print(tg_follower)
                    data_follow = api.friendships_show(tg_follower['pk'])
                    #print(data_follow)
                    #Я на него не подписан
                    if data_follow['following'] == False:
                        print('\t\tОн не в друзьях, подписка')

                        #подписываемся
                        friend = api.friendships_create(tg_follower['pk'])

                        cnt_feed=randint(2, 4)
                        #print('Пролайкаем ' + str(cnt_feed) + 'поста')
                        feed_user = api.user_feed(tg_follower['pk'])
                        f=1
                        sum_time = 0
                        #идем по каждому посту в ленте пользователя
                        for feed in feed_user['items']:
                            id_media = feed['id']
                            #проверим, ставили ли мы лайк на этот пост
                            conn = psycopg2.connect(dbname='grammer', user='insta',
                                                password='123456789', host='localhost')
                            cursor = conn.cursor()
                            cursor.execute("""SELECT id FROM likes WHERE account = %s AND id_account = %s AND id_post = %s  """, (id, str(tg_follower['pk']), str(id_media)))
                            res = cursor.fetchone()
                            cursor.close()
                            conn.close()
                            #если этому посту лайк еще на ставился то поставим
                            if res == None:
                                print('\t\t\tЛайк (' + str(sf) + ') пользователю ' + tg_follower['username'] + ' Ссылка на пост: https://www.instagram.com/p/' + feed['code'])
                                #ставим лайк
                                like = api.post_like(id_media)
                                #print('***')
                                #print(like)
                                #print('***')
                                like_posts.append({'login' : id,
                                                   'pk' : tg_follower['pk'],
                                                   'username' : tg_follower['username'],
                                                   'id_like' : id_media,
                                                   'code' : feed['code'],
                                                   'taken_at' : feed['taken_at']})
                                sf += 1

                                tl = randint(config.START_SLEEP_TIME_LIKE, config.FINISH_SLEEP_TIME_LIKE)
                                sum_time = sum_time + tl
                                print('\t\tДо следующего лайка ' + str(tl) + ' сек')
                                time.sleep(tl)
                                if f == cnt_feed:
                                    break
                                f += 1
                                if sf == config.MAX_LIKE_PER_DAY:
                                    print('Лимит лайков исчерпан')
                                    exit(1)

                            #а если этому посту лайк ставился то возьмем другой пост
                            else:
                                print('\t\t\tПост пролайкан, возьмем следующий')
                                continue
                        print('Всего на человека ушло ' + str(sum_time) + ' секунд')
                        conn = psycopg2.connect(dbname='grammer', user='insta',
                                            password='123456789', host='localhost')
                        cursor = conn.cursor()
                        cursor.executemany("""INSERT INTO likes(account ,id_account, link_account, id_post, link_post, time_stamp)
                                        VALUES (%(login)s, %(pk)s, %(username)s, %(id_like)s, %(code)s, %(taken_at)s)""", like_posts)
                        conn.commit()
                        cursor.close()
                        conn.close()
                        if sum_time > config.FINISH_SLEEP_TIME_TO_FOLLOW:
                            t = randint(config.START_SLEEP_TIME_TO_FOLLOW/10, config.FINISH_SLEEP_TIME_TO_FOLLOW/8)
                        else:
                            t = randint(config.START_SLEEP_TIME_TO_FOLLOW, config.FINISH_SLEEP_TIME_TO_FOLLOW)
                        print('Жди ' + str(t) + ' сек')
                        time.sleep(t)
                    else:
                        print('\t\tПользователь в подписках - пропускаем')
                        t = randint(config.START_SLEEP_TIME_TO_FOLLOW, config.FINISH_SLEEP_TIME_TO_FOLLOW)
                        print('\t\tЖди ' + str(t) + ' сек')
                        time.sleep(t)
                        continue
                else:
                    print('\t\tАккаунт пользователя приватный - пропускаем')
                    t = randint(config.START_SLEEP_TIME_TO_FOLLOW, config.FINISH_SLEEP_TIME_TO_FOLLOW)
                    print('\t\tЖди ' + str(t) + ' сек')
                    time.sleep(t)
                    continue
