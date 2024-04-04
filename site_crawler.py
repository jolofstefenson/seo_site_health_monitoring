#-------------------------------------------------IMPORT LIBRARIES-------------------------------------------
import requests from bs4
import BeautifulSoup
import pandas as pd
import tldextract #extract domain from url
import datetime
from google.oauth2 import service_account
import validators
import time #import random

#---------------------------------------------------------------------------------------------------------------

#-------------------------------------------------SITE CRAWL FUNCTION-------------------------------------------
def crawl_website(site_dict, max_pages):
   to_crawl = [site_dict["start"]]

   # Initialize a counter for the number of pages crawled
   n_crawled = 0

   # Initialize empty lists that will be combined into dataframe with page data
   url_crawled = []
   status_crawled = []
   redirect_url = []
   canonical = []
   robots = []
   xrobots = []
   robotstxt = []
   robotsinstructions = {"Disallow":[], "Allow":[]}
   h1 = []
   title = []

   #Grab domain & subdomain to check outbound links
   domain = tldextract.extract(site_dict["start"]).registered_domain
   subdomain = tldextract.extract(site_dict["start"]).subdomain
   #user_agent_list = ["Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
   #, "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"
   #, "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.83 Safari/537.36"
   #, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36"]
   HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
              "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
              "Accept-Language": "en-US,en;q=0.5",
              "Accept-Encoding": "gzip, deflate",
              "Connection": "keep-alive",
              "Upgrade-Insecure-Requests": "1",
              "Sec-Fetch-Dest": "document",
              "Sec-Fetch-Mode": "navigate",
              "Sec-Fetch-Site": "none",
              "Sec-Fetch-User": "?1",
              "Cache-Control": "max-age=0",
              }
   #-------------------------------------------------Read robots.txt-------------------------------------------
   robotslines = requests.get(url="https://genoplivning.dk/robots.txt", allow_redirects=False, headers=HEADERS).text
   for line in robotslines.split("\n"):
       if line.startswith("Allow"):
           robotsinstructions["Allow"].append(line.split(': ')[1].split(' ')[0])
       elif line.startswith("Disallow"):
           robotsinstructions["Disallow"].append(line.split(': ')[1].split(' ')[0])

   # -------------------------------------------------CRAWL ITERATION-------------------------------------------
   while len(url_crawled) < max_pages and n_crawled < len(to_crawl):
       crawling = to_crawl[n_crawled]
       print(crawling)
       if not validators.url(crawling):
           url_crawled.append(to_crawl[n_crawled])
           status_crawled.append("invalid url")
           redirect_url.append(None)
           canonical.append(None)
           robots.append(None)
           xrobots.append(None)
           robotstxt.append(None)
           h1.append(None)
           title.append(None)
           n_crawled += 1
           continue
       try:
           # Send an HTTP GET request to the URL
           response = requests.get(url=crawling, allow_redirects=False, headers=HEADERS)
           #time.sleep(3)

       except:# handling request errors
           print("Error crawling " + to_crawl[n_crawled])
           url_crawled.append(to_crawl[n_crawled])
           status_crawled.append("get error")
           redirect_url.append(None)
           canonical.append(None)
           robots.append(None)
           xrobots.append(None)
           robotstxt.append(None)
           h1.append(None)
           title.append(None)
           n_crawled += 1
           continue

       # skip not text/html
       if 'Content-Type' in response.headers:
           if "text/html" not in response.headers['Content-Type']:
               n_crawled += 1
               continue

       # write status code before going to redirect location
       url_crawled.append(response.request.url)
       status_crawled.append(str(response.status_code))
       redirect_url.append(None)

       #check redirect chain
       if response.is_redirect:
           redirect_url[-1] = response.headers['Location']

           # Check if redirect is a path and if so convert it into an url
           if not validators.url(redirect_url[-1]):
               if subdomain == "":
                   redirect_url[-1] = "https://" + domain + redirect_url[-1]
               else:
                   redirect_url[-1] = "https://" + subdomain + "." + domain + redirect_url[-1]
           response = requests.get(url=redirect_url[-1], allow_redirects=False, headers=HEADERS)
           #time.sleep(2)

           if response.is_redirect:
               status_crawled[-1] = ("redirect_chain")
               canonical.append(None)
               robots.append(None)
               xrobots.append(None)
               robotstxt.append(None)
               h1.append(None)
               title.append(None)
               n_crawled += 1
               continue

       # Parse the HTML content of the page
       soup = BeautifulSoup(response.text, 'html.parser')
       canonical_temp = soup.find('link', attrs={'rel':'canonical'})

       if canonical_temp is not None:
           canonical.append(str(soup.find('link', attrs={'rel':'canonical'})['href']))
       else:
           canonical.append("no canonical"),

       # check for robots or googlebot tag
       robots_temp = soup.find_all(attrs={'name':['googlebot', 'robots']})
       if len(robots_temp) > 0:
           if "noindex" in soup.find_all(attrs={'name':['googlebot', 'robots']})[0]['content']:
               robots.append("noindex")
           elif "index" in soup.find_all(attrs={'name':['googlebot', 'robots']})[0]['content']:
               robots.append("index")
           else:
               robots.append("other")
       else:
           robots.append("no robots tag")
       if 'X-Robots-Tag' in response.headers:
           if response.headers['X-Robots-Tag'].hasattr('noindex'):
               xrobots.append("noindex")
           elif "index" in response.headers['X-Robots-Tag']:
               xrobots.append("index")
           else:
               xrobots.append("other")
       else:
           xrobots.append("no x-robots tag")

       # Check robotstxt file
       if any(path in response.url
    for path in robotsinstructions["Disallow"]):
           robotstxt.append("disallowed by robots.txt")
       else:
           robotstxt.append("allowed")
       # Check H1 and Title
       h1_temp = soup.find_all('h1')
       if h1_temp is None:
           h1.append("no h1")
       elif len(h1_temp) > 1:
           h1.append("Multiple h1")
       else:
           h1.append(str(soup.find('h1')))
       title_temp = soup.find('title')
       if title_temp is not None:
           title.append(str(soup.find('title')))
       else:
           title.append("no title")

       # -------------------------------------------------ADD LINKS TO QUEUE-------------------------------------------
       links = soup.find_all('a', href=True)
       for link in links:
           link_href = link['href']
           if any(["mailto:" in link_href, link_href[0] == "#",
                   "javascript:" in link_href]): #don't add links that are not pages to queue
               continue
           else:
               if not (validators.url(link_href)):  # check if valid url
                   if subdomain == "":
                       link_href = "https://" + domain + link_href
                   else:
                       link_href = "https://" + subdomain + "." + domain + link_href
               if all([tldextract.extract(link_href).registered_domain == domain
                    #don't add outbounds to queue
                   , not(link_href in to_crawl)
                    #don't add pages already in queue
                   , all(path not in link_href for path in site_dict["disallow"])
                    #don't add disallowed pages
                   , any(path in link_href
    for path in site_dict['allow'])
    #check if link in any allowed path
               ]):
                   #print(link['href'])
                   to_crawl.append(link_href)
                   # ---------------------------------
       # Increment the counter for crawled pages
       n_crawled += 1

   # -------------------------------------------------POST CRAWL ANALYSIS-------------------------------------------
   # Check canonical status
   def canonical_check(url, canonical_link, redirect_url):
       if canonical_link == "no canonical":
           return "Missing canonical"
       elif redirect_url is not None:
           url = redirect_url
       if url == canonical_link:
           return "self referencing"
       else:
           return "canonicalized"
   canonical_status = list(map(canonical_check, url_crawled, canonical, redirect_url))

   # Check indexability
   def index_check(robots, xrobots, robotstxt):
       if any([robots == "noindex", xrobots == "noindex", robotstxt == "disallowed by robots.txt"]):
           return "noindex"
       else:
           return "index"
   index_status = list(map(index_check, robots, xrobots, robotstxt))
   # Check HTTPS
   def https_check(url):
       if "https" in url:
           return "https"
       elif "http" in url:
           return "http"
       else:
           return "Other"
   https_status = list(map(https_check, url_crawled))

   # Check H1
   h1_status = list(range(len(h1)))
   for h in range(len(h1)):
       if h1[h] is None:
           h1_status[h] = "Not applicable"
           continue
       elif h1[h] == "no h1":
           h1_status[h] = "Missing h1"
           continue
       elif h1[h] == "Multiple h1":
           h1_status[h] = "Multiple h1"
           continue
       elif redirect_url[h]  is not None and redirect_url[h] in url_crawled:
           h1_status[h] = "Redirect"
           continue
       else:
           for i in range(h+1, len(h1)):
               if h1[h] == h1[i] and redirect_url[i] is not None:
                   h1_status[h] = "Duplicate"
                   h1_status[i] = "Duplicate"
           if h1_status[h] == h:
               h1_status[h] = "No major issue"
    for hin range(len(h1)):
       if h1_status[h] == "Redirect":
           h1_status[h] = h1_status[url_crawled.index(redirect_url[h])]

   #Check title
   title_status = list(range(len(title)))
   for t in range(len(title)):
       if title[t] is None:
           title_status[t] = "Not applicable"
           continue
       elif title[t] == "no title":
           title_status[t] = "Missing title"
           continue

       elif redirect_url[t]  is not None and redirect_url[t] in url_crawled:
           title_status[t] = "Redirect"
           continue

       else:
           for u in range(t+1, len(title)):
               if title[t] == title[u] and redirect_url[u] is not None:
                   title_status[t] = "Duplicate"
                   title_status[u] = "Duplicate"
           if title_status[t] == t:
               title_status[t] = "No major issue"
   for t in range(len(title)):
       if title_status[t] == "Redirect":
           title_status[t] = title_status[url_crawled.index(redirect_url[t])]

   # Create a DataFrame from the lists of URL data
   dict = {'date': datetime.date.today(), 'domain': domain, 'urls': url_crawled, 'status_code': status_crawled,
           'redirect_url': redirect_url, 'canonical': canonical, 'canonical_status': canonical_status,
           'robots': robots, 'xrobots': xrobots, 'robotstxt': robotstxt, 'index_status': index_status,
           'https_status': https_status, 'h1': h1, 'h1_status': h1_status, 'title': title, 'title_status': title_status}
   result = pd.DataFrame(dict)
   return result

#----------------------------------------------------------------------------------------------------------------------



#-------------------------------------------------CALLING FUNCTION FOR SITES-------------------------------------------
#Each crawled site must be specified in a dictionary with:
# the starting page
# a list of paths disallowed (I will add /wp-admin/ as a default to all sites)
# a list of paths allowed for the crawler

wikipedia = {'start': "https://en.wikipedia.org/wiki/Main_Page",
                'disallow': ["/wp-admin/"],
                'allow':["https://en.wikipedia.org/wiki/Main_Page"]}

search_engine_land = {'start':
"https://searchengineland.com/",
'disallow':["/wp-admin/"],
'allow':["https://searchengineland.com/"]}

sites = [wikipedia, search_engine_land]

site_health = pd.DataFrame(columns=["date",
"domain",
"urls",
"status_code",
"redirect_url",
"canonical",
"canonical_status", "robots",
"xrobots",
"robotstxt",
"index_status",
"https_status",
"h1",
"h1_status",
"title",
"title_status"])

for site in sites:
   data = crawl_website(site, max_pages=500)
   site_health = pd.concat([site_health, data])
   print(data)

#table schema
schema = [{'name': 'date', 'type': 'DATE'},
         {'name': 'domain', 'type': 'STRING'},
         {'name': 'urls', 'type': 'STRING'},
         {'name': 'status_code', 'type': 'STRING'},
         {'name': 'redirect_url', 'type': 'STRING'},
         {'name': 'canonical', 'type': 'STRING'},
         {'name': 'canonical_status', 'type': 'STRING'},
         {'name': 'robots', 'type': 'STRING'},
         {'name': 'xrobots', 'type': 'STRING'},
         {'name': 'robotstxt', 'type': 'STRING'},
         {'name': 'index_status', 'type': 'STRING'},
         {'name': 'https_status', 'type': 'STRING'},
         {'name': 'h1', 'type': 'STRING'},
         {'name': 'h1_status', 'type': 'STRING'},
         {'name': 'title', 'type': 'STRING'},
         {'name': 'title_status', 'type': 'STRING'}]

#-------------------------------------------------NOW UPLOADING TO BIG QUERY-------------------------------------------
#BQ_Credential_File_Path = "credentials_path"
#BQ_Project_ID = "project_name"
#BQ_Job_Location = "eu"

#target_table = "data_set.table_name"
#ipg-mediabrands-sweden.SE_Adverity_Marathon.plan_data_python
credential = service_account.Credentials.from_service_account_file(BQ_Credential_File_Path)

#site_health.to_gbq(target_table, project_id=BQ_Project_ID, if_exists='append', location=BQ_Job_Location,
#                   progress_bar=False, credentials=credential, table_schema=schema)