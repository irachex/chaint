#!/usr/bin/env python
# coding: utf-8

import logging
import tornado.auth
import tornado.escape
import tornado.options
import tornado.web

from base import BaseHandler

class HomeHandler(BaseHandler):
    def get(self):
        self.render("index.html")


handlers = [
    (r"/", HomeHandler),
]