from .pro import user_is_pro


def get_tags(tag):
    if tag not in ["faq", "help", "press", "results"]:
        raise Exception("unknown page")
    if user_is_pro():
        return ["conseiller", tag]
    return ["de", tag]
