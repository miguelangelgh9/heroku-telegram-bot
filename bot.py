# -*- coding: utf-8 -*-
import redis
import os
import telebot
import psycopg2
import urlparse

# Example of your code beginning
#           Config vars
token = os.environ['TELEGRAM_TOKEN']
urlparse.uses_netloc.append("postgres")
dburl = urlparse.urlparse(os.environ["DATABASE_URL"])
con = psycopg2.connect(database=dburl.path[1:],
  user=dburl.username,
  password=dburl.password,
  host=dburl.hostname,
  port=dburl.port
)
cur = con.cursor()


#             ...

# If you use redis, install this add-on https://elements.heroku.com/addons/heroku-redis
#r = redis.from_url(os.environ.get("REDIS_URL"))

#       Your bot code below
# bot = telebot.TeleBot(token)
# some_api = some_api_lib.connect(some_api_token)
#              ...
"""Simple Bot to reply to Telegram messages.
This program is dedicated to the public domain under the CC0 license.
This Bot uses the Updater class to handle the bot.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import feedparser

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    """Send a message when the command /start is issued."""
    update.message.reply_text("Hi!\nI was created to send messages to chats whenever a new One Piece issue is released, if you would like to recieve them as well just use /addchat but if you don't want the updates use /rmchat \nI can also look for a specific manga entry in the MangaStream by using /feed <the name of the manga>, just know that you have to write it as it appears on MangaStream and with spaces.\nBy the way, if you stop recieving updates but didnt /rmchat, it might be becase I was killed. Call the cops.")

def addchat(bot, update):
    """Add the current chat to the list of chats to update"""
    chatid=update.message.chat_id
    global cur
    cur.execute("SELECT id=" + str(chatid) + "FROM chats")
    row=cur.fetchone()
    if row:
        update.message.reply_text("It seems like you are already on the list!")
    else:
        cur.execute("INSERT INTO chats VALUES("+ str(chatid) +")")
        update.message.reply_text("Your chat has been added and will be notified once a update comes!")

def rmchat(bot, update):
    """Remove the current chat from the list of chats to update"""
    chatid=update.message.chat_id
    global cur
    cur.execute("SELECT id=" + str(chatid) + "FROM chats")
    row=cur.fetchone()
    if row:
        cur.execute("DELETE FROM chats WHERE id="+ str(chatid))
        update.message.reply_text("You have been removed succesfully and won't be notified in the future!")
    else:
        update.message.reply_text("Your chat is not in my list... Would you like to /addchat ?")

def feed(bot, update, args):
    url='https://www.mangastream.com/rss'
    feed = feedparser.parse(url)
    name = ' '.join(args).lower()
    piece=''
    for i in feed['items']:
        if name in i['title'].lower():
            piece=i
            break
    if piece:
        link=piece['links'][0]
        update.message.reply_text('The latest issue is '+ piece['title']+ '. It was released on ' +piece['published']+'\nYou can read it on MangaStream: '+ link['href'])

    else:
        update.message.reply_text("I couldn't find anything on the MangaStream RSS feed with that name, maybe you misspelled it?")

def onepiece(bot, update):
    url='https://www.mangastream.com/rss'
    feed = feedparser.parse(url)
    for i in feed['items']:
        if 'One Piece' in i['title']:
            piece=i
            break
    link=piece['links'][0]
    update.message.reply_text('The latest One Piece issue is '+ piece['title']+ '. It was released on ' +piece['published']+'\nYou can read it on MangaStream: '+ link['href'])

def alarm(bot, job):
    url='https://www.mangastream.com/rss'
    feed = feedparser.parse(url)
    global cur
    cur.execute("SELECT * FROM issue")
    issue=cur.fetchone()[0]
    for piece in feed['items']:
        if 'One Piece' in piece['title'] and str(issue + 1) in piece['title']:
            cur.execute("UPDATE issue SET id="+ str(issue+1) +" WHERE id="+ str(issue))
            link=piece['links'][0]
            cur.execute("SELECT * FROM chats")
            row=cur.fetchall()
            for c in row:
                bot.send_message(chat_id=c[0], text='The latest One Piece issue is '+ piece['title']+ '. It was released on ' +piece['published']+'\nYou can read it on MangaStream: '+ link['href'])
            break


def help(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Hey There!\n These are all my commands:\n/start\n/addchat\n/rmchat\n/onepiece\n/issue\n/feed')


def echo(bot, update):
    """Echo the user message."""
    update.message.reply_text("Sorry, I don't fully speak human just yet! Could you please use something I can understand? If you need help you can always use /help")


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)

def unknown(bot, update):
    update.message.reply_text("I don't know what you are trying to say, do you need /help ?")


def main():
    """Start the bot."""

    # Create the EventHandler and pass it your bot's token.
    updater = Updater(token)

    #Add the reapeating job to the job queue
    updater.job_queue.run_repeating(alarm,1800)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("onepiece", onepiece))
    dp.add_handler(CommandHandler("issue", currentIssue))
    dp.add_handler(CommandHandler("addchat", addchat))
    dp.add_handler(CommandHandler("rmchat", rmchat))
    dp.add_handler(CommandHandler('feed', feed, pass_args=True))
    dp.add_handler(MessageHandler(Filters.command, unknown))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
