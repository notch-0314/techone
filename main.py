
import requests
from bs4 import BeautifulSoup
from pprint import pprint
import time
import pandas as pd

# 事前準備
url = 'https://suumo.jp/chintai/tokyo/sc_koto/?page={}'
d_list = []

for i in range(1,4):
    print(len(d_list))
    target_url = url.format(i)
    r = requests.get(target_url)
    time.sleep(1)
    soup = BeautifulSoup(r.text,"html.parser")
    
    contents = soup.find_all('div', class_='cassetteitem')

    for content in contents:
        detail = content.find('div', class_='cassetteitem-detail')
        table = content.find('table', class_='cassetteitem_other')
        title = detail.find('div', class_='cassetteitem_content-title').text
        address = detail.find('li', class_='cassetteitem_detail-col1').text
        access = detail.find('li', class_='cassetteitem_detail-col2').text
        age = detail.find('li', class_='cassetteitem_detail-col3').text
        trtags = table.find_all('tr', class_='js-cassette_link')
        for trtag in trtags:
            floor, price, first_fee, capacity = trtag.find_all('td')[2:6]
            fee, management_fee = price.find_all('li')
            deposit, gratuity = first_fee.find_all('li')
            madori, menseki = capacity.find_all('li')
            d = {
                'title': title,
                'address': address,
                'access': access,
                'age': age,
                'floor': floor.text,
                'fee': fee.text,
                'management_fee': management_fee.text,
                'deposit': deposit.text,
                'gratuity': gratuity.text,
                'madori': madori.text,
                'menseki': menseki.text,
            }
            d_list.append(d)

df = pd.DataFrame(d_list)
print(df.head(5))

