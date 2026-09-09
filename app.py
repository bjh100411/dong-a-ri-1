import streamlit as st
import time
import random

# ---------------------------------------------------------
# 1. 페이지 설정 및 커스텀 CSS
# ---------------------------------------------------------
st.set_page_config(
    page_title="QTE 커맨드 히어로!",
    page_icon="⚔️",
    layout="centered"
)

st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
    }
    .qte-container {
        background: linear-gradient(135deg, #1f2937, #111827);
        border: 3px solid #ff4b4b;
        border-radius: 15px;
        padding: 25px;
        text-align: center;
        box-shadow: 0 0 20px rgba(255, 75, 75, 0.3);
        margin-bottom: 20px;
    }
    .qte-command {
        font-size: 45px;
        font-weight: 900;
        color: #00f2fe;
        letter-spacing: 5px;
        text-shadow: 0 0 12px rgba(0, 242, 254, 0.8);
        margin: 15px 0;
    }
    .hud-card {
        background-color: #1f2937;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #374151;
    }
    .hud-title {
        font-size: 12px;
        color: #9ca3af;
        margin-bottom: 2px;
    }
    .hud-value {
        font-size: 20px;
        font-weight: bold;
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. 커맨드 풀 및 게임 데이터
# ---------------------------------------------------------
COMMAND_POOL = [
    "ATTACK", "DEFEND", "PARRY", "DODGE", "SLASH", 
    "SMASH", "HEAL", "FIREBALL", "CRITICAL", "COUNTER",
    "SHIELD", "BURST", "STRIKE", "CHARGE", "ULTIMATE"
]

# ---------------------------------------------------------
# 3. 세션 상태(Session State) 초기화
# ---------------------------------------------------------
if "game_status" not in st.session_state:
    st.session_state.game_status = "INIT"  # INIT, PLAYING, GAME_OVER
    st.session_state.score = 0
    st.session_state.combo = 0
    st.session_state.max_combo = 0
    st.session_state.hp = 3
    st.session_state.round = 0
    st.session_state.current_cmd = ""
    st.session_state.start_time = 0.0
    st.session_state.time_limit = 3.0
    st.session_state.last_msg = ""
    st.session_state.last_status = "info"

# ---------------------------------------------------------
# 4. 게임 로직 함수
# ---------------------------------------------------------
def start_game():
    st.session_state.game_status = "PLAYING"
    st.session_state.score = 0
    st.session_state.combo = 0
    st.session_state.max_combo = 0
    st.session_state.hp = 3
    st.session_state.round = 1
    st.session_state.time_limit = 3.0
    st.session_state.current_cmd = random.choice(COMMAND_POOL)
    st.session_state.start_time = time.time()
    st.session_state.last_msg = "⚔️ 전투 시작! 커맨드를 빠르게 입력하세요!"
    st.session_state.last_status = "info"

def process_turn(user_input):
    elapsed = time.time() - st.session_state.start_time
    target = st.session_state.current_cmd
    limit = st.session_state.time_limit
    user_cmd = user_input.strip().upper()

    if elapsed > limit:
        # 시간 초과 실패
        st.session_state.hp -= 1
        st.session_state.combo = 0
        st.session_state.last_msg = f"⏰ 시간 초과! ({elapsed:.2f}초 걸림 / 제한: {limit:.1f}초)"
        st.session_state.last_status = "error"
    elif user_cmd == target:
        # 입력 성공
        st.session_state.combo += 1
        if st.session_state.combo > st.session_state.max_combo:
            st.session_state.max_combo = st.session_state.combo
        
        # 반응속도 보너스 점수 계산
        speed_ratio = max(0.0, (limit - elapsed) / limit)
        speed_bonus = int(speed_ratio * 150)
        combo_bonus = st.session_state.combo * 30
        gained_score = 100 + combo_bonus + speed_bonus
        
        st.session_state.score += gained_score
        st.session_state.last_msg = f"⚡ 성공! +{gained_score}점 (반응속도: {elapsed:.2f}초)"
        st.session_state.last_status = "success"
    else:
        # 오타 실패
        st.session_state.hp -= 1
        st.session_state.combo = 0
        st.session_state.last_msg = f"❌ 커맨드 입력 실수! (입력: '{user_cmd}' / 정답: '{target}')"
        st.session_state.last_status = "warning"

    # 게임 오버 여부 판정
    if st.session_state.hp <= 0:
        st.session_state.game_status = "GAME_OVER"
    else:
        # 다음 라운드 진행 및 난이도 상승
        st.session_state.round += 1
        # 1000점마다 제한시간 0.25초 감소 (최소 1.0초까지 제한)
        st.session_state.time_limit = max(1.0, 3.0 - (st.session_state.score // 1000) * 0.25)
        st.session_state.current_cmd = random.choice(COMMAND_POOL)
        st.session_state.start_time = time.time()

# ---------------------------------------------------------
# 5. 화면 렌더링 (UI)
# ---------------------------------------------------------
st.title("⚔️ QTE 커맨드 히어로!")
st.caption("화면에 나타나는 커맨드를 누구보다 빠르게 typing 하세요!")

# [화면 1] 대기 화면 (INIT)
if st.session_state.game_status == "INIT":
    st.markdown("""
    ### 🎮 게임 규칙
    1. 화면 중앙에 나타나는 **영어 커맨드**를 입력창에 똑같이 입력합니다.
    2. 입력 후 **Enter 키**를 누르면 즉시 공격이 실행됩니다.
    3. 빠른 반응 속도와 **연속 콤보**로 더 높은 점수를 획득하세요!
    4. 제한시간을 넘기거나 오타가 나면 **체력(HP)**이 줄어듭니다.
    """)
    st.divider()
    if st.button("🚀 게임 시작하기", use_container_width=True, type="primary"):
        start_game()
        st.rerun()

# [화면 2] 게임 진행 화면 (PLAYING)
elif st.session_state.game_status == "PLAYING":
    # 상단 HUD (상태 표시창)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        hp_hearts = "❤️" * st.session_state.hp + "🖤" * (3 - st.session_state.hp)
        st.markdown(f"<div class='hud-card'><div class='hud-title'>체력</div><div class='hud-value'>{hp_hearts}</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='hud-card'><div class='hud-title'>현재 점수</div><div class='hud-value'>{st.session_state.score}</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='hud-card'><div class='hud-title'>콤보</div><div class='hud-value'>🔥 {st.session_state.combo}</div></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='hud-card'><div class='hud-title'>제한시간</div><div class='hud-value'>⏳ {st.session_state.time_limit:.1f}초</div></div>", unsafe_allow_html=True)

    st.write("")

    # 이전 결과 알림 메시지
    if st.session_state.last_msg:
        if st.session_state.last_status == "success":
            st.success(st.session_state.last_msg)
        elif st.session_state.last_status in ["error", "warning"]:
            st.error(st.session_state.last_msg)
        else:
            st.info(st.session_state.last_msg)

    # QTE 메인 커맨드 박스
    st.markdown(f"""
    <div class='qte-container'>
        <div style='color: #9ca3af; font-size: 14px;'>ROUND {st.session_state.round}</div>
        <div class='qte-command'>{st.session_state.current_cmd}</div>
        <div style='color: #ffcc00; font-size: 12px;'>▲ 대소문자 상관없이 빠르게 입력하세요! ▲</div>
    </div>
    """, unsafe_allow_html=True)

    # 입력 폼 (clear_on_submit으로 제출 시 자동으로 입력창 비움)
    with st.form(key=f"qte_form_{st.session_state.round}", clear_on_submit=True):
        user_input = st.text_input("커맨드 입력 후 Enter:", key=f"input_{st.session_state.round}", label_visibility="collapsed")
        submit_btn = st.form_submit_button("⚡ 커맨드 실행 (Enter)", use_container_width=True, type="primary")
        
        if submit_btn:
            process_turn(user_input)
            st.rerun()

# [화면 3] 게임 오버 화면 (GAME_OVER)
elif st.session_state.game_status == "GAME_OVER":
    st.error("💥 GAME OVER - 용사가 쓰러졌습니다!")
    
    # 등급 평가
    score = st.session_state.score
    if score >= 3000:
        rank = "🏆 S급 (신급 반응속도!)"
    elif score >= 1800:
        rank = "🥇 A급 (빛의 검사)"
    elif score >= 1000:
        rank = "🥈 B급 (숙련된 모험가)"
    else:
        rank = "🥉 C급 (초보 수련생)"

    col1, col2 = st.columns(2)
    with col1:
        st.metric("최종 점수", f"{st.session_state.score} 점")
        st.metric("최대 콤보", f"{st.session_state.max_combo} Combo")
    with col2:
        st.metric("도달 라운드", f"{st.session_state.round} Round")
        st.metric("최종 랭크", rank)

    st.divider()
    if st.button("🔄 다시 도전하기", use_container_width=True, type="primary"):
        start_game()
        st.rerun()
