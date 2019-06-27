from collections import Counter
from os.path import abspath
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import imgkit
import datetime

MONTHS = [None,
          'Jan',
          'Fev',
          'Mars',
          'Avr',
          'Mai',
          'Juin',
          'Juill',
          'Aou',
          'Sep',
          'Oct',
          'Nov',
          'Dec']

path = abspath('charts.py')[:-9]+'images/'


def Pie(ordre, columns_str, df, title, name, a=None):
    col_of_interest = df[columns_str]
    occurences = col_of_interest.value_counts()
    labels_to_change = list(occurences.index)
    values = []
    labels = []
    for k in labels_to_change:
        values.append(occurences[k])
        labels.append('{} ({}) '.format(k, str(occurences[k])))
    plt.pie(values, labels=labels, autopct='%1.1f%%')
    plt.title(title, fontweight='bold')
    plt.savefig(path+ordre+'{}.png'.format(name))
    plt.clf()
    return None


def BoxPlot(ordre, columns_int, df, title, name, start=1):
    data = df[columns_int].dropna().tolist()
    stats = df[columns_int].describe().tolist()
    names_stat = ["Population", "Moyenne", "Ecart-Type",
                  'Min', 'Q1', 'Mediane', 'Q3', 'Max']
    plt.boxplot(data)
    for k in range(start, len(stats)):
        if k in range(3):  # Pop/Moyenne/Ecart-Type
            x = 0.6
            y = stats[-1]*(1-1./10*(k+1))
        else:
            x, y = 1.1, stats[k]
        plt.annotate('{} : {}'.format(
            names_stat[k], round(stats[k], 2)), (x, y))  # 'label : value'
    plt.title(title, fontweight='bold')
    plt.savefig(path+ordre+'{}.png'.format(name))
    plt.clf()
    return [title]+stats


def Graph(ordre, columns_date, df, title, name, time_type='week'):
    def get_label_date(date_tuple):  # en fonction du time type, return good label
        def get_start_and_end_date_from_calendar_week(year, calendar_week):
            try:
                calendar_week -= add_number_for_good_label[str(year)]
            except:
                None
            monday = datetime.datetime.strptime(
                f'{year}-{calendar_week}-1', "%Y-%W-%w").date()
            start_date_uk = (str(monday)).split("-")
            end_date_uk = (
                str(monday + datetime.timedelta(days=6.9))).split("-")
            start_date_uk.reverse()
            end_date_uk.reverse()
            start_date = "-".join(start_date_uk)
            end_date = "-".join(end_date_uk)

            return "{} \n {}".format(start_date, end_date)

        if time_type == 'month':
            label = "{} / {}".format(date_tuple[1], date_tuple[0])
        elif time_type == 'year':
            label = "{}".format(date_tuple[0])
        else:
            label = get_start_and_end_date_from_calendar_week(
                date_tuple[0], date_tuple[1])
        return label

    dates_str = df[columns_date].tolist()
    date = []

    for i in dates_str:
        if time_type == 'week':
            Timestamp = pd.to_datetime(i, format='%Y-%m-%d')
            date.append(datetime.datetime.isocalendar(Timestamp)[:-1])
        else:
            Year = int(i[:4])
            Month = int(i[5:7])
            date.append((Year, Month))
    DPAE = Counter(date)
    blok = False
    tri_compt = 1
    current_year = (datetime.datetime.now().year)+1
    year = []
    year_count = 2018
    while year_count != current_year:
        year.append(str(year_count))
        year_count += 1
    add_number_for_good_label = {}
    for annee in year:  # Si decembre dans semaine 1 : enlever 1 pour repasser en label
        first_week = get_label_date((annee, 0))
        if time_type == 'week' and '12' in first_week.split('-')[1]:
            add_number_for_good_label[annee] = 1
        else:
            add_number_for_good_label[annee] = 0
    year_compt = 0
    x = []
    len_sheet = 0
    while blok == False:
        if time_type != 'week':
            blok = True
        if tri_compt == 5:
            year_compt += 1
            tri_compt = 1
        if year_compt == len(year):
            return len_sheet
        for year_month_week in DPAE:
            if (year_month_week[1] <= tri_compt*13 and year_month_week[1] >= (tri_compt-1)*13 and str(year_month_week[0]) == str(year[year_compt])) or blok == True:
                x.append(year_month_week)
        x.sort()
        y = [DPAE[When] for When in x]
        i = 0
        for elem in x:
            x[i] = get_label_date(elem)
            i += 1
        plt.plot(x, y, "b")
        plt.plot(x, y, "ro")
        for i in range(len(y)):
            plt.annotate(str(y[i]), (x[i], y[i]))
        plt.grid()
        if time_type == 'week':
            title_good = 'Trimestre '+str(tri_compt)+' '+year[year_compt]+title
        else:
            title_good = title
        plt.title(title_good, fontweight='bold')
        plt.xticks(fontsize=8, rotation=315)

        plt.ylim(0, max(DPAE.values())+100)
        if x != []:
            plt.savefig(path+ordre+'{}.png'.format(name +
                                                   str(year_compt)+str(tri_compt)))
            len_sheet += 1
        plt.clf()
        tri_compt += 1
        x = []


def Stacked_Bar(ordre, columns_x, df, titles, name, columns_legend):
    def Table(ordre, columns_x, df, name, columns_y):
        dates_x = df[columns_x].tolist()
        dates_y = df[columns_y].tolist()
        all_dates = [dates_x, dates_y]
        all_dates_good_format = []
        for axis in all_dates:  # Good formatting
            dates_axis_good = []
            for date in axis:
                Year = date[2:4]
                Month = date[5:7]
                if len(Year) == 1:
                    Month = '0'+Month
                dates_axis_good.append('{}-{}'.format(Year, Month))
            all_dates_good_format.append(dates_axis_good)
        dates_x_good = all_dates_good_format[0]
        dates_y_good = all_dates_good_format[1]

        corresp_x_y = {} #Association of each y value with x value
        x_occurences = Counter(dates_x_good)
        for date_unic in x_occurences:
            corresp_x_y[date_unic] = {}
            for i in range(len(dates_x_good)):
                if dates_x_good[i] == date_unic:
                    if dates_y_good[i] in corresp_x_y[date_unic]:
                        corresp_x_y[date_unic][dates_y_good[i]] += 1
                    else:
                        corresp_x_y[date_unic][dates_y_good[i]] = 1

        last_column = {}
        last_row = {}
        import ipdb; ipdb.set_trace()
        for x_label in corresp_x_y:
            last_column[x_label] = 0
            for y_label in corresp_x_y[x_label]:
                last_row[y_label] = 0
                for x_label_bis in corresp_x_y:
                    try:
                        last_row[y_label] += corresp_x_y[x_label_bis][y_label]
                    except:
                        None
                last_column[x_label] += corresp_x_y[x_label][y_label]
        for dates_x_bis in last_column:
            for dates_leg_bis in last_row:
                if not dates_leg_bis in corresp_x_y[dates_x_bis]:
                    corresp_x_y[dates_x_bis][dates_leg_bis] = 0

        corresp_x_y[titles[0]] = last_row
        for i in corresp_x_y:
            try:
                corresp_x_y[i][titles[1]] = last_column[i]
            except:
                corresp_x_y[i][titles[1]] = sum(last_column.values())
        list_month = list(corresp_x_y.keys())
        tri_month = sorted(list_month)
        Table_1 = pd.DataFrame.from_dict(corresp_x_y)
        Table_2 = Table_1[tri_month]
        Table_Final_1 = Table_2.transpose()

        css = """
        <style type=\"text/css\">
        table {
        color: #333;
        font-family: Helvetica, Arial, sans-serif;
        width: 1500px;
        text-align: center;
        border-collapse:
        collapse; 
        border-spacing: 0;
        }

        td, th {
        border: 1px solid transparent; /* No more visible border */
        height: 75px;
        text-align: center;
        }

        th {
        background: #DFDFDF; /* Darken header a bit */
        font-weight: bold;
        text-align: center;
        }

        td {
        background: #FAFAFA;
        text-align: center;
        }

        table tr:nth-child(odd) td{
        background-color: white;
        text-align: center;
        }
        </style>
        """
        with open("filename.html", "w") as text_file:
            # write the CSS
            text_file.write(css)
        # write the HTML-ized Pandas DataFrame
            text_file.write(Table_Final_1.to_html())
        imgkitoptions = {"format": "png", "xvfb": ""}
        imgkit.from_file("filename.html", '{}_table.png'.format(
            path+ordre+name), options=imgkitoptions)
        import ipdb; ipdb.set_trace()
        return Table_Final_1

    Cohorte = Table(ordre, columns_x, df, name, columns_legend)
    N = len(Cohorte.index)-1
    ind = np.arange(N)
    liste_for_legend = []
    bottom = np.zeros(N)
    for colonne in Cohorte.columns[:-1]:
        values = Cohorte[colonne][:-1].tolist()
        p = plt.bar(ind, values, 0.75, bottom=bottom)
        liste_for_legend.append(p)
        for i in range(len(bottom)):
            bottom[i] += values[i]
    name_x = []
    for x in Cohorte.index:
        try:
            name_x.append(MONTHS[int(x[3:])]+'-'+x[:2])
        except:
            None

    color_legend = [p[0] for p in liste_for_legend]
    name_legend = [MONTHS[int(month[3:])]+'-'+month[:2]
                   for month in Cohorte.columns[:-1]]
    plt.legend(color_legend, name_legend, title=titles[2], loc=0)
    plt.xticks(ind, name_x, rotation=315, fontsize=8)
    plt.xlabel(titles[3], verticalalignment="baseline", fontweight='bold')
    plt.title(titles[4], fontweight='bold')
    plt.savefig(path+ordre+name+".png")
    plt.clf()


def graph_sql(ordre, columns_y, df, title, name, columns_x):
    y = df[columns_y].tolist()
    x = df[columns_x].tolist()
    plt.plot(x, y, "g")
    plt.plot(x, y, "yo")
    for i in range(len(y)):
        plt.annotate(str(y[i]), (x[i], y[i]))
    plt.grid()
    plt.title(title, fontweight='bold')
    plt.xticks(fontsize=8, rotation=315)
    plt.ylim(0, plt.axis()[3])
    plt.savefig(path+ordre+'{}.png'.format(ordre+name))
    plt.clf()