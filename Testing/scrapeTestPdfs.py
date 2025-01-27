import os
import requests
from bs4 import BeautifulSoup
import logging
import threading

logging.captureWarnings(True)

years = [2021, 2022, 2023,2024]
base_url = "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?from={year}-01-01&format=pdf"

def download_pdfs(year):
    url = base_url.format(year=year)
    response = requests.get(url, verify=False)
    soup = BeautifulSoup(response.text, "lxml")
    
    pdf_dict = {}
    for record in soup.find_all("record"):
        record_id = record.get("id")
        record_citation = record.get("citation")
        link = record.find("link", {"format": "pdf"})
        if None not in [record_id, link, record_citation]:
            pdf_dict[record_id] = [record_citation, "https://" + link.get("href").split("ftp://")[1]]
    
    os.makedirs(f"./TestPdfs/{year}", exist_ok=True)
    
    for idx, (record_id, record_info) in enumerate(pdf_dict.items(), start=1):
        record_citation, record_url = record_info[0], record_info[1]
        print(f"{idx}/{len(pdf_dict)} ({year})\n{record_citation} : {record_url}\n")

        if f"{record_id}.pdf" in os.listdir(f"./TestPdfs/{year}"):
            continue
        
        response = requests.get(record_url, verify=False)
        with open(f"./TestPdfs/{year}/{record_id}.pdf", "wb") as f:
            f.write(response.content)
    
threads = []
for year in years:
    thread = threading.Thread(target=download_pdfs, args=(year,))
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()