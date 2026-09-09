import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="나만의 리듬게임", layout="centered")

st.title("🎹 웹 기반 건반 리듬게임")
st.write("시작하려면 화면을 한 번 클릭한 뒤 **스페이스바**를 누르세요. (D, F, J, K 키 사용)")

# 난이도 선택
difficulty = st.selectbox("난이도를 선택하세요", ["Easy", "Hard"])
speed = 5 if difficulty == "Easy" else 8
bpm = 120 if difficulty == "Easy" else 180 

game_code = f"""
<!DOCTYPE html>
<html>
<head>
<style>
    body {{ margin: 0; display: flex; justify-content: center; background-color: #111; color: white; font-family: sans-serif; overflow: hidden; }}
    canvas {{ background-color: #000; border: 2px solid #333; box-shadow: 0 0 20px rgba(255, 255, 255, 0.1); }}
    #ui {{ position: absolute; top: 10px; display: flex; justify-content: space-between; width: 380px; pointer-events: none; padding: 0 10px; font-size: 20px; font-weight: bold; }}
</style>
</head>
<body>
    <div id="ui">
        <div>Score: <span id="score">0</span></div>
        <div>Combo: <span id="combo">0</span></div>
    </div>
    <canvas id="gameCanvas" width="400" height="600"></canvas>

<script>
    const canvas = document.getElementById("gameCanvas");
    const ctx = canvas.getContext("2d");
    
    const keys = ["d", "f", "j", "k"];
    const laneWidth = canvas.width / 4;
    const hitY = canvas.height - 100;
    const speed = {speed};
    const bpm = {bpm};
    const beatInterval = 60000 / bpm; 
    
    let score = 0;
    let combo = 0;
    let gameState = 0; 
    let gameStartTime = null;
    let lastBeatTime = 0;
    
    let activeNotes = [];
    let effects = []; 
    
    let judgmentText = "";
    let judgmentColor = "";
    let judgmentTimer = 0;

    // 🎵 여러 가지 노트 패턴 정의 (0=D, 1=F, 2=J, 3=K)
    const patterns = [
        [[0], [1], [2], [3]],                   // 1. 왼쪽에서 오른쪽 계단
        [[3], [2], [1], [0]],                   // 2. 오른쪽에서 왼쪽 계단
        [[0, 3], [1, 2], [0, 3], [1, 2]],       // 3. 양끝 동시 -> 가운데 동시 교차
        [[0], [2], [1], [3]],                   // 4. 지그재그
        [[0, 1], [2, 3], [0, 1], [2, 3]],       // 5. 왼쪽 두개 -> 오른쪽 두개
        [[0, 1, 2, 3], [], [0, 1, 2, 3], []]    // 6. 4키 전체 동시 치기 후 한 박자 쉬기
    ];
    
    let currentPattern = [];
    let patternStep = 0;

    function startGame() {{
        gameState = 1;
        gameStartTime = performance.now();
        lastBeatTime = gameStartTime;
        score = 0;
        combo = 0;
        activeNotes = [];
        patternStep = 0; // 시작할 때 패턴 스텝 초기화
        currentPattern = patterns[0]; // 첫 패턴 설정
        
        document.getElementById("score").innerText = score;
        document.getElementById("combo").innerText = combo;
        requestAnimationFrame(gameLoop);
    }}

    window.addEventListener("keydown", (e) => {{
        if (gameState === 0 && e.code === "Space") {{
            startGame();
            return;
        }}

        if (gameState !== 1) return;

        const keyIndex = keys.indexOf(e.key.toLowerCase());
        if (keyIndex > -1) {{
            const hitZone = 70; 
            let closestNoteIndex = -1;
            let minDistance = Infinity;

            for (let i = 0; i < activeNotes.length; i++) {{
                if (activeNotes[i].lane === keyIndex) {{
                    const dist = Math.abs(activeNotes[i].y - hitY);
                    if (dist < hitZone && dist < minDistance) {{
                        minDistance = dist;
                        closestNoteIndex = i;
                    }}
                }}
            }}

            if (closestNoteIndex > -1) {{
                let text, color, pts;
                if (minDistance <= 15) {{
                    text = "Perfect!"; color = "#FFD700"; pts = 100;
                }} else if (minDistance <= 35) {{
                    text = "Expert"; color = "#00FF00"; pts = 70;
                }} else if (minDistance <= 50) {{
                    text = "Good"; color = "#00BFFF"; pts = 40;
                }} else {{
                    text = "Bad"; color = "#FF4500"; pts = 10;
                }}

                judgmentText = text;
                judgmentColor = color;
                judgmentTimer = 30; 

                score += pts;
                if (text !== "Bad") combo++; else combo = 0;
                
                document.getElementById("score").innerText = score;
                document.getElementById("combo").innerText = combo;

                effects.push({{
                    x: keyIndex * laneWidth + laneWidth / 2,
                    y: hitY,
                    radius: 10,
                    alpha: 1,
                    color: color
                }});

                activeNotes.splice(closestNoteIndex, 1); 
            }} else {{
                combo = 0;
                document.getElementById("combo").innerText = combo;
            }}
        }}
    }});

    function gameLoop(currentTime) {{
        if (gameState !== 1) return;
        
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // 🎵 정해진 패턴에 따라 노트 생성
        if (currentTime - lastBeatTime > beatInterval) {{
            // 현재 패턴의 모든 노트를 다 내보냈다면 새로운 패턴 무작위 선택
            if (patternStep >= currentPattern.length) {{
                const randomIndex = Math.floor(Math.random() * patterns.length);
                currentPattern = patterns[randomIndex];
                patternStep = 0;
            }}

            // 현재 스텝의 레인 배열 가져오기 (예: [0, 3])
            const lanesToSpawn = currentPattern[patternStep];
            
            for(let i = 0; i < lanesToSpawn.length; i++) {{
                activeNotes.push({{
                    time: currentTime + 2000, 
                    lane: lanesToSpawn[i],
                    y: -50
                }});
            }}
            
            patternStep++;
            lastBeatTime = currentTime;
        }}

        ctx.strokeStyle = "#333";
        for(let i=1; i<4; i++) {{
            ctx.beginPath();
            ctx.moveTo(i * laneWidth, 0);
            ctx.lineTo(i * laneWidth, canvas.height);
            ctx.stroke();
        }}

        ctx.fillStyle = "rgba(255, 85, 85, 0.5)";
        ctx.fillRect(0, hitY - 15, canvas.width, 30); 
        ctx.fillStyle = "#FF5555";
        ctx.fillRect(0, hitY, canvas.width, 3); 

        for (let i = activeNotes.length - 1; i >= 0; i--) {{
            let note = activeNotes[i];
            
            const timeUntilHit = note.time - currentTime;
            note.y = hitY - (timeUntilHit / 1000 * 60 * speed);

            if (note.y > canvas.height) {{
                activeNotes.splice(i, 1);
                combo = 0;
                document.getElementById("combo").innerText = combo;
                judgmentText = "Miss";
                judgmentColor = "#888";
                judgmentTimer = 30;
                continue;
            }}

            if (note.y > -50) {{
                ctx.fillStyle = "#00DDFF";
                ctx.beginPath();
                ctx.roundRect(note.lane * laneWidth + 5, note.y - 10, laneWidth - 10, 20, 5);
                ctx.fill();
            }}
        }}

        for (let i = effects.length - 1; i >= 0; i--) {{
            let eff = effects[i];
            ctx.beginPath();
            ctx.arc(eff.x, eff.y, eff.radius, 0, Math.PI * 2);
            ctx.strokeStyle = eff.color;
            ctx.globalAlpha = eff.alpha;
            ctx.lineWidth = 3;
            ctx.stroke();
            ctx.globalAlpha = 1.0; 

            eff.radius += 2; 
            eff.alpha -= 0.05; 

            if (eff.alpha <= 0) effects.splice(i, 1);
        }}

        if (judgmentTimer > 0) {{
            ctx.fillStyle = judgmentColor;
            ctx.font = "bold 30px Arial";
            ctx.textAlign = "center";
            ctx.fillText(judgmentText, canvas.width / 2, hitY - 100);
            judgmentTimer--;
        }}

        requestAnimationFrame(gameLoop);
    }}

    ctx.fillStyle = "white";
    ctx.font = "bold 20px Arial";
    ctx.textAlign = "center";
    ctx.fillText("스페이스바를 눌러 게임 시작!", canvas.width / 2, canvas.height / 2);

</script>
</body>
</html>
"""

components.html(game_code, height=650)
