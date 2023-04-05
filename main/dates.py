import calendar
import datetime
import logging

def eom():   
    today = datetime.date.today()
    first = today.replace(day=1)
    prevEOM = first - datetime.timedelta(days=1)
    logging.debug('Previous End of Month: ' + str(prevEOM))
    return prevEOM

def current_year(automatic_report=True, year=None):
    if automatic_report == True:
        current_year=int(eom().strftime("%Y"))
    elif automatic_report == False:
        current_year = year
    else:
        logging.error("Reporting year not correctly chosen!")
        exit()
    return current_year

def current_month(automatic_report=True, month=None):
    if automatic_report == True:
        current_month=int(eom().strftime("%m"))
    elif automatic_report == False:
        current_month = month
    else:
        logging.error("Reporting month not correctly chosen!")
        exit()
    return current_month

def days_in_month():
    days_in_month = calendar.monthrange(current_year(), current_month())[1]
    return days_in_month

def current_month_str():
    if len(str(current_month())) == 1:
        current_month_str = "0" + str(current_month())
    else:
        current_month_str = str(current_month())
    logging.info('Current month:' + current_month_str)
    return current_month_str

def current_year_str():
    current_year_str = str(current_year())
    logging.info('Current year:' + current_year_str)
    return current_year_str

def current_month_name():
    Méint = {
    "01": "Januar",
    "02": "Februar",
    "03": "Mäerz",
    "04": "Abrëll",
    "05": "Mee",
    "06": "Juni",
    "07": "Juli",
    "08": "August",
    "09": "September",
    "10": "Oktober",
    "11": "November",
    "12": "Dezember" 
    }
    current_month_name = Méint[current_month_str()]
    return current_month_name
