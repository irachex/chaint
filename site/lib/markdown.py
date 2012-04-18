#!/usr/bin/env python
# coding: utf-8

import re
import tornado.escape

escape = tornado.escape.xhtml_escape 
unescape = tornado.escape.xhtml_unescape

RE_LINK = re.compile(r"""(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\x80-\xff\s`!()\[\]{};:'".,<>?«»“”‘’]))""")
RE_SPACE = re.compile(r""" ( +)""")
RE_ENTER = re.compile(r"""(\n+)""")

RE_A = re.compile(r"<a[^>]+>|</a>")
RE_NBSP = re.compile(r"(&nbsp;)+")
RE_BR = re.compile(r"(<br/>)+")

def replace_space(match):
    return " "+len(match.groups()[0])*"&nbsp;"

def replace_enter(match):
	return len(match.groups()[0])*"<br/>"

def replace_link(match):
    g = match.groups()[0]
    if "." not in g:
        return g
    link = g
    if not link.startswith("http"):
        link = "http://%s" % link
    return """<a target="_blank" href="%s" rel="nofollow">%s</a>""" % (link, g)

def replace_a(match):
    return ""

def replace_nbsp(match):
    return (len(match.groups()[0])/6)*" "

def replace_br(match):
    return (len(match.groups()[0])/4)*"\n"


def markdown(content, escape=escape):
    if escape:
        content = escape(content)
    content = RE_LINK.sub(replace_link, content)
    content = RE_SPACE.sub(replace_space, content)
    content = RE_ENTER.sub(replace_enter, content)
    return content


def unmarkdown(content, unescape=unescape):
    content = RE_BR.sub(replace_br, content)
    content = RE_NBSP.sub(replace_nbsp, content)
    content = RE_A.sub(replace_a, content)
    if unescape:
        content = unescape(content)
    return content


if __name__ == "__main__":
    content = """
    

    <script>
	    alert(1);         
	</script>
    http://irachex.com"""

    print content
    print "-------------------------"
    mc = markdown(content)
    print mc
    print "-------------------------"
    print unmarkdown(mc)
