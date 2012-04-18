#!/usr/bin/env python
# coding: utf-8

import logging
import uuid
import time
from datetime import datetime

import tornado.auth
import tornado.escape
import tornado.options
import tornado.web

from base import BaseHandler


class MessageMixin(object):
    waiters = dict()
    messages = dict()
    online = dict()
    cache_size = 200

    def is_online(self, rid, user):
        cls = MessageMixin
        if rid not in cls.online:
            cls.online[rid] = list()
        return user in cls.online[rid]

    def set_online(self, rid, user):
        cls = MessageMixin
        if rid not in cls.online:
            cls.online[rid] = list()
        cls.online[rid].append(user)
    
    def set_offline(self, rid, user):
        cls = MessageMixin
        if rid not in cls.online:
            cls.online[rid] = list()
        cls.online[rid].remove(user)
    
    @classmethod
    def get_onlines(cls, rid):
        if rid not in cls.online:
            cls.online[rid] = list()
        return cls.online[rid]

    @classmethod    
    def clear_messages(cls, rid, mtype="default"):
        if rid not in cls.messages:
            cls.messages[rid] = {}
        if mtype not in cls.messages[rid]:
            cls.messages[rid][mtype] = []
        cls.messages[rid][mtype] = []

    def get_messages(self, rid, mtype="default"):
        """return messages by room id and type"""
        cls = MessageMixin
        if rid not in cls.messages:
            cls.messages[rid] = dict()
        if mtype not in cls.messages[rid]:
            cls.messages[rid][mtype] = list()
        return cls.messages[rid][mtype]
    
    def add_messages(self, rid, messages):
        """simply add messages in room"""
        cls = MessageMixin
        if rid not in cls.messages:
            cls.messages[rid] = dict()
        for message in messages:
            mtype = message.get("type") or "default"
            if mtype not in cls.messages[rid]:
                cls.messages[rid][mtype] = list()
            if "time" not in message:
                message["time"] = time.time()
            cls.messages[rid][mtype].append(message)
            if mtype=="chat" and len(cls.messages[rid][mtype])>cache_size:
                cls.messages[rid][mtype] = cls.messages[rid][mtype][-cache_size:]
    
    def wait_for_messages(self, rid, callback, update_time=None):
        """add asynchronous callback to waiter list"""
        cls = MessageMixin
        if rid not in cls.waiters:
            cls.waiters[rid] = list()
        if rid not in cls.messages:
            cls.messages[rid] = dict()
        
        if update_time:
            recent = list()
            for mtype, tlist in cls.messages[rid].iteritems():
                index = 0
                messages_len = len(tlist)
                for i in xrange(messages_len):
                    index = messages_len - i - 1
                    if tlist[index]["time"] < update_time:
                        break
                recent.extend(tlist[index + 1:])
            if recent:
                callback(rid, recent)
                return
        cls.waiters[rid].append(callback)

    def new_messages(self, rid, messages):
        """run callback in waiter list to return new messages"""
        cls = MessageMixin
        if rid not in cls.waiters:
            cls.waiters[rid] = list()
        logging.info("Sending new message to %d listeners in room %s" % (len(cls.waiters[rid]), rid))
        for callback in cls.waiters[rid]:
            try:
                callback(rid, messages)
            except:
                logging.error("Error in waiter callback", exc_info=True)
        cls.waiters[rid] = list()
        self.add_messages(rid, messages)


class MessageNewHandler(BaseHandler, MessageMixin):
    @tornado.web.authenticated
    def post(self, rid):
        message = tornado.escape.json_decode(self.get_argument("message"))
        
        # if message type is online then set current_user
        if message["type"]=="online":
            message["user"] = self.current_user
            if message["content"] is False and self.is_online(rid, self.current_user):
                self.set_offline(rid, self.current_user)
        
        self.new_messages(rid, [message])
        
        if self.get_argument("next", None):
            self.redirect(self.get_argument("next"))
        else:
            self.finish('{"ok":"y"}')


class MessageUpdatesHandler(BaseHandler, MessageMixin):
    @tornado.web.asynchronous
    def post(self, rid):
        update_time = self.get_argument("update_time", None)
        if update_time is not None:
            update_time = float(update_time)
        self.wait_for_messages(rid, self.async_callback(self.on_wait_messages), update_time=update_time)

    def on_wait_messages(self, rid, messages):
        # Closed client connection
        if self.request.connection.stream.closed():
            if self.is_online(rid, self.current_user):
                self.set_offline(rid, self.current_user)
                message = {
                    "id": unicode(uuid.uuid4()),
                    "type": "online",
                    "content": False,
                    "user": self.current_user
                }
                self.add_messages(rid, [message])
            return
        self.finish(dict(messages=messages))


class MessageInitHandler(BaseHandler, MessageMixin):
    def post(self, rid):
        self.set_online(rid, self.current_user)
        message = {
            "id": unicode(uuid.uuid4()),
            "type": "online",
            "content": True,
            "user": self.current_user
        }
        self.new_messages(rid, [message])

        messages = self.get_messages(rid, "doodle") + self.get_messages(rid, "online")[-1:]
        self.finish(dict(messages=messages))


handlers = [
    (r"/room/([0-9]+)/message/init/", MessageInitHandler),
    (r"/room/([0-9]+)/message/updates/", MessageUpdatesHandler),
    (r"/room/([0-9]+)/message/new/", MessageNewHandler),
]