import streamlit as st
import sqlite3
import pandas as pd

selected_areas = st.sidebar.multiselect('エリア', ['足立区','墨田区','荒川区','世田谷区','板橋区','台東区','江戸川区','千代田区','大田区','中央区','葛飾区','豊島区','北区','中野区','江東区','練馬区','品川区','文京区','渋谷区','港区','新宿区','目黒区','杉並区'])
selected_stations = st.sidebar.multiselect('駅名', ['渋谷駅', '新宿駅', '東京駅'])
selected_fee = st.sidebar.slider('家賃', value=[100000, 150000], min_value=30000, max_value=300000)
search_button = st.sidebar.button('検索する', type='primary')
options = ['人気度⭐⭐⭐以上', '人気度⭐⭐以上', '人気度⭐以上', '選択しない',]

# 初期化
if 'df_all' not in st.session_state:
    # データを取得
    db_path = 'techone_2.db'
    conn = sqlite3.connect(db_path)
    query = 'SELECT * FROM techone_db WHERE scraped_date_time = (SELECT MAX(scraped_date_time) FROM techone_db);'
    df = pd.read_sql_query(query, conn)
    conn.close()
    st.session_state.df_all = df


if 'page' not in st.session_state:
    st.session_state.page = 0
if 'search_button_clicked' not in st.session_state:
    st.session_state['search_button_clicked'] = False
if 'show_scored' not in st.session_state:
    st.session_state['show_scored'] = False
if 'show_all' not in st.session_state:
    st.session_state['show_all'] = False
if 'show_scored_button' not in st.session_state:
    st.session_state['show_scored_button'] = False
if 'show_all_button' not in st.session_state:
    st.session_state['show_all_button'] = False

# 検索を関数化
def filter_dataframe(criteria):
    """
    指定された検索条件に基づいてデータフレームをフィルタリングする関数

    :param df: フィルタリングするデータフレーム
    :param criteria: 検索条件を含む辞書
    :return: フィルタリングされたデータフレーム
    """
    df = st.session_state['df_all']
    if criteria['selected_areas']:
        df = df[df['address'].apply(lambda x: any(area in x for area in criteria['selected_areas']))]

    df = df[df['fee'].between(criteria['selected_fee'][0]/10000, criteria['selected_fee'][1]/10000)]

    # 他の検索条件に基づくフィルタリングもここに追加
    # 'evaluation_score' 列が文字列型の場合、数値型に変換
    if df['evaluation_score'].dtype == object:
        df['evaluation_score'] = pd.to_numeric(df['evaluation_score'], errors='coerce')
    df = df[df['evaluation_score']>=criteria['selected_evaluation_score']]

    return df


# 検索ボタンクリック
if search_button:
    # session_state内のsearch_button_clickedをTrueにする
    st.session_state['search_button_clicked'] = True

    st.session_state['search_criteria'] = {
        'selected_areas': selected_areas,
        'selected_fee': selected_fee,
        # 他の検索条件もここに追加
        'selected_evaluation_score': 0
    }

    criteria = st.session_state['search_criteria']
    df_filtered = filter_dataframe(criteria)
    st.session_state['df_filtered'] = df_filtered

# 初期画面（検索ボタン未クリック）
if not st.session_state['search_button_clicked']:
    st.image('topimage.jpg')

if st.session_state['search_button_clicked']:
    selected_dataset = st.selectbox('人気物件度を選択', options, index=2)
    if selected_dataset == '人気度⭐⭐⭐以上':
        st.session_state['search_criteria']['selected_evaluation_score'] = 3
        criteria = st.session_state['search_criteria']
        st.write(st.session_state['search_criteria'])
        df_filtered = filter_dataframe(criteria)
        st.session_state['df_filtered'] = df_filtered
        st.dataframe(df_filtered, hide_index=True, use_container_width=True)
    #st.dataframe(st.session_state['df_filtered'], hide_index=True, use_container_width=True)
    # st.session_state['show_scored_button'] = True
    # st.session_state['show_all_button'] = True
    if selected_dataset == '人気度⭐⭐以上':
        st.session_state['search_criteria']['selected_evaluation_score'] = 2
        criteria = st.session_state['search_criteria']
        st.write(st.session_state['search_criteria'])
        df_filtered = filter_dataframe(criteria)
        st.session_state['df_filtered'] = df_filtered
        st.dataframe(df_filtered, hide_index=True, use_container_width=True)
    if selected_dataset == '人気度⭐以上':
        st.session_state['search_criteria']['selected_evaluation_score'] = 1
        criteria = st.session_state['search_criteria']
        st.write(st.session_state['search_criteria'])
        df_filtered = filter_dataframe(criteria)
        st.session_state['df_filtered'] = df_filtered
        st.dataframe(df_filtered, hide_index=True, use_container_width=True)
if st.session_state['show_scored_button']:
    show_scored_button = st.button('人気物件をもっと見る')
    if show_scored_button:
        st.session_state['show_scored'] = True
        st.session_state['show_scored_button'] = False
        # session_stateの「score」の値を1以上にして保存
        st.session_state['search_criteria']['selected_evaluation_score'] = 2
        criteria = st.session_state['search_criteria']
        st.write(st.session_state['search_criteria'])
        df_filtered = filter_dataframe(criteria)
        st.session_state['df_filtered'] = df_filtered
if st.session_state['show_all_button']:
    all_button = st.button('物件一覧をもっと見る')
    if all_button:
        st.session_state['show_all'] = True
        # session_stateの「score」の値をなしにして保存
        st.session_state['search_criteria']['selected_evaluation_score'] = 1
        criteria = st.session_state['search_criteria']
        df_filtered = filter_dataframe(criteria)
if st.session_state['show_scored']:
    st.dataframe(st.session_state['df_filtered'], hide_index=True, use_container_width=True)
if st.session_state['show_all']:
    st.dataframe(st.session_state['df_filtered'], hide_index=True, use_container_width=True)

# st.dataframe(df_filtered, hide_index=True, use_container_width=True)

# 検索後は、ドロップダウンで選んでデータを並べ替えるだけにする
# ドロップダウンの値でif分岐→criteria保存→検索実行して表示
