import streamlit as st
import streamlit.components.v1 as components

# 페이지 기본 설정
st.set_page_config(
    page_title="음파 탐지 사운드 탐험 (Sonar Exploration)",
    page_icon="🦇",
    layout="centered"
)

st.title("🦇 음파 탐지 사운드 탐험")
st.caption("웹 오디오 API 기반 3D 입체 음향 & 음파 시각화 2D 탈출 게임")

with st.expander("🎮 조작 방법 및 게임 설명", expanded=True):
    st.markdown("""
    - **이동**: `WASD` 또는 `방향키`
    - **음파 발사**: `Spacebar` (쿨타임 1.2초)
    - **목표**: 암흑 속에서 음파를 쏘아 벽의 잔상을 확인하고, **황금색 탈출구**를 찾으세요!
    - **사운드 피드백**:
      - 탈출구가 가까울수록 **소리의 톤(Pitch)이 높아집니다.**
      - 탈출구가 왼쪽에 있으면 **왼쪽 스피커**, 오른쪽에 있으면 **오른쪽 스피커**에서 소리가 납니다 (이어폰 착용 권장 🎧).
    """)

# 게임 HTML/CSS/JavaScript 코드
game_html = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<style>
    * { box-sizing: border-box; }
    body {
        margin: 0;
        padding: 0;
        background-color: #030508;
        color: #ffffff;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        display: flex;
        justify-content: center;
        align-items: center;
        user-select: none;
    }
    #game-container {
        position: relative;
        width: 800px;
        height: 600px;
        box-shadow: 0 0 30px rgba(0, 234, 255, 0.2);
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #1a2636;
    }
    canvas {
        display: block;
        background: #030508;
    }
    #ui-overlay {
        position: absolute;
        top: 15px;
        left: 20px;
        right: 20px;
        display: flex;
        justify-content: space-between;
        pointer-events: none;
        font-size: 14px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .hud-box {
        background: rgba(10, 20, 30, 0.75);
        padding: 8px 16px;
        border-radius: 20px;
        border: 1px solid rgba(0, 234, 255, 0.3);
        backdrop-filter: blur(4px);
    }
    #cooldown-bg {
        width: 100px;
        height: 6px;
        background: rgba(255, 255, 255, 0.2);
        border-radius: 3px;
        overflow: hidden;
        margin-top: 5px;
    }
    #cooldown-bar {
        width: 100%;
        height: 100%;
        background: #00eaff;
        transition: width 0.1s linear;
    }
    .modal {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(3, 5, 8, 0.92);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        backdrop-filter: blur(8px);
        z-index: 10;
    }
    h2 { margin: 0 0 10px 0; color: #00eaff; text-shadow: 0 0 10px rgba(0,234,255,0.5); }
    p { margin: 5px 0 20px 0; color: #94a3b8; text-align: center; line-height: 1.5; font-size: 14px; }
    .btn {
        background: linear-gradient(135deg, #00eaff, #0077ff);
        color: #000;
        font-weight: bold;
        padding: 12px 30px;
        border-radius: 25px;
        border: none;
        cursor: pointer;
        font-size: 15px;
        box-shadow: 0 0 15px rgba(0, 234, 255, 0.4);
        transition: all 0.2s;
    }
    .btn:hover {
        transform: scale(1.05);
        box-shadow: 0 0 25px rgba(0, 234, 255, 0.7);
    }
</style>
</head>
<body>

<div id="game-container" tabindex="0">
    <canvas id="canvas" width="800" height="600"></canvas>
    
    <div id="ui-overlay">
        <div class="hud-box">
            소나 쿨다운
            <div id="cooldown-bg"><div id="cooldown-bar"></div></div>
        </div>
        <div class="hud-box" id="stage-txt">STAGE 1</div>
    </div>

    <!-- 시작 화면 -->
    <div id="start-modal" class="modal">
        <h2>🦇 음파 탐지 사운드 탐험</h2>
        <p>암흑 속에서 소나 음파를 쏘아 지형을 시각화하고<br>황금색 탈출구를 찾으세요!</p>
        <button class="btn" onclick="startGame()">탐험 시작 (오디오 활성화)</button>
    </div>

    <!-- 클리어 화면 -->
    <div id="clear-modal" class="modal" style="display: none;">
        <h2 style="color: #ffd700; text-shadow: 0 0 15px rgba(255, 215, 0, 0.6);">🎉 스테이지 탈출 성공!</h2>
        <p id="clear-info">성공적으로 소나 탐지를 마쳤습니다.</p>
        <button class="btn" onclick="nextStage()">다음 스테이지</button>
    </div>
</div>

<script>
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const container = document.getElementById('game-container');

// Stage layouts
const STAGES = [
    {
        start: { x: 60, y: 540 },
        exit: { x: 740, y: 70, r: 20 },
        walls: [
            {x: 0, y: 0, w: 800, h: 10}, {x: 0, y: 590, w: 800, h: 10},
            {x: 0, y: 0, w: 10, h: 600}, {x: 790, y: 0, w: 10, h: 600},
            {x: 200, y: 150, w: 20, h: 450},
            {x: 400, y: 0, w: 20, h: 450},
            {x: 600, y: 150, w: 20, h: 450}
        ]
    },
    {
        start: { x: 50, y: 50 },
        exit: { x: 750, y: 550, r: 20 },
        walls: [
            {x: 0, y: 0, w: 800, h: 10}, {x: 0, y: 590, w: 800, h: 10},
            {x: 0, y: 0, w: 10, h: 600}, {x: 790, y: 0, w: 10, h: 600},
            {x: 160, y: 0, w: 20, h: 420},
            {x: 160, y: 500, w: 180, h: 20},
            {x: 340, y: 120, w: 20, h: 400},
            {x: 340, y: 120, w: 280, h: 20},
            {x: 500, y: 240, w: 20, h: 360},
            {x: 640, y: 0, w: 20, h: 480}
        ]
    },
    {
        start: { x: 60, y: 300 },
        exit: { x: 740, y: 300, r: 20 },
        walls: [
            {x: 0, y: 0, w: 800, h: 10}, {x: 0, y: 590, w: 800, h: 10},
            {x: 0, y: 0, w: 10, h: 600}, {x: 790, y: 0, w: 10, h: 600},
            {x: 160, y: 100, w: 120, h: 160},
            {x: 160, y: 340, w: 120, h: 160},
            {x: 360, y: 40, w: 100, h: 220},
            {x: 360, y: 340, w: 100, h: 220},
            {x: 540, y: 100, w: 120, h: 160},
            {x: 540, y: 340, w: 120, h: 160}
        ]
    }
];

let currentStageIdx = 0;
let player = { x: 0, y: 0, r: 6 };
let pulses = [];
let particles = [];
let keys = {};
let gameActive = false;
let sonarCooldown = 0;
const MAX_COOLDOWN = 1200; // 1.2초

// Web Audio API Context
let audioCtx = null;

function initAudio() {
    if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtx.state === 'suspended') {
        audioCtx.resume();
    }
}

// 메인 소나 음파 발사음
function playSonarPingSound() {
    if (!audioCtx) return;
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(700, audioCtx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(250, audioCtx.currentTime + 0.35);

    gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.35);

    osc.connect(gain);
    gain.connect(audioCtx.destination);

    osc.start();
    osc.stop(audioCtx.currentTime + 0.35);
}

// 거리 및 방향(Pan) 기반 에코 반사음
function playEchoSound(pan, distance, isExit = false) {
    if (!audioCtx) return;

    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    const panner = audioCtx.createStereoPanner ? audioCtx.createStereoPanner() : null;

    if (isExit) {
        // 탈출구 신호음: 높고 명확한 정현파
        osc.type = 'triangle';
        // 거리가 가까울수록 고음 (800Hz ~ 1600Hz)
        const freq = 1600 - Math.min(1000, distance * 1.2);
        osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
        
        gain.gain.setValueAtTime(0.35, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.5);
    } else {
        // 벽 에코: 부드러운 둔탁한 소리
        osc.type = 'sine';
        osc.frequency.setValueAtTime(300, audioCtx.currentTime);
        gain.gain.setValueAtTime(0.05, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.15);
    }

    let lastNode = osc;
    if (panner) {
        panner.pan.setValueAtTime(Math.max(-1, Math.min(1, pan)), audioCtx.currentTime);
        osc.connect(panner);
        lastNode = panner;
    }
    lastNode.connect(gain);
    gain.connect(audioCtx.destination);

    osc.start();
    osc.stop(audioCtx.currentTime + (isExit ? 0.5 : 0.15));
}

function loadStage(idx) {
    const stg = STAGES[idx];
    player.x = stg.start.x;
    player.y = stg.start.y;
    pulses = [];
    particles = [];
    document.getElementById('stage-txt').innerText = `STAGE ${idx + 1}`;
}

function startGame() {
    initAudio();
    document.getElementById('start-modal').style.display = 'none';
    currentStageIdx = 0;
    loadStage(currentStageIdx);
    gameActive = true;
    container.focus();
}

function nextStage() {
    document.getElementById('clear-modal').style.display = 'none';
    currentStageIdx++;
    if (currentStageIdx >= STAGES.length) {
        currentStageIdx = 0; // 루프
    }
    loadStage(currentStageIdx);
    gameActive = true;
    container.focus();
}

// 키 입력 이벤트 등록
window.addEventListener('keydown', e => {
    if (['Space', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'KeyW', 'KeyA', 'KeyS', 'KeyD'].includes(e.code)) {
        e.preventDefault();
    }
    keys[e.code] = true;
});
window.addEventListener('keyup', e => { keys[e.code] = false; });

// 광선-AABB (벽) 교차점 계산 (Raycasting)
function getRayWallDistance(px, py, angle, walls) {
    const dx = Math.cos(angle);
    const dy = Math.sin(angle);
    let minDist = 750;

    for (let w of walls) {
        let tmin = 0, tmax = 750;

        if (Math.abs(dx) < 1e-6) {
            if (px < w.x || px > w.x + w.w) continue;
        } else {
            let t1 = (w.x - px) / dx;
            let t2 = (w.x + w.w - px) / dx;
            if (t1 > t2) [t1, t2] = [t2, t1];
            tmin = Math.max(tmin, t1);
            tmax = Math.min(tmax, t2);
        }

        if (Math.abs(dy) < 1e-6) {
            if (py < w.y || py > w.y + w.h) continue;
        } else {
            let t1 = (w.y - py) / dy;
            let t2 = (w.y + w.h - py) / dy;
            if (t1 > t2) [t1, t2] = [t2, t1];
            tmin = Math.max(tmin, t1);
            tmax = Math.min(tmax, t2);
        }

        if (tmax >= tmin && tmin > 0) {
            minDist = Math.min(minDist, tmin);
        }
    }
    return minDist;
}

// 광선-원 (탈출구) 교차점 계산
function getRayExitDistance(px, py, angle, exit) {
    const dx = Math.cos(angle);
    const dy = Math.sin(angle);
    const cx = exit.x - px;
    const cy = exit.y - py;
    const b = cx * dx + cy * dy;
    const c = cx * cx + cy * cy - exit.r * exit.r;
    const disc = b * b - c;
    if (disc < 0) return null;
    const t1 = b - Math.sqrt(disc);
    if (t1 > 0) return t1;
    return null;
}

function fireSonar() {
    playSonarPingSound();
    const stg = STAGES[currentStageIdx];
    const numRays = 180; // 360도 탐지 광선 개수
    const rays = [];

    let hitExit = false;
    let exitMinDist = 999;

    for (let i = 0; i < numRays; i++) {
        const angle = (i / numRays) * Math.PI * 2;
        const wallDist = getRayWallDistance(player.x, player.y, angle, stg.walls);
        const exitDist = getRayExitDistance(player.x, player.y, angle, stg.exit);

        rays.push({
            angle: angle,
            wallDist: wallDist,
            exitDist: exitDist,
            wallTriggered: false,
            exitTriggered: false
        });

        if (exitDist !== null && exitDist < wallDist) {
            hitExit = true;
            exitMinDist = Math.min(exitMinDist, exitDist);
        }
    }

    // 소나 파동 객체 생성
    pulses.push({
        x: player.x,
        y: player.y,
        r: 0,
        maxR: 750,
        speed: 6.5,
        rays: rays
    });

    // 탈출구 감지 시 입체 사운드 재생
    if (hitExit) {
        const dx = stg.exit.x - player.x;
        const dy = stg.exit.y - player.y;
        const dist = Math.hypot(dx, dy);
        const pan = dx / 400; // 좌/우 팬 계산 (-1 ~ 1)
        
        // 소나 파동이 탈출구에 도달할 지연 시간 계산 후 사운드 재생
        setTimeout(() => {
            playEchoSound(pan, dist, true);
        }, (exitMinDist / 6.5) * 16.6);
    }
}

function checkPlayerWallCollision(nx, ny) {
    const stg = STAGES[currentStageIdx];
    for (let w of stg.walls) {
        let closestX = Math.max(w.x, Math.min(nx, w.x + w.w));
        let closestY = Math.max(w.y, Math.min(ny, w.y + w.h));
        let dx = nx - closestX;
        let dy = ny - closestY;
        if ((dx * dx + dy * dy) < (player.r * player.r)) {
            return true;
        }
    }
    return false;
}

let lastTime = performance.now();

function gameLoop(now) {
    const dt = now - lastTime;
    lastTime = now;

    if (gameActive) {
        update(dt);
    }
    render();
    requestAnimationFrame(gameLoop);
}

function update(dt) {
    // 1. 이동 처리
    const speed = 2.4;
    let dx = 0, dy = 0;

    if (keys['KeyW'] || keys['ArrowUp']) dy -= speed;
    if (keys['KeyS'] || keys['ArrowDown']) dy += speed;
    if (keys['KeyA'] || keys['ArrowLeft']) dx -= speed;
    if (keys['KeyD'] || keys['ArrowRight']) dx += speed;

    if (dx !== 0 && dy !== 0) {
        dx *= 0.7071;
        dy *= 0.7071;
    }

    if (dx !== 0 && !checkPlayerWallCollision(player.x + dx, player.y)) {
        player.x += dx;
    }
    if (dy !== 0 && !checkPlayerWallCollision(player.x, player.y + dy)) {
        player.y += dy;
    }

    // 2. 소나 발사 쿨다운
    if (sonarCooldown > 0) {
        sonarCooldown -= dt;
    }
    if (keys['Space'] && sonarCooldown <= 0) {
        fireSonar();
        sonarCooldown = MAX_COOLDOWN;
    }

    // HUD 쿨다운 바 업데이트
    const cdBar = document.getElementById('cooldown-bar');
    if (sonarCooldown <= 0) {
        cdBar.style.width = '100%';
        cdBar.style.background = '#00eaff';
    } else {
        const pct = (1 - sonarCooldown / MAX_COOLDOWN) * 100;
        cdBar.style.width = pct + '%';
        cdBar.style.background = '#0077ff';
    }

    // 3. 파동 확장 & 에코 입자 생성
    for (let p = pulses.length - 1; p >= 0; p--) {
        const pulse = pulses[p];
        pulse.r += pulse.speed;

        for (let ray of pulse.rays) {
            // 벽 부딪힘
            if (!ray.wallTriggered && pulse.r >= ray.wallDist) {
                ray.wallTriggered = true;
                particles.push({
                    x: pulse.x + Math.cos(ray.angle) * ray.wallDist,
                    y: pulse.y + Math.sin(ray.angle) * ray.wallDist,
                    alpha: 1.0,
                    type: 'wall'
                });
            }
            // 탈출구 부딪힘
            if (ray.exitDist !== null && !ray.exitTriggered && pulse.r >= ray.exitDist && ray.exitDist < ray.wallDist) {
                ray.exitTriggered = true;
                particles.push({
                    x: pulse.x + Math.cos(ray.angle) * ray.exitDist,
                    y: pulse.y + Math.sin(ray.angle) * ray.exitDist,
                    alpha: 1.0,
                    type: 'exit'
                });
            }
        }

        if (pulse.r > pulse.maxR) {
            pulses.splice(p, 1);
        }
    }

    // 4. 입자 잔상 페이드아웃
    for (let i = particles.length - 1; i >= 0; i--) {
        const pt = particles[i];
        pt.alpha -= (pt.type === 'exit' ? 0.003 : 0.005); // 잔상 시간 유지
        if (pt.alpha <= 0) {
            particles.splice(i, 1);
        }
    }

    // 5. 승리 조건 검사
    const stg = STAGES[currentStageIdx];
    const distToExit = Math.hypot(player.x - stg.exit.x, player.y - stg.exit.y);
    if (distToExit < stg.exit.r + player.r) {
        gameActive = false;
        document.getElementById('clear-modal').style.display = 'flex';
    }
}

function render() {
    // 배경 암흑 초기화
    ctx.fillStyle = '#030508';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // 1. 반사 잔상 입자 그리기
    for (let pt of particles) {
        if (pt.type === 'wall') {
            ctx.fillStyle = `rgba(0, 234, 255, ${pt.alpha})`;
            ctx.fillRect(pt.x - 1.5, pt.y - 1.5, 3, 3);
        } else if (pt.type === 'exit') {
            ctx.fillStyle = `rgba(255, 215, 0, ${pt.alpha})`;
            ctx.beginPath();
            ctx.arc(pt.x, pt.y, 2.5, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    // 2. 진행 중인 소나 음파링 그리기
    for (let pulse of pulses) {
        const alpha = Math.max(0, 1 - pulse.r / pulse.maxR);
        ctx.strokeStyle = `rgba(0, 234, 255, ${alpha * 0.4})`;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(pulse.x, pulse.y, pulse.r, 0, Math.PI * 2);
        ctx.stroke();
    }

    // 3. 플레이어 본인 위치 표시 (희미한 가이드광)
    ctx.fillStyle = 'rgba(0, 234, 255, 0.15)';
    ctx.beginPath();
    ctx.arc(player.x, player.y, 14, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#00eaff';
    ctx.beginPath();
    ctx.arc(player.x, player.y, player.r, 0, Math.PI * 2);
    ctx.fill();
}

requestAnimationFrame(gameLoop);
</script>
</body>
</html>
"""

# Streamlit 내 HTML 컴포넌트 삽입
components.html(game_html, height=630)
