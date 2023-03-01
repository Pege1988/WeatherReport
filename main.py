'''HTML weather report creator using PEGE_DB sqlite database'''
'''Version 0.3.1'''
#Modules
import base64
import calendar
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import io
import logging
from math import isnan
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
import os
import pandas as pd
import smtplib
import sqlite3
from urllib.request import urlopen

#==============================================================
#   TOC
#==============================================================


#==============================================================
#   PARAMETERS
#==============================================================

# Indicate if local run or on synology NAS
synology = True
automatic_report = 1 # If 1 automatic report dates, if 0 manual report dates
manual_year = 2019 # Integer between 2019-202x
manual_month = 9 # Integer between 1-12

# Paths
if synology == True:
    mainPath = "/volume1/python_scripts/WeatherReport"
    pdbPath = "/volume1/homes/Pege_admin/Python_scripts"
else:
    mainPath = r"C:\Users\neo_1\Dropbox\Projects\Programing\WeatherReport"
    pdbPath = r"C:\Users\neo_1\Dropbox\Projects\Programing"

# Files
pfws = 'pege_froggit_weather_stats.sqlite'
pdb = 'pege_db.sqlite'
conf_file = "confidential.txt"

# URLs
mmp = "https://data.public.lu/fr/datasets/r/b096cafb-02bb-46d0-9fc0-5f63f0cbad98"
dmp = "https://data.public.lu/fr/datasets/r/a67bd8c0-b036-4761-b161-bdab272302e5"
mep = "https://data.public.lu/fr/datasets/r/daf945e9-58e9-4fea-9c1a-9b933d6c8b5e"

#Filepaths
reportPath = os.path.join(mainPath,'reports/')
dataPath = os.path.join(mainPath, 'data')
dataFilepath = os.path.join(dataPath, pfws)
pdbFilepath = os.path.join(pdbPath, pdb)
conf_path = os.path.join(mainPath, conf_file)
log_file_path = os.path.join(mainPath, 'log/main.log')
templateFilepath = os.path.join(mainPath, 'templates/css.txt')

logger = logging.getLogger()
if synology == True:
   logger.setLevel(logging.INFO)
else:
  logger.setLevel(logging.DEBUG)
fhandler = logging.FileHandler(filename = log_file_path, mode = 'a')
formatter = logging.Formatter('%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s', '%d-%m-%Y %H:%M:%S')
fhandler.setFormatter(formatter)
logger.addHandler(fhandler)

logging.getLogger('matplotlib.font_manager').disabled = True
logging.info('Start of program')

#==============================================================
#   DATES
#==============================================================

today = datetime.date.today()
first = today.replace(day=1)
prevEOM = first - datetime.timedelta(days=1)

if automatic_report == 1:
    currentyear=int(prevEOM.strftime("%Y"))
    currentmonth=int(prevEOM.strftime("%m"))
elif automatic_report == 0:
    currentyear = manual_year
    currentmonth = manual_month
else:
    logging.error("Reporting period not correctly chosen!")
    exit()
days_in_month = calendar.monthrange(currentyear, currentmonth)[1]

if len(str(currentmonth)) == 1:
    currentmonthstr = "0" + str(currentmonth)
else:
    currentmonthstr = str(currentmonth)
currentyearstr = str(currentyear)

logging.info('Current month and year:' + currentyearstr + "-" + currentmonthstr)

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

reportPeriod = currentyearstr + "-" + currentmonthstr
reportPeriodName = currentmonthname + " " + currentyearstr

#==============================================================
#   DATABASE AND FILE CONNECTIONS
#==============================================================

try:
    pfwsConn = sqlite3.connect(dataFilepath)
    logging.info('Connection to DB ' + pfws + " successful")
except:
    logging.warning('Connection to DB ' + pfws + " failed")

try:
    pdbConn = sqlite3.connect(pdbFilepath)
    logging.info('Connection to DB ' + pdb + " successful")
except:
    logging.warning('Connection to DB ' + pdb + " failed")

# Add items from confidential file to list
confidential = []
with open(conf_path) as f:
    for line in f:
        confidential.append(line.replace("\n",""))

#==============================================================
#   FUNCTIONS
#==============================================================

def current_df(var, table):
  variable = table[(table['month'] == currentmonth) & (table['year'] == currentyear)][var]
  logging.debug(var + ": ")
  logging.debug(str(variable))
  return(variable)

def month_df(var, table):
  variable = table[table['month'] == currentmonth][var]
  logging.debug(var + ": ")
  logging.debug(str(variable))
  return(variable)

def temp_tile(tile_title, avg, avg_year, min, min_year, max, max_year):
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

def temp_days(columnName, luxName):
  if int(current_df(columnName, temp_df)) != 0:
    htmlName = """<div class="tileMainFont">""" + str(int(current_df(columnName, temp_df))) + """ """+luxName+"""</div>"""
  else:
    htmlName = """"""
  return(htmlName)

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

def send_mail(receiver):
    host = "smtp-mail.outlook.com"
    port = 587
    password = confidential[1]
    sender = confidential[0]
    email_conn = smtplib.SMTP(host,port)
    email_conn.ehlo()
    email_conn.starttls()
    email_conn.login(sender, password)
    the_msg = MIMEMultipart("alternative")
    the_msg['Subject'] = reportName + " -Rapport "+reportPeriod # Subject
    the_msg["From"] = sender
    the_msg["To"] = receiver
    # Create the body of the message
    part = MIMEText(html, "html")
    # Attach parts into message container.
    the_msg.attach(part)
    email_conn.sendmail(sender, receiver, the_msg.as_string())
    email_conn.quit()
    logging.info("E-Mail sent to: "+receiver)

def create_html():
    file = open(reportFilepath,"w")
    file.write(html)
    file.close()
    logging.info("HTML file created")

#==============================================================
#   DATAFRAMES PREP
#==============================================================

# Pege Froggit weather stats
daily_temp_df = pd.read_sql_query("SELECT year, month, day, temp_min, temp_max, temp_avg from daily_stats", pfwsConn)
temp_df = pd.read_sql_query("SELECT * from temp_stats_monthly", pfwsConn)
rain_df = pd.read_sql_query("SELECT * from rain_stats_monthly", pfwsConn)
sun_df = pd.read_sql_query("SELECT * from sun_stats_monthly", pfwsConn)

# Open Weather
ow_df = pd.read_sql_query("SELECT date, cloudiness FROM openweather", pdbConn)
ow_df['month'] = ow_df['date'].str[3:5].astype(int)
ow_df['year'] = ow_df['date'].str[6:10].astype(int)

# Meteolux
mmp_df = pd.read_fwf(mmp, encoding='latin-1')
mmp_df['MYT (°C)']=mmp_df['(°C)']
mmp_df['MMR06_06 (mm)']=mmp_df['(mm)']
mmp_df['MINS (h)']=mmp_df['MINS (h)']
mmp_df['year'] = mmp_df['Year']
mmp_df['month'] = mmp_df['Month']
mmp_df = mmp_df[['year', 'month','MYT (°C)','MMR06_06 (mm)','MINS (h)']]

dmp_df = pd.read_csv(dmp, encoding = 'ISO-8859-1')
dmp_df['day'] = dmp_df['DATE'].str[0:2].astype(int)
dmp_df['month'] = dmp_df['DATE'].str[3:5].astype(int)
dmp_df['year'] = dmp_df['DATE'].str[6:10].astype(int)
dmp_df = dmp_df[['year', 'month', 'day', 'DXT (°C)', 'DNT (°C)', 'DRR06_06 (mm)']]

mep_df = pd.read_csv(mep, encoding = 'ISO-8859-1', sep = ';')
mep_df_transposed = mep_df.T
mep_df = pd.melt(mep_df, id_vars = 'MONTH', value_vars = ['JAN', 'FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']) 

logging.info("Dataframes created")

#==============================================================
#   TEMPERATURE
#==============================================================

# Daily temps WIP

daily_min_temp = daily_temp_df[(daily_temp_df['month'] == currentmonth) & (daily_temp_df['year'] == currentyear)]['temp_min']
daily_max_temp = daily_temp_df[(daily_temp_df['month'] == currentmonth) & (daily_temp_df['year'] == currentyear)]['temp_max']
daily_avg_temp = daily_temp_df[(daily_temp_df['month'] == currentmonth) & (daily_temp_df['year'] == currentyear)]['temp_avg']

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
# Temp extremes current reporting period
min_temp_rp = str(round(float(current_df('min_temp_m', temp_df)),1))
max_temp_rp = str(round(float(current_df('max_temp_m', temp_df)),1))
avg_temp_rp = str(round(float(current_df('avg_temp_m', temp_df)),1))

current_temp_tile = temp_tile("Temperatur " + str(reportPeriod),avg_temp_rp, "", min_temp_rp, "", max_temp_rp, "")

# Average temp extremes current reporting period month
avg_min_temp_m = str(round(month_df('min_temp_m', temp_df).mean(),1))
avg_avg_temp_m = str(round(month_df('avg_temp_m', temp_df).mean(),1))
avg_max_temp_m = str(round(month_df('max_temp_m', temp_df).mean(),1))

# Minimum temp extremes current reporting period month
min_temp_m = str(round(month_df('min_temp_m', temp_df).min(),1))
min_temp_m_row = month_df('min_temp_m', temp_df).idxmin()
min_temp_m_year = str(int(temp_df.loc[min_temp_m_row,['year']]))


# Maximum temp extremes current reporting period month
max_temp_m = str(round(month_df('max_temp_m', temp_df).max(),1))
max_temp_m_row = month_df('max_temp_m', temp_df).idxmax()
max_temp_m_year = str(int(temp_df.loc[max_temp_m_row,['year']]))

month_ext_temp_tile = temp_tile("Extremwäerter " + str(currentmonthname) + " - Pege Froggit", avg_avg_temp_m, "", min_temp_m, " ("+min_temp_m_year+")", max_temp_m, " ("+max_temp_m_year+")")

# Average temp extremes current reporting period month
min_avg_temp_m = str(round(month_df('avg_temp_m', temp_df).min(),1))
min_avg_temp_m_row = month_df('avg_temp_m', temp_df).idxmin()
min_avg_temp_m_year = str(int(temp_df.loc[min_avg_temp_m_row,['year']]))

max_avg_temp_m = str(round(month_df('avg_temp_m', temp_df).max(),1))
max_avg_temp_m_row = month_df('max_temp_m', temp_df).idxmax()
max_avg_temp_m_year = str(int(temp_df.loc[max_avg_temp_m_row,['year']]))

# Meteolux temp extremes current reporting period month

ml_avg_min_temp_m = str(round(month_df('DNT (°C)', dmp_df).mean(),1))
ml_avg_avg_temp_m = str(round(month_df('MYT (°C)', mmp_df).mean(),1))
ml_avg_max_temp_m = str(round(month_df('DXT (°C)', dmp_df).mean(),1))

ml_min_temp_m = str(round(float(month_df('DNT (°C)', dmp_df).min()),1))
ml_min_temp_m_row = month_df('DNT (°C)', dmp_df).idxmin()
ml_min_temp_m_year = str(int(dmp_df.loc[ml_min_temp_m_row,['year']]))

ml_max_temp_m = str(round(float(month_df('DXT (°C)', dmp_df).max()),1))
ml_max_temp_m_row = month_df('DXT (°C)', dmp_df).idxmax()
ml_max_temp_m_year = str(int(dmp_df.loc[ml_max_temp_m_row,['year']]))

ml_min_avg_temp_m = str(round(float(month_df('MYT (°C)', mmp_df).min()),1))
ml_min_avg_temp_m_row = month_df('MYT (°C)', mmp_df).idxmin()
ml_min_avg_temp_m_year = str(int(mmp_df.loc[ml_min_avg_temp_m_row,['year']]))

ml_max_avg_temp_m = str(round(float(month_df('MYT (°C)', mmp_df).max()),1))
ml_max_avg_temp_m_row = month_df('MYT (°C)', mmp_df).idxmax()
ml_max_avg_temp_m_year = str(int(mmp_df.loc[ml_max_avg_temp_m_row,['year']]))

ml_month_ext_temp_tile = temp_tile("Extremwäerter " + str(currentmonthname) + " - Meteolux", ml_avg_avg_temp_m, "", ml_min_temp_m, " ("+ml_min_temp_m_year+")", ml_max_temp_m, " ("+ml_max_temp_m_year+")")

# Number of days per temp category

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

logging.info("Temperatures data retrieved")

#==============================================================
#   RAIN
#==============================================================
# Rain extremes current reporting period
sum_rain_rp = str(round(int(current_df('max_rain_m', rain_df)),1))

# Average rain current reporting period month
avg_max_rain_m = str(round(month_df('max_rain_m', rain_df).mean(),1))

# Minimum rain extremes current reporting period month
min_rain_m = str(round(month_df('max_rain_m', rain_df).min(),1))
min_rain_m_row = month_df('max_rain_m', rain_df).idxmin()
min_rain_m_year = str(int(rain_df.loc[min_rain_m_row,['year']]))

# Maximum rain extremes current reporting period month
max_rain_m = str(round(month_df('max_rain_m', rain_df).max(),1))
max_rain_m_row = month_df('max_rain_m', rain_df).idxmax()
max_rain_m_year = str(int(rain_df.loc[max_rain_m_row,['year']]))

qty_rain_tile = rain_tile("Reenquantitéit "+currentmonthname+" - Pege Froggit", " l/m2", avg_max_rain_m, "",min_rain_m, " ("+min_rain_m_year+")", max_rain_m, " ("+max_rain_m_year+")")

# Rainy Days
rain_days_rp = str(round(current_df('rainy_days', rain_df).max(),1))

# Minimum rain days current reporting period month
min_rain_days_m = str(round(month_df('rainy_days', rain_df).min(),1))
min_rain__days_m_row = month_df('rainy_days', rain_df).idxmin()
min_rain_days_m_year = str(int(rain_df.loc[min_rain__days_m_row,['year']]))

# Maximum rain days current reporting period month
max_rain_days_m = str(round(month_df('rainy_days', rain_df).max(),1))
max_rain_days_m_row = month_df('rainy_days', rain_df).idxmax()
max_rain_days_m_year = str(int(rain_df.loc[max_rain_days_m_row,['year']]))

# Average rain days current reporting period month
avg_max_rain_days_m = str(round(month_df('rainy_days', rain_df).mean(),1))

days_rain_tile = rain_tile("Reendeeg "+currentmonthname+" - Pege Froggit", " Deeg", avg_max_rain_days_m, "",min_rain_days_m, " ("+min_rain_days_m_year+")", max_rain_days_m, " ("+max_rain_days_m_year+")")

# Meteolux
# Rain quantity
ml_avg_rain_m = str(round(month_df('MMR06_06 (mm)', mmp_df).mean(),1))

ml_min_rain_m = str(month_df('MMR06_06 (mm)', mmp_df).min())
ml_min_rain_m_row = month_df('MMR06_06 (mm)', mmp_df).idxmin()
ml_min_rain_m_year = str(int(mmp_df.loc[ml_min_rain_m_row,['year']]))

ml_max_rain_m = str(month_df('MMR06_06 (mm)', mmp_df).max())
ml_max_rain_m_row = month_df('MMR06_06 (mm)', mmp_df).idxmax()
ml_max_rain_m_year = str(int(mmp_df.loc[ml_max_rain_m_row,['year']]))

ml_qty_rain_tile = rain_tile("Reenquantitéit "+currentmonthname+" - Meteolux", " l/m2", ml_avg_rain_m, "",ml_min_rain_m, " ("+ml_min_rain_m_year+")", ml_max_rain_m, " ("+ml_max_rain_m_year+")")

# Rain days
# Loop through each year-month pair
Years = dmp_df['year'].unique()

rain_days = {}
sum_rain_days = 0

for year in Years:
    # Retrieve number of rainy days for current month for each year
    temp_dmp_df = dmp_df[dmp_df['month'] == currentmonth][dmp_df['year'] == year]
    rainy_days = 0
    day = 1
    while day <= days_in_month:
      if temp_dmp_df[temp_dmp_df['day'] == day]['DRR06_06 (mm)'].max() > 0:
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

logging.info("Rain data retrieved")



#==============================================================
#   SUN
#==============================================================
# Sun extremes current reporting period
sum_sun_rp = str(round(int(current_df('sunshine_hours_m', sun_df)),1))

# Average sun current reporting period month
avg_sun_m = str(round(month_df('sunshine_hours_m', sun_df).mean(),1))

# Minimum sun extremes current reporting period month
min_sun_m = str(round(month_df('sunshine_hours_m', sun_df).min(),1))
min_sun_m_row = month_df('sunshine_hours_m', sun_df).idxmin()
min_sun_m_year = str(int(sun_df.loc[min_sun_m_row,['year']]))

# Maximum sun extremes current reporting period month
max_sun_m = str(round(month_df('sunshine_hours_m', sun_df).max(),1))
max_sun_m_row = month_df('sunshine_hours_m', sun_df).idxmax()
max_sun_m_year = str(int(sun_df.loc[max_sun_m_row,['year']]))

qty_sun_tile = sun_tile("Sonnenstonnen "+currentmonthname+" - Pege Froggit", " Stonnen", avg_sun_m, "",min_sun_m, " ("+min_sun_m_year+")", max_sun_m, " ("+max_sun_m_year+")")

# Meteolux
# Sun quantity
ml_avg_sun_m = str(round(month_df('MINS (h)', mmp_df).mean(),1))

ml_min_sun_m = str(month_df('MINS (h)', mmp_df).min())
ml_min_sun_m_row = month_df('MINS (h)', mmp_df).idxmin()
ml_min_sun_m_year = str(int(mmp_df.loc[ml_min_sun_m_row,['year']]))

ml_max_sun_m = str(month_df('MINS (h)', mmp_df).max())
ml_max_sun_m_row = month_df('MINS (h)', mmp_df).idxmax()
ml_max_sun_m_year = str(int(mmp_df.loc[ml_max_sun_m_row,['year']]))

ml_qty_sun_tile = sun_tile("Sonnenstonnen "+currentmonthname+" - Meteolux", " Stonnen", ml_avg_sun_m, "",ml_min_sun_m, " ("+ml_min_sun_m_year+")", ml_max_sun_m, " ("+ml_max_sun_m_year+")")

logging.info("Sun data retrieved")


#==============================================================
#   WIND
#==============================================================



#==============================================================
#   OTHER - WIP
#==============================================================

ow_cloud = ow_df[(ow_df['month'] == currentmonth) & (ow_df['year'] == currentyear)][['cloudiness', 'year']]
ow_cloud_count = ow_cloud.groupby(['cloudiness'])['cloudiness'].count()

plot = ow_cloud_count.plot.bar(figsize=(5, 5))
plt.savefig(os.path.join(mainPath, 'plots/ow_cloudiness.png'))

#==============================================================
#   HTML
#==============================================================

css_file = open(templateFilepath, 'r')
css = css_file.read()

# Report file name
reportName="Wieder Rapport Kautebaach"
reportFileName="Wieder Rapport "+reportPeriod+".html"
reportFilepath = os.path.join(reportPath, reportFileName)

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
				<p class="disclaimerContent">Dësen Rapport gouf automatesch generéiert. D'Donnée'en vunn der Statioun Pege Froggit sinn disponibel vunn Juni 2019 bis """ + currentmonthname + """ """ + currentyearstr + """.</p>
				<p class="disclaimerContent">D'Donnée'en vunn Meteolux sinn disponibel vunn Januar 1947 bis """ + currentmonthname + """ """ + currentyearstr + """.</p>
			</div>  
  </body>
</html>
"""

#==============================================================
#   SCRIPT
#==============================================================

if synology == False:
    create_html()
    send_mail(confidential[0])

if synology == True:
    send_mail(confidential[2])
