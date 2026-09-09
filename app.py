import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="나만의 리듬게임", layout="centered")

st.title("🎹 웹 기반 건반 리듬게임")
st.write("노래에 맞춰 D, F, J, K 키를 눌러보세요!")

# 난이도 선택 (스트림릿 UI)
difficulty = st.selectbox("난이도를 선택하세요", ["Easy", "Hard"])

# 선택된 난이도에 따라 HTML/JS로 전달할 변수 설정
speed = 5 if difficulty == "Easy" else 8

# 실제 게임이 구동될 HTML, CSS, JavaScript 코드
game_code = f"""
<!DOCTYPE html>
<html>
<head>
<style>
    body {{ margin: 0; display: flex; justify-content: center; background-color: #111; color: white; font-family: sans-serif; }}
    canvas {{ background-color: #000; border: 2px solid #333; box-shadow: 0 0 20px rgba(255, 255, 255, 0.1); }}
    #ui {{ position: absolute; top: 10px; font-size: 20px; font-weight: bold; text-align: center; width: 400px; pointer-events: none; }}
</style>
</head>
<body>
    <div id="ui">Score: <span id="score">0</span></div>
    <canvas id="gameCanvas" width="400" height="600"></canvas>

<script>
    const canvas = document.getElementById("gameCanvas");
    const ctx = canvas.getContext("2d");
    
    // 게임 설정
    const keys = ["d", "f", "j", "k"]; // 사용할 키보드 키
    const laneWidth = canvas.width / 4;
    const hitY = canvas.height - 100; // 판정선 위치
    const speed = {speed}; // 파이썬에서 전달받은 떨어지는 속도
    
    let score = 0;
    let gameStartTime = null;
    let isPlaying = false;

    // 🎵 채보 (Beatmap): 무작위가 아닌 특정 시간에 맞춰 떨어지도록 설계
    // time: 노래 시작 후 몇 밀리초(ms) 뒤에 판정선에 닿아야 하는지
    // lane: 0(D), 1(F), 2(J), 3(K) 레인
    const beatmap = [
        {{ time: 1000, lane: 0 }},
        {{ time: 1500, lane: 1 }},
        {{ time: 2000, lane: 2 }},
        {{ time: 2500, lane: 3 }},
        {{ time: 3000, lane: 1 }},
        {{ time: 3000, lane: 2 }}, // 동시치기
        {{ time: 3500, lane: 0 }},
        {{ time: 4000, lane: 3 }}
    ];

    let activeNotes = [];

    // 게임 시작 시 노트 생성
    function startGame() {{
        // 실제 노래를 넣을 경우 여기서 오디오를 재생합니다.
        // const bgm = new Audio('song.mp3'); bgm.play();
        
        gameStartTime = performance.now();
        activeNotes = JSON.parse(JSON.stringify(beatmap)); // 노트 복사
        isPlaying = true;
        requestAnimationFrame(gameLoop);
    }}

    // 키보드 입력 처리 (판정)
    window.addEventListener("keydown", (e) => {{
        const keyIndex = keys.indexOf(e.key.toLowerCase());
        if (keyIndex > -1) {{
            // 해당 레인의 가장 아래에 있는 노트 찾기
            const noteIndex = activeNotes.findIndex(n => n.lane === keyIndex && n.y > hitY - 50 && n.y < hitY + 50);
            
            if (noteIndex > -1) {{
                activeNotes.splice(noteIndex, 1); // 노트 제거 (Hit!)
                score += 100;
                document.getElementById("score").innerText = score;
                
                // 타격 이펙트 (간단한 화면 반짝임)
                ctx.fillStyle = "rgba(255, 255, 255, 0.3)";
                ctx.fillRect(keyIndex * laneWidth, 0, laneWidth, canvas.height);
            }}
        }}
    }});

    // 매 프레임마다 화면을 그리는 메인 루프
    function gameLoop(currentTime) {{
        if (!isPlaying) return;
        
        // 화면 지우기
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // 판정선 그리기
        ctx.fillStyle = "#FF5555";
        ctx.fillRect(0, hitY, canvas.width, 5);
        
        // 레인 구분선 그리기
        ctx.strokeStyle = "#333";
        for(let i=1; i<4; i++) {{
            ctx.beginPath();
            ctx.moveTo(i * laneWidth, 0);
            ctx.lineTo(i * laneWidth, canvas.height);
            ctx.stroke();
        }}

        const timeElapsed = currentTime - gameStartTime;

        // 노트 위치 계산 및 그리기
        for (let i = activeNotes.length - 1; i >= 0; i--) {{
            let note = activeNotes[i];
            
            // 노트가 화면에 보여야 할 시간 계산 (시간 거리 = 속력 * 시간)
            // note.time에 판정선(hitY)에 닿아야 함
            const timeUntilHit = note.time - timeElapsed;
            note.y = hitY - (timeUntilHit / 1000 * 60 * speed);

            // 노트가 화면 아래로 지나갔는지 확인 (Miss)
            if (note.y > canvas.height) {{
                activeNotes.splice(i, 1);
                score -= 10; // 감점
                document.getElementById("score").innerText = score;
                continue;
            }}

            // 화면에 보이는 노트만 그리기
            if (note.y > -50) {{
                ctx.fillStyle = "#00DDFF";
                ctx.fillRect(note.lane * laneWidth + 5, note.y, laneWidth - 10, 20);
            }}
        }}

        // 애니메이션 계속 진행
        requestAnimationFrame(gameLoop);
    }}

    // 화면 클릭 시 게임 시작 (브라우저 정책 상 사용자의 입력이 있어야 오디오/게임 시작 가능)
    canvas.addEventListener("click", () => {{
        if (!isPlaying) startGame();
    }});
    
    // 시작 대기 화면
    ctx.fillStyle = "white";
    ctx.font = "20px Arial";
    ctx.fillText("화면을 클릭하면 시작합니다!", 80, canvas.height / 2);

</script>
</body>
</html>
"""

# HTML 컴포넌트를 스트림릿 화면에 렌더링
components.html(game_code, height=650)
