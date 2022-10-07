from csv import *  # noqa: F403


class excel_semi(excel):  # noqa: F405
    delimiter = ";"


register_dialect('excel-semi', excel_semi)  # noqa: F405
