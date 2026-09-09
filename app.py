import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="2D 탄막 슈팅 (Bullet Hell)",
    page_icon="🚀",
    layout="centered"
)

st.title("🚀 2D 탄막 슈팅 (Bullet Hell)")
st.caption("삼각함수 기반 기하학 탄막 패턴 & 미세 히트박스 회피 게임")

with st.expander("🎮 조작 방법 및 개발 포인트", expanded=True):
    st.markdown("""
    - **이동**: `방향키`
    - **저속 정밀 이동**: `Shift` (누르고 있을 때 이동 속도 감속 및 히트박스 표시)
    - **일반 사격**: `Z`
    - **필살기 (폭탄)**: `X` (화면 내 모든 탄막 제거 및 보스 대량 데미지)
    - **개발 핵심**: 
      - $v_x = v \cdot \cos(\theta)$, $v_y = v \cdot \sin(\theta)$ 삼각함수를 이용한 나선형/원형 탄막 알고리즘
      - 플레이어 중앙 반경 3px 미세 히트박스(Point Hitbox) 판정
    """)

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
        background-color: #050508;
        color: #ffffff;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        display: flex;
        justify-content: center;
        align-items: center;
        user-select: none;
    }
    #game-container {
        position: relative;
        width: 600px;
        height: 700px;
        box-shadow: 0 0 25px rgba(255, 0, 100, 0.25);
        border-radius: 8px;
        overflow: hidden;
        border: 2px solid #2a1b3d;
    }
    canvas {
        display: block;
        background: #080710;
    }
    #ui-overlay {
        position: absolute;
        top: 10px;
        left: 10px;
        right: 10px;
        display: flex;
        justify-content: space-between;
        pointer-events: none;
        font-size: 13px;
        font-weight: bold;
    }
    .hud-card {
        background: rgba(15, 12, 25, 0.8);
        padding: 6px 12px;
        border-radius: 6px;
        border: 1px solid rgba(255, 255, 255, 0.15);
    }
    #boss-hp-container {
        position: absolute;
        top: 45px;
        left: 20px;
        right: 20px;
        height: 8px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 4px;
        overflow: hidden;
        border: 1px solid rgba(255, 0, 100, 0.3);
    }
    #boss-hp-bar {
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, #ff0055, #ff5500);
        transition: width 0.1s linear;
    }
    .modal {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(8, 7, 16, 0.9);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        backdrop-filter: blur(5px);
        z-index: 10;
    }
    h2 { margin: 0 0 10px 0; color: #ff0055; text-shadow: 0 0 10px rgba(ff,0,85,0.5); }
    p { margin: 5px 0 20px 0; color: #a0a0b0; text-align: center; font-size: 14px; }
    .btn {
        background: linear-gradient(135deg, #ff0055, #9900ff);
        color: #fff;
        font-weight: bold;
        padding: 10px 24px;
        border-radius: 20px;
        border: none;
        cursor: pointer;
        font-size: 14px;
        box-shadow: 0 0 15px rgba(255, 0, 85, 0.4);
    }
    .btn:hover { transform: scale(1.05); }
</style>
</head>
<body>

<div id="game-container" tabindex="0">
    <canvas id="canvas" width="600" height="700"></canvas>
    
    <div id="ui-overlay">
        <div class="hud-card" id="score-txt">SCORE: 0</div>
        <div class="hud-card" id="life-txt">LIVES: ❤️❤️❤️</div>
        <div class="hud-card" id="bomb-txt">BOMBS: 💣💣💣</div>
    </div>
    
    <div id="boss-hp-container">
        <div id="boss-hp-bar"></div>
    </div>

    <!-- 시작 화면 -->
    <div id="start-modal" class="modal">
        <h2>🚀 BULLET HELL SHMUP</h2>
        <p>화면을 채우는 탄막을 사슬처럼 피해 보스를 격파하세요!<br><b>Shift</b>로 정밀 이동, <b>Z</b>로 공격, <b>X</b>로 폭탄</p>
        <button class="btn" onclick="startGame()">게임 시작</button>
    </div>

    <!-- 게임 오버 / 클리어 화면 -->
    <div id="end-modal" class="modal" style="display: none;">
        <h2 id="end-title">GAME OVER</h2>
        <p id="end-desc"></p>
        <button class="btn" onclick="restartGame()">다시 도전</button>
    </div>
</div>

<script>
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const container = document.getElementById('game-container');

// 오디오 합성기 (Web Audio API)
let audioCtx = null;
function initAudio() {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    if (audioCtx.state === 'suspended') audioCtx.resume();
}

function playSound(type) {
    if (!audioCtx) return;
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);

    if (type === 'shoot') {
        osc.type = 'square';
        osc.frequency.setValueAtTime(800, audioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(200, audioCtx.currentTime + 0.05);
        gain.gain.setValueAtTime(0.05, audioCtx.currentTime);
        gain.gain.linearRampToValueAtTime(0.01, audioCtx.currentTime + 0.05);
        osc.start(); osc.stop(audioCtx.currentTime + 0.05);
    } else if (type === 'bomb') {
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(150, audioCtx.currentTime);
        osc.frequency.linearRampToValueAtTime(40, audioCtx.currentTime + 0.6);
        gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
        gain.gain.linearRampToValueAtTime(0.01, audioCtx.currentTime + 0.6);
        osc.start(); osc.stop(audioCtx.currentTime + 0.6);
    } else if (type === 'hit') {
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(120, audioCtx.currentTime);
        osc.frequency.linearRampToValueAtTime(30, audioCtx.currentTime + 0.2);
        gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
        gain.gain.linearRampToValueAtTime(0.01, audioCtx.currentTime + 0.2);
        osc.start(); osc.stop(audioCtx.currentTime + 0.2);
    }
}

// 상태 변수
let keys = {};
let gameActive = false;
let score = 0;
let frameCount = 0;

// 플레이어 설정
const player = {
    x: 300, y: 580,
    hitRadius: 3, // 미세 히트박스 (Point Hitbox)
    drawRadius: 14,
    speedNormal: 5.0,
    speedSlow: 2.2,
    lives: 3,
    bombs: 3,
    invulnerableTimer: 0,
    shootCooldown: 0
};

// 보스 설정
const boss = {
    x: 300, y: 120,
    radius: 30,
    maxHp: 1200,
    hp: 1200,
    pattern: 0,
    patternTimer: 0,
    angleOffset: 0
};

let playerBullets = [];
let enemyBullets = [];

// 키 입력 이벤트 Listener
window.addEventListener('keydown', e => {
    if (['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','ShiftLeft','ShiftRight','KeyZ','KeyX'].includes(e.code)) {
        e.preventDefault();
    }
    keys[e.code] = true;
});
window.addEventListener('keyup', e => { keys[e.code] = false; });

function startGame() {
    initAudio();
    document.getElementById('start-modal').style.display = 'none';
    resetGame();
    gameActive = true;
    container.focus();
}

function restartGame() {
    document.getElementById('end-modal').style.display = 'none';
    resetGame();
    gameActive = true;
    container.focus();
}

function resetGame() {
    score = 0;
    frameCount = 0;
    player.x = 300; player.y = 580;
    player.lives = 3; player.bombs = 3;
    player.invulnerableTimer = 0;
    boss.hp = boss.maxHp;
    boss.x = 300; boss.y = 120;
    boss.pattern = 0; boss.patternTimer = 0;
    playerBullets = [];
    enemyBullets = [];
    updateHUD();
}

function updateHUD() {
    document.getElementById('score-txt').innerText = `SCORE: ${score}`;
    document.getElementById('life-txt').innerText = `LIVES: ${'❤️'.repeat(Math.max(0, player.lives))}`;
    document.getElementById('bomb-txt').innerText = `BOMBS: ${'💣'.repeat(Math.max(0, player.bombs))}`;
    document.getElementById('boss-hp-bar').style.width = `${Math.max(0, (boss.hp / boss.maxHp) * 100)}%`;
}

// 삼각함수 탄막 발사 로직
function spawnBossBullets() {
    boss.patternTimer++;
    boss.angleOffset += 0.04;

    // Pattern 1: 나선형 연속 탄막 (Spiral Pattern)
    if (boss.pattern === 0) {
        if (boss.patternTimer % 3 === 0) {
            const arms = 4;
            const speed = 3.2;
            for (let i = 0; i < arms; i++) {
                const angle = boss.angleOffset + (i * Math.PI * 2 / arms);
                enemyBullets.push({
                    x: boss.x, y: boss.y,
                    vx: Math.cos(angle) * speed,
                    vy: Math.sin(angle) * speed,
                    r: 4, color: '#ff0055'
                });
            }
        }
        if (boss.patternTimer > 300) {
            boss.pattern = 1;
            boss.patternTimer = 0;
        }
    }
    // Pattern 2: 방사형 파동 + 기하학적 링 (Radial Wave)
    else if (boss.pattern === 1) {
        if (boss.patternTimer % 45 === 0) {
            const count = 24;
            const speed = 2.8;
            for (let i = 0; i < count; i++) {
                const angle = (i * Math.PI * 2 / count) + (boss.patternTimer * 0.01);
                enemyBullets.push({
                    x: boss.x, y: boss.y,
                    vx: Math.cos(angle) * speed,
                    vy: Math.sin(angle) * speed,
                    r: 5, color: '#00eaff'
                });
            }
        }
        if (boss.patternTimer > 250) {
            boss.pattern = 2;
            boss.patternTimer = 0;
        }
    }
    // Pattern 3: 조준격발 + 삼각함수 교차 탄막 (Targeted Cross)
    else if (boss.pattern === 2) {
        if (boss.patternTimer % 20 === 0) {
            const angleToPlayer = Math.atan2(player.y - boss.y, player.x - boss.x);
            const spread = 0.25;
            [-spread, 0, spread].forEach(offset => {
                enemyBullets.push({
                    x: boss.x, y: boss.y,
                    vx: Math.cos(angleToPlayer + offset) * 4.0,
                    vy: Math.sin(angleToPlayer + offset) * 4.0,
                    r: 4.5, color: '#ffcc00'
                });
            });
        }
        if (boss.patternTimer > 200) {
            boss.pattern = 0;
            boss.patternTimer = 0;
        }
    }
}

// 폭탄 (필살기) 사용
function useBomb() {
    if (player.bombs > 0) {
        player.bombs--;
        playSound('bomb');
        enemyBullets = []; // 탄막 소멸
        boss.hp -= 80;    // 보스 대량 데미지
        player.invulnerableTimer = 90; // 무적 90프레임
        updateHUD();
    }
}

function update() {
    frameCount++;

    // 1. 플레이어 이동
    const isSlow = keys['ShiftLeft'] || keys['ShiftRight'];
    const currentSpeed = isSlow ? player.speedSlow : player.speedNormal;

    let moveX = 0, moveY = 0;
    if (keys['ArrowLeft']) moveX -= 1;
    if (keys['ArrowRight']) moveX += 1;
    if (keys['ArrowUp']) moveY -= 1;
    if (keys['ArrowDown']) moveY += 1;

    if (moveX !== 0 && moveY !== 0) {
        moveX *= 0.7071;
        moveY *= 0.7071;
    }

    player.x = Math.max(15, Math.min(canvas.width - 15, player.x + moveX * currentSpeed));
    player.y = Math.max(15, Math.min(canvas.height - 15, player.y + moveY * currentSpeed));

    // 2. 플레이어 사격 (Z)
    if (player.shootCooldown > 0) player.shootCooldown--;
    if (keys['KeyZ'] && player.shootCooldown <= 0) {
        playSound('shoot');
        playerBullets.push({ x: player.x - 8, y: player.y - 10, vy: -12 });
        playerBullets.push({ x: player.x + 8, y: player.y - 10, vy: -12 });
        player.shootCooldown = 5;
    }

    // 3. 폭탄 발사 (X)
    if (keys['KeyX']) {
        keys['KeyX'] = false; // 단발 입력
        useBomb();
    }

    // 무적 타이머 감쇠
    if (player.invulnerableTimer > 0) player.invulnerableTimer--;

    // 4. 아군 총알 업데이트 및 충돌
    for (let i = playerBullets.length - 1; i >= 0; i--) {
        const pb = playerBullets[i];
        pb.y += pb.vy;

        // 보스 충돌
        const distBoss = Math.hypot(pb.x - boss.x, pb.y - boss.y);
        if (distBoss < boss.radius + 4) {
            boss.hp -= 2.5;
            score += 10;
            playerBullets.splice(i, 1);
            updateHUD();
            continue;
        }

        if (pb.y < -10) playerBullets.splice(i, 1);
    }

    // 5. 보스 탄막 업데이트 및 히트박스 충돌 판정
    spawnBossBullets();

    for (let i = enemyBullets.length - 1; i >= 0; i--) {
        const eb = enemyBullets[i];
        eb.x += eb.vx;
        eb.y += eb.vy;

        // 플레이어 정밀 충돌 판정 (Point Hitbox vs Circle)
        if (player.invulnerableTimer <= 0) {
            const distPlayer = Math.hypot(eb.x - player.x, eb.y - player.y);
            if (distPlayer < eb.r + player.hitRadius) {
                // 피격!
                playSound('hit');
                player.lives--;
                player.invulnerableTimer = 120; // 2초간 무적
                enemyBullets.splice(i, 1);
                updateHUD();

                if (player.lives <= 0) {
                    endGame(false);
                    return;
                }
                continue;
            }
        }

        // 화면 밖 제거
        if (eb.x < -20 || eb.x > canvas.width + 20 || eb.y < -20 || eb.y > canvas.height + 20) {
            enemyBullets.splice(i, 1);
        }
    }

    // 6. 보스 사망 판정
    if (boss.hp <= 0) {
        endGame(true);
    }
}

function endGame(isWin) {
    gameActive = false;
    const modal = document.getElementById('end-modal');
    const title = document.getElementById('end-title');
    const desc = document.getElementById('end-desc');

    if (isWin) {
        title.innerText = "🎉 STAGE CLEAR!";
        title.style.color = "#00eaff";
        desc.innerText = `축하합니다! 보스를 격파했습니다.\n최종 점수: ${score}`;
    } else {
        title.innerText = "GAME OVER";
        title.style.color = "#ff0055";
        desc.innerText = `탄막 회피 실패...\n최종 점수: ${score}`;
    }
    modal.style.display = 'flex';
}

function render() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 1. 보스 그리기
    if (boss.hp > 0) {
        ctx.fillStyle = '#ff0055';
        ctx.shadowBlur = 15;
        ctx.shadowColor = '#ff0055';
        ctx.beginPath();
        ctx.arc(boss.x, boss.y, boss.radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;
    }

    // 2. 플레이어 사격 탄막 그리기
    ctx.fillStyle = '#ffff00';
    for (let pb of playerBullets) {
        ctx.fillRect(pb.x - 2, pb.y - 6, 4, 12);
    }

    // 3. 적 탄막 그리기
    for (let eb of enemyBullets) {
        ctx.fillStyle = eb.color;
        ctx.beginPath();
        ctx.arc(eb.x, eb.y, eb.r, 0, Math.PI * 2);
        ctx.fill();
    }

    // 4. 플레이어 기체 그리기
    if (player.invulnerableTimer % 6 < 3) { // 무적 시 깜빡임
        // 기체 외형 (삼각형)
        ctx.fillStyle = '#00eaff';
        ctx.beginPath();
        ctx.moveTo(player.x, player.y - player.drawRadius);
        ctx.lineTo(player.x - player.drawRadius, player.y + player.drawRadius);
        ctx.lineTo(player.x + player.drawRadius, player.y + player.drawRadius);
        ctx.closePath();
        ctx.fill();

        // Shift(저속 모드) 누를 시 미세 히트박스 시각화
        const isSlow = keys['ShiftLeft'] || keys['ShiftRight'];
        if (isSlow) {
            ctx.fillStyle = '#ffffff';
            ctx.strokeStyle = '#ff0055';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.arc(player.x, player.y, player.hitRadius + 2, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();
        }
    }
}

function gameLoop() {
    if (gameActive) {
        update();
    }
    render();
    requestAnimationFrame(gameLoop);
}

requestAnimationFrame(gameLoop);
</script>
</body>
</html>
"""

components.html(game_html, height=730)
