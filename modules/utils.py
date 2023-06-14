# coding: utf-8

import os 
from os import system, name

##################################################################################################################
# def colors
##################################################################################################################

def default_c(text):
    return f'\033[0m{text}\033[0m'

def white(text):
    return f'\033[97m{text}\033[0m'

def cyan(text):
    return f'\033[96m{text}\033[0m'

def magenta(text):
    return f'\033[95m{text}\033[0m'

def blue(text):
    return f'\033[94m{text}\033[0m'

def yellow(text):
    return f'\033[93m{text}\033[0m'

def green(text):
    return f'\033[92m{text}\033[0m'

def red(text):
    return f'\033[91m{text}\033[0m'

def black(text):
    return f'\033[90m{text}\033[0m'

##################################################################################################################
# clear shell screen
##################################################################################################################

def clear():
    # -----------------------------
    # for windows
    # -----------------------------
    if name == 'nt':
        system('cls')

    # -----------------------------
    # for mac and linux(here, os.name is 'posix')
    # -----------------------------
    else:
        system('clear')

##################################################################################################################
# expand local path
##################################################################################################################

def path_expander(path):

    path = os.path.expanduser(path)
    
    return path