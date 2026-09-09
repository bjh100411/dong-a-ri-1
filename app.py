import streamlit as st
import random

# --- 페이지 설정 ---
st.set_page_config(page_title="Breach Protocol", layout="wide")

# --- 커스텀 CSS (사이버펑크 테마) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
    
    /* 전체 배경 및 폰트 설정 */
    .stApp {
        background-color: #0B0C10;
        color: #C5C6C7;
        font-family: 'Share Tech Mono', monospace;
    }
    
    h1, h2, h3 {
        color: #FF003C !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        text-shadow: 2px 2px 0px #00E6F6;
    }

    /* 버튼 스타일 (매트릭스 코드) */
    div.stButton > button {
        background-color: transparent !important;
        color: #00E6F6 !important;
        border: 2px solid #1F2833 !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 20px !important;
        width: 100%;
        height: 60px;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        border-color: #FF003C !important;
        color: #FF003C !important;
        box-shadow: 0 0 10px #FF003C;
    }
    div.stButton > button:active {
        background-color: #FF003C !important;
        color: #0B0C10 !important;
    }
    
    /* 버퍼 및 텍스트 스타일 */
    .buffer-box {
        display: inline-block;
        width: 40px;
        height: 40px;
        border: 2px solid #F3E600;
        text-align: center;
        line-height: 36px;
        font-size: 20px;
        color: #F3E600;
        margin-right: 10px;
        background-color: rgba(243, 230, 0, 0.1);
    }
    .target-seq {
        font-size: 22px;
        color: #FFFFFF;
        background-color: #1F2833;
        padding: 5px 15px;
        margin-bottom: 10px;
        border-left: 5px solid #FF003C;
    }
    .highlight { color: #F3E600; }
    </style>
""", unsafe_allow_html=True)

# --- 게임 상태 초기화 ---
HEX_CODES = ['1C', '55', 'BD', 'E9', '7A']
MATRIX_SIZE = 5
BUFFER_SIZE = 6

if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    # 5x5 행렬 생성
    st.session_state.matrix = [[random.choice(HEX_CODES) for _ in range(MATRIX_SIZE)] for _ in range(MATRIX_SIZE)]
    # 타겟 시퀀스 생성 (길이 3)
    st.session_state.targets = {
        "DATAMINE_V1": [random.choice(HEX_CODES) for _ in range(3)],
        "DATAMINE_V2": [random.choice(HEX_CODES) for _ in range(3)]
    }
    st.session_state.buffer = []
    st.session_state.clicked = set() # 클릭된 좌표 (r, c) 저장
    st.session_state.is_row = True   # True면 가로(행) 선택 차례, False면 세로(열) 선택 차례
    st.session_state.current_idx = 0 # 현재 활성화된 행/열의 인덱스
    st.session_state.game_over = False
    st.session_state.success = []

# --- 게임 로직 ---
def handle_click(r, c, code):
    if st.session_state.game_over: return
    
    # 룰 체크: 현재 활성화된 행(또는 열)인지 확인
    if st.session_state.is_row and r != st.session_state.current_idx: return
    if not st.session_state.is_row and c != st.session_state.current_idx: return
    
    # 버퍼 추가 및 상태 업데이트
    st.session_state.buffer.append(code)
    st.session_state.clicked.add((r, c))
    
    # 방향 전환 및 다음 활성 인덱스 설정
    st.session_state.is_row = not st.session_state.is_row
    st.session_state.current_idx = c if not st.session_state.is_row else r
    
    # 타겟 달성 확인
    for name, seq in st.session_state.targets.items():
        if name in st.session_state.success: continue
        # 버퍼 내에서 시퀀스가 연속으로 존재하는지 확인
        seq_str = " ".join(seq)
        buf_str = " ".join(st.session_state.buffer)
        if seq_str in buf_str:
            st.session_state.success.append(name)
            
    # 종료 조건 (버퍼가 가득 참)
    if len(st.session_state.buffer) >= BUFFER_SIZE:
        st.session_state.game_over = True

def reset_game():
    del st.session_state['initialized']

# --- UI 렌더링 ---
st.title("BREACH PROTOCOL_")

col1, col2 = st.columns([2, 1])

with col2:
    st.markdown("### TARGET SEQUENCES")
    for name, seq in st.session_state.targets.items():
        status = "✅ UPLOADED" if name in st.session_state.success else "WAITING..."
        color = "#00E6F6" if name in st.session_state.success else "#FF003C"
        st.markdown(f"""
        <div class="target-seq">
            <span style="color:{color}; font-weight:bold;">{name}</span><br>
            {" ".join(seq)} - {status}
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("### BUFFER")
    buffer_html = ""
    for i in range(BUFFER_SIZE):
        if i < len(st.session_state.buffer):
            buffer_html += f'<div class="buffer-box">{st.session_state.buffer[i]}</div>'
        else:
            buffer_html += '<div class="buffer-box"></div>'
    st.markdown(buffer_html, unsafe_allow_html=True)

    if st.session_state.game_over:
        if len(st.session_state.success) > 0:
            st.success("ACCESS GRANTED: Data Extracted.")
        else:
            st.error("BREACH FAILED: Disconnected.")
        st.button("REBOOT SYSTEM", on_click=reset_game)
    else:
        direction = "HORIZONTAL (ROW)" if st.session_state.is_row else "VERTICAL (COLUMN)"
        st.info(f"CURRENT TRACE: **{direction}**")

with col1:
    st.markdown("### CODE MATRIX")
    
    # 매트릭스 그리드 생성
    for r in range(MATRIX_SIZE):
        cols = st.columns(MATRIX_SIZE)
        for c in range(MATRIX_SIZE):
            with cols[c]:
                code = st.session_state.matrix[r][c]
                
                # 버튼 비활성화 로직 (이미 클릭했거나, 룰에 어긋나는 경우)
                is_disabled = (r, c) in st.session_state.clicked or st.session_state.game_over
                if not is_disabled:
                    if st.session_state.is_row and r != st.session_state.current_idx:
                        is_disabled = True
                    if not st.session_state.is_row and c != st.session_state.current_idx:
                        is_disabled = True
                
                # 라벨 텍스트 표시 (클릭된 건 [XX] 로 표시)
                label = f"[{code}]" if (r, c) in st.session_state.clicked else code
                
                st.button(
                    label,
                    key=f"btn_{r}_{c}",
                    disabled=is_disabled,
                    on_click=handle_click,
                    args=(r, c, code)
                )

# 가이드 추가
st.caption("SYSTEM INSTRUCTION: 1. 첫 클릭은 반드시 맨 윗줄(가로)에서 시작합니다. 2. 가로 -> 세로 -> 가로 순으로 번갈아 선택해야 합니다. 3. Target Sequence를 조합해 데이터를 빼내십시오.")
