import logging

from main import dates as dt

def current_df(var, table):
  variable = table[(table['month'] == dt.current_month()) & (table['year'] == dt.current_year())][var]
  logging.debug(var + ": ")
  logging.debug(str(variable))
  return(variable)

def month_df(var, table):
  variable = table[table['month'] == dt.current_month()][var]
  logging.debug(var + ": ")
  logging.debug(str(variable))
  return(variable)