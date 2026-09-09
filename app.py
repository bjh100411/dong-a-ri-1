import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="2D Grappling Hook Swing", page_icon="🪝", layout="centered")

st.title("🪝 2D Grappling Hook Swing Engine")
st.caption("조작법: 방향키(이동/조준) | Space(와이어 발사 및 줄 감기) | Shift(와이어 해제) | R(리셋)")

# 물리 엔진 및 레이캐스팅이 포함된 HTML5 Canvas 게임 코드
game_code = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { margin: 0; padding: 0; background-color: #1a1a1a; display: flex; justify-content: center; align-items: center; color: white; font-family: sans-serif; }
        canvas { border: 2px solid #444; background: #0f172a; border-radius: 8px; }
    </style>
</head>
<body>
    <canvas id="gameCanvas" width="800" height="500"></canvas>

<script>
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

// 물리 환경 변수
const GRAVITY = 0.35;
const FRICTION = 0.99;
const AIR_RESISTANCE = 0.995;

// 플레이어 객체
const player = {
    x: 100, y: 300,
    vx: 0, vy: 0,
    radius: 12,
    speed: 0.5,
    aimAngle: -Math.PI / 4
};

// 와이어 객체
const hook = {
    active: false,
    x: 0, y: 0,
    length: 0,
    maxLength: 400
};

// 지형 장애물 (고정 블록)
const obstacles = [
    {x: 200, y: 100, w: 120, h: 30},
    {x: 450, y: 150, w: 150, h: 30},
    {x: 300, y: 300, w: 100, h: 20},
    {x: 650, y: 200, w: 100, h: 30},
    {x: 0, y: 0, w: 800, h: 20} // 천장
];

const keys = {};

window.addEventListener('keydown', e => {
    keys[e.code] = true;
    if (e.code === 'Space' && !hook.active) fireHook();
    if (e.code === 'ShiftLeft' || e.code === 'ShiftRight') releaseHook();
    if (e.code === 'KeyR') resetPlayer();
});

window.addEventListener('keyup', e => { keys[e.code] = false; });

// DDA 레이캐스팅 알고리즘 (와이어 발사 위치 계산)
function raycast(startX, startY, angle, maxDist) {
    const dirX = Math.cos(angle);
    const dirY = Math.sin(angle);
    let hit = null;
    let minT = maxDist;

    for (let obs of obstacles) {
        // AABB 사각형 4개 변과의 교점 검사
        const lines = [
            {p1: {x: obs.x, y: obs.y}, p2: {x: obs.x + obs.w, y: obs.y}},
            {p1: {x: obs.x, y: obs.y + obs.h}, p2: {x: obs.x + obs.w, y: obs.y + obs.h}},
            {p1: {x: obs.x, y: obs.y}, p2: {x: obs.x, y: obs.y + obs.h}},
            {p1: {x: obs.x + obs.w, y: obs.y}, p2: {x: obs.x + obs.w, y: obs.y + obs.h}}
        ];

        for (let line of lines) {
            const intersect = lineIntersect(startX, startY, startX + dirX * maxDist, startY + dirY * maxDist, line.p1.x, line.p1.y, line.p2.x, line.p2.y);
            if (intersect && intersect.t < minT) {
                minT = intersect.t;
                hit = { x: intersect.x, y: intersect.y };
            }
        }
    }
    return hit;
}

function lineIntersect(x1, y1, x2, y2, x3, y3, x4, y4) {
    const denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1);
    if (denom === 0) return null;
    const ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom;
    const ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom;
    if (ua >= 0 && ua <= 1 && ub >= 0 && ub <= 1) {
        return { x: x1 + ua * (x2 - x1), y: y1 + ua * (y2 - y1), t: ua * 400 };
    }
    return null;
}

function fireHook() {
    const hit = raycast(player.x, player.y, player.aimAngle, hook.maxLength);
    if (hit) {
        hook.active = true;
        hook.x = hit.x;
        hook.y = hit.y;
        hook.length = Math.hypot(player.x - hook.x, player.y - hook.y);
    }
}

function releaseHook() {
    hook.active = false;
}

function resetPlayer() {
    player.x = 100; player.y = 300;
    player.vx = 0; player.vy = 0;
    releaseHook();
}

function update() {
    // 조준 및 위치 조절
    if (keys['ArrowUp']) player.aimAngle -= 0.04;
    if (keys['ArrowDown']) player.aimAngle += 0.04;
    if (keys['ArrowLeft']) player.vx -= player.speed;
    if (keys['ArrowRight']) player.vx += player.speed;

    // 중력 및 공기저항 적용
    player.vy += GRAVITY;
    player.vx *= AIR_RESISTANCE;
    player.vy *= AIR_RESISTANCE;

    // 진자 운동 (Pendulum Constraint) 로직
    if (hook.active) {
        if (keys['Space']) hook.length = Math.max(30, hook.length - 3); // 줄 감기

        let dx = player.x - hook.x;
        let dy = player.y - hook.y;
        let distance = Math.hypot(dx, dy);

        if (distance > hook.length) {
            let angle = Math.atan2(dy, dx);
            player.x = hook.x + Math.cos(angle) * hook.length;
            player.y = hook.y + Math.sin(angle) * hook.length;

            // 속도를 구속 구면에 대해 구직교 투영 (수직 속도 제거)
            let nx = dx / distance;
            let ny = dy / distance;
            let dot = player.vx * nx + player.vy * ny;
            player.vx -= dot * nx;
            player.vy -= dot * ny;
        }
    }

    // 위치 업데이트
    player.x += player.vx;
    player.y += player.vy;

    // 바닥 충돌
    if (player.y + player.radius > canvas.height) {
        player.y = canvas.height - player.radius;
        player.vy = 0;
        player.vx *= FRICTION;
    }
}

function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 장애물 수식 렌더링
    ctx.fillStyle = '#334155';
    obstacles.forEach(obs => {
        ctx.fillRect(obs.x, obs.y, obs.w, obs.h);
        ctx.strokeStyle = '#38bdf8';
        ctx.strokeRect(obs.x, obs.y, obs.w, obs.h);
    });

    // 와이어 조준선 표시 (비활성 시)
    if (!hook.active) {
        const hit = raycast(player.x, player.y, player.aimAngle, hook.maxLength);
        ctx.beginPath();
        ctx.moveTo(player.x, player.y);
        ctx.lineTo(
            hit ? hit.x : player.x + Math.cos(player.aimAngle) * hook.maxLength,
            hit ? hit.y : player.y + Math.sin(player.aimAngle) * hook.maxLength
        );
        ctx.strokeStyle = hit ? 'rgba(52, 211, 153, 0.6)' : 'rgba(239, 68, 68, 0.3)';
        ctx.setLineDash([4, 4]);
        ctx.stroke();
        ctx.setLineDash([]);
    }

    // 와이어 연결선 (활성 시)
    if (hook.active) {
        ctx.beginPath();
        ctx.moveTo(player.x, player.y);
        ctx.lineTo(hook.x, hook.y);
        ctx.strokeStyle = '#f59e0b';
        ctx.lineWidth = 3;
        ctx.stroke();
        ctx.lineWidth = 1;

        // 앵커 포인트
        ctx.beginPath();
        ctx.arc(hook.x, hook.y, 5, 0, Math.PI * 2);
        ctx.fillStyle = '#ef4444';
        ctx.fill();
    }

    // 플레이어
    ctx.beginPath();
    ctx.arc(player.x, player.y, player.radius, 0, Math.PI * 2);
    ctx.fillStyle = '#38bdf8';
    ctx.fill();
    ctx.strokeStyle = '#fff';
    ctx.stroke();

    requestAnimationFrame(() => {
        update();
        draw();
    });
}

draw();
</script>
</body>
</html>
"""

components.html(game_code, height=520)
