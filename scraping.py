#!/usr/bin/env python
# coding: utf-8

# In[50]:


import requests
from bs4 import BeautifulSoup
from pprint import pprint
import time
import pandas as pd
import re
from tqdm import tqdm
import sqlite3
import numpy as np


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
url = 'https://airdoor.jp/list?si=d-131016-131024-131032-131041-131059-131067-131075-131083-131091-131105-131113-131121-131130-131148-131156-131164-131172-131181-131199-131202-131211-131229-131237&p={}'

for i in tqdm(range(1,200)):
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
current_time = datetime.today().strftime('%Y-%m-%d %H:%M')
df_scraped['scraped_date_time'] = current_time


# In[ ]:


# データを読み込んでdf_dbに格納
db_path = 'techone_2.db'
conn = sqlite3.connect(db_path)
query = 'SELECT * FROM techone_db;'
df_db = pd.read_sql_query(query, conn)
conn.close()

# df_dbのうち、最新のもののみをdf_db_1に格納
last_datetime = df_db['scraped_date_time'].max()
df_db_1 = df_db[df_db['scraped_date_time']==last_datetime]

# df_db_1のscraped_date_timeは使用しないのでカラム名を変更する
df_db_1.rename(columns={'scraped_date_time': 'scraped_date_time_last_time'}, inplace=True)

# df_db_1にあってdf_scrapedにない部屋を抽出してdf_uniqueに入れる
df_merged = pd.merge(df_db_1, df_scraped[['title', 'address', 'room_number', 'scraped_date_time']], on=['title', 'address', 'room_number'], how='left', indicator=True)

# scraped_date_timeのすべてに日時を入れる
latest_scraped_time = df_merged['scraped_date_time'].dropna().unique()[0]
df_merged['scraped_date_time'] = df_merged['scraped_date_time'].fillna(latest_scraped_time)

df_unique = df_merged[df_merged['_merge']=='left_only']

# 直近、いつ、どのマンションの部屋が何部屋減ったかを表示するdf_sold_last_timeを作成
df_sold_last_time = df_unique.groupby(['title', 'address', 'scraped_date_time']).size().reset_index(name='count')
df_sold_last_time.shape



# In[56]:


# techone_sold_count テーブルに書き込み
conn = sqlite3.connect('techone_2.db')
df_sold_last_time.to_sql('techone_sold_count', conn, if_exists='append', index=False)
conn.close()

# techone_sold_count テーブルを読み込んでdf_sold_all_timeを作成
db_path = 'techone_2.db'
conn = sqlite3.connect(db_path)
query = 'SELECT * FROM techone_sold_count;'
df_sold_all_time = pd.read_sql_query(query, conn)
conn.close()

# title、addressをキーにcountを合計
df_sold_total_count = df_sold_all_time.groupby(['title', 'address'])['count'].sum().reset_index(name='total_count')


# In[57]:

# 条件を設定
conditions = [
    df_sold_total_count['total_count'] < 5,  # 最大値の1/3以下
    (5 <= df_sold_total_count['total_count']) & (df_sold_total_count['total_count'] < 10),  # 最大値の1/3を超え、2/3未満
    df_sold_total_count['total_count'] >= 10  # 最大値の2/3以上
]
# 各条件に対する値を設定
values = [1, 2, 3]
# numpy.selectを使用して条件に基づく値を設定
df_sold_total_count['evaluation'] = np.select(conditions, values, default=np.nan)


# In[58]:


# スクレイピングしたデータに、販売済みの部屋数と評価値をつけた df_scraped_with_score を作成
df_scraped_with_score = pd.merge(df_scraped, df_sold_total_count[['title', 'address', 'total_count', 'evaluation']], on=['title', 'address'], how='left')
df_scraped_with_score['evaluation_score'] = df_scraped_with_score['evaluation']
df_scraped_with_score['total_sold_count'] = df_scraped_with_score['total_count']
df_scraped_with_score.drop(columns=['evaluation', 'total_count'], inplace=True)
df_scraped_with_score


# In[59]:


# techone_db テーブルに書き込み
conn = sqlite3.connect('techone_2.db')
df_scraped_with_score.to_sql('techone_db', conn, if_exists='append', index=False)
conn.close()


# In[ ]:




