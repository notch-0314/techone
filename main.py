import streamlit as st
import sqlite3
import pandas as pd

# データを取得してdf_dbに格納
db_path = 'techone_2.db'
conn = sqlite3.connect(db_path)
query = 'SELECT * FROM techone_scraped WHERE scraped_date_time = (SELECT MAX(scraped_date_time) FROM techone_scraped);'
df_db = pd.read_sql_query(query, conn)
print(df_db)
conn.close()


area = st.sidebar.multiselect('エリア', ['千代田区', '中央区', '江東区'])
station = st.sidebar.multiselect('駅名', ['渋谷駅', '新宿駅', '東京駅'])
fee = st.sidebar.slider('家賃', value=[100000, 150000], min_value=30000, max_value=300000)
st.sidebar.button('検索する', type='primary')

st.dataframe(df_db, hide_index=True, use_container_width=True)


