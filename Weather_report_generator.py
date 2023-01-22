'''HTML weather report creator using PEGE_DB sqlite database'''
'''Version 0.3.0'''
#Modules
import sqlite3
import datetime
import calendar
from datetime import date
import pandas as pd
from urllib.request import urlopen
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import io
import base64
from math import isnan
import os



'''-------------------------------------------------------------------------------------------
--------------------------- Table of contents ----------------------------------------------
----------------------------------------------------------------------------------------------

   0 - Script filters

   1 - Define Report Period
   
   2 - Connect to DB
   
   3 - Prepare Dataframe
   
   4 - Extract temperatures data

-------------------------------------------------------------------------------------------'''

'''-------------------------------------------------------------------------------------------
------------------------------- 0 - Script filters -------------------------------------------
-------------------------------------------------------------------------------------------'''

# Indicate if local run or on synology NAS
synology = True

automatic_report = 1 # If 1 automatic report dates, if 0 manual report dates
manual_year = 2019 # Integer between 2019-202x
manual_month = 9 # Integer between 1-12

'''-------------------------------------------------------------------------------------------
------------------------- 1 - Define Report Period -------------------------------------------
-------------------------------------------------------------------------------------------'''
# Returns the current local date
today = datetime.date.today()
# Get first day of current month
first = today.replace(day=1)
# Substract one day to get to last day of previous month
prevEOM = first - datetime.timedelta(days=1)

if automatic_report == 1:
    currentyear=int(prevEOM.strftime("%Y"))
    currentmonth=int(prevEOM.strftime("%m"))
elif automatic_report == 0:
    currentyear = manual_year
    currentmonth = manual_month
else:
    print("Reporting period not correctly chosen!")
    exit()

print("1 - Report period defined")

'''-------------------------------------------------------------------------------------------
------------------------- 2 - Connect to DB --------------------------------------------------
-------------------------------------------------------------------------------------------'''
if synology == True:
    mainPath = "/volume1/python_scripts/WeatherReport"
    dataPath = "/volume1/python_scripts/WeatherReport/Data"
else:
    mainPath = r"C:\Users\neo_1\Dropbox\Projects\Programing\WeatherReport"
    dataPath = r"C:\Users\neo_1\Dropbox\Projects\Programing\WeatherReport\Data"
    reportPath = r"C:\Users\neo_1\Dropbox\Projects\Programing\WeatherReport\Reports"

DB='pege_froggit_weather_stats.sqlite'

dataFilepath = os.path.join(dataPath, DB)

try:
    # Create connection to database
    conn = sqlite3.connect(dataFilepath)
    print("2 - Connection to DB "+DB+" successful")
except:
    print("Connection to DB "+DB+" failed")

conf_file = "confidential.txt"

conf_path = os.path.join(mainPath, conf_file)

# Add items from confidential file to list
confidential = []
with open(conf_path) as f:
    for line in f:
        confidential.append(line.replace("\n",""))

# E-Mail recipient(s)
PJ = confidential[2]

'''-------------------------------------------------------------------------------------------
------------------------- 3 - Prepare Dataframes ----------------------------------------------
-------------------------------------------------------------------------------------------'''

# Get number of days in current month
days_in_month = calendar.monthrange(currentyear, currentmonth)[1]

# Report period (add 0 to single digit months)
if len(str(currentmonth))==1:
    currentmonthstr="0"+str(currentmonth)
else:
    currentmonthstr=str(currentmonth)
currentyearstr=str(currentyear)

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

currentmonthname = Méint[currentmonthstr]

reportPeriod=currentyearstr+"-"+currentmonthstr
reportPeriodName=currentmonthname+" "+currentyearstr


'''-------------------------------------------------------------------------------------------
------------------- x - Prepare MeteoLux dataframes - WIP ----------------------------------------------
-------------------------------------------------------------------------------------------'''


# Monthly meteorological parameters - Luxembourg/Findel Airport (WMO ID 06590)
# https://data.public.lu/fr/datasets/monthly-meteorological-parameters-luxembourg-findel-airport-wmo-id-06590/
'''
MYT (°C): MONTHLY MEAN AIR TEMPERATURE AT 2 M
MMR06_06 (mm): MONTHLY AMOUNT OF PRECIPITATION
MINS (h): MONTHLY SUNSHINE DURATION BY OBSERVER
MYP (hPa): MONTHLY MEAN ATMOSPHERIC PRESSURE AT FIELD / AERODROME ELEVATION (QFE)
MYPSL (hPa): MONTHLY MEAN ATMOSPHERIC PRESSURE REDUCED TO MEAN SEA LEVEL (QFF)'''

mmp="https://data.public.lu/fr/datasets/r/b096cafb-02bb-46d0-9fc0-5f63f0cbad98"

mmp_df = pd.read_fwf(mmp, encoding='latin-1')

# Columns needed to be renamed because wrongly split in source file
mmp_df['MYT (°C)']=mmp_df['(°C)']
mmp_df['MMR06_06 (mm)']=mmp_df['(mm)']
mmp_df['MINS (h)']=mmp_df['MINS (h)']
mmp_df = mmp_df[['Year', 'Month','MYT (°C)','MMR06_06 (mm)','MINS (h)']]

# Daily meteorological parameters - Luxembourg/Findel Airport (WMO ID 06590)
# https://data.public.lu/fr/datasets/daily-meteorological-parameters-luxembourg-findel-airport-wmo-id-06590/
dmp = "https://data.public.lu/fr/datasets/r/a67bd8c0-b036-4761-b161-bdab272302e5"

dmp_df = pd.read_csv(dmp, encoding = 'ISO-8859-1')
dmp_df['Day'] = dmp_df['DATE'].str[0:2].astype(int)
dmp_df['Month'] = dmp_df['DATE'].str[3:5].astype(int)
dmp_df['Year'] = dmp_df['DATE'].str[6:10].astype(int)
dmp_df = dmp_df[['Year', 'Month', 'Day', 'DXT (°C)', 'DNT (°C)', 'DRR06_06 (mm)']]

# Meteorological extreme parameters since 1947 - Luxembourg/Findel Airport (WMO ID 06590)
# https://data.public.lu/fr/datasets/meteorological-extreme-parameters-since-1947-luxembourg-findel-airport-wmo-id-06590/

mep = "https://data.public.lu/fr/datasets/r/daf945e9-58e9-4fea-9c1a-9b933d6c8b5e"

mep_df = pd.read_csv(mep, encoding = 'ISO-8859-1', sep = ';')
mep_df_transposed = mep_df.T
mep_df = pd.melt(mep_df, id_vars = 'MONTH', value_vars = ['JAN', 'FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']) 

print("3 - Dataframes created")

'''-------------------------------------------------------------------------------------------
------------------------- 4 - Extract temperatures data --------------------------------------
-------------------------------------------------------------------------------------------'''
# Daily temps WIP
daily_temp_df = pd.read_sql_query("SELECT year, month, day, temp_min, temp_max, temp_avg from daily_stats", conn)

daily_min_temp = daily_temp_df[(daily_temp_df['month'] == currentmonth) & (daily_temp_df['year'] == currentyear)]['temp_min']
daily_max_temp = daily_temp_df[(daily_temp_df['month'] == currentmonth) & (daily_temp_df['year'] == currentyear)]['temp_max']
daily_avg_temp = daily_temp_df[(daily_temp_df['month'] == currentmonth) & (daily_temp_df['year'] == currentyear)]['temp_avg']

# Meteolux data

ml_daily_avg_temp = mmp_df[(mmp_df['Month'] == currentmonth) & (mmp_df['Year'] == currentyear)]['MYT (°C)']

# In case of multiple values, loop through series (WIP: make conditional on data type)
for i in ml_daily_avg_temp:
  ml_daily_avg_temp = i

x = daily_temp_df[(daily_temp_df['month'] == currentmonth) & (daily_temp_df['year'] == currentyear)]['day']

plot_title = "Temperaturschwankungen " + currentmonthname + " " + currentyearstr
font = {'family':'verdana','color':'white'}
def temp_plot():
  plt.figure(0)
  plt.title(plot_title)
  plt.xlabel("Dag", fontdict = font)
  plt.ylabel("Temperatur (° C)", fontdict = font)
  #plt.figure(facecolor='#001E34')
  plt.plot(x, daily_max_temp,marker = '^', label = 'Maximum', color='red')
  plt.plot(x, daily_avg_temp,marker = 'o', label = 'Moyenne', color='black')
  plt.plot(x, daily_min_temp,marker = 'v', label = 'Minimum', color='blue')
  plt.legend()
  plt.xticks(rotation = 45)
  plt.grid(color = '#001E34', linestyle = '--')
  my_stringIObytes = io.BytesIO()
  plt.savefig(my_stringIObytes, format='jpg', bbox_inches="tight")
  my_stringIObytes.seek(0)
  my_base64_tempData = base64.b64encode(my_stringIObytes.read())
  my_base64_tempData = my_base64_tempData.decode("utf-8") 
  my_base64_tempData = my_base64_tempData+'"'
  return(my_base64_tempData)

temp_chart = temp_plot()

# Monthly extremes (PROD ready)
temp_df = pd.read_sql_query("SELECT * from temp_stats_monthly", conn)

firstPeriod = str(temp_df['yearMonth'].min())
lastPeriod = str(temp_df['yearMonth'].max())

# Functions on temp_df
def current_temp_df(var):
  variable = temp_df[(temp_df['month'] == currentmonth) & (temp_df['year'] == currentyear)][var]
  return(variable)

def month_temp_df(var):
  variable = temp_df[temp_df['month'] == currentmonth][var]
  return(variable)

def temp_tile(tile_title,avg, avg_year, min, min_year, max, max_year):
  tile_content = """<div class="tile">
      <div class="tileTitle">
        """ + tile_title + """
      </div>
      <div class="tileContent">
          <div class="tileMainFont"> """ + avg + """ °C""" + avg_year + """
          </div>
          <div class="tileLeftSub">
              <div class="redArrow">&#8711;</div>
              <div class="extremeValue"> """ + min + """ °C""" + min_year + """</div>
          </div>
          <div class="tileRightSub">
              <div class="greenArrow">&#8710;</div>
              <div class="extremeValue">  """ + max + """ °C""" + max_year + """</div>
          </div>
      </div>
  </div>"""
  return(tile_content)

# Temp extremes current reporting period
min_temp_rp = str(round(float(current_temp_df('min_temp_m')),1))
max_temp_rp = str(round(float(current_temp_df('max_temp_m')),1))
avg_temp_rp = str(round(float(current_temp_df('avg_temp_m')),1))

current_temp_tile = temp_tile("Temperatur " + str(reportPeriod),avg_temp_rp, "", min_temp_rp, "", max_temp_rp, "")

# Average temp extremes current reporting period month
avg_min_temp_m = str(round(month_temp_df('min_temp_m').mean(),1))
avg_avg_temp_m = str(round(month_temp_df('avg_temp_m').mean(),1))
avg_max_temp_m = str(round(month_temp_df('max_temp_m').mean(),1))

# Minimum temp extremes current reporting period month
min_temp_m = str(round(month_temp_df('min_temp_m').min(),1))
min_temp_m_row = month_temp_df('min_temp_m').idxmin()
min_temp_m_year = str(int(temp_df.loc[min_temp_m_row,['year']]))


# Maximum temp extremes current reporting period month
max_temp_m = str(round(month_temp_df('max_temp_m').max(),1))
max_temp_m_row = month_temp_df('max_temp_m').idxmax()
max_temp_m_year = str(int(temp_df.loc[max_temp_m_row,['year']]))

month_ext_temp_tile = temp_tile("Extremwäerter " + str(currentmonthname) + " - Pege Froggit", avg_avg_temp_m, "", min_temp_m, " ("+min_temp_m_year+")", max_temp_m, " ("+max_temp_m_year+")")

# Average temp extremes current reporting period month
min_avg_temp_m = str(round(month_temp_df('avg_temp_m').min(),1))
min_avg_temp_m_row = month_temp_df('avg_temp_m').idxmin()
min_avg_temp_m_year = str(int(temp_df.loc[min_avg_temp_m_row,['year']]))

max_avg_temp_m = str(round(month_temp_df('avg_temp_m').max(),1))
max_avg_temp_m_row = month_temp_df('max_temp_m').idxmax()
max_avg_temp_m_year = str(int(temp_df.loc[max_avg_temp_m_row,['year']]))

# Meteolux temp extremes current reporting period month

def month_dmp_df(var):
  variable = dmp_df[dmp_df['Month'] == currentmonth][var]
  return(variable)

def month_mmp_df(var):
  variable = mmp_df[mmp_df['Month'] == currentmonth][var]
  return(variable)

ml_avg_min_temp_m = str(round(month_dmp_df('DNT (°C)').mean(),1))
ml_avg_avg_temp_m = str(round(month_mmp_df('MYT (°C)').mean(),1))
ml_avg_max_temp_m = str(round(month_dmp_df('DXT (°C)').mean(),1))

ml_min_temp_m = str(round(float(month_dmp_df('DNT (°C)').min()),1))
ml_min_temp_m_row = month_dmp_df('DNT (°C)').idxmin()
ml_min_temp_m_year = str(int(dmp_df.loc[ml_min_temp_m_row,['Year']]))

ml_max_temp_m = str(round(float(month_dmp_df('DXT (°C)').max()),1))
ml_max_temp_m_row = month_dmp_df('DXT (°C)').idxmax()
ml_max_temp_m_year = str(int(dmp_df.loc[ml_max_temp_m_row,['Year']]))

ml_min_avg_temp_m = str(round(float(month_mmp_df('MYT (°C)').min()),1))
ml_min_avg_temp_m_row = month_mmp_df('MYT (°C)').idxmin()
ml_min_avg_temp_m_year = str(int(mmp_df.loc[ml_min_avg_temp_m_row,['Year']]))

ml_max_avg_temp_m = str(round(float(month_mmp_df('MYT (°C)').max()),1))
ml_max_avg_temp_m_row = month_mmp_df('MYT (°C)').idxmax()
ml_max_avg_temp_m_year = str(int(mmp_df.loc[ml_max_avg_temp_m_row,['Year']]))

ml_month_ext_temp_tile = temp_tile("Extremwäerter " + str(currentmonthname) + " - Meteolux", ml_avg_avg_temp_m, "", ml_min_temp_m, " ("+ml_min_temp_m_year+")", ml_max_temp_m, " ("+ml_max_temp_m_year+")")

# Number of days per temp category
def temp_days(columnName, luxName):
  if int(current_temp_df(columnName)) != 0:
    htmlName = """<div class="tileMainFont">""" + str(int(current_temp_df(columnName))) + """ """+luxName+"""</div>"""
  else:
    htmlName = """"""
  return(htmlName)

WüstentageHTML = temp_days('wuestentage', 'Wüstendeeg')
TropennächteHTML = temp_days('tropennaechte', 'Tropennuechten')
HeißeTageHTML = temp_days('heisseTage', 'Waarm Deeg')
SommertageHTML = temp_days('sommertage', 'Summerdeeg')
VegetationstageHTML = temp_days('vegetationstage', 'Vegetatiounsdeeg')
FrosttageHTML = temp_days('frosttage', 'Fraschtdeeg')
EistageHTML = temp_days('eistage', 'Äisdeeg')

extremeTempHTML = """   				<div class="tile">
					<div class="tileTitle">
					  Kenndeeg
					</div>
					<div class="tileContent">
						 """ + WüstentageHTML + """
						 """ + TropennächteHTML + """
						 """ + HeißeTageHTML + """
						 """ + SommertageHTML + """
						 """ + VegetationstageHTML + """
						 """ + FrosttageHTML + """
						 """ + EistageHTML + """
					</div>
				</div>"""

print("4 - Temperatures data retrieved")

'''-------------------------------------------------------------------------------------------
------------------------- 5 - Extract rain data ----------------------------------------------
-------------------------------------------------------------------------------------------'''
rain_df = pd.read_sql_query("SELECT * from rain_stats_monthly", conn)

firstPeriod = str(rain_df['yearMonth'].min())
lastPeriod = str(rain_df['yearMonth'].max())


# Functions on rain_df
def current_rain_df(var):
  variable = rain_df[(rain_df['month'] == currentmonth) & (rain_df['year'] == currentyear)][var]
  return(variable)

def month_rain_df(var):
  variable = rain_df[rain_df['month'] == currentmonth][var]
  return(variable)

def rain_tile(tile_title, var, avg, avg_year, min, min_year, max, max_year):
  tile_content = """
				<div class="tile">
					<div class="tileTitle">
					  """ + tile_title + """
					</div>
                    <div class="tileContent">
                        <div class="tileMainFont"> """ + avg + var + avg_year + """
                        </div>
                        <div class="tileLeftSub">
                            <div class="redArrow">&#8711;</div>
                            <div class="extremeValue"> """ + min + var + min_year + """</div>
                        </div>
                        <div class="tileRightSub">
                            <div class="greenArrow">&#8710;</div>
                            <div class="extremeValue">  """ + max + var + max_year + """</div>
                        </div>
                    </div>
				</div>"""

  
  return(tile_content)

# Rain extremes current reporting period
sum_rain_rp = str(round(int(current_rain_df('max_rain_m')),1))

# Average rain current reporting period month
avg_max_rain_m = str(round(month_rain_df('max_rain_m').mean(),1))

# Minimum rain extremes current reporting period month
min_rain_m = str(round(month_rain_df('max_rain_m').min(),1))
min_rain_m_row = month_rain_df('max_rain_m').idxmin()
min_rain_m_year = str(int(rain_df.loc[min_rain_m_row,['year']]))

# Maximum rain extremes current reporting period month
max_rain_m = str(round(month_rain_df('max_rain_m').max(),1))
max_rain_m_row = month_rain_df('max_rain_m').idxmax()
max_rain_m_year = str(int(rain_df.loc[max_rain_m_row,['year']]))

qty_rain_tile = rain_tile("Reenquantitéit "+currentmonthname+" - Pege Froggit", " l/m2", avg_max_rain_m, "",min_rain_m, " ("+min_rain_m_year+")", max_rain_m, " ("+max_rain_m_year+")")

# Rainy Days
rain_days_rp = str(round(current_rain_df('rainy_days').max(),1))

# Minimum rain days current reporting period month
min_rain_days_m = str(round(month_rain_df('rainy_days').min(),1))
min_rain__days_m_row = month_rain_df('rainy_days').idxmin()
min_rain_days_m_year = str(int(rain_df.loc[min_rain__days_m_row,['year']]))

# Maximum rain days current reporting period month
max_rain_days_m = str(round(month_rain_df('rainy_days').max(),1))
max_rain_days_m_row = month_rain_df('rainy_days').idxmax()
max_rain_days_m_year = str(int(rain_df.loc[max_rain_days_m_row,['year']]))

# Average rain days current reporting period month
avg_max_rain_days_m = str(round(month_rain_df('rainy_days').mean(),1))

days_rain_tile = rain_tile("Reendeeg "+currentmonthname+" - Pege Froggit", " Deeg", avg_max_rain_days_m, "",min_rain_days_m, " ("+min_rain_days_m_year+")", max_rain_days_m, " ("+max_rain_days_m_year+")")

# Meteolux
# Rain quantity
ml_avg_rain_m = str(round(month_mmp_df('MMR06_06 (mm)').mean(),1))

ml_min_rain_m = str(month_mmp_df('MMR06_06 (mm)').min())
ml_min_rain_m_row = month_mmp_df('MMR06_06 (mm)').idxmin()
ml_min_rain_m_year = str(int(mmp_df.loc[ml_min_rain_m_row,['Year']]))

ml_max_rain_m = str(month_mmp_df('MMR06_06 (mm)').max())
ml_max_rain_m_row = month_mmp_df('MMR06_06 (mm)').idxmax()
ml_max_rain_m_year = str(int(mmp_df.loc[ml_max_rain_m_row,['Year']]))

ml_qty_rain_tile = rain_tile("Reenquantitéit "+currentmonthname+" - Meteolux", " l/m2", ml_avg_rain_m, "",ml_min_rain_m, " ("+ml_min_rain_m_year+")", ml_max_rain_m, " ("+ml_max_rain_m_year+")")

# Rain days
# Loop through each year-month pair
Years = dmp_df['Year'].unique()

rain_days = {}
sum_rain_days = 0

for year in Years:
    # Retrieve number of rainy days for current month for each year
    temp_dmp_df = dmp_df[dmp_df['Month'] == currentmonth][dmp_df['Year'] == year]
    rainy_days = 0
    day = 1
    while day <= days_in_month:
      if temp_dmp_df[temp_dmp_df['Day'] == day]['DRR06_06 (mm)'].max() > 0:
          rainy_days = rainy_days + 1
      day = day + 1
    rain_days[year]=rainy_days
    sum_rain_days = sum_rain_days + rainy_days
    year = year + 1 


ml_avg_rain_days_m = str(round(sum_rain_days / len(rain_days),0))

ml_max_rain_days_keys = [key for key, value in rain_days.items() if value == max(rain_days.values())]
ml_max_rain_days_m = str(rain_days[ml_max_rain_days_keys[0]])
ml_max_rain_days_m_year = str(ml_max_rain_days_keys[0])

ml_min_rain_days_keys = [key for key, value in rain_days.items() if value == min(rain_days.values())]
ml_min_rain_days_m = str(rain_days[ml_min_rain_days_keys[0]])
ml_min_rain_days_m_year = str(ml_min_rain_days_keys[0])

ml_days_rain_tile = rain_tile("Reendeeg "+currentmonthname+" - Meteolux", " Deeg", ml_avg_rain_days_m, "",ml_min_rain_days_m, " ("+ml_min_rain_days_m_year+")", ml_max_rain_days_m, " ("+ml_max_rain_days_m_year+")")

print("5 - Rain data retrieved")


'''-------------------------------------------------------------------------------------------
------------------------- 6 - Extract sun data ----------------------------------------------
-------------------------------------------------------------------------------------------'''
sun_df = pd.read_sql_query("SELECT * from sun_stats_monthly", conn)

firstPeriod = str(sun_df['yearMonth'].min())
lastPeriod = str(sun_df['yearMonth'].max())


# Functions on sun_df
def current_sun_df(var):
  variable = sun_df[(sun_df['month'] == currentmonth) & (sun_df['year'] == currentyear)][var]
  return(variable)

def month_sun_df(var):
  variable = sun_df[sun_df['month'] == currentmonth][var]
  return(variable)

def sun_tile(tile_title, var, avg, avg_year, min, min_year, max, max_year):
  tile_content = """
				<div class="tile">
					<div class="tileTitle">
					  """ + tile_title + """
					</div>
                    <div class="tileContent">
                        <div class="tileMainFont"> """ + avg + var + avg_year + """
                        </div>
                        <div class="tileLeftSub">
                            <div class="redArrow">&#8711;</div>
                            <div class="extremeValue"> """ + min + var + min_year + """</div>
                        </div>
                        <div class="tileRightSub">
                            <div class="greenArrow">&#8710;</div>
                            <div class="extremeValue">  """ + max + var + max_year + """</div>
                        </div>
                    </div>
				</div>"""

  
  return(tile_content)


# Sun extremes current reporting period
sum_sun_rp = str(round(int(current_sun_df('sunshine_hours_m')),1))
print(sum_sun_rp)

# Average sun current reporting period month
avg_sun_m = str(round(month_sun_df('sunshine_hours_m').mean(),1))

# Minimum sun extremes current reporting period month
min_sun_m = str(round(month_sun_df('sunshine_hours_m').min(),1))
min_sun_m_row = month_sun_df('sunshine_hours_m').idxmin()
min_sun_m_year = str(int(sun_df.loc[min_sun_m_row,['year']]))

# Maximum sun extremes current reporting period month
max_sun_m = str(round(month_sun_df('sunshine_hours_m').max(),1))
max_sun_m_row = month_sun_df('sunshine_hours_m').idxmax()
max_sun_m_year = str(int(sun_df.loc[max_sun_m_row,['year']]))

qty_sun_tile = sun_tile("Sonnenstonnen "+currentmonthname+" - Pege Froggit", " Stonnen", avg_sun_m, "",min_sun_m, " ("+min_sun_m_year+")", max_sun_m, " ("+max_sun_m_year+")")

# Meteolux
# Sun quantity
ml_avg_sun_m = str(round(month_mmp_df('MINS (h)').mean(),1))

ml_min_sun_m = str(month_mmp_df('MINS (h)').min())
ml_min_sun_m_row = month_mmp_df('MINS (h)').idxmin()
ml_min_sun_m_year = str(int(mmp_df.loc[ml_min_sun_m_row,['Year']]))

ml_max_sun_m = str(month_mmp_df('MINS (h)').max())
ml_max_sun_m_row = month_mmp_df('MINS (h)').idxmax()
ml_max_sun_m_year = str(int(mmp_df.loc[ml_max_sun_m_row,['Year']]))

ml_qty_sun_tile = sun_tile("Sonnenstonnen "+currentmonthname+" - Meteolux", " Stonnen", ml_avg_sun_m, "",ml_min_sun_m, " ("+ml_min_sun_m_year+")", ml_max_sun_m, " ("+ml_max_sun_m_year+")")

print("6 - Sun data retrieved")

'''-------------------------------------------------------------------------------------------
------------------------- 7 - Extract wind data ----------------------------------------------
-------------------------------------------------------------------------------------------'''




# print("7 - Wind data retrieved")

'''-------------------------------------------------------------------------------------------
------------------------- 10 - Prepare report ------------------------------------------------
-------------------------------------------------------------------------------------------'''

# Report file name
reportName="Wieder Rapport Kautebaach"
reportFileName="Wieder Rapport "+reportPeriod+".html"

templateFilepath = os.path.join(mainPath, 'Templates/css.txt')

css_file = open(templateFilepath, 'r')
css = css_file.read()

html = """\
<html>
  <head>
      <title>"""+reportName+" "+reportPeriodName+"""</title>
      <style>
            """+css+"""
      </style>
  </head>
  <body>
		<div class="container">
			<div class="titleBar">
        <p class="titleFont">"""+reportName+"""</p>
        <p class="titleSub">"""+reportPeriodName+"""</p>
		  </div>
			<div class="chapterHeader">1 - Résumé</div>
			<div class="chapterContainer">
				""" + current_temp_tile + """
				<div class="tile">
					<div class="tileTitle">
					  Reen
					</div>
					<div class="tileContent">
						<div class="tileMainFont">""" + sum_rain_rp + """ l/m2</div>
						<div class="tileMainFont">""" + rain_days_rp + """ Reendeeg</div>
					</div>
				</div>
				<div class="tile">
					<div class="tileTitle">
					  Sonn
					</div>
					<div class="tileContent">
						<div class="tileMainFont">""" + sum_sun_rp + """ Stonnen</div>
					</div>
				</div>
      </div>
      <div class="chapterHeader">2 - Temperatur</div>
			<div class="chapterContainer">
            """ + current_temp_tile + month_ext_temp_tile + ml_month_ext_temp_tile +  extremeTempHTML + """
              <div class="tileContent">
                <div>
                  <img src="data:image/png;base64,""" + temp_chart + """/>
                </div>
              </div>
          <br>
          <br>
      </div> 
      <div>
      <div class="chapterHeader">3 - Reen</div>
			<div class="chapterContainer">
            """+ qty_rain_tile + """
            """+ ml_qty_rain_tile + """
            """+ days_rain_tile + """
            """+ ml_days_rain_tile + """
			</div>""""""
          <br>
          <br>
          <br>
          <br>
      </div>  
      <div>		
		<div class="chapterHeader">4 - Sonn</div>
			<div class="chapterContainer">
            """+ qty_sun_tile + """
            """+ ml_qty_sun_tile + """
			</div>""""""
          <br>
          <br>
          <br>
          <br>
      </div>  
      <div> 
				<div class="chapterHeader">5 - Wand</div>
			  <div class="chapterContainer">
          <div class="italic">Geplangt</div>
          <br>
				</div>
      </div> 

      <div>
				<div class="chapterHeader">6 - Erkläerungen</div>
        <table class="extremeTempTable">
            <tr>
                <th>Kenndaag</th>
                <th>Erkläerung</th>
            </tr>
            <tr>
                <td>Wüstendag</td>
                <td>Maximaltemperatur mind. 35 °C</td>
            </tr>
            <tr>
                <td>Tropennuecht</td>
                <td>Minimaltemperatur mind. 20 °C</td>
            </tr>
            <tr>
                <td>Waarmen Daag</td>
                <td>Maximaltemperatur mind. 30 °C</td>
            </tr>
            <tr>
                <td>Summerdaag</td>
                <td>Maximaltemperatur mind. 25 °C</td>
            </tr>
            <tr>
                <td>Vegetatiounsdeeg</td>
                <td>Mediantemperatur mind. 5 °C</td>
            </tr>
            <tr>
                <td>Frascht</td>
                <td>Mindesttemperatur ënnert 0 °C</td>
            </tr>
            <tr>
                <td>Äisdaag</td>
                <td>Maximaltemparatur ënnert 0 °C</td>
            </tr>
        </table></div>
			<div class="disclaimer">
				<p class="disclaimerTitle">Disclaimer</p>  
				<p class="disclaimerContent">Dësen Rapport gouf automatesch generéiert. D'Donnée'en vunn der Statioun Pege Froggit sinn disponibel vunn """+firstPeriod+""" bis """+lastPeriod+""".</p>
				<p class="disclaimerContent">D'Donnée'en vunn Meteolux sinn disponibel vunn Januar 1947 bis """+lastPeriod+""".</p>
			</div>  
  </body>
</html>
"""

reportFilepath = os.path.join(reportPath, reportFileName)

def create_html():
    file = open(reportFilepath,"w")
    file.write(html)
    file.close()
    print("10 - HTML report created")


'''-------------------------------------------------------------------------------------------
----------------------------- 6 - Send E-Mail ------------------------------------------------
-------------------------------------------------------------------------------------------'''

def send_mail(x):
    host = "smtp-mail.outlook.com"
    port = 587
    password = confidential[1]
    sender = confidential[0]
    to_list = [x]
    email_conn = smtplib.SMTP(host,port)
    email_conn.ehlo()
    email_conn.starttls()
    email_conn.login(sender, password)
    the_msg = MIMEMultipart("alternative")
    the_msg['Subject'] = reportName + " -Rapport "+reportPeriod # Subject
    the_msg["From"] = sender
    the_msg["To"] = PJ # Receiver
    # Create the body of the message
    part = MIMEText(html, "html")
    # Attach parts into message container.
    the_msg.attach(part)
    email_conn.sendmail(sender, to_list, the_msg.as_string())
    email_conn.quit()
    print("Weather report sent to recipient(s)")

if synology == False:
    create_html()
    send_mail(confidential[0])

if synology == True:
    send_mail(PJ)