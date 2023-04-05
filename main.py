'''HTML weather report creator using PEGE_DB sqlite database'''
'''Version 0.4.0'''
#Modules
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import io
import jinja2
import logging
from math import isnan
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import os
import pandas as pd
import smtplib
import sqlite3
from urllib.request import urlopen

from main import dates as dt
from main import df
from main import html

#==============================================================
#   PARAMETERS
#==============================================================

# Indicate if local run or on synology NAS

automatic_report = True # If True automatic report dates, if False manual report dates
manual_year = 2019 # Integer between 2019-202x
manual_month = 9 # Integer between 1-12

# Paths
main_path = os.getcwd()
if main_path.find("Dropbox") != -1:
  synology = False
else:
  synology = True
  
if synology == True:
    main_path = "/volume1/python_scripts/WeatherReport"
    pdb_path = "/volume1/homes/Pege_admin/Python_scripts"
else:
    main_path = r"C:\Users\neo_1\Dropbox\Projects\Programing\WeatherReport"
    pdb_path = r"C:\Users\neo_1\Dropbox\Projects\Programing"

# Files
pfws = 'pege_froggit_weather_stats.sqlite'
pdb = 'pege_db.sqlite'
conf_file = "confidential.txt"

# URLs
mmp = "https://data.public.lu/fr/datasets/r/b096cafb-02bb-46d0-9fc0-5f63f0cbad98"
dmp = "https://data.public.lu/fr/datasets/r/a67bd8c0-b036-4761-b161-bdab272302e5"
mep = "https://data.public.lu/fr/datasets/r/daf945e9-58e9-4fea-9c1a-9b933d6c8b5e"

#Filepaths
report_path = os.path.join(main_path,'reports/')
data_path = os.path.join(main_path, 'data')
data_filepath = os.path.join(data_path, pfws)
pdb_filepath = os.path.join(pdb_path, pdb)
conf_path = os.path.join(main_path, conf_file)
log_file_path = os.path.join(main_path, 'log/main.log')
template_filepath = os.path.join(main_path, 'templates/css.txt')

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

report_period = dt.current_year_str() + "-" + dt.current_month_str()
report_period_name = dt.current_month_name() + " " + dt.current_year_str()

#==============================================================
#   DATABASE AND FILE CONNECTIONS
#==============================================================

try:
    pfwsConn = sqlite3.connect(data_filepath)
    logging.info('Connection to DB ' + pfws + " successful")
except:
    logging.warning('Connection to DB ' + pfws + " failed")

try:
    pdbConn = sqlite3.connect(pdb_filepath)
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


def main_tile_title(title):
  tile_content = """<div class="tile">
      <div class="tileTitle">
        """ + title + """
      </div>
      """
  return(tile_content)

def main_tile_current(title, avg, min, max):
  tile_content = """
      <div class="tileContent">
        <div class="tileCurrent">
            <div class="tileCurrentTitle">
            """ + title + """
            </div>
            <div class="tileMainFont"> """ + avg + """ °C
            </div>
            <div class="tileSub">""" + min + """ °C / """ + max + """ °C
            </div>
        </div>"""
  return(tile_content)

def main_tile_hist(avg, min, min_year, max, max_year):
  tile_content = """
        <div class="tileHist">
            <div class="tileHistTitle">
            Historesch
            </div>
            <div class="tileMainFont"> """ + avg + """ °C
            </div>
            <div class="tileSub"> """ + min + """ °C""" + min_year + """ / """ + max + """ °C""" + max_year + """
            </div>
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

def temp_days(column_name, lux_name):
  if int(df.current_df(column_name, temp_df)) != 0:
    html_name = """<div class="tileMainFont">""" + str(int(df.current_df(column_name, temp_df))) + """ """+lux_name+"""</div>"""
  else:
    html_name = """"""
  return(html_name)

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
    the_msg['Subject'] = report_name + " -Rapport "+report_period # Subject
    the_msg["From"] = sender
    the_msg["To"] = receiver
    # Create the body of the message
    part = MIMEText(html, "html")
    # Attach parts into message container.
    the_msg.attach(part)
    email_conn.sendmail(sender, receiver, the_msg.as_string())
    email_conn.quit()
    logging.info("E-Mail sent to: "+receiver)

def create_html(content):
    file = open(report_filepath,"w")
    file.write(content)
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

daily_min_temp = daily_temp_df[(daily_temp_df['month'] == dt.current_month()) & (daily_temp_df['year'] == dt.current_year())]['temp_min']
daily_max_temp = daily_temp_df[(daily_temp_df['month'] == dt.current_month()) & (daily_temp_df['year'] == dt.current_year())]['temp_max']
daily_avg_temp = daily_temp_df[(daily_temp_df['month'] == dt.current_month()) & (daily_temp_df['year'] == dt.current_year())]['temp_avg']

x = daily_temp_df[(daily_temp_df['month'] == dt.current_month()) & (daily_temp_df['year'] == dt.current_year())]['day']

plot_title = "Temperaturschwankungen " + dt.current_month_name() + " " + dt.current_year_str()
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

# Monthly extremes (PROD ready)
# Meteolux temp extremes current reporting period month
ml_min_temp_m = str(round(float(df.month_df('DNT (°C)', dmp_df).min()),1))
ml_min_temp_m_row = df.month_df('DNT (°C)', dmp_df).idxmin()
ml_min_temp_m_year = str(int(dmp_df.loc[ml_min_temp_m_row,['year']]))

ml_max_temp_m = str(round(float(df.month_df('DXT (°C)', dmp_df).max()),1))
ml_max_temp_m_row = df.month_df('DXT (°C)', dmp_df).idxmax()
ml_max_temp_m_year = str(int(dmp_df.loc[ml_max_temp_m_row,['year']]))

logging.info("Temperatures data retrieved")

#==============================================================
#   RAIN
#==============================================================
ml_min_rain_m = str(df.month_df('MMR06_06 (mm)', mmp_df).min())
ml_min_rain_m_row = df.month_df('MMR06_06 (mm)', mmp_df).idxmin()
ml_min_rain_m_year = str(int(mmp_df.loc[ml_min_rain_m_row,['year']]))

ml_max_rain_m = str(df.month_df('MMR06_06 (mm)', mmp_df).max())
ml_max_rain_m_row = df.month_df('MMR06_06 (mm)', mmp_df).idxmax()
ml_max_rain_m_year = str(int(mmp_df.loc[ml_max_rain_m_row,['year']]))

# Rain days
# Loop through each year-month pair
years = dmp_df['year'].unique()
rain_days = {}
sum_rain_days = 0

for year in years:
    # Retrieve number of rainy days for current month for each year
    temp_dmp_df = dmp_df[dmp_df['month'] == dt.current_month()][dmp_df['year'] == year]
    rainy_days = 0
    day = 1
    while day <= dt.days_in_month():
      if temp_dmp_df[temp_dmp_df['day'] == day]['DRR06_06 (mm)'].max() > 0:
          rainy_days = rainy_days + 1
      day = day + 1
    rain_days[year]=rainy_days
    sum_rain_days = sum_rain_days + rainy_days
    year = year + 1 

ml_max_rain_days_keys = [key for key, value in rain_days.items() if value == max(rain_days.values())]
ml_max_rain_days_m = str(rain_days[ml_max_rain_days_keys[0]])
ml_max_rain_days_m_year = str(ml_max_rain_days_keys[0])

ml_min_rain_days_keys = [key for key, value in rain_days.items() if value == min(rain_days.values())]
ml_min_rain_days_m = str(rain_days[ml_min_rain_days_keys[0]])
ml_min_rain_days_m_year = str(ml_min_rain_days_keys[0])

logging.info("Rain data retrieved")

#==============================================================
#   SUN
#==============================================================
# Sun extremes current reporting period
sum_sun_rp = str(round(int(df.current_df('sunshine_hours_m', sun_df)),1))

# Average sun current reporting period month
avg_sun_m = str(round(df.month_df('sunshine_hours_m', sun_df).mean(),1))

# Minimum sun extremes current reporting period month
min_sun_m = str(round(df.month_df('sunshine_hours_m', sun_df).min(),1))
min_sun_m_row = df.month_df('sunshine_hours_m', sun_df).idxmin()
min_sun_m_year = str(int(sun_df.loc[min_sun_m_row,['year']]))

# Maximum sun extremes current reporting period month
max_sun_m = str(round(df.month_df('sunshine_hours_m', sun_df).max(),1))
max_sun_m_row = df.month_df('sunshine_hours_m', sun_df).idxmax()
max_sun_m_year = str(int(sun_df.loc[max_sun_m_row,['year']]))

# Meteolux
# Sun quantity
ml_avg_sun_m = str(round(df.month_df('MINS (h)', mmp_df).mean(),1))

ml_min_sun_m = str(df.month_df('MINS (h)', mmp_df).min())
ml_min_sun_m_row = df.month_df('MINS (h)', mmp_df).idxmin()
ml_min_sun_m_year = str(int(mmp_df.loc[ml_min_sun_m_row,['year']]))

ml_max_sun_m = str(df.month_df('MINS (h)', mmp_df).max())
ml_max_sun_m_row = df.month_df('MINS (h)', mmp_df).idxmax()
ml_max_sun_m_year = str(int(mmp_df.loc[ml_max_sun_m_row,['year']]))

logging.info("Sun data retrieved")

#==============================================================
#   WIND
#==============================================================



#==============================================================
#   OTHER - WIP
#==============================================================

ow_cloud = ow_df[(ow_df['month'] == dt.current_month()) & (ow_df['year'] == dt.current_year())][['cloudiness', 'year']]
ow_cloud_count = ow_cloud.groupby(['cloudiness'])['cloudiness'].count()

plot = ow_cloud_count.plot.bar(figsize=(5, 5))
plt.savefig(os.path.join(main_path, 'plots/ow_cloudiness.png'))

#==============================================================
#   HTML
#==============================================================

css_file = open(template_filepath, 'r')
css = css_file.read()

# Report file name
report_name="Wieder Rapport Kautebaach"
report_file_name="Wieder Rapport " + report_period + ".html"
report_filepath = os.path.join(report_path, report_file_name)

template_loader = jinja2.FileSystemLoader(searchpath=os.path.join(main_path, 'templates'))
template_env = jinja2.Environment(loader=template_loader)
MAIN_TEMPLATE_FILE = "main.html"
main_template = template_env.get_template(MAIN_TEMPLATE_FILE)

main_html_var = {
    'currentyearstr': dt.current_year_str(),
    'css': css,
    'report_name': report_name,
    'report_period_name': report_period_name,
    'avg_temp_rp': str(round(float(df.current_df('avg_temp_m', temp_df)),1)),
    'min_temp_rp':str(round(float(df.current_df('min_temp_m', temp_df)),1)),
    'max_temp_rp': str(round(float(df.current_df('max_temp_m', temp_df)),1)), 
    'avg_avg_temp_m': str(round(df.month_df('MYT (°C)', mmp_df).mean(),1)),
    'min_temp_m': ml_min_temp_m, 
    'min_temp_m_year': ml_min_temp_m_year,
    'max_temp_m': ml_max_temp_m, 
    'max_temp_m_year': ml_max_temp_m_year,
    'wüstentage_html': temp_days('wuestentage', 'Wüstendeeg'),
    'tropennächte_html': temp_days('tropennaechte', 'Tropennuechten'),
    'heiße_tage_html': temp_days('heisseTage', 'Waarm Deeg'),
    'sommertage_html': temp_days('sommertage', 'Summerdeeg'),
    'vegetationstage_html': temp_days('vegetationstage', 'Vegetatiounsdeeg'),
    'frosttage_html': temp_days('frosttage', 'Fraschtdeeg'),
    'eistage_html': temp_days('eistage', 'Äisdeeg'),
    'temp_chart': temp_plot(),
    'sum_rain_rp': str(round(int(df.current_df('max_rain_m', rain_df)),1)),
    'rain_days_rp': str(round(df.current_df('rainy_days', rain_df).max(),1)),
    'ml_avg_rain_m': str(round(df.month_df('MMR06_06 (mm)', mmp_df).mean(),1)), 
    'ml_min_rain_m': ml_min_rain_m, 
    'ml_min_rain_m_year': ml_min_rain_m_year, 
    'ml_max_rain_m': ml_max_rain_m, 
    'ml_max_rain_m_year': ml_max_rain_m_year,
    'ml_avg_rain_days_m': str(int(round(sum_rain_days / len(rain_days),0))),
    'ml_min_rain_days_m': ml_min_rain_days_m,
    'ml_min_rain_days_m_year': ml_min_rain_days_m_year,
    'ml_max_rain_days_m': ml_max_rain_days_m,
    'ml_max_rain_days_m_year': ml_max_rain_days_m_year,
    'sum_sun_rp': sum_sun_rp,
    'ml_avg_sun_m': ml_avg_sun_m,
    'ml_min_sun_m': ml_min_sun_m,
    'ml_min_sun_m_year': ml_min_sun_m_year,
    'ml_max_sun_m': ml_max_sun_m,
    'ml_max_sun_m_year': ml_max_sun_m_year,
    'current_month_name': dt.current_month_name(),
    'current_year_str': dt.current_year_str()
}

html = main_template.render(**main_html_var)

#==============================================================
#   SCRIPT
#==============================================================

if synology == False:
    create_html(html)
    send_mail(confidential[0])

if synology == True:
    send_mail(confidential[2])
