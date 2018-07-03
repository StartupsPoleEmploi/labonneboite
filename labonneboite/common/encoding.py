# coding: utf8

import unidecode

def sanitize_string(s):
    """
    Returns a correctly decoded unicode from any given string

    Note that some of our data sources have very poor quality,
    and sometimes even mix different encodings
    """
    if isinstance(s, bytes):
        # the main optimistic case : UTF-8
        try:
            return s.decode('utf-8')
        except UnicodeDecodeError:
            pass
        # a trick to deal with french accents found in unknown encoding
        # removing \xa3 makes it utf-8
        # e.g.
        # é : \xc3\xa3\xa9 unknown encoding => \xc3\xa9 utf-8
        # à : \xc3\xa3\xa0 unknown encoding => \xc3\xa0 utf-8
        try:
            return s.replace('\xa3', '').decode('utf-8')
        except UnicodeDecodeError:
            pass
        # a special character often seen is the degree sign (e.g. in N°)
        # see http://www.codetable.net/hex/b0
        # which matches the latin1 encoding
        try:
            return s.decode('latin1')
        except UnicodeDecodeError:
            pass
        # last resort
        # 'ignore' will removed any unrecognized character
        return s.decode('utf-8', 'ignore')
    elif isinstance(s, str):
        return s
    elif s is None:
        return s # leave None value untouched
    raise Exception("not a string nor bytes nor None")


def strip_french_accents(u):
    """
    Remove french accents in unicode

    Useful to cleanup buggy emails and websites URLs which are found
    in our data sources
    e.g. frédéric@gmail.com becomes frederic@gmail.com

    Theoretically accented characters are perfectly acceptable in
    both emails and websites, e.g. read
    https://gmail.googleblog.com/2014/08/a-first-step-toward-more-global-email.html
    https://en.wikipedia.org/wiki/Internationalized_domain_name

    However, in practise our data (emails and websites) have poor quality
    and many human-typing mistakes. All the examples of websites with
    accented characters we could found were mistakes, the correct websites
    were obtained by stripping accents. This is why we keep this logic.
    """
    return unidecode.unidecode(u)
