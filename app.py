import streamlit as st
import pandas as pd
import math

# 페이지 설정
st.set_page_config(page_title="🀄 리치마작 가이드", page_icon="🀄", layout="wide")

# 사이드바 네비게이션
st.sidebar.title("🀄 리치마작 메뉴")
menu = st.sidebar.radio("이동할 페이지를 선택하세요:", ["홈 (소개)", "역(족보) 사전", "점수 계산기"])

# ----------------------------------------
# 1. 홈 (소개) 페이지
# ----------------------------------------
if menu == "홈 (소개)":
    st.title("🀄 리치마작 (Riichi Mahjong) 가이드")
    st.markdown("""
    환영합니다! 이 사이트는 **리치마작** 입문자 및 플레이어들을 위한 가이드 사이트입니다.
    좌측 메뉴를 통해 마작의 족보(역)를 확인하거나, 점수를 계산해 보세요.
    
    ### 📌 리치마작이란?
    리치마작은 일본에서 발전한 마작의 한 종류로, 전 세계적으로 가장 인기 있는 마작 규칙 중 하나입니다.
    기본적으로 13장의 패를 들고 시작하며, 1장을 가져오고 1장을 버리는 과정을 반복하여 **4개의 몸통과 1개의 머리(4면자 1안커)** 를 먼저 완성하는 사람이 승리합니다.
    
    ### 🎲 기본 용어
    *   **수패**: 만즈(萬), 통즈(筒), 소즈(索)로 이루어진 숫자패 (각 1~9)
    *   **자패**: 풍패(동, 남, 서, 북)와 삼원패(백, 발, 중)
    *   **멘젠**: 남의 버림패를 가져오지(치, 퐁, 깡) 않고 스스로 패를 완성해 나가는 상태
    *   **텐파이**: 화료(승리)까지 단 1장의 패만 남은 상태
    *   **리치**: 멘젠 상태에서 텐파이가 되었을 때, 1000점을 공탁하고 선언하는 행위
    """)
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Mahjong_tiles_set.jpg/800px-Mahjong_tiles_set.jpg", caption="마작패 세트 예시")

# ----------------------------------------
# 2. 역(족보) 사전 페이지
# ----------------------------------------
elif menu == "역(족보) 사전":
    st.title("📖 리치마작 역(족보) 사전")
    st.write("마작에서 승리하기 위해서는 최소 1판 이상의 '역'이 필요합니다. 아래에서 대표적인 역들을 확인하세요.")
    
    # 데이터프레임으로 족보 리스트 만들기
    yaku_data = {
        "판수": ["1판", "1판", "1판", "1판", "2판", "2판", "2판", "3판", "3판", "6판", "역만", "역만"],
        "역 이름": ["리치 (立直)", "탕야오 (断幺九)", "핑후 (平和)", "역패 (役牌)", 
                 "삼색동순 (三色同順)", "일기통관 (一気通貫)", "또이또이 (対々和)", 
                 "혼일색 (混一色)", "량페코 (二盃口)", "청일색 (清一色)", 
                 "국사무쌍 (国士無双)", "대삼원 (大三元)"],
        "설명": [
            "멘젠 텐파이 상태에서 1000점을 내고 선언",
            "1, 9, 자패 없이 2~8의 수패로만 구성",
            "모든 몸통이 슌츠(연속된 숫자)이며, 대기패가 양면대기인 멘젠 상태",
            "백, 발, 중 또는 장풍/자풍을 3장 모음",
            "만즈, 통즈, 소즈에서 같은 숫자의 슌츠 3개를 모음 (울면 1판)",
            "같은 종류의 수패로 123, 456, 789를 모음 (울면 1판)",
            "모든 몸통을 커츠(같은 패 3장)로 구성",
            "한 종류의 수패와 자패로만 구성 (울면 2판)",
            "같은 슌츠 2쌍을 2개 만듦 (멘젠 한정)",
            "자패 없이 단 한 종류의 수패로만 구성 (울면 5판)",
            "1, 9패와 모든 자패를 1장씩 모으고 그 중 하나를 머리로 만듦",
            "백, 발, 중 3가지를 모두 3장씩 모음"
        ]
    }
    
    df = pd.DataFrame(yaku_data)
    
    # 판수별 필터링 기능
    selected_han = st.selectbox("판수 필터링:", ["전체", "1판", "2판", "3판", "6판", "역만"])
    
    if selected_han != "전체":
        filtered_df = df[df["판수"] == selected_han]
        st.table(filtered_df.reset_index(drop=True))
    else:
        st.table(df.reset_index(drop=True))

# ----------------------------------------
# 3. 점수 계산기 페이지
# ----------------------------------------
elif menu == "점수 계산기":
    st.title("🧮 점수 계산기 (론 화료 기준)")
    st.write("판수(飜)와 부수(符)를 입력하면 기본 론(Ron) 점수를 계산해 줍니다.")
    
    col1, col2 = st.columns(2)
    with col1:
        is_oya = st.radio("포지션", ["자 (Ko)", "친 (Oya/Dealer)"])
        han = st.number_input("판수 (Han)", min_value=1, max_value=13, value=1)
    
    with col2:
        if han < 5:
            fu_options = [20, 25, 30, 40, 50, 60, 70, 80, 90, 100, 110]
            fu = st.selectbox("부수 (Fu)", fu_options, index=2)
        else:
            st.info("5판 이상은 만관 이상이 확정되어 부수를 계산하지 않습니다.")
            fu = 0
            
    if st.button("점수 계산하기", type="primary"):
        is_dealer = True if is_oya == "친 (Oya/Dealer)" else False
        
        # 점수 계산 로직
        score_name = "기본 점수"
        total_score = 0
        
        if han >= 13:
            score_name = "역만 (Yakuman)"
            total_score = 48000 if is_dealer else 32000
        elif han >= 11:
            score_name = "삼배만 (Sanbaiman)"
            total_score = 36000 if is_dealer else 24000
        elif han >= 8:
            score_name = "배만 (Baiman)"
            total_score = 24000 if is_dealer else 16000
        elif han >= 6:
            score_name = "하네만 (Haneman)"
            total_score = 18000 if is_dealer else 12000
        elif han == 5 or (han == 4 and fu >= 40) or (han == 3 and fu >= 70):
            score_name = "만관 (Mangan)"
            total_score = 12000 if is_dealer else 8000
        else:
            # 기본 점수 공식: 기본점 = 부수 * 2^(판수+2)
            base_points = fu * math.pow(2, han + 2)
            if is_dealer:
                total_score = math.ceil((base_points * 6) / 100) * 100
            else:
                total_score = math.ceil((base_points * 4) / 100) * 100
                
        st.success(f"### 🎉 최종 점수: {int(total_score)} 점 ({score_name})")
        if score_name != "기본 점수":
            st.balloons()
