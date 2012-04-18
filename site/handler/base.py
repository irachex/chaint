#!/usr/bin/env python
# coding: utf-8

import logging
import tornado.auth
import tornado.escape
import tornado.options
import tornado.web


class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db
    
    def get_current_user(self):
        user_json = self.get_secure_cookie("user")
        if not user_json: 
            return None
        return tornado.escape.json_decode(user_json)