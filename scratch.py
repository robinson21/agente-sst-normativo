import requests
from bs4 import BeautifulSoup
url = "https://www.suseso.cl/607/w3-propertyvalue-10368.html" # Normativa
try:
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers, timeout=10)
    print("STATUS:", r.status_code)
    soup = BeautifulSoup(r.text, 'html.parser')
    for a in soup.find_all('a', href=True):
        if '/607/' in a['href'] or '/608/' in a['href'] or '/612/' in a['href']:
             text = a.text.strip()
             if len(text) > 20:
                print(text)
except Exception as e:
    print(e)
