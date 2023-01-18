'''HTML weather report creator using PEGE_DB sqlite database'''
'''Version 0.2'''
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
synology = False

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
lastMonth = first - datetime.timedelta(days=1)

if automatic_report == 1:
    currentyear=int(lastMonth.strftime("%Y"))
    currentmonth=int(lastMonth.strftime("%m"))
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
    mainPath = "/volume1/python_scripts/WeatherReport/"
    dataPath = "/volume1/python_scripts/WeatherReport/Data/"
else:
    mainPath = r"C:\Users\neo_1\Dropbox\Projects\Programing\WeatherReport\\"
    dataPath = r"C:\Users\neo_1\Dropbox\Projects\Programing\WeatherReport\Data\\"
    reportPath = r"C:\Users\neo_1\Dropbox\Projects\Programing\WeatherReport\Reports\\"

DB='pege_froggit_weather_stats.sqlite'
    
try:
    # Create connection to database
    conn = sqlite3.connect(dataPath+DB)
    print("2 - Connection to DB "+DB+" successful")
except:
    print("Connection to DB "+DB+" failed")

conf_file = "confidential.txt"

conf_path = os.path.join(mainPath, conf_file)

confidential = []
with open(conf_path) as f:
    for line in f:
        confidential.append(line.replace("\n",""))

# Recipients
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
mmp="https://data.public.lu/fr/datasets/r/b096cafb-02bb-46d0-9fc0-5f63f0cbad98"

mmp_df = pd.read_fwf(mmp, encoding='latin-1')

mmp_df['MYT (°C)']=mmp_df['(°C)']
mmp_df['MMR06_06 (mm)']=mmp_df['(mm)']
mmp_df['MINS (h)']=mmp_df['MINS (h)']
mmp_df['MYP (hPa)']=mmp_df['(hPa)']
mmp_df['MYPSL (hPa)']=mmp_df['(hPa).1']
mmp_df = mmp_df[['Year', 'Month','MYT (°C)','MMR06_06 (mm)','MINS (h)','MYP (hPa)','MYPSL (hPa)']]
#print(mmp_df)

# Daily meteorological parameters - Luxembourg/Findel Airport (WMO ID 06590)
# https://data.public.lu/fr/datasets/daily-meteorological-parameters-luxembourg-findel-airport-wmo-id-06590/
dmp = "https://data.public.lu/fr/datasets/r/a67bd8c0-b036-4761-b161-bdab272302e5"

dmp_df = pd.read_csv(dmp, encoding = 'ISO-8859-1')
dmp_df['Day'] = dmp_df['DATE'].str[0:2]
dmp_df['Month'] = dmp_df['DATE'].str[3:5]
dmp_df['Year'] = dmp_df['DATE'].str[6:10]
dmp_df = dmp_df[['Year', 'Month', 'Day','DXT (°C)', 'DNT (°C)', 'DRR06_06 (mm)']]
# print(dmp_df)

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

x = daily_temp_df[(daily_temp_df['month'] == currentmonth) & (daily_temp_df['year'] == currentyear)]['day']

plot_title = "Temperaturschwankungen " + currentmonthname + " " + currentyearstr
font = {'family':'verdana','color':'white'}

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

# Monthly extremes (PROD ready)
temp_df = pd.read_sql_query("SELECT * from temp_stats_monthly", conn)

firstPeriod = str(temp_df['yearMonth'].min())
lastPeriod = str(temp_df['yearMonth'].max())

# Temp extremes current reporting period
min_temp_rp = str(round(int(temp_df[(temp_df['month'] == currentmonth) & (temp_df['year'] == currentyear)]['min_temp_m']),1))
max_temp_rp = str(round(int(temp_df[(temp_df['month'] == currentmonth) & (temp_df['year'] == currentyear)]['max_temp_m']),1))
avg_temp_rp = str(round(int(temp_df[(temp_df['month'] == currentmonth) & (temp_df['year'] == currentyear)]['avg_temp_m']),1))
med_temp_rp = str(round(int(temp_df[(temp_df['month'] == currentmonth) & (temp_df['year'] == currentyear)]['med_temp_m']),1))

# Average temp extremes current reporting period month
avg_min_temp_m = str(round(temp_df[temp_df['month'] == currentmonth]['min_temp_m'].mean(),1))
avg_avg_temp_m = str(round(temp_df[temp_df['month'] == currentmonth]['avg_temp_m'].mean(),1))
avg_med_temp_m = str(round(temp_df[temp_df['month'] == currentmonth]['med_temp_m'].mean(),1))
avg_max_temp_m = str(round(temp_df[temp_df['month'] == currentmonth]['max_temp_m'].mean(),1))

# Minimum temp extremes current reporting period month
min_temp_m = str(round(temp_df[temp_df['month'] == currentmonth]['min_temp_m'].min(),1))
min_temp_m_row = temp_df[temp_df['month'] == currentmonth]['min_temp_m'].idxmin()
min_temp_m_year = str(int(temp_df.loc[min_temp_m_row,['year']]))

# Maximum temp extremes current reporting period month
max_temp_m = str(round(temp_df[temp_df['month'] == currentmonth]['max_temp_m'].max(),1))
max_temp_m_row = temp_df[temp_df['month'] == currentmonth]['max_temp_m'].idxmax()
max_temp_m_year = str(int(temp_df.loc[max_temp_m_row,['year']]))

# Average temp extremes current reporting period month
min_avg_temp_m = str(round(temp_df[temp_df['month'] == currentmonth]['avg_temp_m'].min(),1))
min_avg_temp_m_row = temp_df[temp_df['month'] == currentmonth]['avg_temp_m'].idxmin()
min_avg_temp_m_year = str(int(temp_df.loc[min_avg_temp_m_row,['year']]))

max_avg_temp_m = str(round(temp_df[temp_df['month'] == currentmonth]['avg_temp_m'].max(),1))
max_avg_temp_m_row = temp_df[temp_df['month'] == currentmonth]['max_temp_m'].idxmax()
max_avg_temp_m_year = str(int(temp_df.loc[max_avg_temp_m_row,['year']]))

# Preparation of temperature stats HTML table
Temp_Table = """      
<table>
          <tr>
            <th rowspan="2">Wäert</th>
            <th rowspan="2">"""+reportPeriod+"""</th>
            <th rowspan="2">Moyenne</th>
            <th colspan="2">Déifstwäert</th>
            <th colspan="2">Hëchstwäert</th>
          </tr>
          <tr>
            <th>Wäert</th>
            <th>Joer
            <th>Wäert</th>
            <th>Joer</th>
          </tr>          
          <tr>
            <td class="headerColumn">Minimum</td>
            <td>"""+min_temp_rp+"""</td>
            <td>"""+avg_min_temp_m+"""</td>
            <td>"""+min_temp_m+"""</td>
            <td>"""+min_temp_m_year+"""</td>
            <td>-</td>
            <td>-</td>
          </tr>
          <tr>
            <td class="headerColumn">Mediane</td>
            <td>"""+med_temp_rp+"""</td>
            <td>"""+avg_med_temp_m+"""</td>
            <td>-</td>
            <td>-</td>
            <td>-</td>
            <td>-</td>
          </tr>
          <tr>
            <td class="headerColumn">Moyenne</td>
            <td>"""+avg_temp_rp+"""</td>
            <td>"""+avg_avg_temp_m+"""</td>
            <td>"""+min_avg_temp_m+"""</td>
            <td>"""+min_avg_temp_m_year+"""</td>
            <td>"""+max_avg_temp_m+"""</td>
            <td>"""+max_avg_temp_m_year+"""</td>
          </tr>
          <tr>
            <td class="headerColumn">Maximum</td>
            <td>"""+max_temp_rp+"""</td>
            <td>"""+avg_max_temp_m+"""</td>
            <td>-</td>
            <td>-</td>
            <td>"""+max_temp_m+"""</td>
            <td>"""+max_temp_m_year+"""</td>
          </tr>
      </table>"""


# Number of days per temp category
Wüstentage = int(temp_df[(temp_df['month'] == currentmonth) & (temp_df['year'] == currentyear)]['wuestentage'])
if Wüstentage != 0:
  WüstentageHTML = """<div class="tileMainFont">""" + str(Wüstentage) + """ Wüstendeeg</div>"""
else:
  WüstentageHTML = """"""
Tropennächte = int(temp_df[(temp_df['month'] == currentmonth) & (temp_df['year'] == currentyear)]['tropennaechte'])
if Tropennächte != 0:
  TropennächteHTML = """<div class="tileMainFont">""" + str(Tropennächte) + """ Tropennuechten</div>"""
else:
  TropennächteHTML = """"""
HeißeTage = int(temp_df[(temp_df['month'] == currentmonth) & (temp_df['year'] == currentyear)]['heisseTage'])
if HeißeTage != 0:
  HeißeTageHTML = """<div class="tileMainFont">""" + str(HeißeTage) + """ Waarm Deeg</div>"""
else:
  HeißeTageHTML = """"""
Sommertage = int(temp_df[(temp_df['month'] == currentmonth) & (temp_df['year'] == currentyear)]['sommertage'])
if Sommertage != 0:
  SommertageHTML = """<div class="tileMainFont">""" + str(Sommertage) + """ Summerdeeg</div>"""
else:
  SommertageHTML = """"""
Vegetationstage = int(temp_df[(temp_df['month'] == currentmonth) & (temp_df['year'] == currentyear)]['vegetationstage'])
if Vegetationstage != 0:
  VegetationstageHTML = """<div class="tileMainFont">""" + str(Vegetationstage) + """ Vegetatiounsdeeg</div>"""
else:
  VegetationstageHTML = """"""
Frosttage = int(temp_df[(temp_df['month'] == currentmonth) & (temp_df['year'] == currentyear)]['frosttage'])
if Frosttage != 0:
  FrosttageHTML = """<div class="tileMainFont">""" + str(Frosttage) + """ Fraschtdeeg</div>"""
else:
  FrosttageHTML = """"""
Eistage = int(temp_df[(temp_df['month'] == currentmonth) & (temp_df['year'] == currentyear)]['eistage'])
if Eistage != 0:
  EistageHTML = """<div class="tileMainFont">""" + str(Eistage) + """ Äisdeeg</div>"""
else:
  EistageHTML = """"""

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

# Rain extremes current reporting period
sum_rain_rp = str(round(int(rain_df[(rain_df['month'] == currentmonth) & (rain_df['year'] == currentyear)]['max_rain_m']),1))

# Average rain current reporting period month
avg_max_rain_m = str(round(rain_df[rain_df['month'] == currentmonth]['max_rain_m'].mean(),1))

# Minimum rain extremes current reporting period month
min_rain_m = str(round(rain_df[rain_df['month'] == currentmonth]['max_rain_m'].min(),1))
min_rain_m_row = rain_df[rain_df['month'] == currentmonth]['max_rain_m'].idxmin()
min_rain_m_year = str(int(rain_df.loc[min_rain_m_row,['year']]))

# Maximum rain extremes current reporting period month
max_rain_m = str(round(rain_df[rain_df['month'] == currentmonth]['max_rain_m'].max(),1))
max_rain_m_row = rain_df[rain_df['month'] == currentmonth]['max_rain_m'].idxmax()
max_rain_m_year = str(int(rain_df.loc[max_rain_m_row,['year']]))

# Rainy Days
rain_days_rp = str(round(rain_df[(rain_df['month'] == currentmonth) & (rain_df['year'] == currentyear)]['rainy_days'].max(),1))

# Minimum rain days current reporting period month
min_rain_days_m = str(round(rain_df[rain_df['month'] == currentmonth]['rainy_days'].min(),1))
min_rain__days_m_row = rain_df[rain_df['month'] == currentmonth]['rainy_days'].idxmin()
min_rain_days_m_year = str(int(rain_df.loc[min_rain__days_m_row,['year']]))

# Maximum rain days current reporting period month
max_rain_days_m = str(round(rain_df[rain_df['month'] == currentmonth]['rainy_days'].max(),1))
max_rain_days_m_row = rain_df[rain_df['month'] == currentmonth]['rainy_days'].idxmax()
max_rain_days_m_year = str(int(rain_df.loc[max_rain_days_m_row,['year']]))

# Average rain days current reporting period month
avg_max_rain_days_m = str(round(rain_df[rain_df['month'] == currentmonth]['rainy_days'].mean(),1))

# HTML rain table
Rain_Table = """      <table>
          <tr>
            <th rowspan="2">Wäert</th>
            <th rowspan="2">"""+reportPeriod+"""</th>
            <th colspan="2">Déifstwäert</th>
            <th colspan="2">Hëchstwäert</th>
            <th rowspan="2">Duerchschnëtt</th>
          </tr>  
          <tr>
            <th>Wäert</th>
            <th>Joer</th>
            <th>Wäert</th>
            <th>Joer</th>
          </tr>         
          <tr>
            <td class="headerColumn">Quantéit (l/m2)</td>
            <td>"""+sum_rain_rp+"""</td>
            <td>"""+min_rain_m+"""</td>
            <td>"""+min_rain_m_year+"""</td>
            <td>"""+max_rain_m+"""</td>
            <td>"""+max_rain_m_year+"""</td>
            <td>"""+avg_max_rain_m+"""</td>
          </tr>       
          <tr>
            <td class="headerColumn">Reendeeg</td>
            <td>"""+rain_days_rp+"""</td>
            <td>"""+min_rain_days_m+"""</td>
            <td>"""+min_rain_days_m_year+"""</td>
            <td>"""+max_rain_days_m+"""</td>
            <td>"""+max_rain_days_m_year+"""</td>
            <td>"""+avg_max_rain_days_m+"""</td>
          </tr>
      </table>"""

# print("5 - Rain data retrieved")


'''-------------------------------------------------------------------------------------------
------------------------- 6 - Extract sun data ----------------------------------------------
-------------------------------------------------------------------------------------------'''
sun_df = pd.read_sql_query("SELECT * from sun_stats_monthly", conn)

firstPeriod = str(sun_df['yearMonth'].min())
lastPeriod = str(sun_df['yearMonth'].max())

# Rain extremes current reporting period
sum_sun_rp = str(round(int(sun_df[(sun_df['month'] == currentmonth) & (sun_df['year'] == currentyear)]['sunshine_hours_m']),1))

# Average sun current reporting period month
avg_sunshine_hours_m = str(round(sun_df[sun_df['month'] == currentmonth]['sunshine_hours_m'].mean(),1))

# Minimum sun extremes current reporting period month
min_sun_m = str(round(sun_df[sun_df['month'] == currentmonth]['sunshine_hours_m'].min(),1))
min_sun_m_row = sun_df[sun_df['month'] == currentmonth]['sunshine_hours_m'].idxmin()
min_sun_m_year = str(int(sun_df.loc[min_sun_m_row,['year']]))

# Maximum sun extremes current reporting period month
max_sun_m = str(round(sun_df[sun_df['month'] == currentmonth]['sunshine_hours_m'].max(),1))
max_sun_m_row = sun_df[sun_df['month'] == currentmonth]['sunshine_hours_m'].idxmax()
max_sun_m_year = str(int(sun_df.loc[max_sun_m_row,['year']]))

Sun_Table = """      <table>
          <tr>
            <th rowspan="2">Wäert</th>
            <th rowspan="2">"""+reportPeriod+"""</th>
            <th colspan="2">Déifstwäert</th>
            <th colspan="2">Hëchstwäert</th>
            <th rowspan="2">Duerchschnëtt</th>
          </tr>  
          <tr>
            <th>Wäert</th>
            <th>Joer</th>
            <th>Wäert</th>
            <th>Joer</th>
          </tr>         
          <tr>
            <td class="headerColumn">Sonnenstonnen</td>
            <td>"""+sum_sun_rp+"""</td>
            <td>"""+min_sun_m+"""</td>
            <td>"""+min_sun_m_year+"""</td>
            <td>"""+max_sun_m+"""</td>
            <td>"""+max_sun_m_year+"""</td>
            <td>"""+avg_sunshine_hours_m+"""</td>
          </tr>
      </table>"""


# print("6 - Sun data retrieved")

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

css = """body {
			  background-repeat: no-repeat;
			  background-attachment: fixed;
			} 

			table, th, td {
			  border: 1px solid;
			  border-collapse: collapse;
			  border-color: white;
			  padding: 15px;
			  font-family:verdana;
			  margin-left: auto;
			  margin-right: auto;
				font-size:0.8em;
			}

			.container {
				min-height: 100%;
				background-color:#001E34;
				padding: 10px;
        color: white;
			  font-family:verdana;
			}

			.titleBar {
				padding: 0px;
				border-radius: 3px;
        margin-bottom: 10px;
				margin: 10px;
			}

			.titleFont {
        font-size: 2em;
        color: white;
				font-family:verdana;
				text-align:center;
			}

      .titleSub {
        font-size: 1em;
        color: white;
				font-family:verdana;
				text-align:center;
      }

			.station {
				background-color:#005F88;
				padding: 0px;
				border-radius: 3px;
			}
			.disclaimer {
				padding: 1px;
				border: 2px solid white;
				margin: 5px;
				border-radius: 3px;
			}

      .disclaimerTitle {
        font-size:0.8 em;
				font-family:verdana;
        text-decoration: underline;
      }

      .disclaimerContent {
        font-size:0.8 em; 
				font-family:verdana;       
      }

			.chapterHeader {
				background-color:#005F88;
				padding: 1px;
				padding-bottom: 7px;
				padding-top: 7px;
				border-radius: 3px;
        margin-bottom: 10px;
				color: white;
				text-align:center;
				font-family:verdana;
				font-size:1.2em;
		    font-weight: bold;
			}
			
			.chapterContainer {
				padding: 5px;
        overflow: auto;
        margin-bottom: 10px;
			}
			
			.tile {
				background-color:#004162;
				padding: 0px;
				margin: 5px;
				border-radius: 2px;
        float: center;
			}
			
			.tileTitle {
				background-color:#003F5F;
				padding-left: 5px;
				padding-bottom: 15px;
				padding-top: 15px;
				border-bottom: 1px solid #003856;
				border-radius: 2px;
        font-size: 1em;
		    font-weight: bold;
			}

      .tileContent {
        overflow: hidden;
				padding-bottom: 15px;
				padding-top: 15px;
      }
      
			.tileMainFont {
        font-size: 1em;
				text-align:center;
        
      }

      .tileLeftSub {
        width: 50%; 
        float: left;
        font-size: 1em;
      }

      .tileRightSub {
        width: 50%; 
        float: right;
        font-size: 1em;
      }

			tr {
			  border-bottom: 1px solid #ddd;
			}

			img {
			  display: block;
			  margin-left: auto;
			  margin-right: auto;
			  max-width: 100%;
			  height: auto;
			}

			hr {
				color:#2E75B6;
				background-color:#2E75B6;
			}
      

			.greenArrow {
				color: green;
				font-family: verdana;
				font-size: 0.75em;
				font-style: bold;
				text-align: center;
        width: 25%;
        float: left;
			}
			
			.redArrow {
				color: red;
				font-family:verdana;
				font-size:0.75m;
				font-style: bold;
				text-align:center;
        width: 25%;
        float: left;
			}
			
      .italic {
        font-style: italic;
      }
			.extremeValue{
				font-size:0.75em;
        width: 75%;
        float: right;
			}

			.headerColumn {
				text-align: left;
				font-weight: bold;
			}

			td {
				text-align: center;
			}

			tr:nth-child(even) {background-color: #004F76;}

			th {
			  background-color: #003F5F;
			  color: white;
			}
			tr {
			  color: white;
			}

			tr:hover {background-color: #004162;}"""

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
				<div class="tile">
					<div class="tileTitle">
					  Temperatur
					</div>
					<div class="tileContent">
						<div class="tileMainFont"> """ + avg_temp_rp + """ °C
						</div>
						<div class="tileLeftSub">
							<div class="redArrow">&#8711;</div>
							<div class="extremeValue"> """ + min_temp_rp + """ °C</div>
						</div>
						<div class="tileRightSub">
							<div class="greenArrow">&#8710;</div>
							<div class="extremeValue">  """ + max_temp_rp + """ °C</div>
						</div>
					</div>
				</div>
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
					<div class="tileContent">
            <div>
              <img src="data:image/png;base64,"""+my_base64_tempData+"""/>
            </div>
					</div>
          """+ Temp_Table +"""
          <br>
          """+ extremeTempHTML +"""
          <br>
          <br>
      </div> 
      <div>
      <div class="chapterHeader">3 - Reen</div>
			<div class="chapterContainer">
			</div>"""+Rain_Table+"""
          <br>
          <br>
          <br>
          <br>
      </div>  
      <div>		
		<div class="chapterHeader">4 - Sonn</div>
			<div class="chapterContainer">
		</div>"""+Sun_Table+"""
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
				<p class="disclaimerContent">Dësen Rapport gouf automatesch generéiert. D'Donnée'en sinn disponibel vunn """+firstPeriod+""" bis """+lastPeriod+""".</p>
			</div>  
  </body>
</html>
"""
def create_html():
    file = open(reportPath+reportFileName,"w")
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