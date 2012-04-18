#!/usr/bin/env python
# coding: utf-8

import logging
import tornado.auth
import tornado.escape
import tornado.options
import tornado.web

from base import BaseHandler


class UserBaseHandler(BaseHandler):
    def get_user(self, url):
        user = self.db.get("SELECT * FROM `user` WHERE `url`=%s", url)
        return user


class UserHandler(UserBaseHandler):
    def get(self, id):
        user = self.get_user(int(id))
        if user is None:
        	self.redirect("/")
        	return 
        self.render("user.html", user=user)


handlers = [
    (r"/people/([0-9]+)/", UserHandler),
]