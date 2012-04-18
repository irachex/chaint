#!/usr/bin/env python
# coding: utf-8

import logging
import tornado.auth
import tornado.escape
import tornado.options
import tornado.web

from base import BaseHandler

class TopicModel(object):
    

class TopicListHandler(BaseHandler):
    def get(self):
        sortby = self.get_argument("sortby", "reply")
        page = self.get_argument("page", "1")
        count = int(self.get_argument("count", "20"))
        count = count > 20 ? 20 : count
        
        if sortby == "submit":
            topics = self.db.query("SELECT * FROM topic ORDER BY created DESC")
        elif sortby == "reply":
            topics = self.db.query("SELECT * FROM topic ORDER BY updated DESC")
        elif sortby == "hot":
            topics = self.db.query("SELECT * FROM topic ORDER BY LIMIT")
        self.render("topic_list.html", topics=topics)

class TopicCreateHandler(BaseHandler):
    def get(self):
        self.render("topic_create.html")
    
    def post(self):
        title = self.get_argument("title", None)
        content = self.get_argument("content", None)
        if not (title and content):
            self.render("topic_create.html", msg="null")
        self.redirect("/topics/")

class TopicDetailHandler(BaseHandler):
    def get(self, id):
        topics = self.db.query("SELECT * FROM topic WHERE tid=%s ORDER BY created DESC", int(id))
        self.render("topic_detail.html", topic = topics)

class TopicReplyHandler(BaseHandler):
    def post(self, id):
        content = self.get_argument("content")
        self.db.query("INSERT INTO topic() VALUES ()")
        

class TopicEditHandler(BaseHandler):
    def get(self, id):
        topic = self.db.get("SELECT * FROM topic WHERE id=%s ORDER BY created DESC", int(id))
        self.render("topic_edit.html", topic=topic)
    
    def post(self, id):
        title = self.get_argument("title", None)
        content = self.get_argument("content", None)
        if not (title and content):
            self.render("topic_create.html", msg="null")
        self.redirect("/topic/"+id)
        

class TopicDeleteHandler(BaseHandler):
    def get(self):
        pass


handlers = [
    (r"/topics/", TopicListHandler),
    (r"/topic/create/", TopicCreateHandler),
    (r"/topic/([0-9]+)/", TopicDetailHandler),
    (r"/topic/([0-9]+)/reply/", TopicDetailHandler),
    (r"/topic/([0-9]+)/edit/", TopicEditHandler),
    (r"/topic/([0-9]+)/delete/", TopicDeleteHandler),
]