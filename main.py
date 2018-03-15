#-*-coding: utf-8 -*-
from flask import Flask
from flask import request
from flask import jsonify
import telebot
import time
import requests
import json
import os
import sqlite3
API_TOKEN = 's'
bot = telebot.TeleBot(API_TOKEN,threaded=False)
conn = sqlite3.connect('my.db',check_same_thread=False)
c = conn.cursor()
app = Flask(__name__)
myid=352375345



def main_menu(message,text= 'Главное меню'):
    markup = telebot.types.ReplyKeyboardMarkup(True,False)
    markup.row('Настройки', 'Информация', 'Когда игра?')
    markup.row('Записаться на игру',  'Кто уже записался?')
    markup.row('Записать друга', '/help', 'Отправить фото')
    bot.reply_to(message, text, reply_markup=markup)

def eror(message):
    bot.reply_to(message,'Что-то пошло не так...')
    bot.send_message(myid, "Что-то пошло не так...")




@bot.message_handler(commands=['start'])
def start(message):
    print(time.mktime(time.strptime(time.time(), '%d.%m.%Y %H:%M')))
    try:

        c.execute('INSERT INTO users (user_id,name,alerts,state) VALUES(?,?,?,?)',(message.from_user.id, message.from_user.first_name,"Да","Новый"))
    except:
        print("Er")
    conn.commit()
    main_menu(message,'Приветствую, ' + message.from_user.first_name + '!')

@bot.message_handler(commands=['help'])
def help(message):
    main_menu(message,'Этот бот создан для записи и оповещениях на игры в Помидорка Mafia Club.\n'
                      '/reset - для сброса всех настроек.\n'
                      '/help - для помощи')


@bot.message_handler(commands=['reset'])
def reset(message):
    try:
        c.execute('DELETE FROM users WHERE user_id=?',(str(message.from_user.id),))
        c.execute('INSERT INTO users (user_id,name,alerts,state) VALUES(?,?,?,?)',(message.from_user.id, message.from_user.first_name,"Да","Новый"))
        bot.reply_to(message, 'Все настройки сброшены')
    except:
        eror(message)

@bot.message_handler(content_types=['document', 'photo'])
def save_photo(message):
    bot.forward_message(352375345,message.chat.id,message.message_id)


@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    if message.text == 'В главное меню':
        main_menu(message)

    if message.text == 'Информация':
        bot.send_message(message.chat.id, '«Ма́фия» — салонная командная психологическая пошаговая ролевая игра с детективным сюжетом,'
                              ' моделирующая борьбу информированных друг о друге членов организованного меньшинства с неорганизованным большинством.'
                              'Завязка сюжета: Жители города, обессилевшие от разгула мафии, выносят решение пересажать в тюрьму всех мафиози до единого.'
                              ' В ответ мафия объявляет войну до полного уничтожения всех мирных горожан.', reply_markup=telebot.types.ForceReply())
        bot.send_message(message.chat.id, 'Правила:')
        bot.send_document(message.chat.id,'BQADAgADaAEAAgJVQUkONYlShtzcAgI')
        main_menu(message)

    if message.text == 'Отправить фото':
        bot.reply_to(message, 'Готов принять фотку',reply_markup=telebot.types.ForceReply())

    if message.text == 'Изменить имя':
        msg=bot.reply_to(message, 'Введите ваше новое имя',reply_markup=telebot.types.ForceReply())
        bot.register_next_step_handler(msg,change_name)

    if message.text == 'Включить оповещения':
        try:
            c.execute('UPDATE users SET alerts=? WHERE user_id=?', ("Да", message.from_user.id))
            conn.commit()
            main_menu(message,'Оповещения включены!')
        except:
            eror(message)

    if message.text == 'Выключить оповещения':
        try:
            c.execute('UPDATE users SET alerts=? WHERE user_id=?', ("Нет", message.from_user.id))
            conn.commit()
            main_menu(message,'Оповещения выключены!')
        except:
            eror(message)

    if message.text == 'Когда игра?':
        c.execute('SELECT * FROM games WHERE rowid = (SELECT MAX(rowid) FROM games)')
        row = c.fetchone()
        dg = int(time.mktime(time.strptime(row[0], '%d.%m.%Y %H:%M')))
        if dg > time.time():
            bot.reply_to(message, row[0])
        else:
            c.execute('UPDATE users SET reg=?', ("Нет",))
            conn.commit()
            bot.reply_to(message, 'Пока еще нету записи на новую игру')

    if message.text == 'Записаться на игру':
        try:
            c.execute('SELECT * FROM games WHERE rowid = (SELECT MAX(rowid) FROM games)')
            row = c.fetchone()
            dg = int(time.mktime(time.strptime(row[0], '%d.%m.%Y %H:%M')))-7200
            print(dg)
            if dg > time.time():
                c.execute('UPDATE users SET reg=? WHERE user_id=?', ("Да", message.from_user.id))
                conn.commit()
                main_menu(message,'Вы успешно записались на игру')
            else:
                bot.reply_to(message, 'Пока еще нету записи на новую игру')
        except:
            eror(message)

    if message.text == 'Кто уже записался?':
        c.execute('SELECT * FROM games WHERE rowid = (SELECT MAX(rowid) FROM games)')
        row = c.fetchone()

        dg = int(time.mktime(time.strptime(row[0], '%d.%m.%Y %H:%M')))
        if dg > time.time():
            c.execute('SELECT * FROM users WHERE reg=?',("Да",))
            count=1
            st=""
            while True:
                row = c.fetchone()
                if row == None:
                    break
                st+=str(count)
                st+=" "
                st+=row[1]
                st+="\n"
                count=count+1
            if(st==""):
                bot.reply_to(message, "Пока еще никкто.\nЗапишись первым!")
            else:
                bot.reply_to(message,st)
        else:
            bot.reply_to(message, 'Пока еще нету записи на новую игру')

    if message.text == 'Настройки':
        markup = telebot.types.ReplyKeyboardMarkup(True, False)
        markup.row('/reset', 'Изменить имя')
        c.execute('SELECT alerts FROM users WHERE user_id=?', (message.from_user.id,))
        row = c.fetchone()
        if row[0]=="Да":
            markup.row('Выключить оповещения', 'В главное меню')
        else:
            markup.row('Включить оповещения', 'В главное меню')
        bot.reply_to(message, 'Настройки', reply_markup=markup)

    if message.text == 'Во славу помидорок' and message.from_user.id==myid:
        msg = bot.reply_to(message, 'Дата', reply_markup=telebot.types.ForceReply())
        bot.register_next_step_handler(msg, date_game)

    if message.text == 'Записать друга':
        try:
            c.execute('SELECT * FROM games WHERE rowid = (SELECT MAX(rowid) FROM games)')
            row = c.fetchone()
            dg = int(time.mktime(time.strptime(row[0], '%d.%m.%Y %H:%M')))-7200
            if dg > time.time():
                msg = bot.reply_to(message, 'Имя', reply_markup=telebot.types.ForceReply())
                bot.register_next_step_handler(msg, enroll_friend)
            else:
                bot.reply_to(message, 'Пока еще нету записи на новую игру')
        except:
            eror(message)

def enroll_friend(message):
    try:
        c.execute('INSERT INTO users (name,reg,state) VALUES(?,?,?)',
                      (message.text, "Да", "Друг"))
        conn.commit()
        main_menu(message, 'Вы успешно записали '+message.text+' на игру')
    except:
        eror(message)

def change_name(message):
    try:
        c.execute('UPDATE users SET name=? WHERE user_id=?',(message.text,message.from_user.id))
        conn.commit()
        main_menu(message,'Имя успешно изменено!')
    except:
        eror(message)


def date_game(message):
    c.execute('SELECT * FROM users WHERE user_id=?', (message.from_user.id,))
    row = c.fetchone()
    c.execute('INSERT INTO games (date,master) VALUES(?,?)',(message.text,row[1]))
    conn.commit()
    msg = bot.reply_to(message, 'Место', reply_markup=telebot.types.ForceReply())
    bot.register_next_step_handler(msg, place_game)
def place_game(message):
    c.execute('SELECT * FROM games WHERE rowid = (SELECT MAX(rowid) FROM games)')
    row = c.fetchone()
    c.execute('UPDATE games SET place=? WHERE date=?', (message.text,row[0]))
    conn.commit()
    try:
        c.execute('SELECT * FROM games WHERE rowid = (SELECT MAX(rowid) FROM games)')
        g = c.fetchone()
        c.execute('SELECT * FROM users WHERE alerts=?', ("Да",))
        answer="Открыта запись на новую игру\nДата и время : "+g[0]+"\nМесто : "+g[1]+"\nВедущий : "+g[2]
        mark=telebot.types.ReplyKeyboardMarkup(True, True)
        mark.row("Записаться на игру",'Выключить оповещения')
        while True:
            row = c.fetchone()
            if row == None:
                break
            bot.send_message(int(row[0]), answer, reply_markup=mark)
    except:
        eror(message)

@app.route("/", methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@app.route("/")
def index():
    return "!", 200

if __name__ == '__main__':
    app.run()