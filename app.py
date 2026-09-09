import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Parry & Skill Action", page_icon="⚔️", layout="centered")

st.title("⚔️ 멀티 적 패링 & 랜덤 스킬 액션")
st.caption("WASD / 방향키 : 이동 | Spacebar : 패링 | 숫자 1, 2, 3 또는 클릭 : 스킬 선택")

game_html = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <style>
        body {
            margin: 0;
            background-color: #0f0f15;
            color: #fff;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            user-select: none;
            overflow: hidden;
        }
        #game-container {
            position: relative;
            width: 800px;
            height: 500px;
        }
        canvas {
            border: 2px solid #2a2a3a;
            border-radius: 12px;
            background-color: #161622;
            box-shadow: 0 10px 30px rgba(0,0,0,0.8);
        }
        /* 스킬 선택 카드 UI Overlay */
        #skill-overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 800px;
            height: 500px;
            background: rgba(0, 0, 0, 0.75);
            backdrop-filter: blur(4px);
            display: none;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            border-radius: 12px;
            z-index: 10;
        }
        .skill-title {
            font-size: 24px;
            font-weight: bold;
            color: #00e5ff;
            margin-bottom: 20px;
            text-shadow: 0 0 10px rgba(0, 229, 255, 0.6);
        }
        .card-container {
            display: flex;
            gap: 15px;
        }
        .skill-card {
            width: 210px;
            height: 240px;
            background: linear-gradient(145deg, #1e1e2f, #131320);
            border: 2px solid #3a3a55;
            border-radius: 12px;
            padding: 15px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: space-between;
            cursor: pointer;
            transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;
            box-sizing: border-box;
        }
        .skill-card:hover {
            transform: translateY(-8px);
            border-color: #00ffff;
            box-shadow: 0 8px 20px rgba(0, 255, 255, 0.3);
        }
        .skill-key {
            background: #00e5ff;
            color: #000;
            font-weight: bold;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 14px;
        }
        .skill-icon {
            font-size: 42px;
            margin: 10px 0;
        }
        .skill-name {
            font-weight: bold;
            font-size: 18px;
            color: #fff;
            text-align: center;
        }
        .skill-desc {
            font-size: 12px;
            color: #aaa;
            text-align: center;
            line-height: 1.4;
        }
    </style>
</head>
<body>
    <div id="game-container">
        <canvas id="gameCanvas" width="800" height="500"></canvas>
        <div id="skill-overlay">
            <div class="skill-title">⚡ PERFECT PARRY! 스킬을 선택하세요 ⚡</div>
            <div class="card-container" id="cardContainer"></div>
        </div>
    </div>

    <script>
        const canvas = document.getElementById("gameCanvas");
        const ctx = canvas.getContext("2d");
        const skillOverlay = document.getElementById("skill-overlay");
        const cardContainer = document.getElementById("cardContainer");

        // 키 입력 관리
        let keys = {};
        window.addEventListener("keydown", (e) => {
            keys[e.code] = true;
            if (isSkillMenuOpen) {
                if (e.code === "Digit1") selectSkill(0);
                if (e.code === "Digit2") selectSkill(1);
                if (e.code === "Digit3") selectSkill(2);
            } else {
                if (e.code === "Space") triggerParry();
            }
        });
        window.addEventListener("keyup", (e) => { keys[e.code] = false; });

        // 플레이어 객체
        let player = {
            x: 400,
            y: 250,
            radius: 18,
            speed: 3.5,
            vx: 0,
            vy: 0,
            hp: 100,
            maxHp: 100,
            isParrying: false,
            parryTimer: 0,
            parryCooldown: 0
        };

        // 적 목록 및 웨이브 시스템
        let enemies = [];
        let particles = [];
        let damageTexts = [];
        let screenShake = 0;
        let score = 0;
        let isSkillMenuOpen = false;
        let currentOptions = [];

        // 전체 스킬 풀
        const SKILL_POOL = [
            {
                name: "천둥 벼락",
                icon: "⚡",
                desc: "화면 전체의 모든 적에게 70 데미지 벼락을 내리칩니다.",
                action: () => {
                    enemies.forEach(e => {
                        e.hp -= 70;
                        addDamageText(e.x, e.y - 20, "70", "#00ffff");
                        createParticles(e.x, e.y, "#00ffff", 12);
                    });
                }
            },
            {
                name: "폭발 쇼크웨이브",
                icon: "💥",
                desc: "내 주위 넓은 범위에 90 데미지를 주고 적들을 멀리 밀쳐냅니다.",
                action: () => {
                    screenShake = 15;
                    enemies.forEach(e => {
                        let dx = e.x - player.x;
                        let dy = e.y - player.y;
                        let dist = Math.hypot(dx, dy) || 1;
                        if (dist < 220) {
                            e.hp -= 90;
                            e.x += (dx / dist) * 120;
                            e.y += (dy / dist) * 120;
                            addDamageText(e.x, e.y - 20, "90", "#ff5500");
                            createParticles(e.x, e.y, "#ff5500", 15);
                        }
                    });
                }
            },
            {
                name: "빙결 파동",
                icon: "❄️",
                desc: "모든 적에게 40 데미지를 주고 3초간 완전히 얼립니다.",
                action: () => {
                    enemies.forEach(e => {
                        e.hp -= 40;
                        e.freezeTimer = 180; // 3초 (60fps 기준)
                        addDamageText(e.x, e.y - 20, "40", "#88ffff");
                        createParticles(e.x, e.y, "#88ffff", 10);
                    });
                }
            },
            {
                name: "회오리 난무",
                icon: "🌪️",
                desc: "칼날 회오리를 일으켜 가까운 적들에게 100 데미지를 입힙니다.",
                action: () => {
                    enemies.forEach(e => {
                        let dist = Math.hypot(e.x - player.x, e.y - player.y);
                        if (dist < 180) {
                            e.hp -= 100;
                            addDamageText(e.x, e.y - 20, "100", "#00ff88");
                            createParticles(e.x, e.y, "#00ff88", 15);
                        }
                    });
                }
            },
            {
                name: "흡혈 충격파",
                icon: "🩸",
                desc: "적들에게 50 데미지를 입히고, 플레이어의 HP를 30 회복합니다.",
                action: () => {
                    player.hp = Math.min(player.maxHp, player.hp + 30);
                    addDamageText(player.x, player.y - 25, "+30 HP", "#00ff00");
                    enemies.forEach(e => {
                        e.hp -= 50;
                        addDamageText(e.x, e.y - 20, "50", "#ff0055");
                        createParticles(e.x, e.y, "#ff0055", 10);
                    });
                }
            },
            {
                name: "유도 검기",
                icon: "🗡️",
                desc: "모든 적 위치에 검기를 소환하여 각 60의 데미지를 가합니다.",
                action: () => {
                    enemies.forEach(e => {
                        e.hp -= 60;
                        addDamageText(e.x, e.y - 20, "60", "#ffff00");
                        createParticles(e.x, e.y, "#ffff00", 12);
                    });
                }
            }
        ];

        // 적 생성
        function spawnEnemy() {
            if (enemies.length >= 8) return; // 최대 적 제한
            let x, y;
            if (Math.random() < 0.5) {
                x = Math.random() < 0.5 ? -20 : canvas.width + 20;
                y = Math.random() * canvas.height;
            } else {
                x = Math.random() * canvas.width;
                y = Math.random() < 0.5 ? -20 : canvas.height + 20;
            }
            enemies.push({
                x: x,
                y: y,
                radius: 16,
                hp: 120,
                maxHp: 120,
                speed: 1.2 + Math.random() * 0.8,
                state: "chase", // chase, windup, attack, stun
                stateTimer: 0,
                freezeTimer: 0
            });
        }
        setInterval(spawnEnemy, 2500);

        function triggerParry() {
            if (player.parryCooldown <= 0) {
                player.isParrying = true;
                player.parryTimer = 14; // 패링 유효 프레임
                player.parryCooldown = 35;
            }
        }

        // 패링 성공 시 스킬 선택창 오픈
        function openSkillMenu() {
            isSkillMenuOpen = true;
            // 스킬 중 무작위 3개 추출
            let shuffled = [...SKILL_POOL].sort(() => 0.5 - Math.random());
            currentOptions = shuffled.slice(0, 3);

            cardContainer.innerHTML = "";
            currentOptions.forEach((skill, index) => {
                let card = document.createElement("div");
                card.className = "skill-card";
                card.onclick = () => selectSkill(index);
                card.innerHTML = `
                    <span class="skill-key">[ Key ${index + 1} ]</span>
                    <div class="skill-icon">${skill.icon}</div>
                    <div class="skill-name">${skill.name}</div>
                    <div class="skill-desc">${skill.desc}</div>
                `;
                cardContainer.appendChild(card);
            });
            skillOverlay.style.display = "flex";
        }

        function selectSkill(index) {
            if (!isSkillMenuOpen) return;
            if (currentOptions[index]) {
                currentOptions[index].action();
            }
            isSkillMenuOpen = false;
            skillOverlay.style.display = "none";
        }

        function addDamageText(x, y, text, color) {
            damageTexts.push({ x, y, text, color, life: 30, opacity: 1 });
        }

        function createParticles(x, y, color, count = 15) {
            for (let i = 0; i < count; i++) {
                particles.push({
                    x: x,
                    y: y,
                    vx: (Math.random() - 0.5) * 12,
                    vy: (Math.random() - 0.5) * 12,
                    size: Math.random() * 5 + 2,
                    color: color,
                    life: 20 + Math.random() * 10
                });
            }
        }

        function update() {
            if (isSkillMenuOpen) return; // 메뉴 창 열리면 게임 일시정지

            // 1. 플레이어 이동 처리
            let moveX = 0, moveY = 0;
            if (keys["KeyW"] || keys["ArrowUp"]) moveY -= 1;
            if (keys["KeyS"] || keys["ArrowDown"]) moveY += 1;
            if (keys["KeyA"] || keys["ArrowLeft"]) moveX -= 1;
            if (keys["KeyD"] || keys["ArrowRight"]) moveX += 1;

            if (moveX !== 0 && moveY !== 0) {
                moveX *= 0.7071;
                moveY *= 0.7071;
            }

            player.x += moveX * player.speed;
            player.y += moveY * player.speed;

            // 묵직한 패링 관성 반동 물리 (Friction)
            player.x += player.vx;
            player.y += player.vy;
            player.vx *= 0.82;
            player.vy *= 0.82;

            // 맵 경계 제한
            player.x = Math.max(player.radius, Math.min(canvas.width - player.radius, player.x));
            player.y = Math.max(player.radius, Math.min(canvas.height - player.radius, player.y));

            // 패링 타이머 관리
            if (player.parryTimer > 0) {
                player.parryTimer--;
                if (player.parryTimer === 0) player.isParrying = false;
            }
            if (player.parryCooldown > 0) player.parryCooldown--;

            // 2. 적 AI 및 충돌 로직
            enemies.forEach((enemy, index) => {
                if (enemy.freezeTimer > 0) {
                    enemy.freezeTimer--;
                    return;
                }

                let dx = player.x - enemy.x;
                let dy = player.y - enemy.y;
                let dist = Math.hypot(dx, dy);

                enemy.stateTimer++;

                if (enemy.state === "chase") {
                    // 플레이어 추적
                    enemy.x += (dx / dist) * enemy.speed;
                    enemy.y += (dy / dist) * enemy.speed;

                    // 일정 거리 접근 시 공격 전조(Windup) 시작
                    if (dist < 45) {
                        enemy.state = "windup";
                        enemy.stateTimer = 0;
                    }
                } else if (enemy.state === "windup") {
                    // 0.5초 동안 주황색으로 준비
                    if (enemy.stateTimer > 25) {
                        enemy.state = "attack";
                        enemy.stateTimer = 0;
                    }
                } else if (enemy.state === "attack") {
                    // 공격 판정 순간
                    if (player.isParrying && dist < 65) {
                        // ★ 패링 성공 ★
                        screenShake = 18;
                        score += 200;

                        // 묵직한 밀림 연출: 공격한 적의 반대 방향으로 강하게 튕겨나감
                        let pushAngle = Math.atan2(dy, dx); // 적 -> 플레이어 방향
                        player.vx = Math.cos(pushAngle) * 26; 
                        player.vy = Math.sin(pushAngle) * 26;

                        // 이펙트 및 적 데미지
                        createParticles(player.x, player.y, "#00ffff", 25);
                        enemy.hp -= 40;
                        addDamageText(enemy.x, enemy.y - 15, "PARRY! -40", "#00ffff");
                        enemy.state = "stun";
                        enemy.stateTimer = 0;

                        // 스킬 메뉴 트리거
                        openSkillMenu();
                    } else if (enemy.stateTimer > 8) {
                        // 패링 실패 (피격)
                        if (dist < 45) {
                            player.hp = Math.max(0, player.hp - 15);
                            screenShake = 10;
                            addDamageText(player.x, player.y - 20, "-15 HP", "#ff0000");
                            // 피격 밀림
                            player.vx = (dx / dist) * 10;
                            player.vy = (dy / dist) * 10;
                        }
                        enemy.state = "stun";
                        enemy.stateTimer = 0;
                    }
                } else if (enemy.state === "stun") {
                    if (enemy.stateTimer > 40) {
                        enemy.state = "chase";
                        enemy.stateTimer = 0;
                    }
                }
            });

            // 적 사망 처리
            enemies = enemies.filter(e => {
                if (e.hp <= 0) {
                    createParticles(e.x, e.y, "#ff3366", 20);
                    score += 100;
                    return false;
                }
                return true;
            });

            // 화면 흔들림
            if (screenShake > 0) screenShake *= 0.85;

            // 파티클 업데이트
            particles.forEach((p, i) => {
                p.x += p.vx;
                p.y += p.vy;
                p.life--;
                if (p.life <= 0) particles.splice(i, 1);
            });

            // 데미지 텍스트 업데이트
            damageTexts.forEach((dt, i) => {
                dt.y -= 0.8;
                dt.life--;
                if (dt.life <= 0) damageTexts.splice(i, 1);
            });
        }

        function draw() {
            ctx.save();
            if (screenShake > 0.5) {
                ctx.translate((Math.random() - 0.5) * screenShake, (Math.random() - 0.5) * screenShake);
            }

            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // 격자 배경그리기
            ctx.strokeStyle = "#1f1f2e";
            ctx.lineWidth = 1;
            for (let x = 0; x < canvas.width; x += 40) {
                ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
            }
            for (let y = 0; y < canvas.height; y += 40) {
                ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
            }

            // 1. 적 그리기
            enemies.forEach(enemy => {
                ctx.beginPath();
                ctx.arc(enemy.x, enemy.y, enemy.radius, 0, Math.PI * 2);

                if (enemy.freezeTimer > 0) ctx.fillStyle = "#00e5ff"; // 빙결 상태
                else if (enemy.state === "chase") ctx.fillStyle = "#ff4444";
                else if (enemy.state === "windup") ctx.fillStyle = "#ffbb00"; // 경고
                else if (enemy.state === "attack") ctx.fillStyle = "#ff0055"; // 공격
                else ctx.fillStyle = "#555566"; // 스턴

                ctx.fill();
                ctx.strokeStyle = "#fff";
                ctx.lineWidth = 1.5;
                ctx.stroke();

                // 적 HP 바
                ctx.fillStyle = "rgba(0,0,0,0.5)";
                ctx.fillRect(enemy.x - 15, enemy.y - 25, 30, 4);
                ctx.fillStyle = "#ff3366";
                ctx.fillRect(enemy.x - 15, enemy.y - 25, Math.max(0, (enemy.hp / enemy.maxHp) * 30), 4);
            });

            // 2. 플레이어 그리기
            ctx.beginPath();
            ctx.arc(player.x, player.y, player.radius, 0, Math.PI * 2);
            ctx.fillStyle = player.isParrying ? "#00ffff" : "#3388ff";
            ctx.fill();
            ctx.strokeStyle = "#ffffff";
            ctx.lineWidth = 2;
            ctx.stroke();

            // 패링 쉴드 이펙트
            if (player.isParrying) {
                ctx.beginPath();
                ctx.arc(player.x, player.y, player.radius + 12, 0, Math.PI * 2);
                ctx.strokeStyle = "rgba(0, 255, 255, 0.8)";
                ctx.lineWidth = 4;
                ctx.stroke();
            }

            // 3. 파티클 그리기
            particles.forEach(p => {
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                ctx.fillStyle = p.color;
                ctx.fill();
            });

            // 4. 데미지 텍스트
            damageTexts.forEach(dt => {
                ctx.fillStyle = dt.color;
                ctx.font = "bold 15px sans-serif";
                ctx.fillText(dt.text, dt.x - 10, dt.y);
            });

            ctx.restore();

            // HUD
            // 플레이어 HP 바
            ctx.fillStyle = "rgba(255, 255, 255, 0.1)";
            ctx.fillRect(20, 20, 200, 16);
            ctx.fillStyle = "#00ff88";
            ctx.fillRect(20, 20, (player.hp / player.maxHp) * 200, 16);
            ctx.strokeStyle = "#fff";
            ctx.strokeRect(20, 20, 200, 16);

            ctx.fillStyle = "#ffffff";
            ctx.font = "bold 13px sans-serif";
            ctx.fillText(`HP: ${player.hp} / ${player.maxHp}`, 25, 33);
            ctx.fillText(`SCORE: ${score}`, 20, 55);
        }

        function gameLoop() {
            update();
            draw();
            requestAnimationFrame(gameLoop);
        }

        // 게임 시작
        spawnEnemy();
        spawnEnemy();
        gameLoop();
    </script>
</body>
</html>
"""

components.html(game_html, height=520)
