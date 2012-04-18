#!/usr/bin/env python
# coding: utf-8

import os
from tornado.options import define, options

class CONST(object):
    admin = 100
    host = 50
    partner = 40
    
    
def parse_config_file(path):
    """Rewrite tornado default parse_config_file.
    
    Parses and loads the Python config file at the given path.
    
    This version allow customize new options which are not defined before
    from a configuration file.
    """
    config = {}
    execfile(path, config, config)
    for name in config:
        if name in options:
            options[name].set(config[name])
        else:
            define(name, config[name])



def save_file(filepath, filename, content):
    if not os.path.exists(filepath):
        os.makedirs(filepath)
    f = open(filepath + filename, "w")
    f.write(content)
    f.close()

def save_doodle(room, filename, content):
    filepath = options.root_dir + "doodle/" + room +"/"
    save_file(filepath, filname, content)
    return filepath + filename


if __name__ == "__main__":
    save_file("1/2/3/", "1.png", "1234")