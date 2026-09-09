import streamlit as st

# 페이지 구성
st.set_page_config(page_title="Element Combo Wizard", page_icon="🧙‍♂️", layout="centered")

# 세션 상태 초기화
if "queue" not in st.session_state:
    st.session_state.queue = []
if "logs" not in st.session_state:
    st.session_state.logs = []
if "target_hp" not in st.session_state:
    st.session_state.target_hp = 500
if "target_status" not in st.session_state:
    st.session_state.target_status = []

# 원소 정보
ELEMENTS = {
    "Q": {"name": "불", "icon": "🔥"},
    "W": {"name": "물", "icon": "💧"},
    "E": {"name": "대지", "icon": "🪨"},
    "R": {"name": "번개", "icon": "⚡"},
}

# 스펠 매핑 데이터베이스 (상태 머신/트라이 패턴 대용)
SPELL_BOOK = {
    "Q": {"name": "화염 화살", "damage": 25, "status": "화상", "desc": "작은 화염 화살을 발사합니다."},
    "W": {"name": "물대포", "damage": 15, "status": "젖음", "desc": "적을 적시는 물대포를 쏩니다."},
    "E": {"name": "암석 던지기", "damage": 30, "status": "둔화", "desc": "바위를 던져 피해를 줍니다."},
    "R": {"name": "전기 충격", "damage": 20, "status": "전율", "desc": "찌릿한 전기를 방출합니다."},
    "QQ": {"name": "화염구", "damage": 60, "status": "화상", "desc": "거대한 화염구를 폭발시킵니다."},
    "WW": {"name": "거대 파도", "damage": 40, "status": "젖음", "desc": "강한 파도로 적을 완전히 적십니다."},
    "QW": {"name": "증기 폭발", "damage": 75, "status": None, "desc": "불과 물이 만나 고온 증기 폭발을 일으킵니다."},
    "WR": {"name": "감전 레이저", "damage": 85, "status": "감전", "desc": "전기 줄기를 쏘아 큰 타격을 줍니다."},
    "EQ": {"name": "용암 탄환", "damage": 80, "status": "화상", "desc": "녹아내린 용암 덩어리를 발사합니다."},
    "WE": {"name": "진흙 늪", "damage": 45, "status": "속박", "desc": "적의 움직임을 봉쇄합니다."},
    "QR": {"name": "과부하 폭발", "damage": 90, "status": "초과열", "desc": "고전압 화염 레이저를 쏩니다."},
    "QWER": {"name": "아르카나 메테오", "damage": 250, "status": "파괴", "desc": "4대 원소를 융합한 궁극의 운석을 소환합니다."},
}

# 마법 발사 처리 함수
def cast_spell():
    seq = "".join(st.session_state.queue)
    if not seq:
        return
    
    spell = SPELL_BOOK.get(seq)
    
    if spell:
        damage = spell["damage"]
        new_status = spell["status"]
        log_msg = f"✨ **[{spell['name']}]** ({spell['desc']}) ➔ **{damage}** 피해"
        
        # 속성 상호작용 (상태 이상 시너지)
        if "젖음" in st.session_state.target_status and "R" in seq:
            extra_dmg = 45
            damage += extra_dmg
            log_msg += f" | ⚡ **[감전 시너지!]** 추가 피해 +{extra_dmg}"
            
        if "화상" in st.session_state.target_status and "W" in seq:
            log_msg += " | 💨 **[증발]** 적의 화상 상태가 해제되었습니다."
            st.session_state.target_status.remove("화상")

        # 체력 및 상태 업데이트
        st.session_state.target_hp = max(0, st.session_state.target_hp - damage)
        if new_status and new_status not in st.session_state.target_status:
            st.session_state.target_status.append(new_status)
            
        st.session_state.logs.insert(0, log_msg)
    else:
        st.session_state.logs.insert(0, f"💥 **[마법 실패]** 조합 **'{seq}'**에 해당하는 마법이 없습니다.")
    
    st.session_state.queue = []

# 대시보드 UI
st.title("🧙‍♂️ Element Combo Wizard")
st.caption("원소 키를 조합해 마법을 생성하고 발사하세요!")

# 타겟 몬스터 UI
st.subheader("🎯 타겟 훈련용 더미")
hp_ratio = st.session_state.target_hp / 500
st.progress(hp_ratio)

col_hp, col_st = st.columns(2)
with col_hp:
    st.write(f"**HP:** {st.session_state.target_hp} / 500")
with col_st:
    status_text = ", ".join(st.session_state.target_status) if st.session_state.target_status else "없음"
    st.write(f"**적용 중인 상태 이상:** `{status_text}`")

if st.button("🔄 더미 초기화"):
    st.session_state.target_hp = 500
    st.session_state.target_status = []
    st.session_state.logs = []
    st.session_state.queue = []
    st.rerun()

st.divider()

# 조합 슬롯 시각화
queue_display = " ".join([ELEMENTS[k]["icon"] for k in st.session_state.queue]) if st.session_state.queue else "빈 슬롯"
st.info(f"### 조합 슬롯: [ {queue_display} ]")

# 입력 키 버튼
col_q, col_w, col_e, col_r = st.columns(4)

with col_q:
    if st.button("🔥 Q (불)", use_container_width=True):
        if len(st.session_state.queue) < 4:
            st.session_state.queue.append("Q")
            st.rerun()

with col_w:
    if st.button("💧 W (물)", use_container_width=True):
        if len(st.session_state.queue) < 4:
            st.session_state.queue.append("W")
            st.rerun()

with col_e:
    if st.button("🪨 E (대지)", use_container_width=True):
        if len(st.session_state.queue) < 4:
            st.session_state.queue.append("E")
            st.rerun()

with col_r:
    if st.button("⚡ R (번개)", use_container_width=True):
        if len(st.session_state.queue) < 4:
            st.session_state.queue.append("R")
            st.rerun()

# 실행 및 캐스팅 버튼
col_cast, col_clear = st.columns([3, 1])
with col_cast:
    if st.button("🚀 마법 발사!", type="primary", use_container_width=True):
        cast_spell()
        st.rerun()
with col_clear:
    if st.button("❌ 취소", use_container_width=True):
        st.session_state.queue = []
        st.rerun()

# 전투 로그
st.divider()
st.write("**📜 캐스팅 로그**")
for log in st.session_state.logs[:5]:
    st.write(log)
