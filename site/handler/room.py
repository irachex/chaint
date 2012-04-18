#!/usr/bin/env python
# coding: utf-8

import logging
import uuid
import random
import time

import tornado.auth
import tornado.escape
import tornado.options
import tornado.web

from lib.utils import CONST
from lib import markdown
from message import MessageMixin
from base import BaseHandler

class RoomBaseHandler(BaseHandler):
    def get_room(self, id):
        return self.db.get("SELECT room.*, saved.file FROM room LEFT JOIN saved ON room.savedid=saved.id WHERE room.id=%s LIMIT 1;", int(id))
    
    def get_random_room(self):
        room = self.db.get("""SELECT * FROM `room` AS t1 JOIN 
                              (SELECT ROUND(RAND() * ((SELECT MAX(id) FROM `room`)-
                                (SELECT MIN(id) FROM `room`))+
                              (SELECT MIN(id) FROM `room`)) AS id) AS t2 
                             WHERE t1.id >= t2.id ORDER BY t1.id LIMIT 1;""")
        return room
    
    def get_rooms(self, sortby="created", page=1, count=20):
        if count>20:
            count = 20
        if page<=0:
            page = 1
        if sortby == "created":
            rooms = self.db.query("SELECT room.*, saved.file FROM room LEFT JOIN saved ON room.savedid=saved.id ORDER BY room.created DESC LIMIT %s, %s", (page-1)*count, count)
        elif sortby == "likes":
            rooms = self.db.query("SELECT room.*, saved.file FROM room LEFT JOIN saved ON room.savedid=saved.id ORDER BY room.likes DESC LIMIT %s, %s", (page-1)*count, count)
        elif sortby == "views":
            rooms = self.db.query("SELECT room.*, saved.file FROM room LEFT JOIN saved ON room.savedid=saved.id ORDER BY room.views DESC LIMIT %s, %s", (page-1)*count, count)
        return rooms
    
    def get_room_user(self, rid):
        return self.db.query("SELECT * FROM room_user WHERE rid=%s", int(rid))
    
    def is_user_in_room(self, rid, user):
        if not user:
            return None
        return self.db.get("SELECT * FROM room_user WHERE rid=%s AND uid=%s LIMIT 1;", rid, user["id"])
         
    
    def insert_room_user(self, rid, user, role):
        if not user:
            return None
        self.db.execute("INSERT INTO room_user(uid, name, icon, url, rid, role) VALUES(%s, %s, %s, %s, %s, %s)",
                         user["id"], user["name"], user["icon"], int(user["url"]), int(rid), role)
        
    def create_room(self, title, intro, private, user):
        password = ""
        if private:
            password = "".join(random.sample("abcdefghijklmnopqrstuvwxyz0123456789",8))
        rid = self.db.execute("INSERT INTO room(title, intro, password, likes, views, created) VALUES(%s, %s, %s, 0, 0, UTC_TIMESTAMP())", 
                               title, intro, password)
        self.insert_room_user(rid, user, CONST.host)
        return rid
    
    def update_room(self, rid, title, intro, password):
        self.db.execute("UPDATE room SET title=%s, intro=%s, password=%s WHERE id=%s", title, intro, password, int(rid))
    
    def save_room(self, rid, user, data):
        sid = self.db.execute("INSERT INTO saved (rid, uid, file, created) VALUES(%s, %s, %s, UTC_TIMESTAMP())", rid, user["id"], data)
        self.db.execute("UPDATE room SET savedid = %s WHERE id=%s", sid, int(rid))
    
    def add_views(self, rid):
        self.db.execute("UPDATE room SET views=views+1 WHERE id=%s", int(rid))

    def add_likes(self, rid, delta=1):
        self.db.execute("UPDATE room SET likes=likes+%s WHERE id=%s", delta, int(rid))
    
    def delete_room(self, rid):
        self.db.execute("DELETE FROM room WHERE id=%s", rid)
    
    def is_user_like(self, rid, user):
        return self.db.get("SELECT * FROM user_like WHERE rid=%s AND uid=%s LIMIT 1;", int(rid), user["id"])

    def insert_user_like(self, rid, user):
        self.db.execute("INSERT INTO user_like(uid, rid) VALUES(%s, %s)", user["id"], int(rid))
    
    def delete_user_like(self, rid, user):
        self.db.execute("DELETE FROM user_like WHERE uid=%s AND rid=%s", user["id"], int(rid))


class RoomDetailHandler(RoomBaseHandler):
    @tornado.web.authenticated
    def get(self, rid):
        room = self.get_room(int(rid))
        if not room:
            raise tornado.web.HTTPError(404)
        password = self.get_argument("code", None)
        if not self.is_user_in_room(rid, self.current_user):
            if room.password:
                if password == room.password:
                    self.insert_room_user(rid, self.current_user, CONST.partner)
                else:
                    self.redirect("/room/%s/view/" %(rid,))
            else:
                self.insert_room_user(rid, self.current_user, CONST.partner)
        users = self.get_room_user(rid)
        onlines = MessageMixin.get_onlines(rid) or []
        self.render("room/detail.html", room=room, onlines=onlines, users=users)


class RoomViewHandler(RoomBaseHandler):
    def get(self, rid):
        room = self.get_room(int(rid))
        self.add_views(rid)
        if not room:
            raise tornado.web.HTTPError(404)
        onlines = len(MessageMixin.get_onlines(rid) or [])
        self.render("room/view.html", room=room, onlines=onlines)


class RoomLikeHandler(RoomBaseHandler):
    def get(self, rid):
        pass


class RoomRandomHandler(RoomBaseHandler):
    def get(self):
        room = self.get_random_room()
        if not room:
            self.redirect("/rooms/")
            return
        self.redirect("/room/%s/view/" % (int(room["id"]),))


class RoomListHandler(RoomBaseHandler):
    def get(self):
        sortby = self.get_argument("sortby", "created")
        page = int(self.get_argument("page", "1"))
        count = int(self.get_argument("count", "20"))
        rooms = self.get_rooms(sortby, page, count)
        self.render("room/list.html", rooms=rooms, sortby=sortby, page=page)


class RoomCreateHandler(RoomBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("room/create.html")
    
    @tornado.web.authenticated
    def post(self):
        title = self.get_argument("title", None)
        intro = self.get_argument("intro", None)
        if not (title and intro):
            self.render("room/create.html", msg=None)
        title = markdown.escape(title)
        intro = markdown.markdown(intro)
        private = self.get_argument("private")=="true"
        rid = self.create_room(title, intro, private, self.current_user)
        self.redirect("/room/%s/" % (rid,))
        

class RoomEditHandler(RoomBaseHandler):
    @tornado.web.authenticated
    def get(self, rid):
        room = self.get_room(rid)
        if not room:
            raise tornado.web.HTTPError(404)
        self.render("room/edit.html", room=room)
    
    @tornado.web.authenticated    
    def post(self, rid):
        title = self.get_argument("title")
        intro = self.get_argument("intro")
        private = self.get_argument("private")=="true"
        password = self.get_argument("password")
        if not private:
            password = ""
        self.update_room(rid, title, intro, password)
        self.redirect( "/room/%s/" % (rid,))
        

class RoomDeleteHandler(RoomBaseHandler):
    @tornado.web.authenticated
    def get(self, rid):
        if not (self.current_user and (self.current_user.get("role")!=CONST.admin)):
            self.redirect("/rooms/")
            return
        self.delete_room(rid)
        self.redirect("/rooms/")


class RoomSaveHandler(RoomBaseHandler):
    @tornado.web.authenticated
    def post(self, rid):
        data = self.get_argument("data", None)
        if not data:
            self.finish(dict(ok=False))
        self.save_room(rid, self.current_user, data)
        MessageMixin.clear_messages(rid, "doodle")
        self.finish(dict(ok=True))
        #except:
        #    self.finish(dict(ok=False))


class RoomLikeHandler(RoomBaseHandler):
    @tornado.web.authenticated
    def get(self, rid):
        if self.is_user_like(rid, self.current_user):
            self.finish(dict(like=True))
        else:
            self.finish(dict(like=False))
    
    @tornado.web.authenticated
    def post(self, rid):
        islike = self.get_argument("like")
        if islike == "true":
            self.delete_user_like(rid, self.current_user)
            self.finish(dict(like=False))
        else:
            self.insert_user_like(rid, self.current_user)
            self.finish(dict(like=True))
        

handlers = [
    (r"/rooms/", RoomListHandler),
    (r"/room/create/", RoomCreateHandler),
    (r"/room/([0-9]+)/", RoomDetailHandler),
    (r"/room/([0-9]+)/view/", RoomViewHandler),
    (r"/room/random/", RoomRandomHandler),
    (r"/room/([0-9]+)/edit/", RoomEditHandler),
    (r"/room/([0-9]+)/delete/", RoomDeleteHandler),
    (r"/room/([0-9]+)/save/", RoomSaveHandler),
    (r"/room/([0-9]+)/like/", RoomLikeHandler),
]