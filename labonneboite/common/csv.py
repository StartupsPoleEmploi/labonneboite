from csv import *


class excel_semi(excel):
    delimiter = ";"

register_dialect('excel-semi', excel_semi)
