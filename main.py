#!/usr/bin/python3
import sys
import imaplib
import time
from imapclient import IMAPClient
from socket import gethostbyname, gaierror, create_connection
from email.header import decode_header
import os
import email
import telebot
from dotenv import find_dotenv, load_dotenv, set_key
from charset_normalizer import from_bytes

# Get variables
dotenv_file = find_dotenv()
load_dotenv(dotenv_file)
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
ID_MESSAGE = os.getenv('ID_MESSAGE')
SERVER = os.getenv('IMAP')
USERNAME = os.getenv('USRNAME')
PASSWORD = os.getenv('PASSWORD')
url = os.getenv('URL')

bot = telebot.TeleBot(token=TELEGRAM_TOKEN)

## Conection
### If using gmail remember to enable insecure apps https://support.google.com/accounts/answer/6010255?hl=en
MAILBOX = "INBOX"
PROVIDER = ""
MYTIME = 60  # Time refresh

# Check queue. If it not working, define full path to file
def check_queue(id):
    with open('queue.txt', 'r+') as file:
        lines = [line.rstrip() for line in file]
        s = []
        count = 0
        for line in lines:
            s.append(int(line))
            count += 1
        s.append(id)
        file.seek(0)
        if count >= 4:
            for line in range(1, len(s)):
                file.write(str(s[line]) + '\n')
            try:
                bot.delete_message(chat_id=CHAT_ID, message_id=s[0])
            except:
                print(f"Error deleting message {s[0]}...")
        else:
            for line in range(0, len(s)):
                file.write(str(s[line]) + '\n')
    file.close()

# Check dic. If it not working, define full path to file
def check_mail(mail_from):
    with open('dict.txt','r') as file:
        for line in file:
            s = line.rstrip()
            if s.lower() in mail_from:
                file.close()
                return True
    file.close()
    return False

# Convert funcs
def dec_hed(message):
    bytes, mail_subject = decode_header(message)[0]
    try:
        return bytes.decode(mail_subject)
    except:
        return str(bytes)

def convert_subj(a):
    if a[:2] == "b'" and len(a) > 3:
        a = a[2:-1]
    if a[:15] == "*****SPAM***** ":
        a = a[15:]
    return a

# Send to telegram chat
def send_mail_to_tg(text):
    time.sleep(0.1)
    new_id_message = bot.send_message(chat_id=CHAT_ID, text=text)
    check_queue(new_id_message.id)

# Main func
def start():
    i = 1
    while i !=0:
        try:
            gethostbyname(SERVER)
            #TODO: connect to port 993
        except gaierror as e:
            print('invalid server: '+SERVER)
            print(str(e))
            sys.exit()

        server = IMAPClient(SERVER, use_uid=True)

        try:
            server.login(USERNAME,PASSWORD)
        except imaplib.IMAP4.error as e:
            print('invalid credentials')
            print("Username: "+USERNAME)
            print("Password: "+PASSWORD)
            print(str(e))
            server.logout()
            sys.exit()

        ## Reading emails
        ### Folder select
        try:
            server.select_folder(MAILBOX)
        except imaplib.IMAP4.error as e:
            print("Unknown Mailbox: "+MAILBOX)
            print(str(e))
            server.logout()
            sys.exit()

        ### Reading emails
        messages = server.search(['FROM', PROVIDER, 'UNSEEN'])
        #print("%d messages found" % len(messages))

        for msgid, data in server.fetch(messages, ['RFC822', 'BODY[TEXT]','ENVELOPE', 'FLAGS']).items():
            envelope = data[b'ENVELOPE']
            body = data[b'BODY[TEXT]']
            subject = dec_hed(convert_subj(envelope.subject.decode()))
            email1 = dec_hed(str(list(envelope.sender)[0]))
            lst = str(list(envelope.sender)[0]).split(" ")
            if len(lst) > 10:
                email2 = lst[1]
            else:
                lst = str(list(envelope.sender)[0])
                email2 = lst[lst.index('<'):]

            email_message = email.message_from_bytes(data[b'RFC822'])
            if check_mail(email_message.get('From')):
                send_mail_to_tg(f'Вам письмо!\nОт: {email1} {email2}\nТема: {convert_subj(subject)}')
            ## TODO: extract just the HTML

        server.logout()
        time.sleep(MYTIME)

if __name__ == '__main__':
    start()
