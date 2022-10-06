from csv import excel, register_dialect


class excel_semi(excel):
    delimiter = ";"


register_dialect('excel-semi', excel_semi)
