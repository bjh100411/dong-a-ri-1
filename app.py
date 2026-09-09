import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Parry Action Game", page_icon="⚔️", layout="centered")

st.title("⚔️ 타이밍 패링 액션 게임")

# HTML5/JS 기반 실시간 액션 엔진
game_html = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <style>
        body {
            margin: 0;
            background-color: #121212;
            color: #fff;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            font-family: sans-serif;
            user-select: none;
        }
        canvas {
            border: 2px solid #333;
            border-radius: 10px;
            background-color: #1a1a1a;
            box-shadow: 0 8px 24px rgba(0,0,0,0.6);
        }
        .info-panel {
            margin-top: 12px;
            text-align: center;
            color: #888;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <canvas id="gameCanvas" width="680" height="320"></canvas>
    <div class="info-panel">
        키보드 [Spacebar] 또는 화면 클릭으로 적의 공격을 쳐내세요!
    </div>

    <script>
        const canvas = document.getElementById("gameCanvas");
        const ctx = canvas.getContext("2d");

        // 플레이어 상태
        let player = {
            baseX: 180,
            x: 180,
            y: 190,
            width: 40,
            height: 70,
            vx: 0,
            isParrying: false,
            parryTimer: 0,
            parryWindow: 12, // 패링 유효 프레임
            hp: 100
        };

        // 적 상태
        let enemy = {
            x: 480,
            y: 170,
            width: 55,
            height: 90,
            state: "idle", // idle, windup, attack, recover
            timer: 0
        };

        let particles = [];
        let screenShake = 0;
        let score = 0;
        let statusText = "적의 전조 증상(주황색)을 잘 관찰하세요!";

        // 키 입력 제어
        window.addEventListener("keydown", (e) => {
            if (e.code === "Space") {
                triggerParry();
            }
        });

        canvas.addEventListener("mousedown", () => {
            triggerParry();
        });

        function triggerParry() {
            if (player.parryTimer <= 0) {
                player.isParrying = true;
                player.parryTimer = player.parryWindow;
            }
        }

        // 패링 파티클 생성
        function createParrySparks(x, y) {
            for (let i = 0; i < 30; i++) {
                particles.push({
                    x: x,
                    y: y,
                    vx: (Math.random() - 0.5) * 16,
                    vy: (Math.random() - 0.5) * 16,
                    size: Math.random() * 5 + 2,
                    color: Math.random() > 0.3 ? '#00ffff' : '#ffffff',
                    life: 25
                });
            }
        }

        function update() {
            // 1. 묵직한 밀림 연출 (감쇠 물리)
            player.x += player.vx;
            player.vx *= 0.82; // 강한 마찰력으로 묵직하게 멈춤

            // 복원력 (천천히 원래 자리로)
            if (Math.abs(player.vx) < 0.2) {
                player.x += (player.baseX - player.x) * 0.05;
            }

            // 패링 타이머 계산
            if (player.parryTimer > 0) {
                player.parryTimer--;
                if (player.parryTimer === 0) {
                    player.isParrying = false;
                }
            }

            // 2. 적 AI 및 공격 상태 머신
            enemy.timer++;
            if (enemy.state === "idle") {
                if (enemy.timer > 80) { // 준비
                    enemy.state = "windup";
                    enemy.timer = 0;
                }
            } else if (enemy.state === "windup") { // 선주동 (주황색 경고)
                if (enemy.timer > 40) { // 공격 시작
                    enemy.state = "attack";
                    enemy.timer = 0;
                }
            } else if (enemy.state === "attack") { // 공격 적중 순간
                if (player.isParrying) {
                    // ★ 패링 성공 ★
                    statusText = "⚡ PERFECT PARRY! ⚡";
                    screenShake = 16;
                    player.vx = -22; // 강하게 뒤로 튕겨 나감 (묵직한 연출)
                    createParrySparks(player.x + player.width + 10, player.y + 35);
                    score += 150;
                    enemy.state = "recover";
                    enemy.timer = 0;
                } else if (enemy.timer > 8) {
                    // 패링 실패 (피격)
                    statusText = "💥 피격당했습니다!";
                    screenShake = 10;
                    player.hp = Math.max(0, player.hp - 20);
                    player.vx = -10;
                    enemy.state = "recover";
                    enemy.timer = 0;
                }
            } else if (enemy.state === "recover") {
                if (enemy.timer > 45) {
                    enemy.state = "idle";
                    enemy.timer = 0;
                }
            }

            // 화면 흔들림 감쇠
            if (screenShake > 0) screenShake *= 0.88;

            // 파티클 처리
            particles.forEach((p, index) => {
                p.x += p.vx;
                p.y += p.vy;
                p.life--;
                if (p.life <= 0) particles.splice(index, 1);
            });
        }

        function draw() {
            ctx.save();

            // 화면 흔들림 적용
            if (screenShake > 0.5) {
                ctx.translate((Math.random() - 0.5) * screenShake, (Math.random() - 0.5) * screenShake);
            }

            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // 바닥 선
            ctx.strokeStyle = "#444";
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(0, 260);
            ctx.lineTo(680, 260);
            ctx.stroke();

            // 플레이어 그리기
            ctx.fillStyle = player.isParrying ? "#00e5ff" : "#2ecc71";
            ctx.fillRect(player.x, player.y, player.width, player.height);

            // 패링 쉴드 이펙트
            if (player.isParrying) {
                ctx.strokeStyle = "rgba(0, 229, 255, 0.9)";
                ctx.lineWidth = 5;
                ctx.beginPath();
                ctx.arc(player.x + player.width, player.y + player.height / 2, 35, -Math.PI / 2, Math.PI / 2);
                ctx.stroke();
            }

            // 적 그리기
            if (enemy.state === "idle") ctx.fillStyle = "#e74c3c";
            else if (enemy.state === "windup") ctx.fillStyle = "#f39c12"; // 공격 전조
            else if (enemy.state === "attack") ctx.fillStyle = "#ff0055"; // 실제 공격
            else if (enemy.state === "recover") ctx.fillStyle = "#555555"; // 후딜레이

            ctx.fillRect(enemy.x, enemy.y, enemy.width, enemy.height);

            // 적 공격 이펙트
            if (enemy.state === "attack") {
                ctx.fillStyle = "rgba(255, 0, 85, 0.4)";
                ctx.beginPath();
                ctx.arc(enemy.x, enemy.y + 45, 100, Math.PI * 0.75, Math.PI * 1.25);
                ctx.fill();
            }

            // 파티클 그리기
            particles.forEach(p => {
                ctx.fillStyle = p.color;
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                ctx.fill();
            });

            ctx.restore();

            // HUD UI
            ctx.fillStyle = "#ffffff";
            ctx.font = "bold 15px sans-serif";
            ctx.fillText(`HP: ${player.hp}`, 20, 30);
            ctx.fillText(`SCORE: ${score}`, 20, 52);

            ctx.font = "bold 16px sans-serif";
            ctx.textAlign = "center";
            ctx.fillStyle = player.isParrying ? "#00e5ff" : "#cccccc";
            ctx.fillText(statusText, canvas.width / 2, 35);
            ctx.textAlign = "start";
        }

        function loop() {
            update();
            draw();
            requestAnimationFrame(loop);
        }

        loop();
    </script>
</body>
</html>
"""

components.html(game_html, height=380)
