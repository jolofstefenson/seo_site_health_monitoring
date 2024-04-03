#-------------------------------------------------IMPORT LIBRARIES-------------------------------------------
import requests
import pandas as pd
import tldextract #extract domain from url
import datetime
from google.oauth2 import service_account
import json

# testing core web vitals
def speed_check(url):
   domain = tldextract.extract(url).registered_domain
   page_speed = requests.get(url="https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url="
                                 + url + "&strategy=mobile&key=" + "my_key")
   data = json.loads(page_speed.text)
   lcp = round(data["lighthouseResult"]["audits"]["largest-contentful-paint"]["numericValue"])
   cls = float(data["lighthouseResult"]["audits"]["cumulative-layout-shift"]["displayValue"])
   return [datetime.date.today(), domain, url, lcp, cls]

page_speed = pd.DataFrame(columns=["date", "domain", "url", "lcp", "cls"])

urls = ["https://en.wikipedia.org/wiki/Lorem_ipsum",
        "https://en.wikipedia.org/wiki/Google_Lighthouse"]

for url in urls:
   page_speed.loc[len(page_speed)] = speed_check(url)

schema = [{'name': 'date', 'type': 'DATE'},
          {'name': 'domain', 'type': 'STRING'},
          {'name': 'url', 'type': 'STRING'},
          {'name': 'lcp_milliseconds', 'type': 'FLOAT'},
          {'name': 'cls', 'type': 'FLOAT'}
         ]

#-------------------------------------------------NOW UPLOADING TO BIG QUERY-------------------------------------------
#BQ_Credential_File_Path = "credential_path"
#BQ_Project_ID = "project_name"
#BQ_Job_Location = "eu"

#target_table = "data_set.table"
#ipg-mediabrands-sweden.SE_Adverity_Marathon.plan_data_python

credential = service_account.Credentials.from_service_account_file(BQ_Credential_File_Path)

page_speed.to_gbq(target_table, project_id=BQ_Project_ID, if_exists='append', location=BQ_Job_Location,
                  progress_bar=False, credentials=credential, table_schema=schema)
#----------------------------------------------------------------------------------------------------------------------