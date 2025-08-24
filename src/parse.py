#!/usr/bin/env python3

import os
import stat
import time
import sqlite3
import requests
from bs4 import BeautifulSoup

class news_entry:
    SENTIMENT_POSITIVE = 0
    SENTIMENT_NEUTRAL  = 1
    SENTIMENT_NEGATIVE = 2
    SENTIMENT_UNKNOWN  = 3

    def __init__(self, sentiment, text):
        self.timestamp = int(time.time())
        self.sentiment = sentiment
        self.text = text
    
    def __str__(self):
        return "({}, {}, '{}')".format(self.timestamp, self.sentiment, self.text)

    def __repr__(self):
        return self.__str__()

class db_connector:
    def __init__(self, sqlite_filename):
        self._sqlite_filename = sqlite_filename
        self._table_name = 'news'

        # Open (or create) database file
        con = sqlite3.connect(self._sqlite_filename)

        # Check for table
        res = con.execute("SELECT * FROM sqlite_master WHERE name='{}'".format(self._table_name))

        if res.fetchone() is None:
            # Table does not exist, create it
            print("Create table:", self._table_name)
            con.execute('CREATE TABLE {}(timestamp, sentiment, text)'.format(self._table_name))

        con.close()

    def delete_entries_older_than(self, timestamp):
        con = sqlite3.connect(self._sqlite_filename)
        count = con.execute('DELETE FROM {} WHERE timestamp < {}'.format(self._table_name, timestamp)).rowcount
        if count > 0:
            print('Deleted', str(count), 'news older than', str(timestamp))
        con.commit()
        con.close()

    def check_entry_exists(self, news):
        con = sqlite3.connect(self._sqlite_filename)

        res = con.execute("SELECT * FROM {} WHERE sentiment = {} AND text = '{}'".format(self._table_name, news.sentiment, news.text)).fetchmany()

        if len(res) == 0:
            # Entry not found, add it
            found = False
        else:
            # Entry found
            found = True

        con.close()
        return found

    def add_entry(self, news):
        con = sqlite3.connect(self._sqlite_filename)
        con.execute("INSERT INTO {} VALUES ({}, {}, '{}')".format(self._table_name, news.timestamp, news.positive, news.text))
        con.commit()
        con.close()

db = db_connector('modern-banking-news.db')

# Delete all entries older than a month
delta_time = time.time() - 60 * 24 * 60 * 60
db.delete_entries_older_than(delta_time)

headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '3600',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
}

url = 'https://www.modern-banking.at/'
req = requests.get(url, headers)
soup = BeautifulSoup(req.content, 'html.parser')

top = soup.find(id='bereich')

print('~'*50)
print(req.content)
print('~'*50)

secs = top.find_all(class_='entry-title')

new_news = {}

for sec in secs:
    sec_title = sec.contents[0]
    new_news[sec_title] = []

    # Skip <br> item:
    #                 <br>         <ul>
    sec_ul = sec.next_sibling.next_sibling
    sec_as = sec_ul.find_all('a')
    sec_neu = sec_ul.find_all(class_='neu')

    print('='*30)
    print('Section:', sec_title)
 
    print('#'*50)
    print(sec)
    print('#'*50)
    print(sec_ul)
    print('#'*50)
    print(sec_as)
    print('#'*50)
    print(sec_neu)
    print('#'*50)

    for idx, a in enumerate(sec_as):
        print('='*10)
        #print('Index:', idx)
        s = ''.join(a.strings)
        #print(s)

        sentiment = news_entry.SENTIMENT_UNKNOWN
        if 'positiv' in str(sec_neu[idx])[:24]:
            sentiment = news_entry.SENTIMENT_POSITIVE
        elif 'neutral' in str(sec_neu[idx])[:24]:
            sentiment = news_entry.SENTIMENT_NEUTRAL
        elif 'negativ' in str(sec_neu[idx])[:24]:
            sentiment = news_entry.SENTIMENT_NEGATIVE
        news = news_entry(sentiment, s)

        #print('Sentiment:', sentiment)
        #print(s)

        if not db.check_entry_exists(news):
            #db.add_entry(news)
            new_news[sec_title].append(news)

print('*'*50)

exit(0)

empty = True

subject = "[modern-banking.at] Neuigkeiten"

body = "modern-banking.at hat Neuigkeiten für dich:\n\n"

for key in new_news.keys():
    if len(new_news[key]) == 0:
        continue
    empty = False
    body += '='*10 + ' ' + key + ' ' + '='*10 + "\n\n"
    for news in new_news[key]:
        body += '+ ' if news.positive else '- '
        body += news.text
        body += "\n\n"

if not empty:
    print(subject)
    print()
    print(body)

    pipe_path = "/var/run/mailifier"

    if not os.path.exists(pipe_path) or not stat.S_ISFIFO(os.stat(pipe_path).st_mode):
        print('ERROR: pipe does not exist or is not of type pipe!')
        exit(1)

    if subject.find(';') != -1:
        print('WARNING: Subject contains semicolons. Will be replaced with colons.')
        subject = subject.replace(';', ':')

    if body.find(';') != -1:
        print('WARNING: Body contains semicolons. Will be replaced with colons.')
        body = body.replace(';', ':')

    if body.find('\\n') != -1:
        print('WARNING: Body contains the character sequences "\\n". Will be replaced with newlines.')
        body = body.replace('\\n', '\n')

    command = subject + ';' + body

    print('Sending to pipe:', command)

    #with open(pipe_path, 'w') as pipe:
    #    pipe.write(command)
