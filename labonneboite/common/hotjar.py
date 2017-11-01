# coding: utf8
from .pro import user_is_pro

def get_hotjar_tag():
    if user_is_pro():
        return "conseiller"
    return "de"
