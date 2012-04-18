#!/usr/bin/env python
# coding: utf-8

import logging
from datetime import datetime

import tornado.auth
import tornado.escape
import tornado.options
import tornado.web

from lib import markdown
from lib.utils import CONST

from base import BaseHandler

class TopicBaseHandler(BaseHandler):
    def get_topics(self, sortby="replied", page=1, count=20):
        if count>20:
            count = 20
        if page<=0:
            page = 1
        if sortby == "posted":
            topics = self.db.query("SELECT * FROM topic WHERE tid=0 ORDER BY created DESC LIMIT %s, %s", (page-1)*count, count)
        elif sortby == "replied":
            topics = self.db.query("SELECT * FROM topic WHERE tid=0 ORDER BY replied DESC LIMIT %s, %s", (page-1)*count, count)
        elif sortby == "replies":
            topics = self.db.query("SELECT * FROM topic WHERE tid=0 ORDER BY reply_count DESC LIMIT %s, %s", (page-1)*count, count)
        return topics
    
    def get_replies(self, tid=0, page=1, count=50):
        if count>50:
            count = 50
        if page<=0:
            page = 1
        topics = self.db.query("SELECT * FROM topic WHERE tid=%s ORDER BY created LIMIT %s, %s", tid, (page-1)*count, count)
        return topics
        
    def get_topic(self, id):
        topic = self.db.get("SELECT * FROM topic WHERE id=%s", int(id))
        return topic
    
    def insert_topic(self, tid, title, content):
        user = self.current_user
        tid = self.db.execute("""
              INSERT INTO topic
              (tid, uid, url, name, icon, title, content, created, replied, reply_count)
              VALUES(%s, %s, %s, %s, %s, %s, %s, UTC_TIMESTAMP(), UTC_TIMESTAMP(), 0)""",
               tid, user["id"], user["url"], user["name"], user["icon"], title, content)
        return tid
    
    def update_topic(self, id, title=None, content=None):
        self.db.execute("UPDATE topic SET title=%s, content=%s WHERE id=%s", 
                         title, content, id)
    
    def reply_topic(self, id, content):
        self.insert_topic(id, "", content)
        user = self.current_user
        self.db.execute("""UPDATE topic SET reply_uid=%s, reply_url=%s, reply_name=%s, 
                           reply_icon=%s, reply_count=reply_count+1, 
                           replied=UTC_TIMESTAMP() WHERE id=%s""",
                        user["id"], user["url"], user["name"], user["icon"], id)      
    
    def delete_topic(self, id):
        self.db.execute("DELETE FROM topic WHERE id=%s", id)
    
    def update_reply_count(self, id, delta):
        self.db.execute("UPDATE topic SET reply_count=reply_count+%s WHERE id=%s", delta, id)
        
    def get_read_status(self, topics):
        read_status = self.get_secure_cookie("read", None)
        if read_status:
            read_status = tornado.escape.json_decode(read_status)
        else:
            read_status = {}
        for topic in topics:
            if unicode(topic.id) in read_status and read_status[unicode(topic.id)]>=topic.replied.isoformat():
                topic.read_status = True
            else:
                topic.read_status = False
        return topics
    
    def set_read_status(self, id):
        read_status = self.get_secure_cookie("read", None)
        if read_status:
            read_status = tornado.escape.json_decode(read_status)
        else:
            read_status = {}
        read_status[id] = datetime.utcnow().isoformat()
        self.set_secure_cookie("read", tornado.escape.json_encode(read_status))
    
    def user_in_topics(self):
        user = self.current_user
        if user:
            self.db.execute("""REPLACE INTO userintopic(uid, url, name, icon, time) VALUES
                               (%s, %s, %s, %s, UTC_TIMESTAMP())""",
                             user["id"], user["url"], user["name"], user["icon"])
        users = self.db.query("SELECT * FROM userintopic ORDER BY time DESC LIMIT 0, 30")
        return users;
        

class TopicListHandler(TopicBaseHandler):
    def get(self):
        sortby = self.get_argument("sortby", "replied")
        page = int(self.get_argument("page", "1"))
        count = int(self.get_argument("count", "20"))
        topics = self.get_topics(sortby, page, count)     
        self.get_read_status(topics)
        users = self.user_in_topics()
        self.render("topic/list.html", topics=topics, users=users, page=page, sortby=sortby)


class TopicCreateHandler(TopicBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("topic/create.html")
    
    @tornado.web.authenticated
    def post(self):
        title = self.get_argument("title", None)
        content = self.get_argument("content", None)
        if not (title and content):
            self.render("topic/create.html", msg=None)
        title = markdown.escape(title)
        content = markdown.markdown(content)
        tid = self.insert_topic(0, title, content)
        self.redirect("/topic/%s/" % (tid,))


class TopicDetailHandler(TopicBaseHandler):
    def get(self, id):
        topic = self.get_topic(id)
        page = self.get_argument("page", "1")
        if page=="last":
            page = topic.reply_count>0 and int((topic.reply_count-1)/50)+1 or 0
        else:
            page = int(page)
        count = int(self.get_argument("count", "50"))
        if page==1:
            topics = [topic]
        else:
            topics = []
        replies = self.get_replies(id, page, count)
        topics.extend(replies)
        recent_posts = self.get_topics("posted", 1, 7)
        self.set_read_status(id)
        self.render("topic/detail.html", topic=topic, topics=topics, page=page, recent_posts=recent_posts)


class TopicReplyHandler(TopicBaseHandler):
    @tornado.web.authenticated
    def post(self, id):
        content = self.get_argument("content", None)
        content = markdown.markdown(content)
        if not content:
            self.redirect("/topic/"+id+"/")
            return
        self.reply_topic(id, content)
        self.redirect("/topic/"+id+"/?page=last#last")


class TopicEditHandler(TopicBaseHandler):
    @tornado.web.authenticated
    def get(self, id):
        topic = self.get_topic(int(id))
        topic.title = topic.title
        topic.content = markdown.unmarkdown(topic.content)
        self.render("topic/edit.html", topic=topic)
    
    @tornado.web.authenticated
    def post(self, id):
        title = self.get_argument("title", None)
        content = self.get_argument("content", None)
        if not (title and content):
            self.render("topic/edit.html", msg=None)
        topic = self.get_topic(int(id))
        if not (self.current_user and (self.current_user["id"] == topic.uid or self.current_user.get("role")!=CONST.admin)):
            return
        title = markdown.escape(title)
        content = markdown.markdown(content)
        self.update_topic(id, title, content)
        self.redirect("/topic/%s/" % (id,))


class TopicDeleteHandler(TopicBaseHandler):
    @tornado.web.authenticated
    def get(self, id):
        topic = self.get_topic(int(id))
        if not (self.current_user and (self.current_user["id"] == topic.uid or self.current_user.get("role")!=CONST.admin)):
            self.redirect("/topics/")
            return
        if topic.tid == 0:
            self.delete_topic(int(id))
            self.redirect("/topics/")
            return
        else:
            self.delete_topic(int(id))
            self.update_reply_count(int(topic.tid), -1)
            self.redirect("/topic/%s/" % (topic.tid))


handlers = [
    (r"/topics/", TopicListHandler),
    (r"/topic/create/", TopicCreateHandler),
    (r"/topic/([0-9]+)/", TopicDetailHandler),
    (r"/topic/([0-9]+)/reply/", TopicReplyHandler),
    (r"/topic/([0-9]+)/edit/", TopicEditHandler),
    (r"/topic/([0-9]+)/delete/", TopicDeleteHandler),
]

uimodules = {
}
