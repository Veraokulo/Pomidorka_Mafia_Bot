#-*-coding: utf-8 -*-
from flask import Flask
from flask import request
import telebot
import time

import sqlite3
API_TOKEN = ''
bot = telebot.TeleBot(API_TOKEN,threaded=False)
conn = sqlite3.connect('my.db',check_same_thread=False)
c = conn.cursor()
app = Flask(__name__)
myid=352375345
tm=10800


def main_menu(message,text= 'Главное меню'):
	markup = telebot.types.ReplyKeyboardMarkup(True,False)
	markup.row('Информация о ближайшей игре', 'Записаться на игру' )
	markup.row('Записать друга', 'Удалить запись')
	markup.row('Настройки', 'Справка')
	markup.row('/help', 'Отправить фото')
	if message.from_user.id==myid:
		markup.row('Админка')
	bot.reply_to(message, text, reply_markup=markup)



def eror(message):
	bot.reply_to(message,'Что-то пошло не так...')
	bot.send_message(myid, "Что-то пошло не так...")

@bot.message_handler(commands=['start'])
def start(message):
	try:
		c.execute('INSERT INTO users (user_id,name,alerts,state) VALUES(?,?,?,?)',(message.from_user.id, message.from_user.first_name,"Да","Новый"))
	except:
		pass
	conn.commit()
	main_menu(message,'Приветствую, ' + message.from_user.first_name + '!')
@bot.message_handler(commands=['help'])
def help(message):
	main_menu(message,'Этот бот создан для записи и оповещениях на игры в Помидорка Mafia Club.\n'
					  '/reset - для сброса всех настроек.\n'
					  '/help - для помощи.\n'
			  		  '@veraokulo - по всем вопросам')
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
	try:
		c.execute('INSERT INTO users (user_id,name,alerts,state) VALUES(?,?,?,?)',(message.from_user.id, message.from_user.first_name,"Да","Новый"))
		conn.commit()
	except:
		pass
	try:
		print(message)
		print(message.from_user)
		print(message.from_user.id)
		print(message.from_user.username)
		c.execute('UPDATE users SET username=? WHERE user_id=?',(message.from_user.username,message.from_user.id))
		conn.commit()
	except:
		pass
	if message.text == 'Информация о ближайшей игре':
		c.execute('SELECT * FROM games WHERE rowid = (SELECT MAX(rowid) FROM games)')
		row = c.fetchone()
		dg = int(time.mktime(time.strptime(row[0], '%d.%m.%Y %H:%M'))) - tm
		if dg > time.time():
			answer="Дата и время: "+row[0]+"\nМесто: "+row[1]+"\nВедущий: @"+row[2]+"\nВход бесплатный.\n"
			c.execute('SELECT * FROM zapis WHERE game_id=(SELECT MAX(rowid) FROM games)')
			count = 1
			st = ""
			row = c.fetchall()
			while True:
				try:
					wor = row[count - 1]
				except:
					break
				st += str(count)
				st += " "
				c.execute('SELECT name FROM users WHERE user_id=?', (wor[1],))
				n = c.fetchone()
				if wor[2] == None:
					st += n[0]
				else:
					st += wor[2]
					st += ' от '
					st += n[0]
				st += "\n"
				count = count + 1
			if (st == ""):
				st="Пока еще никто не записался.\nЗапишись первым!"
			else:
				st="Записавшиеся:\n"+st
			bot.reply_to(message, answer+st)
		else:
			bot.reply_to(message, 'Пока еще нету записи на новую игру')
	if message.text == 'Удалить запись':
		c.execute('SELECT * FROM users WHERE user_id = ?', (message.from_user.id,))
		n=c.fetchone()
		c.execute('SELECT * FROM zapis WHERE user_id = ? and game_id=(SELECT MAX(rowid) FROM games)',(message.from_user.id,))
		row = c.fetchone()
		markup = telebot.types.ReplyKeyboardMarkup(True, False)
		flag=False
		while row != None:
			flag=True
			if row[2]==None:
				markup.row(n[1])
			else:
				markup.row(row[2])
			row = c.fetchone()
		if flag:
			msg = bot.reply_to(message, 'Кого удалить?', reply_markup=markup)
			bot.register_next_step_handler(msg, delete_enroll)
		else:
			bot.reply_to(message, 'Некого удалять')
	if message.text == 'В главное меню':
		main_menu(message)
	if message.text == 'Админка' and message.from_user.id==myid:
		markup = telebot.types.ReplyKeyboardMarkup(True, False)
		markup.row('Создать запись на новую игру')
		markup.row('Сделать рассылку')
		markup.row('В главное меню')
		bot.reply_to(message, 'Информация о ближайшей игре', reply_markup=markup)

	if message.text == 'Сделать рассылку' and message.from_user.id ==myid:
		c.execute('SELECT * FROM games WHERE rowid = (SELECT MAX(rowid) FROM games)')
		g = c.fetchone()
		c.execute('SELECT * FROM users WHERE alerts=?', ("Да",))
		answer = "Открыта запись на новую игру\nДата и время : " + g[0] + "\nМесто : " + g[1] + "\nВедущий : @" + g[2]+"\nВход бесплатный.\n"
		mark = telebot.types.ReplyKeyboardMarkup(True, True)
		mark.row("Записаться на игру", 'Выключить оповещения')
		mark.row("В главное меню")
		while True:
			row = c.fetchone()
			if row == None:
				break
			try:
				bot.send_message(int(row[0]), answer, reply_markup=mark)
				try:
					bot.send_message(myid, row[0]+" удачно")
				except:
					pass
			except:
				try:
					bot.send_message(myid, row[0]+" неудачно")
				except:
					pass
	if message.text == 'Справка':
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


	if message.text == 'Записаться на игру':
		try:
			c.execute('SELECT * FROM games WHERE rowid = (SELECT MAX(rowid) FROM games)')
			row = c.fetchone()
			dg = int(time.mktime(time.strptime(row[0], '%d.%m.%Y %H:%M')))-tm
			if dg > time.time():
				c.execute('select rowid from games where rowid = (SELECT MAX(rowid) FROM games)')
				k = c.fetchone()
				c.execute('SELECT * FROM zapis WHERE game_id = (SELECT MAX(rowid) FROM games) and user_id=? and name IS NULL',(message.from_user.id,))
				a = c.fetchone()
				if a == None:
					c.execute('INSERT INTO zapis (game_id,user_id) VALUES(?,?)',(k[0], message.from_user.id))
				conn.commit()
				main_menu(message,'Вы успешно записались на игру')
			else:
				bot.reply_to(message, 'Пока еще нету записи на новую игру')
		except:
			eror(message)

	if message.text == 'Кто уже записался?':
		c.execute('SELECT * FROM games WHERE rowid = (SELECT MAX(rowid) FROM games)')
		row = c.fetchone()

		dg = int(time.mktime(time.strptime(row[0], '%d.%m.%Y %H:%M')))-tm
		if dg > time.time():
			c.execute('select rowid from games where rowid = (SELECT MAX(rowid) FROM games)')
			k = c.fetchone()
			c.execute('SELECT * FROM zapis WHERE game_id=?',(k[0],))
			count=1
			st=""
			row = c.fetchall()
			while True:
				try:
					wor=row[count-1]
				except:
					break
				st+=str(count)
				st+=" "
				c.execute('SELECT name FROM users WHERE user_id=?', (wor[1],))
				n = c.fetchone()
				if wor[2]==None:
					st += n[0]
				else:
					st+=wor[2]
					st+=' от '
					st += n[0]
				st+="\n"
				count=count+1
			if(st==""):
				bot.reply_to(message, "Пока еще никто.\nЗапишись первым!")
			else:
				bot.reply_to(message,st)
		else:
			bot.reply_to(message, 'Пока еще нету записи на новую игру')

	if message.text == 'Настройки':
		if message.chat.type=='private':
			markup = telebot.types.ReplyKeyboardMarkup(True, False)
			markup.row('/reset', 'Изменить имя')
			c.execute('SELECT alerts FROM users WHERE user_id=?', (message.from_user.id,))
			row = c.fetchone()
			if row[0]=="Да":
				markup.row('Выключить оповещения', 'В главное меню')
			else:
				markup.row('Включить оповещения', 'В главное меню')
			bot.reply_to(message, 'Настройки', reply_markup=markup)
		else:
			bot.reply_to(message, "Иди в личку настраивай")

	if message.text == 'Создать запись на новую игру' and message.from_user.id==myid:
		msg = bot.reply_to(message, 'Дата', reply_markup=telebot.types.ForceReply())
		bot.register_next_step_handler(msg, date_game)

	if message.text == 'Записать друга':
		try:
			c.execute('SELECT * FROM games WHERE rowid = (SELECT MAX(rowid) FROM games)')
			row = c.fetchone()
			dg = int(time.mktime(time.strptime(row[0], '%d.%m.%Y %H:%M')))-tm
			if dg > time.time():
				msg = bot.reply_to(message, 'Имя', reply_markup=telebot.types.ForceReply())
				bot.register_next_step_handler(msg, enroll_friend)
			else:
				bot.reply_to(message, 'Пока еще нету записи на новую игру')
		except:
			eror(message)

def delete_enroll(message):
	try:
		f=True
		c.execute('SELECT * FROM users WHERE user_id = ?', (message.from_user.id,))
		n = c.fetchone()
		if message.text == n[1]:
			c.execute('SELECT * FROM zapis WHERE name IS NULL and user_id=? and game_id=(SELECT MAX(rowid) FROM games)', (message.from_user.id,))
			if c.fetchone()==None:
				f=False
			c.execute('DELETE FROM zapis WHERE name IS NULL and user_id=? and game_id=(SELECT MAX(rowid) FROM games)',(message.from_user.id,))
		else:
			c.execute('SELECT * FROM zapis WHERE name=? and game_id=(SELECT MAX(rowid) FROM games)', (message.text,))
			if c.fetchone() == None:

				f = False
			c.execute('DELETE FROM zapis WHERE name=? and game_id=(SELECT MAX(rowid) FROM games)',(message.text,))
		conn.commit()
		if f:
			main_menu(message, 'Записанный успешно удален!')
		else:
			main_menu(message, 'Не найдено такой записи!')
	except:
		eror(message)
def enroll_friend(message):
	try:
		c.execute('select rowid from games where rowid = (SELECT MAX(rowid) FROM games)')
		k = c.fetchone()
		c.execute('INSERT INTO zapis (user_id,game_id,name) VALUES(?,?,?)',(message.from_user.id,k[0], message.text))
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

@app.route("/", methods=['POST'])
def getMessage():
	bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
	return "!", 200

@app.route("/")
def index():
	return "!", 200

if __name__ == '__main__':
	app.run()
