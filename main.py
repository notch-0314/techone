import streamlit as st
import sqlite3
import pandas as pd

# データを取得してdf_dbに格納
db_path = 'techone_2.db'
conn = sqlite3.connect(db_path)
query = 'SELECT * FROM techone_db WHERE scraped_date_time = (SELECT MAX(scraped_date_time) FROM techone_db);'
df_db = pd.read_sql_query(query, conn)
conn.close()

selected_areas = st.sidebar.multiselect('エリア', ['足立区','墨田区','荒川区','世田谷区','板橋区','台東区','江戸川区','千代田区','大田区','中央区','葛飾区','豊島区','北区','中野区','江東区','練馬区','品川区','文京区','渋谷区','港区','新宿区','目黒区','杉並区'])
selected_stations = st.sidebar.multiselect('駅名', ['渋谷駅', '新宿駅', '東京駅'])
selected_fee = st.sidebar.slider('家賃', value=[100000, 150000], min_value=30000, max_value=300000)
search_button = st.sidebar.button('検索する', type='primary')

if 'search_button_clicked' not in st.session_state:
    st.session_state['search_button_clicked'] = False


if search_button:
    # session_state内のsearch_button_clickedをTrueにする
    st.session_state['search_button_clicked'] = True

if st.session_state['search_button_clicked']:
    # area
    if selected_areas:
        df_filtered = df_db[df_db['address'].apply(lambda x: any(area in x for area in selected_areas))]
    else:
        df_filtered = df_db

    # fee
    df_filtered = df_filtered[df_filtered['fee'].between(selected_fee[0]/10000, selected_fee[1]/10000)]

    st.dataframe(df_filtered, hide_index=True, use_container_width=True)


# st.dataframe(df_filtered, hide_index=True, use_container_width=True)


