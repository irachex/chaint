#!/usr/bin/env python
# coding: utf-8

import logging
import tornado.auth
import tornado.escape
import tornado.options
import tornado.web

from base import BaseHandler
from lib.doubanauth import DoubanMixin
from lib.weiboauth import WeiboMixin
from lib.utils import CONST


class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect(self.get_argument("next", "/"))


class AuthBaseHandler(BaseHandler):
    def prepare(self):
        self.cache_next()
        if self.current_user is not None:
            self.redirect(self.get_secure_cookie("next") or "/")
    
    def cache_next(self):
        next_url = self.get_argument("next", False)
        if next_url:
            self.set_secure_cookie("next", next_url)
        
    def create_user(self, id, site, site_id, access_key, access_secret,
                          name, icon, email=None, password=None):
        user = dict(id=id, site=site, site_id=site_id, access_key=access_key,
                    access_secret=access_key, name=name, icon=icon, email=email,
                    password=password)
        if id=="douban-iRachex":
            user["role"] = CONST.admin
        url = self.db.execute("""REPLACE INTO user
                           (id, site, site_id, access_key, access_secret,
                            name, icon, email, password, created) VALUES
                           (%s, %s, %s, %s, %s, %s, %s, %s, %s, UTC_TIMESTAMP())""",
                        id, site, site_id, access_key, access_secret,
                        name, icon, email, password)
        user["url"] = url
        self.set_secure_cookie("user", tornado.escape.json_encode(user))


class AuthLoginHandler(AuthBaseHandler):
    def get(self):
        self.render("login.html")
    

class GoogleAuthHandler(AuthBaseHandler, tornado.auth.GoogleMixin):
    @tornado.web.asynchronous
    def get(self):
        redirect = self.request.uri
        if self.get_argument("openid.mode", None):
            self.get_authenticated_user(self.async_callback(self._on_auth))
            return
        self.authenticate_redirect(callback_uri=redirect_uri)
    
    def _on_auth(self, user):
        if not user:
            raise tornado.web.HTTPError(500, "Google auth failed")
        self.set_secure_cookie("user", tornado.escape.json_encode(user))
        self.redirect(self.get_login_url())


class FacebookAuthHandler(AuthBaseHandler, tornado.auth.FacebookGraphMixin):
    @tornado.web.asynchronous
    def get(self):
        redirect = self.request.uri
        if self.get_argument("code", False):
            self.get_authenticated_user(
                redirect_uri=my_url,
                client_id=self.settings["facebook_api_key"],
                client_secret=self.settings["facebook_secret"],
                code=self.get_argument("code"),
                callback=self._on_auth)
            return
        self.authorize_redirect(redirect_uri=redirect,
                                client_id=self.settings["facebook_api_key"],
                                extra_params={"scope": "read_stream"})
    
    def _on_auth(self, user):
        if not user:
            raise tornado.web.HTTPError(500, "Facebook auth failed")
        self.set_secure_cookie("user", tornado.escape.json_encode(user))
        self.redirect(self.get_login_url())


class TwitterAuthHandler(AuthBaseHandler, tornado.auth.TwitterMixin):
    @tornado.web.asynchronous
    def get(self):
        redirect = self.request.host + self.request.uri
        if self.get_argument("oauth_token", None):
            self.get_authenticated_user(self.async_callback(self._on_auth))
            return
        self.authorize_redirect(callback_uri=redirect)

    def _on_auth(self, user):
        if not user:
            raise tornado.web.HTTPError(500, "Twitter auth failed")
        self.set_secure_cookie("user", tornado.escape.json_encode(user))
        self.redirect(self.get_login_url())


class DoubanAuthHandler(AuthBaseHandler, DoubanMixin):
    @tornado.web.asynchronous
    def get(self):
        redirect = self.request.uri
        try:
            if self.get_argument("oauth_token", None):
                self.get_authenticated_user(self.async_callback(self._on_auth))
                return
            self.authorize_redirect(callback_uri=redirect)
        except:
            raise tornado.web.HTTPError(500, "Douban auth failed")
    
    def _on_auth(self, user):
        if not user:
            raise tornado.web.HTTPError(500, "Douban auth failed")
        self.create_user(id="douban-"+user["uid"], site="douban", site_id=user["uid"], 
                         access_key=None, access_secret=None,
                         name=user["nickname"], icon=user["avatar"])
        self.redirect(self.get_login_url())
        
 
class WeiboAuthHandler(AuthBaseHandler, WeiboMixin):
    @tornado.web.asynchronous
    def get(self):
        redirect = self.request.protocol + "://"+ self.request.host + self.request.path
        if self.get_argument("code", False):
            self.get_authenticated_user(
                redirect_uri=redirect,
                client_id=self.settings["weibo_api_key"],
                client_secret=self.settings["weibo_secret"],
                code=self.get_argument("code"),
                callback=self.async_callback(self._on_auth))
            return
        self.authorize_redirect(redirect_uri=redirect,
                                client_id=self.settings["weibo_api_key"],
                                extra_params={"response_type": "code"})

    def _on_auth(self, user):
        if not user:
            raise tornado.web.HTTPError(500, "Weibo auth failed")
        self.create_user(id="weibo-"+unicode(user["id"]), site="weibo", site_id=user["id"], 
                         access_key=user.get("access_key"), access_secret=user.get("access_secret"),
                         name=user["screen_name"], icon=user["profile_image_url"])
        self.redirect(self.get_login_url())


handlers = [
    (r"/auth/login/", AuthLoginHandler),
    (r"/auth/logout/", AuthLogoutHandler),
    (r"/auth/douban/", DoubanAuthHandler),
    (r"/auth/weibo/", WeiboAuthHandler),
    (r"/auth/facebook/", FacebookAuthHandler),
    (r"/auth/twitter/", TwitterAuthHandler),
    (r"/auth/google/", GoogleAuthHandler),
]