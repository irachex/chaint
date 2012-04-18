#!/usr/bin/env python
# coding: utf-8

import os
import logging
import uuid

import tornado
import tornado.web
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.options import options
import tornado.database
import tornado.autoreload

from lib.utils import parse_config_file
from handler import home
from handler import room
from handler import message
from handler import topic
from handler import user
#import handler.gallery
from handler import auth
                         

class Application(tornado.web.Application):
    def __init__(self):
        handlers = []
        handlers.extend(home.handlers)
        handlers.extend(room.handlers)
        handlers.extend(message.handlers)
        handlers.extend(topic.handlers)
        handlers.extend(auth.handlers)
        handlers.extend(user.handlers)
        uimodules = {}
        uimodules.update(topic.uimodules)
        
        settings = dict(
            debug=options.debug,
            cookie_secret=options.cookie_secret,
            xsrf_cookies=options.xsrf_cookies,
            login_url=options.login_url,
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
#            autoescape="xhtml_escape",
            autoescape=None,
            ui_modules=uimodules,
            douban_consumer_key=options.douban_consumer_key,
            douban_consumer_secret=options.douban_consumer_secret,
            weibo_api_key=options.weibo_api_key,
            weibo_secret=options.weibo_secret,
            facebook_api_key=options.facebook_api_key,
            facebook_secret=options.facebook_secret,
            twitter_consumer_key=options.douban_consumer_key,
            twitter_consumer_secret=options.twitter_consumer_secret,
        )
        tornado.web.Application.__init__(self, handlers, **settings)
        
        self.db = tornado.database.Connection(
            host=options.mysql_host, database=options.mysql_database,
            user=options.mysql_user, password=options.mysql_password)


def main():
    parse_config_file(os.path.join(os.path.dirname(__file__), "config.py"))
    tornado.options.parse_command_line()
    
    http_server = HTTPServer(Application())
    port = options.port
    num_processes = options.num_processes
    http_server.bind(int(port))
    http_server.start(int(num_processes))
    
    instance = IOLoop.instance()
    tornado.autoreload.start(instance)
    instance.start()


if __name__ == "__main__":
    main()
