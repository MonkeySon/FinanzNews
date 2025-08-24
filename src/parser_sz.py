#!/usr/bin/env python3

import time
import sqlite3
from dateutil.parser import parse
import requests
import re
from bs4 import BeautifulSoup

class news_entry:
    def __init__(self, timestamp, headline, text, url):
        self.timestamp = timestamp
        self.headline  = headline
        self.text      = text
        self.url       = url
    
    def __str__(self):
        return f"({self.timestamp}, '{self.headline}', '{self.text}', '{self.url})'"

    def __repr__(self):
        return self.__str__()

class db_connector:
    def __init__(self, sqlite_filename):
        self._sqlite_filename = sqlite_filename
        self._table_name = 'news'

        # Open (or create) database file
        con = sqlite3.connect(self._sqlite_filename)

        # Check for table
        res = con.execute(f"SELECT * FROM sqlite_master WHERE name='{self._table_name}'")

        if res.fetchone() is None:
            # Table does not exist, create it
            print("Create table:", self._table_name)
            con.execute(f"CREATE TABLE {self._table_name}(timestamp, headline, text, url)")

        con.close()

    def delete_entries_older_than(self, timestamp):
        con = sqlite3.connect(self._sqlite_filename)
        count = con.execute(f"DELETE FROM {self._table_name} WHERE timestamp < {timestamp}").rowcount
        if count > 0:
            print('Deleted', str(count), 'news older than', str(timestamp))
        else:
            print('No news older than', str(timestamp))
        con.commit()
        con.close()

    def check_entry_exists(self, news):
        con = sqlite3.connect(self._sqlite_filename)

        res = con.execute(f"SELECT * FROM {self._table_name} WHERE headline = '{news.headline}' AND text = '{news.text}' AND url = '{news.url}'").fetchmany()

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
        con.execute(f"INSERT INTO {self._table_name} VALUES ({news.timestamp}, '{news.headline}', '{news.text}', '{news.url}')")
        con.commit()
        con.close()

def parse_sz():

    db = db_connector('sparzinsen-news.db')

    # Delete all entries older than 60 days
    delta_time = time.time() - 60 * 86400
    db.delete_entries_older_than(delta_time)

    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '3600',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
    }

    new_news = []

    url = 'https://www.sparzinsen.at/news/'
    req = requests.get(url, headers)
    soup = BeautifulSoup(req.content, 'html.parser')

    main = soup.find('main')

    articles = main.find_all('article')

    for article in articles:
        #print('-'*10)
        headline_p = article.find(class_='gb-headline')
        if headline_p.name == 'p':
            time_str = headline_p.contents[0]['datetime']
            dt = parse(time_str)
            article_time = int(dt.timestamp())
        else:
            article_time = int(time.time())

        #print(article_time)

        headline_h = article.find(re.compile('h[2-3]'), class_='gb-headline')
        headline_text = ''.join(headline_h.strings).strip()
        #print(headline_text)

        #        <h*>         <a> 
        url = headline_h.contents[0]['href']
        #print(url)

        content = article.find(class_='dynamic-entry-excerpt')
        content_text = ''.join(content.strings).strip()
        #print(content_text)

        news = news_entry(article_time, headline_text, content_text, url)
        if not db.check_entry_exists(news):
            print(f"Add entry: {news}")
            db.add_entry(news)
            new_news.append(news)

    if len(new_news) == 0:
        print('No news')
        return None
    
    body = ''

    for entry in new_news:
        body += '<hr/>'
        body += '<p>'
        body += '<p>'
        body += entry.headline.strip()
        body += '</p>'
        body += entry.text.strip()
        body += ' <a href="'
        body += entry.url.strip()
        body += '">MEHR</a>'
        body += '</p>'

    if body.find(';') != -1:
        print('WARNING: Body contains semicolons. Will be replaced with commas.')
        body = body.replace(';', ',')

    if body.find('\\n') != -1:
        print('WARNING: Body contains the character sequences "\\n". Will be replaced with newlines.')
        body = body.replace('\\n', '\n')

    #print(body)

    return body