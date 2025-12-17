from urllib.request import Request, urlopen, HTTPError
import os
import json
from multiprocessing import Process, Array
import sys
import requests
import pandas as pd
import numpy as np

## to find this, right click and 'inspect element' on the workday page in your browser. from there, navigate to the network tab
## and ctrl + r to refresh the page. you should see a whole bunch of requests come in. sort by Fetch/XHR and click through them until you see one 
## that has a Request Method: of POST instead of GET and it has a request URL and payload that makes sense
POST_url = "https://tempus.wd5.myworkdayjobs.com/wday/cxs/tempus/Tempus_Careers/jobs"
ind_job_url = "https://tempus.wd5.myworkdayjobs.com/en-US/Tempus_Careers/job/"
payload = {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": ""}


def today_jobs(POST_url, ind_job_url,payload):

    url = POST_url
    payload = payload
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.post(url, json=payload, headers=headers)

    offsets = np.arange(0, r.json()['total'], 20)
    titles = []
    location = []
    postedOn = []
    externalURL = []

    for offset in offsets:
        
        url = POST_url
        payload['offset'] = float(offset)
        payload = payload
        headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
        }
        
        
        r = requests.post(url, json=payload, headers=headers)
        data = r.json()
        for job in data["jobPostings"]:
            titles = np.append(titles, job.get('title'))
            location = np.append(location, job.get("locationsText", ""))
            postedOn = np.append(postedOn, job.get('postedOn'))

            try:
                externalURL = np.append(externalURL, ind_job_url+ job['externalPath'].split('/')[-1])
            except:
                externalURL = np.append(externalURL, 'not avail')

    pd.set_option('display.max_colwidth', 800)
    jobs_dict = dict(zip(['location', 'postedOn', 'titles', 'externalURL'], [location, postedOn, titles, externalURL]))
    df = pd.DataFrame(jobs_dict)
    posted_recently = df[df["postedOn"].str.contains('Posted Today|Posted Yesterday', case=False, na=False)]
    location = posted_recently
    return location

import smtplib
from email.message import EmailMessage
from datetime import datetime

def send_email_report(df):
    if df.empty:
        body = "No new job postings today."
    else:
        body = f"{len(df)} new job(s) posted today:\n\n" + "\n".join(df['title'].tolist())

    msg = EmailMessage()
    msg['Subject'] = f"Tempus Workday Jobs Report – {datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = 'bdev1238@gmail.com'
    msg['To'] = "benjamin.devlin@duke.edu"
    msg.set_content(body)

    # Attach CSV if there are new postings
    if not df.empty:
        csv_data = df.to_csv(index=False)
        msg.add_attachment(csv_data, filename="tempus_workday_jobs_today.csv", subtype="csv")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login('bdev1238@gmail.com', 'macw dblk fqmc qldy')
        smtp.send_message(msg)

# Call this after your DataFrame is ready:
send_email_report(today_jobs(POST_url,ind_job_url, payload))