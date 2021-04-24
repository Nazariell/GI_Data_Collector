import telebot
import flask
import time
from threading import Semaphore
from os import getcwd
import json
from flask import Flask, request

try:
    fd = open(getcwd() + '/save', 'r')
    st = fd.read()
    res = json.loads(st)
except IOError:
    res = {}

try:
    fd = open(getcwd() + '/save_global', 'r')
    st = fd.read()
    res_g = json.loads(st)
except IOError:
    res_g = {}

token = '1758008542:AAFnF3MIIfyMLgLnW97rzkVmZtsEGOspPFM'

server = Flask(__name__)

w_a = "Wrong ammount of parameters use /help to see how the bot is used."

e_p = "Error in parameters"

help_msg = """GI_Data_Collector_Bot is a tool to collect GI data and apply stadistical operations to the collected data.
Commands:
/start Starts the bot
/help Shows this help message
/add_entry Adds to the database the ammount of killed monsters and the ammount of dropped items once entered the data, adding a new entry if it doesn't exists
/finish_entry Finishes the last entry opened by the command /add_entry should be used once you have stopped adding entries
/show_data Shows the data collected in the current chat
/show_data <monster_name> Shows the data collected in the current chat about the monster
/show_global Works loke /show_data but showing the data collected in every chat the bot has been started in
/reset resets the data collected in the chat

---------------------------------------------------------------
!!! IMPORTANT !!!:
The bot will only collect up to (2^32) - 1 entries monster type in every chat.
---------------------------------------------------------------
"""


def save(dic, name):
    _dic_to_str = str(dic)
    to_save = ''
    safe = False
    for i in _dic_to_str:
        if i == '"' and not safe:
            safe = True
            to_save += i
        elif i == '"':
            safe = False
            to_save += i
        elif i == '\'' and not safe:
            to_save += '"'
        else: to_save += i

    fd = open(getcwd() + '/' + name, 'w')
    fd.write(to_save)

def get_real_words(message):
    words = message.text.split(' ')
    real_words = []
    for i in range(1, len(words)):
        if len(words[i]) > 0:
            real_words.append(words[i])

    return real_words

def get_real_words_str(message):
    words = message.split(' ')
    real_words = []
    for i in range(len(words)):
        if len(words[i]) > 0:
            real_words.append(words[i])

    return real_words

def show_data_monster_item_amm(dic, chat_id, monster_name, item_name, ammount):
    try:
        if abs((float)(dic[monster_name][0])) < 0.00001:
            return "Zero division." 
        num = (float)((float)(dic[monster_name][1][item_name][ammount])/(float)(dic[monster_name][0]))
        str_num = str(num)
        rounded = ''
        for i in range(min(len(str_num), 4)):
            rounded += str(str_num[i])
        text = f"Ammount of times the { item_name } was obtained { ammount } times at once: { dic[monster_name][1][item_name][ammount] } approximated probability: { rounded }\n\n"
        return text
    
    except KeyError:
        bot.send_message(chat_id, e_p)

def show_data_monster_item(dic, chat_id, monster_name, item_name):
    try:
        text = ''
        for i in dic[monster_name][1][item_name].keys():
            text += show_data_monster_item_amm(dic, chat_id, monster_name, item_name, i)

        return text
    
    except KeyError:
        bot.send_message(chat_id, e_p)

def show_data_monster(dic, chat_id, monster_name):
    try:
        text = f"Ammount of { monster_name } killed: { dic[monster_name][0] }\n\n"
        for i in dic[monster_name][1].keys():
            text += '\t' + show_data_monster_item(dic, chat_id, monster_name, i)

        bot.send_message(chat_id, text)

    except KeyError:
        bot.send_message(chat_id, e_p)

def show_data_general(dic, chat_id):
    try:
        for i in dic.keys():
            show_data_monster(dic, chat_id, i)

    except KeyError:
        bot.send_message(chat_id, e_p)

mutex = Semaphore()

entry_monster = {}

current_monster = {}

_dictionary = res

_global = res_g

bot = telebot.TeleBot(token, parse_mode=None)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not message.chat.id in _dictionary:
        mutex.acquire()
        _dictionary[str(message.chat.id)] = {}
        mutex.release()
    
    bot.reply_to(message, "Welcome to NazDia's GI data collector's bot.")

@bot.message_handler(commands=['add_entry'])
def create_entry(message):
    chat_id = message.chat.id

    real_words = get_real_words(message)

    mutex.acquire()

    if len(real_words) > 0:
        bot.reply_to(message, w_a)

    else:
        bot.reply_to(message, """Write the monster's name and the ammount killed in the following format:
<Monster Name> - <Ammount Killed>""")
        entry_monster[chat_id] = True
        current_monster[chat_id] = ''

    save(_dictionary, 'save')
    save(_global, 'save_global')
    mutex.release()


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, help_msg)


@bot.message_handler(commands=['show_data'])
def show_data(message):
    chat_id = message.chat.id
    change = False
    real_words = get_real_words(message)
    for i in real_words:
        if len(i) > 0:
            change = True

    if change:
        real_words = [' '.join(real_words)]

    else:
        real_words = []
    mutex.acquire()

    if len(real_words) == 0:
        show_data_general(_dictionary[str(chat_id)], chat_id)

    elif len(real_words) == 1:
        show_data_monster(_dictionary[str(chat_id)], chat_id, real_words[0])

    else:
        bot.send_message(chat_id, w_a)

    mutex.release()


@bot.message_handler(commands=['finish_entry'])
def finish(message):
    mutex.acquire()
    entry_monster[message.chat.id] = False
    mutex.release()


@bot.message_handler(commands=['show_global'])
def show_global(message):
    chat_id = message.chat.id
    change = False
    real_words = get_real_words(message)
    for i in real_words:
        if len(i) > 0:
            change = True

    if change:
        real_words = [' '.join(real_words)]

    else:
        real_words = []
    mutex.acquire()

    if len(real_words) == 0:
        show_data_general(_global, chat_id)

    elif len(real_words) == 1:
        show_data_monster(_global, chat_id, real_words[0])

    else:
        bot.send_message(chat_id, w_a)

    mutex.release()
    

@bot.message_handler(commands=['reset'])
def reset(message):
    chat_id = message.chat.id
    mutex.acquire()
    _dictionary[str(chat_id)] = {}
    save(_dictionary, 'save')
    mutex.release()


@bot.message_handler(func=lambda message : (message.chat.id in entry_monster.keys() and entry_monster[message.chat.id]))
def receive_monster_entry(message):
    chat_id = message.chat.id
    del_minus = message.text.split('-')
    if len(del_minus) != 2:
        bot.reply_to(message, w_a)
        return
    
    real_words = get_real_words_str(del_minus[0])
    sub = get_real_words_str(del_minus[1])
    if len(sub) != 1:
        bot.reply_to(message, w_a)
        return

    try:
        test = (int)(sub[0])

    except:
        bot.reply_to(message, e_p)
        return

    temp = ' '.join(real_words)
    real_words = [temp] + sub
    mutex.acquire()


    try:
        if test + _dictionary[str(chat_id)][real_words[0]][0] >= 2**32:
            bot.reply_to(message, """This entry and the previous collected data exceeds the data collector's capacity of data about this monster.

Try sending us data about other monsters instead.""")
            return

        _dictionary[str(chat_id)][real_words[0]][0] += (int)(real_words[1])

    except KeyError:
        _dictionary[str(chat_id)][real_words[0]] = [(int)(real_words[1]), {}]

    try:
        _global[real_words[0]][0] += (int)(real_words[1])

    except KeyError:
        _global[real_words[0]] = [(int)(real_words[1]), {}]

    bot.reply_to(message, """Monster entry updated, now entry the ammount of drops in the following format:
<Item Dropped> * <Ammount Dropped in every instance> - <Ammount of times this Drop ocurred>""")
    save(_dictionary, 'save')
    save(_global, 'save_global')
    entry_monster[chat_id] = False
    current_monster[chat_id] = real_words[0]
    mutex.release()


@bot.message_handler(func=lambda message: (message.chat.id in current_monster.keys() and len(current_monster[message.chat.id]) > 0))
def receive_item_entry(message):
    chat_id = message.chat.id
    _current_monster = current_monster[chat_id]
    del_minus = message.text.split('-')
    if len(del_minus) != 2:
        bot.reply_to(message, w_a)
        return
    temp = del_minus[0].split('*')
    if len(temp) != 2:
        bot.reply_to(message, w_a)
        return
    temp2 = get_real_words_str(del_minus[1])
    del_minus = temp + temp2
    if len(del_minus) != 3:
        bot.reply_to(message, w_a)
        
    real_words = get_real_words_str(del_minus[0])
    sub = get_real_words_str(del_minus[1])
    sub2 = get_real_words_str(del_minus[2])
    if len(sub) != 1:
        bot.reply_to(message, w_a)
        return

    try:
        (int)(sub[0])

    except:
        bot.reply_to(message, e_p)
        return

    if len(sub2) != 1:
        bot.reply_to(message, w_a)
        return

    try:
        (int)(sub2[0])

    except:
        bot.reply_to(message, e_p)
        return

    temp = ' '.join(real_words)
    real_words = [temp] + sub + sub2
    mutex.acquire()
    try:
        current = _dictionary[str(chat_id)][_current_monster][1][real_words[0]]

    except KeyError:
        _dictionary[str(chat_id)][_current_monster][1][real_words[0]] = {}
        current = _dictionary[str(chat_id)][_current_monster][1][real_words[0]]

    try:
        current[real_words[1]] += (int)(real_words[2])

    except KeyError:
        current[real_words[1]] = (int)(real_words[2])

    try:
        current = _global[_current_monster][1][real_words[0]]

    except KeyError:
        _global[_current_monster][1][real_words[0]] = {}
        current = _global[_current_monster][1][real_words[0]]

    try:
        current[real_words[1]] += (int)(real_words[2])

    except KeyError:
        current[real_words[1]] = (int)(real_words[2])

    bot.reply_to(message, "Item drop entry updated, use the command /show_data to see the collected data, and if you are done, with this monster's entry, use the command /finish_entry , otherwise keep sending item drops.")
    save(_dictionary, 'save')
    save(_global, 'save_global')
    mutex.release()

@server.route('/' + token, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@server.route('/')
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https')
    return "!", 200

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))

