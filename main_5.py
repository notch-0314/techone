#!/usr/bin/env python
# coding: utf-8

# In[7]:


import requests
from bs4 import BeautifulSoup
from pprint import pprint
import time
import pandas as pd
import re
from tqdm import tqdm
import streamlit as st
import sqlite3


# In[2]:


def extract_number(text, return_type=float):
    """テキスト内から数字を取り出して返す（float or int）

    Parameters:
    ----------
    text : str
        数字が入ったテキスト
    return_type : type
        返す値の型。引数なしではfloat型となる

    Returns:
    ----------
    型：return_typeで選択した型
        textから取り出した数字を返す
    """
    matched_text = re.search(r'\d+(\.\d+)?', text)
    if matched_text:
        number = matched_text.group()
        if return_type == int:
            return int(float(number))  # floatへの変換後にintへ変換
        else:
            return float(number)
    else:
        return 0 if return_type == int else 0.0


# In[15]:


# Airdoorデータ取得
d_list = []
url = 'https://airdoor.jp/list?si=d-131083&p={}'

for i in tqdm(range(1,15)):
    target_url = url.format(i)
    r = requests.get(target_url)
    time.sleep(1) # 1秒ずつ
    soup = BeautifulSoup(r.text,"html.parser")
    contents = soup.find_all('div', {'class': 'PropertyPanel_propertyPanel__8oJ13'}) or None
    for content in contents:
        # タイトル
        title = content.find('div', {'class': 'PropertyPanelBuilding_buildingTitle__tuPqN'}).get_text(strip=True) or None
        # 住所
        building_info = content.find_all('div', {'class': 'PropertyPanelBuilding_buildingInformationSection__deSLp'})
        address = building_info[0].find('p', {'class': 'is-mt5'}).get_text(strip=True) or None
        access = ', '.join(p.get_text() for p in building_info[0].find_all('p', {'class': False})) or None
        # 築年数、総階数
        p_tags = building_info[1].find_all('p')
        age = re.search(r'\((.*?)\)', p_tags[0].get_text()).group(1) or '築0年'
        story = p_tags[1].get_text(strip=True)
        # 階数、間取り、面積
        roomItems = content.findAll('a', {'class': 'PropertyPanelRoom_roomItem__95jRr'})
        for roomItem in roomItems:
            p_tag_text = roomItem.find('span', {'class': 'is-ml5'}).get_text(strip=True)
            room_number, madori, menseki, hogaku = [part.strip() for part in p_tag_text.split('/')]
            # 階数
            floor = re.findall(r'\d+', room_number)[0][:-2] if re.findall(r'\d+', room_number) and len(re.findall(r'\d+', room_number)[0]) > 2 else '1'
            # 家賃、管理費
            div_text = roomItem.find('div', {'class': 'PropertyPanelRoom_rentPrice__XdPUp'}).text
            fee = div_text.split()[0].replace(',', '') or '0円'
            management_fee = div_text.split()[1].replace(',', '') or '0円'
            # 敷金、礼金
            div = roomItem.find('div', {'class': 'PropertyPanelRoom_initialPrices__d90C3'})
            deposit = div.find_all('li')[0].get_text(strip=True) or '0円'
            gratuity = div.find_all('li')[1].get_text(strip=True) or '0円'
            d = {
                'title': title,
                'address': address,
                'access': access,
                'age': age,
                'story': story,
                'floor': floor,
                'room_number': room_number,
                'fee': fee,
                'management_fee': management_fee,
                'deposit': deposit,
                'gratuity': gratuity,
                'madori': madori,
                'menseki': menseki,
            }
            d_list.append(d)
df_airdoor = pd.DataFrame(d_list)


# In[16]:


df_airdoor['title'] = df_airdoor['title'].str.replace(r'【.*?】', '', regex=True)
df_airdoor['fee'] = df_airdoor['fee'].apply(extract_number)/10000
df_airdoor['management_fee'] = df_airdoor['management_fee'].apply(extract_number)/10000
df_airdoor['deposit'] = df_airdoor['deposit'].apply(lambda x: "0円" if x in ["無料"] else x).apply(extract_number)
df_airdoor['gratuity'] = df_airdoor['gratuity'].apply(lambda x: "0円" if x in ["無料"] else x).apply(extract_number)
df_airdoor['age'] = df_airdoor['age'].apply(lambda x: "築1年" if x in ["新築", "築0年"] else x).apply(extract_number)
df_airdoor['story'] = df_airdoor['story'].apply(extract_number)
df_airdoor['floor'] = df_airdoor['floor'].apply(extract_number)
df_airdoor['menseki'] = df_airdoor['menseki'].apply(extract_number)


# In[17]:


# accessを取得し、「路線」「駅名」「徒歩分数」に分割し、それぞれ「access1_1」「access1_2」「access1_3」に格納する。アクセスは最大2件まで取得する
# df_airdoorにカラム追加
for i in range(1, 3):
    for j in range(1, 4):
        df_airdoor[f'access{i}_{j}'] = ''
df_airdoor.head()
# 行ごとにテキストを分解してカラムに格納
for index, row in df_airdoor.iterrows():
    accesses = row['access'].split(',')[:3] # アクセス情報をコンマで分割し、最大3つまで取得
    for i, access in enumerate(accesses, start=1):
        match = re.match(r'(.+?)\s+(.+?)\s+徒歩(\d+)分', access.strip()) # 正規表現でテキストを解析
        if match:
            df_airdoor.at[index, f'access{i}_1'] = match.group(1)
            df_airdoor.at[index, f'access{i}_2'] = match.group(2)
            df_airdoor.at[index, f'access{i}_3'] = match.group(3)


# In[26]:


# 複数のスクレイピングデータを統合、重複物件を排除する場合はここで
df_scraped = df_airdoor

# 共通データを付与
from datetime import datetime
current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
df_scraped['scraped_date_time'] = current_time
df_scraped['daily_decreased_room'] = None
df_scraped['weekly_decreased_room'] = None
df_scraped['evaluation_score'] = None

print(df_scraped.head())


# SQLiteデータベースへの接続
conn = sqlite3.connect('/Users/ryosukeinoue/Library/CloudStorage/GoogleDrive-ryosuke.inoue0314@gmail.com/マイドライブ/00_本データ/31_Tech0/Step3/techone_new/techone_2.db')

# DataFrameをSQLiteデータベースにインポート
df_airdoor.to_sql('techone_db', conn, if_exists='append', index=False)

# 接続を閉じる
conn.close()

# In[ ]:




