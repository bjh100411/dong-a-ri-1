import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="RNG Weather Platformer", layout="centered")

st.title("🌪️ 무작위 카오스 기상 플랫포머")
st.write("방향키: 이동 및 점프 (↑) | **Shift**: 강풍/지형 버티기")

game_code = """
<!DOCTYPE html>
<html>
<head>
<style>
  body { margin: 0; background: #0e1117; display: flex; justify-content: center; }
  canvas { border: 3px solid #31333F; border-radius: 8px; background: #1a1c23; }
</style>
</head>
<body>
<canvas id="canvas" width="750" height="400"></canvas>

<script>
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');

// 게임 및 물리 변수 정의
const player = { x: 50, y: 300, w: 24, h: 24, vx: 0, vy: 0, grounded: false };
const platforms = [
  { x: 0, y: 360, w: 750, h: 40 },
  { x: 120, y: 280, w: 120, h: 16 },
  { x: 300, y: 210, w: 140, h: 16 },
  { x: 500, y: 150, w: 120, h: 16 },
  { x: 670, y: 90, w: 60, h: 16 }
];
const goal = { x: 685, y: 50, w: 30, h: 30 };

// 기본 물리 계수
let gravity = 0.55;
let friction = 0.82;
let wind = 0;

// RNG 기상 시스템
const weathers = [
  { name: 'NORMAL', color: '#888', g: 0.55, f: 0.82, w: 0 },
  { name: '강풍 (WIND)', color: '#00d2ff', g: 0.55, f: 0.82, w: -0.9 },
  { name: '저중력 (LOW GRAVITY)', color: '#a855f7', g: 0.18, f: 0.85, w: 0 },
  { name: '빙판 (ICE)', color: '#38bdf8', g: 0.55, f: 0.98, w: 0 },
  { name: '벼락 (THUNDER)', color: '#eab308', g: 0.85, f: 0.82, w: 0 }
];

let currentWeather = weathers[0];
let timer = 5.0; // 5초 주기 변경
let lastTime = performance.now();

const keys = {};
window.addEventListener('keydown', e => keys[e.code] = true);
window.addEventListener('keyup', e => keys[e.code] = false);

function changeWeather() {
  const nextIdx = Math.floor(Math.random() * weathers.length);
  currentWeather = weathers[nextIdx];
}

function update(dt) {
  // 타이머 카운트다운
  timer -= dt;
  if (timer <= 0) {
    changeWeather();
    timer = 5.0;
  }

  // 실시간 물리 변수 동적 동기화
  gravity = currentWeather.g;
  friction = currentWeather.f;
  let activeWind = currentWeather.w;

  // Shift 버티기 조작 (바람 저항력 증가)
  const isShift = keys['ShiftLeft'] || keys['ShiftRight'];
  if (isShift && activeWind !== 0) {
    activeWind *= 0.2;
  }

  // 이동 처리
  if (keys['ArrowRight']) player.vx += 0.8;
  if (keys['ArrowLeft']) player.vx -= 0.8;
  if ((keys['ArrowUp'] || keys['KeyW']) && player.grounded) {
    player.vy = -11;
    player.grounded = false;
  }

  // 물리 가속도 적용
  player.vx += activeWind;
  player.vx *= friction;
  player.vy += gravity;

  player.x += player.vx;
  player.y += player.vy;

  // 발판 충돌 판정 (AABB)
  player.grounded = false;
  for (let p of platforms) {
    if (player.x < p.x + p.w && player.x + player.w > p.x &&
        player.y + player.h >= p.y && player.y + player.h <= p.y + p.h + player.vy) {
      player.y = p.y - player.h;
      player.vy = 0;
      player.grounded = true;
    }
  }

  // 화면 경계 제약
  if (player.x < 0) player.x = 0;
  if (player.x + player.w > canvas.width) player.x = canvas.width - player.w;
  if (player.y > canvas.height) { // 낙하 시 리셋
    player.x = 50; player.y = 300; player.vx = 0; player.vy = 0;
  }
}

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // 배경 기상 이펙트
  ctx.fillStyle = currentWeather.color + '15';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // 발판 그려주기
  ctx.fillStyle = currentWeather.name === '빙판 (ICE)' ? '#7dd3fc' : '#4b5563';
  for (let p of platforms) ctx.fillRect(p.x, p.y, p.w, p.h);

  // 골인 지점
  ctx.fillStyle = '#22c55e';
  ctx.fillRect(goal.x, goal.y, goal.w, goal.h);

  // 플레이어
  ctx.fillStyle = '#f43f5e';
  ctx.fillRect(player.x, player.y, player.w, player.h);

  // UI 헤더 표시
  ctx.fillStyle = '#fff';
  ctx.font = 'bold 16px sans-serif';
  ctx.fillText(`현재 기후: ${currentWeather.name}`, 20, 30);
  ctx.fillText(`기후 변화까지: ${timer.toFixed(1)}초`, 20, 55);
}

function loop(now) {
  const dt = (now - lastTime) / 1000;
  lastTime = now;
  update(Math.min(dt, 0.1));
  draw();
  requestAnimationFrame(loop);
}
requestAnimationFrame(loop);
</script>
</body>
</html>
"""

components.html(game_code, height=430)
