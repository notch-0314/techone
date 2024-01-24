import streamlit as st
import sqlite3
import pandas as pd

# ページ設定を行う
st.set_page_config(layout="wide")

selected_areas = st.sidebar.multiselect('エリア', ['足立区','墨田区','荒川区','世田谷区','板橋区','台東区','江戸川区','千代田区','大田区','中央区','葛飾区','豊島区','北区','中野区','江東区','練馬区','品川区','文京区','渋谷区','港区','新宿区','目黒区','杉並区'])
selected_stations = st.sidebar.multiselect('駅名', ['渋谷駅', '新宿駅', '東京駅'])
selected_fee = st.sidebar.slider('家賃', value=[50000, 250000], min_value=30000, max_value=300000)
search_button = st.sidebar.button('検索する', type='primary')
options = ['人気度⭐⭐⭐以上', '人気度⭐⭐以上', '人気度⭐以上', 'すべて']

# 初期化
if 'df_all' not in st.session_state:
    # データを取得
    db_path = 'techone_2.db'
    conn = sqlite3.connect(db_path)
    query = 'SELECT * FROM techone_db WHERE scraped_date_time = (SELECT MAX(scraped_date_time) FROM techone_db);'
    df = pd.read_sql_query(query, conn)
    conn.close()
    df['checked'] = False
    st.session_state.df_all = df


if 'search_button_clicked' not in st.session_state:
    st.session_state['search_button_clicked'] = False
if 'selected_items' not in st.session_state:
    st.session_state.selected_items = []


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
    # 欠損値（null）を0で埋める
    df['evaluation_score'] = df['evaluation_score'].fillna(0)
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
    st.session_state['df_filtered'] = filter_dataframe(criteria)

# 初期画面（検索ボタン未クリック）
if not st.session_state['search_button_clicked']:
    st.image('topimage.jpg')

if st.session_state['search_button_clicked']:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader('人気度の高い物件一覧')
    with col2:
        with st.expander("人気度とは？"):
            st.write("""
                マンションごとに最近の販売状況を表したスコアです。
                最近1ヶ月で販売があればスコアがつき、
                スコアがついた中でも上位60%以上の販売数のマンションには人気度⭐⭐、
                上位30%以上の販売数のマンションには人気度⭐⭐⭐ がついています。
            """)
    selected_dataset = st.selectbox('', options, index=2)
    if selected_dataset == '人気度⭐⭐⭐以上':
        st.session_state['search_criteria']['selected_evaluation_score'] = 3
    if selected_dataset == '人気度⭐⭐以上':
        st.session_state['search_criteria']['selected_evaluation_score'] = 2
    if selected_dataset == '人気度⭐以上':
        st.session_state['search_criteria']['selected_evaluation_score'] = 1
    if selected_dataset == 'すべて':
        st.session_state['search_criteria']['selected_evaluation_score'] = 0
    criteria = st.session_state['search_criteria']
    st.session_state['df_filtered'] = filter_dataframe(criteria)
    df_limit = st.session_state['df_filtered'].head(50)
    if len(df_limit) == 0:
        st.error('検索結果はありません。別の検索をお試しください。')
    else:
        # カスタム関数を定義
        def create_combined_text(row):
            parts = []

            # evaluation_scoreに基づくテキストを追加
            if row['evaluation_score'] == 3:
                parts.append('人気度⭐⭐⭐')
            elif row['evaluation_score'] == 2:
                parts.append('人気度⭐⭐')
            elif row['evaluation_score'] == 1:
                parts.append('人気度⭐')

            # depositが0の場合
            if row['deposit'] == 0:
                parts.append('敷金無料')

            # gratuityが0の場合
            if row['gratuity'] == 0:
                parts.append('礼金無料')

            # 生成された文字列を「/」で結合
            return ' / '.join(parts)

        # apply関数を使用して行ごとにカスタム関数を適用
        df_limit['good_point'] = df_limit.apply(create_combined_text, axis=1)

        # 'evaluation_score'の値に基づいて'text'を設定
        def score_to_text(score):
            if score == 3:
                return '人気度⭐⭐⭐'
            elif score == 2:
                return '人気度⭐⭐'
            elif score == 1:
                return '人気度⭐'
            else:
                return ''
        df_limit['evaluation_score_text'] = df_limit['evaluation_score'].apply(score_to_text)
        # カスタム関数を定義
        def format_total_sold_count(value):
            # NaNの場合は空の文字列を返す
            if pd.isna(value):
                return ''
            # NaNでない場合は整数に変換してテキストを設定
            else:
                return f'{int(value)}部屋以上が契約済'

        # apply関数を使用して行ごとにカスタム関数を適用
        df_limit['total_sold_count_text'] = df_limit['total_sold_count'].apply(format_total_sold_count)
        df_limit['total_fee_text'] = df_limit['fee'].astype(str) + '万円(' + df_limit['management_fee'].astype(str) + '万円)'
        # カスタム関数を定義
        def format_deposit_and_gratuity(row):
            deposit_text = '無料' if row['deposit'] == 0 else f"{row['deposit']}万円"
            gratuity_text = '無料' if row['gratuity'] == 0 else f"{row['gratuity']}万円"
            return f"{deposit_text} / {gratuity_text}"

        # apply関数を使用して行ごとにカスタム関数を適用
        df_limit['deposit_text'] = df_limit.apply(format_deposit_and_gratuity, axis=1)
        df_limit['access_1_station'] = df_limit['access1_1'] + ' ' +df_limit['access1_2']
        df_limit['access_1_time'] = '徒歩' + df_limit['access1_3'] + '分'
        df_limit = df_limit[['checked', 'good_point', 'title', 'total_sold_count_text', 'total_fee_text', 'deposit_text', 'madori', 'access_1_station', 'access_1_time', 'evaluation_score_text', 'address']]
        df_display = st.data_editor(
            df_limit,
            column_config={
                'checked': '',
                'good_point': 'おすすめポイント',
                'title': '物件名',
                'total_sold_count_text': '直近1ヶ月の状況',
                'total_fee_text': '家賃(管理費)',
                'deposit_text': '敷金 / 礼金',
                'madori': '間取り',
                'access_1_station': '最寄り駅',
                'access_1_time': '徒歩分数',
                'evaluation_score_text': '人気度',
                'address': '住所',
            },
            height=550,
            disabled=['good_point', 'title', 'total_sold_count_text', 'total_fee_text', 'deposit_text', 'madori', 'access_1_station', 'access_1_time', 'evaluation_score_text', 'address'],
            hide_index=True,
        )
        # ボタンが押されたときの動作
        if st.button("チェックした物件をメールに送信"):
            selected_items = df_display[df_display['checked']]['title'].tolist()
            st.session_state.selected_items = selected_items
            # リスト内の要素をカンマで区切って結合
            items_str = '、'.join(selected_items)
            # 結合された文字列をst.successで表示
            st.success(f"{items_str}の情報をメールで送信しました。")

