import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Parry & Skill Action", page_icon="⚔️", layout="centered")

st.title("⚔️ WASD & Shift 액션")
st.caption("WASD : 이동 | Spacebar : 패링 | Shift : 특수 상태 불공격(쿨타임 5초)")

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
    </style>
</head>
<body>
    <div id="game-container">
        <canvas id="gameCanvas" width="800" height="500"></canvas>
    </div>

    <script>
        const canvas = document.getElementById("gameCanvas");
        const ctx = canvas.getContext("2d");

        // 키 입력 관리 (한글 입력 상태에서도 작동하도록 e.code 사용)
        let keys = {};
        window.addEventListener("keydown", (e) => {
            keys[e.code] = true;
            
            // 스페이스바 스크롤 방지
            if (e.code === "Space") {
                e.preventDefault();
                triggerParry();
            }
            // Shift 불공격 (쿨타임이 없을 때 즉시 발동)
            if ((e.code === "ShiftLeft" || e.code === "ShiftRight") && fireCooldown <= 0) {
                triggerFireAttack();
            }
        });
        window.addEventListener("keyup", (e) => { keys[e.code] = false; });

        // 플레이어 객체
        let player = {
            x: 400,
            y: 250,
            radius: 18,
            speed: 3.8, // 이동속도 소폭 상향
            vx: 0,
            vy: 0,
            hp: 100,
            maxHp: 100,
            isParrying: false,
            parryTimer: 0,
            parryCooldown: 0
        };

        // 게임 상태 변수
        let enemies = [];
        let projectiles = [];
        let particles = [];
        let damageTexts = [];
        let fireRings = [];
        let screenShake = 0;
        let score = 0;
        
        let parryCombo = 0;
        let comboTimer = 0;
        let fireCooldown = 0; // Shift 쿨타임 관리

        // 자동 발동 스킬 풀
        const SKILL_POOL = [
            {
                name: "⚡천둥 벼락",
                action: () => {
                    enemies.forEach(e => {
                        e.hp -= 70;
                        addDamageText(e.x, e.y - 20, "70", "#00ffff");
                        createParticles(e.x, e.y, "#00ffff", 12);
                    });
                }
            },
            {
                name: "💥폭발 쇼크웨이브",
                action: () => {
                    screenShake = 15;
                    enemies.forEach(e => {
                        let dx = e.x - player.x;
                        let dy = e.y - player.y;
                        let dist = Math.hypot(dx, dy) || 1;
                        if (dist < 300) {
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
                name: "❄️빙결 파동",
                action: () => {
                    enemies.forEach(e => {
                        e.hp -= 40;
                        e.freezeTimer = 60;
                        addDamageText(e.x, e.y - 20, "40", "#88ffff");
                        createParticles(e.x, e.y, "#88ffff", 10);
                    });
                }
            }
        ];

        function spawnEnemy() {
            if (enemies.length >= 12) return;
            let x, y;
            if (Math.random() < 0.5) {
                x = Math.random() < 0.5 ? -20 : canvas.width + 20;
                y = Math.random() * canvas.height;
            } else {
                x = Math.random() * canvas.width;
                y = Math.random() < 0.5 ? -20 : canvas.height + 20;
            }

            let isRanged = Math.random() < 0.4;
            enemies.push({
                x: x,
                y: y,
                type: isRanged ? "ranged" : "melee",
                radius: isRanged ? 14 : 16,
                hp: isRanged ? 80 : 120,
                maxHp: isRanged ? 80 : 120,
                speed: isRanged ? 1.0 : 1.5,
                state: "chase",
                stateTimer: 0,
                freezeTimer: 0,
                burnTimer: 0
            });
        }
        setInterval(spawnEnemy, 2000);

        function triggerParry() {
            if (player.parryCooldown <= 0) {
                player.isParrying = true;
                player.parryTimer = 16;
                player.parryCooldown = 30;
            }
        }

        // Shift 불공격 로직
        function triggerFireAttack() {
            fireCooldown = 300; // 5초 쿨타임 (60프레임 * 5)
            screenShake = 18;
            fireRings.push({ x: player.x, y: player.y, radius: player.radius, maxRadius: 280, life: 25 });
            createParticles(player.x, player.y, "#ff4400", 50);
            
            enemies.forEach(e => {
                let dist = Math.hypot(e.x - player.x, e.y - player.y);
                if (dist < 280) {
                    e.hp -= 50; 
                    e.burnTimer = 240; // 4초 동안 도트 데미지
                    addDamageText(e.x, e.y - 20, "FIRE! -50", "#ffaa00");
                }
            });
            addDamageText(player.x, player.y - 45, "🔥파이어 스톰!🔥", "#ff4400");
        }

        function onParrySuccess() {
            parryCombo++;
            comboTimer = 90;

            // 패링 2회 성공마다 랜덤 스킬 자동 발동
            if (parryCombo % 2 === 0) {
                let randomSkill = SKILL_POOL[Math.floor(Math.random() * SKILL_POOL.length)];
                randomSkill.action();
                addDamageText(player.x, player.y - 35, randomSkill.name + " 연계기!", "#ffffff");
            }
        }

        function addDamageText(x, y, text, color) {
            damageTexts.push({ x, y, text, color, life: 40, opacity: 1 });
        }

        function createParticles(x, y, color, count = 15) {
            for (let i = 0; i < count; i++) {
                particles.push({
                    x: x, y: y,
                    vx: (Math.random() - 0.5) * 14,
                    vy: (Math.random() - 0.5) * 14,
                    size: Math.random() * 5 + 2,
                    color: color,
                    life: 20 + Math.random() * 15
                });
            }
        }

        function update() {
            if (comboTimer > 0) {
                comboTimer--;
                if (comboTimer === 0) parryCombo = 0;
            }
            if (fireCooldown > 0) fireCooldown--;

            // 1. 플레이어 이동 처리 (오직 WASD 만 적용)
            let moveX = 0, moveY = 0;
            if (keys["KeyW"]) moveY -= 1;
            if (keys["KeyS"]) moveY += 1;
            if (keys["KeyA"]) moveX -= 1;
            if (keys["KeyD"]) moveX += 1;

            if (moveX !== 0 && moveY !== 0) {
                moveX *= 0.7071;
                moveY *= 0.7071;
            }

            player.x += moveX * player.speed;
            player.y += moveY * player.speed;

            // 넉백 관성
            player.x += player.vx;
            player.y += player.vy;
            player.vx *= 0.82;
            player.vy *= 0.82;

            // 화면 밖으로 나가지 못하게 제한
            player.x = Math.max(player.radius, Math.min(canvas.width - player.radius, player.x));
            player.y = Math.max(player.radius, Math.min(canvas.height - player.radius, player.y));

            if (player.parryTimer > 0) {
                player.parryTimer--;
                if (player.parryTimer === 0) player.isParrying = false;
            }
            if (player.parryCooldown > 0) player.parryCooldown--;

            // 2. 적 행동 제어
            enemies.forEach((enemy) => {
                // 화상 도트 데미지
                if (enemy.burnTimer > 0) {
                    enemy.burnTimer--;
                    if (enemy.burnTimer % 30 === 0) {
                        enemy.hp -= 15;
                        addDamageText(enemy.x, enemy.y - 10, "-15 (Burn)", "#ff4400");
                        createParticles(enemy.x, enemy.y, "#ff4400", 4);
                    }
                }

                if (enemy.freezeTimer > 0) {
                    enemy.freezeTimer--;
                    return;
                }

                let dx = player.x - enemy.x;
                let dy = player.y - enemy.y;
                let dist = Math.hypot(dx, dy) || 1;

                enemy.stateTimer++;

                if (enemy.type === "melee") {
                    if (enemy.state === "chase") {
                        enemy.x += (dx / dist) * enemy.speed;
                        enemy.y += (dy / dist) * enemy.speed;
                        if (dist < 85) { 
                            enemy.state = "windup";
                            enemy.stateTimer = 0;
                        }
                    } else if (enemy.state === "windup") {
                        if (enemy.stateTimer > 25) {
                            enemy.state = "attack";
                            enemy.stateTimer = 0;
                        }
                    } else if (enemy.state === "attack") {
                        if (player.isParrying && dist < 120) { 
                            screenShake = 18;
                            score += 200;
                            let pushAngle = Math.atan2(dy, dx);
                            player.vx = Math.cos(pushAngle) * 26;
                            player.vy = Math.sin(pushAngle) * 26;

                            createParticles(player.x, player.y, "#00ffff", 25);
                            enemy.hp -= 40;
                            addDamageText(enemy.x, enemy.y - 15, "PARRY! -40", "#00ffff");
                            enemy.state = "stun";
                            enemy.stateTimer = 0;
                            onParrySuccess();
                        } else if (enemy.stateTimer > 8) {
                            if (dist < 90) { 
                                player.hp = Math.max(0, player.hp - 15);
                                screenShake = 10;
                                addDamageText(player.x, player.y - 20, "-15 HP", "#ff0000");
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
                } else if (enemy.type === "ranged") {
                    let idealDist = 220;
                    if (enemy.state === "chase") {
                        if (dist < idealDist - 30) {
                            enemy.x -= (dx / dist) * enemy.speed;
                            enemy.y -= (dy / dist) * enemy.speed;
                        } else if (dist > idealDist + 30) {
                            enemy.x += (dx / dist) * enemy.speed;
                            enemy.y += (dy / dist) * enemy.speed;
                        }

                        if (enemy.stateTimer > 70) { 
                            enemy.state = "windup";
                            enemy.stateTimer = 0;
                        }
                    } else if (enemy.state === "windup") {
                        if (enemy.stateTimer > 35) {
                            let projSpeed = 5.5;
                            projectiles.push({
                                x: enemy.x, y: enemy.y,
                                vx: (dx / dist) * projSpeed, vy: (dy / dist) * projSpeed,
                                radius: 7
                            });
                            enemy.state = "chase";
                            enemy.stateTimer = 0;
                        }
                    }
                }
            });

            // 3. 투사체 및 패링
            projectiles.forEach((p, pIdx) => {
                p.x += p.vx;
                p.y += p.vy;

                if (p.x < -20 || p.x > canvas.width + 20 || p.y < -20 || p.y > canvas.height + 20) {
                    projectiles.splice(pIdx, 1);
                    return;
                }

                let pdx = player.x - p.x;
                let pdy = player.y - p.y;
                let pDist = Math.hypot(pdx, pdy);

                if (pDist < player.radius + p.radius + 35) {
                    if (player.isParrying) {
                        screenShake = 16;
                        score += 150;
                        let pSpeed = Math.hypot(p.vx, p.vy) || 1;
                        player.vx = (p.vx / pSpeed) * 24;
                        player.vy = (p.vy / pSpeed) * 24;

                        createParticles(p.x, p.y, "#00ffff", 25);
                        addDamageText(player.x, player.y - 25, "RANGED PARRY!", "#00ffff");

                        projectiles.splice(pIdx, 1);
                        onParrySuccess();
                    } else if (pDist < player.radius + p.radius) {
                        player.hp = Math.max(0, player.hp - 12);
                        screenShake = 8;
                        addDamageText(player.x, player.y - 20, "-12 HP", "#ff0055");
                        createParticles(p.x, p.y, "#ff0055", 10);
                        player.vx = p.vx * 0.7;
                        player.vy = p.vy * 0.7;
                        projectiles.splice(pIdx, 1);
                    }
                }
            });

            enemies = enemies.filter(e => {
                if (e.hp <= 0) {
                    createParticles(e.x, e.y, "#ff3366", 20);
                    score += 120;
                    return false;
                }
                return true;
            });

            if (screenShake > 0) screenShake *= 0.85;

            particles.forEach((p, i) => {
                p.x += p.vx; p.y += p.vy; p.life--;
                if (p.life <= 0) particles.splice(i, 1);
            });
            damageTexts.forEach((dt, i) => {
                dt.y -= 0.8; dt.life--;
                if (dt.life <= 0) damageTexts.splice(i, 1);
            });
            fireRings.forEach((r, i) => {
                r.radius += (r.maxRadius - r.radius) * 0.2;
                r.life--;
                if (r.life <= 0) fireRings.splice(i, 1);
            });
        }

        function draw() {
            ctx.save();
            if (screenShake > 0.5) {
                ctx.translate((Math.random() - 0.5) * screenShake, (Math.random() - 0.5) * screenShake);
            }

            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // 격자 배경
            ctx.strokeStyle = "#1f1f2e";
            ctx.lineWidth = 1;
            for (let x = 0; x < canvas.width; x += 40) {
                ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
            }
            for (let y = 0; y < canvas.height; y += 40) {
                ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
            }

            // 불공격 고리 이펙트
            fireRings.forEach(r => {
                ctx.beginPath();
                ctx.arc(r.x, r.y, r.radius, 0, Math.PI * 2);
                ctx.strokeStyle = `rgba(255, 68, 0, ${r.life / 25})`;
                ctx.lineWidth = 10;
                ctx.stroke();
            });

            enemies.forEach(enemy => {
                ctx.beginPath();
                ctx.arc(enemy.x, enemy.y, enemy.radius, 0, Math.PI * 2);

                if (enemy.freezeTimer > 0) ctx.fillStyle = "#00e5ff"; 
                else if (enemy.burnTimer > 0 && Math.random() > 0.5) ctx.fillStyle = "#ff5500"; 
                else if (enemy.type === "melee") {
                    if (enemy.state === "chase") ctx.fillStyle = "#ff4444";
                    else if (enemy.state === "windup") ctx.fillStyle = "#ffbb00";
                    else if (enemy.state === "attack") ctx.fillStyle = "#ff0055";
                    else ctx.fillStyle = "#555566";
                } else if (enemy.type === "ranged") {
                    if (enemy.state === "chase") ctx.fillStyle = "#a855f7"; 
                    else if (enemy.state === "windup") ctx.fillStyle = "#ff9900"; 
                    else ctx.fillStyle = "#555566";
                }

                ctx.fill();
                ctx.strokeStyle = enemy.type === "ranged" ? "#e9d5ff" : "#ffffff";
                ctx.lineWidth = 1.5;
                ctx.stroke();

                ctx.fillStyle = "rgba(0,0,0,0.5)";
                ctx.fillRect(enemy.x - 15, enemy.y - 22, 30, 4);
                ctx.fillStyle = "#ff3366";
                ctx.fillRect(enemy.x - 15, enemy.y - 22, Math.max(0, (enemy.hp / enemy.maxHp) * 30), 4);
            });

            projectiles.forEach(p => {
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
                ctx.fillStyle = "#ff00cc";
                ctx.fill();
                ctx.strokeStyle = "#ffffff";
                ctx.lineWidth = 2;
                ctx.stroke();
            });

            // 플레이어 그리기
            ctx.beginPath();
            ctx.arc(player.x, player.y, player.radius, 0, Math.PI * 2);
            ctx.fillStyle = player.isParrying ? "#00ffff" : "#3388ff";
            ctx.fill();
            ctx.strokeStyle = "#ffffff"; 
            ctx.lineWidth = 2;
            ctx.stroke();

            if (player.isParrying) {
                ctx.beginPath();
                ctx.arc(player.x, player.y, player.radius + 18, 0, Math.PI * 2); 
                ctx.strokeStyle = "rgba(0, 255, 255, 0.8)";
                ctx.lineWidth = 4;
                ctx.stroke();
            }

            particles.forEach(p => {
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                ctx.fillStyle = p.color;
                ctx.fill();
            });

            damageTexts.forEach(dt => {
                ctx.fillStyle = dt.color;
                ctx.font = "bold 15px sans-serif";
                ctx.fillText(dt.text, dt.x - 10, dt.y);
            });

            ctx.restore();

            // HUD
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
            ctx.fillText(`COMBO: ${parryCombo}`, 20, 75);
            
            // Shift 불공격 쿨타임 표시
            let shiftReady = fireCooldown <= 0;
            ctx.fillStyle = shiftReady ? "#ff4400" : "#888888";
            ctx.fillText(`SHIFT (불공격) : ${shiftReady ? "READY!" : (fireCooldown/60).toFixed(1) + "s"}`, 20, 95);
        }

        function gameLoop() {
            update();
            draw();
            requestAnimationFrame(gameLoop);
        }

        spawnEnemy();
        spawnEnemy();
        gameLoop();
    </script>
</body>
</html>
"""

components.html(game_html, height=520)
