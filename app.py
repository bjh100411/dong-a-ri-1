import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Action Roguelite - Optimized", page_icon="⚔️", layout="centered")

st.title("⚔️ 광역 패링 액션 (랙 원인 완전 제거 및 적 공격 표시 추가)")
st.caption("WASD: 이동 | Spacebar: 패링 | Shift: 불공격 | 파란색 원거리 적 & 보스 공격 전조 표시 기능 추가")

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
            background-color: #0f0f15;
        }
        canvas {
            border: 2px solid #2a2a3a;
            border-radius: 12px;
            background-color: #161622;
            box-shadow: 0 10px 30px rgba(0,0,0,0.8);
            width: 800px;
            height: 500px;
        }
        
        #game-container:fullscreen canvas, #game-container:-webkit-full-screen canvas {
            width: 100vw;
            height: 100vh;
            object-fit: contain;
            border: none;
            border-radius: 0;
        }
        #game-container:fullscreen, #game-container:-webkit-full-screen {
            display: flex;
            align-items: center;
            justify-content: center;
        }

        #fullscreen-btn {
            position: absolute;
            top: 15px;
            right: 15px;
            background: rgba(0, 0, 0, 0.6);
            color: #fff;
            border: 1px solid #555;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 14px;
            cursor: pointer;
            z-index: 30;
            transition: 0.2s;
        }
        #fullscreen-btn:hover {
            background: rgba(255, 255, 255, 0.2);
            border-color: #fff;
        }

        .overlay-ui {
            display: none;
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.85);
            border-radius: 12px;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 10;
        }
        #game-container:fullscreen .overlay-ui, #game-container:-webkit-full-screen .overlay-ui {
            border-radius: 0;
        }

        #game-over-ui h1 {
            color: #ff3366;
            text-shadow: 0 0 20px #ff3366;
            margin-bottom: 10px;
            font-size: 50px;
        }
        #game-over-ui p {
            font-size: 24px;
            margin-bottom: 30px;
        }
        .action-btn {
            padding: 12px 30px;
            font-size: 20px;
            background: #222233;
            color: #fff;
            border: 2px solid #00ffff;
            border-radius: 8px;
            cursor: pointer;
            transition: 0.2s;
            box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
        }
        .action-btn:hover {
            background: #00ffff;
            color: #000;
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.8);
        }

        #upgrade-ui h2 {
            color: #ffaa00;
            text-shadow: 0 0 10px #ffaa00;
            margin-bottom: 20px;
            font-size: 28px;
        }
        .upgrade-cards {
            display: flex;
            gap: 20px;
        }
        .card {
            background: #222233;
            border: 2px solid #444466;
            border-radius: 10px;
            padding: 20px;
            width: 160px;
            text-align: center;
            cursor: pointer;
            transition: 0.2s;
        }
        .card:hover {
            background: #33334d;
            border-color: #00ffff;
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0, 255, 255, 0.4);
        }
        .card h3 {
            font-size: 18px;
            margin: 0 0 10px 0;
            color: #fff;
        }
        .card p {
            font-size: 13px;
            color: #aaa;
            margin: 0;
        }
    </style>
</head>
<body>
    <div id="game-container">
        <canvas id="gameCanvas" width="800" height="500"></canvas>
        <button id="fullscreen-btn">⛶ 전체화면</button>
        
        <div id="upgrade-ui" class="overlay-ui">
            <h2>보상 선택</h2>
            <div class="upgrade-cards" id="cards-container"></div>
        </div>

        <div id="game-over-ui" class="overlay-ui">
            <h1>GAME OVER</h1>
            <p>최종 점수: <span id="final-score" style="color:#00ffff; font-weight:bold;">0</span></p>
            <button class="action-btn" onclick="restartGame()">🔄 다시하기</button>
        </div>
    </div>

    <script>
        const canvas = document.getElementById("gameCanvas");
        const ctx = canvas.getContext("2d");
        const upgradeUI = document.getElementById("upgrade-ui");
        const gameOverUI = document.getElementById("game-over-ui");
        const cardsContainer = document.getElementById("cards-container");
        const container = document.getElementById("game-container");
        const fsBtn = document.getElementById("fullscreen-btn");

        fsBtn.addEventListener("click", () => {
            try {
                if (!document.fullscreenElement && !document.webkitFullscreenElement) {
                    if (container.requestFullscreen) {
                        container.requestFullscreen();
                    } else if (container.webkitRequestFullscreen) {
                        container.webkitRequestFullscreen();
                    }
                } else {
                    if (document.exitFullscreen) {
                        document.exitFullscreen();
                    } else if (document.webkitExitFullscreen) {
                        document.webkitExitFullscreen();
                    }
                }
            } catch(e) {
                alert("현재 환경에서 전체화면을 지원하지 않습니다.");
            }
        });

        document.addEventListener("fullscreenchange", updateFsButton);
        document.addEventListener("webkitfullscreenchange", updateFsButton);

        function updateFsButton() {
            if (document.fullscreenElement || document.webkitFullscreenElement) {
                fsBtn.innerText = "✖ 원래화면";
            } else {
                fsBtn.innerText = "⛶ 전체화면";
            }
        }

        let keys = {};
        window.addEventListener("keydown", (e) => {
            if (isPaused || isGameOver) return;
            keys[e.code] = true;
            if (e.code === "Space") {
                e.preventDefault();
                triggerParry();
            }
            if ((e.code === "ShiftLeft" || e.code === "ShiftRight") && fireCooldown <= 0) {
                triggerFireAttack();
            }
        });
        window.addEventListener("keyup", (e) => { keys[e.code] = false; });

        let player = {};
        let isPaused = false;
        let isGameOver = false;
        let enemies = [], projectiles = [], particles = [], damageTexts = [], effectRings = [], chests = [];
        let screenShake = 0, screenFlash = { timer: 0, color: "" }, score = 0;
        let stage = 1, stageKills = 0, nextBossTarget = 20, isBossAlive = false;
        let parryCombo = 0, comboTimer = 0, fireCooldown = 0, baseFireCooldown = 300; 

        function initGame() {
            player = {
                x: 400, y: 250,
                radius: 18, speed: 3.8, vx: 0, vy: 0,
                hp: 100, maxHp: 100,
                isParrying: false, parryTimer: 0, parryCooldown: 0,
                damageMult: 1.0,
                invincibleTimer: 0,
                criticalRate: 0.15,
                vampireRate: 0.0
            };
            isPaused = false;
            isGameOver = false;
            enemies = []; projectiles = []; particles = [];
            damageTexts = []; effectRings = []; chests = [];
            screenShake = 0; screenFlash = { timer: 0, color: "" };
            score = 0; stage = 1; stageKills = 0;
            nextBossTarget = 20; isBossAlive = false;
            parryCombo = 0; comboTimer = 0;
            fireCooldown = 0; baseFireCooldown = 300;
            keys = {};

            gameOverUI.style.display = "none";
            upgradeUI.style.display = "none";
        }

        function restartGame() {
            initGame();
            spawnEnemy();
        }

        const UPGRADES = [
            { id: "dmg", title: "⚔️ 공격력 증가", desc: "모든 피해량 25% 증가", action: () => { player.damageMult += 0.25; } },
            { id: "spd", title: "👟 속도 증가", desc: "이동 속도 15% 증가", action: () => { player.speed *= 1.15; } },
            { id: "hp", title: "❤️ 체력 강화", desc: "최대 체력 +50 및 회복", action: () => { player.maxHp += 50; player.hp = player.maxHp; } },
            { id: "cool", title: "⏳ 쿨타임 감소", desc: "Shift 불공격 쿨타임 20% 감소", action: () => { baseFireCooldown *= 0.8; } },
            { id: "crit", title: "🎯 치명타 강화", desc: "치명타 확률 +15%", action: () => { player.criticalRate += 0.15; } },
            { id: "vamp", title: "🩸 흡혈 본능", desc: "적 처치 시 체력 10 회복", action: () => { player.vampireRate += 10; } },
            { id: "heal", title: "🧪 즉시 회복", desc: "체력 50 회복", action: () => { player.hp = Math.min(player.maxHp, player.hp + 50); } }
        ];

        const SKILL_POOL = [
            {
                name: "⚡천둥 벼락",
                action: () => {
                    screenFlash = { timer: 10, color: "rgba(0, 255, 255, 0.3)" };
                    screenShake = 15;
                    enemies.forEach(e => {
                        let isCrit = Math.random() < player.criticalRate;
                        let dmg = 80 * player.damageMult * (isCrit ? 1.5 : 1.0);
                        e.hp -= dmg;
                        addDamageText(e.x, e.y - 20, (isCrit ? "CRIT! " : "") + Math.floor(dmg), isCrit ? "#ffff00" : "#00ffff", 25);
                    });
                }
            },
            {
                name: "💥폭발 쇼크웨이브",
                action: () => {
                    screenFlash = { timer: 10, color: "rgba(255, 85, 0, 0.3)" };
                    screenShake = 20;
                    effectRings.push({ x: player.x, y: player.y, radius: player.radius, maxRadius: 350, life: 20, maxLife: 20, color: "255, 85, 0" });
                    enemies.forEach(e => {
                        let dx = e.x - player.x; let dy = e.y - player.y; let dist = Math.hypot(dx, dy) || 1;
                        if (dist < 350) {
                            let isCrit = Math.random() < player.criticalRate;
                            let dmg = 100 * player.damageMult * (isCrit ? 1.5 : 1.0);
                            e.hp -= dmg;
                            if (e.type !== "boss") { e.x += (dx/dist)*100; e.y += (dy/dist)*100; e.state = "stun"; e.stateTimer = 0; }
                            addDamageText(e.x, e.y - 20, (isCrit ? "CRIT! " : "") + Math.floor(dmg), isCrit ? "#ffff00" : "#ff5500", 25);
                        }
                    });
                }
            }
        ];

        function spawnEnemy() {
            if (isPaused || isGameOver) return;
            let maxEnemies = 6 + (stage * 2); 
            if (enemies.length >= maxEnemies || isBossAlive) return;

            let x = Math.random() < 0.5 ? (Math.random() < 0.5 ? -20 : canvas.width + 20) : Math.random() * canvas.width;
            let y = Math.random() < 0.5 ? Math.random() * canvas.height : (Math.random() < 0.5 ? -20 : canvas.height + 20);

            let randType = Math.random();
            let isRanged = randType < 0.4; // 파란색 원거리 적
            let isTank = randType >= 0.4 && randType < 0.55;
            let hpMult = 1 + (stage - 1) * 0.3;
            
            enemies.push({
                x, y, 
                type: isTank ? "tank" : (isRanged ? "ranged" : "melee"), 
                radius: isTank ? 22 : (isRanged ? 14 : 16),
                hp: (isTank ? 180 : (isRanged ? 70 : 100)) * hpMult, 
                maxHp: (isTank ? 180 : (isRanged ? 70 : 100)) * hpMult,
                speed: isTank ? 0.9 : (isRanged ? 1.0 : (1.4 + stage * 0.05)),
                state: "chase", stateTimer: 0, freezeTimer: 0, burnTimer: 0
            });
        }
        setInterval(spawnEnemy, 1800);

        function spawnBoss() {
            isBossAlive = true;
            addDamageText(canvas.width/2, canvas.height/2, "⚠️ WARNING: BOSS INCOMING ⚠️", "#ff0000", 80);
            screenShake = 25;
            let hpMult = 1 + (stage - 1) * 0.5;
            enemies.push({
                x: canvas.width / 2, y: -50, type: "boss", radius: 35,
                hp: 1000 * hpMult, maxHp: 1000 * hpMult, speed: 1.3,
                state: "enter", stateTimer: 0, freezeTimer: 0, burnTimer: 0, patternIndex: 0
            });
        }

        function triggerParry() {
            if (player.parryCooldown <= 0) {
                player.isParrying = true; player.parryTimer = 16; player.parryCooldown = 30;
            }
        }

        function triggerFireAttack() {
            fireCooldown = baseFireCooldown; screenShake = 15;
            effectRings.push({ x: player.x, y: player.y, radius: player.radius, maxRadius: 250, life: 20, maxLife: 20, color: "255, 68, 0" });
            createParticles(player.x, player.y, "#ff4400", 10);
            
            let dmg = 50 * player.damageMult;
            enemies.forEach(e => {
                if (Math.hypot(e.x - player.x, e.y - player.y) < 250) {
                    e.hp -= dmg; e.burnTimer = 180;
                    addDamageText(e.x, e.y - 20, "FIRE!", "#ffaa00", 20);
                }
            });
            addDamageText(player.x, player.y - 45, "🔥파이어 스톰!🔥", "#ff4400", 40);
        }

        function executeParry(sourceX, sourceY, isBoss) {
            player.isParrying = false; player.parryTimer = 0; player.invincibleTimer = 40; 
            screenShake = isBoss ? 20 : 12;
            createParticles(player.x, player.y, "#00ffff", 10);
            addDamageText(player.x, player.y - 25, "PERFECT PARRY!", "#00ffff", 30);
            effectRings.push({ x: player.x, y: player.y, radius: player.radius, maxRadius: 150, life: 15, maxLife: 15, color: "0, 255, 255" });

            let parryRadius = 160;
            let pDmg = (isBoss ? 150 : 60) * player.damageMult;
            score += isBoss ? 1000 : 200;

            enemies.forEach(e => {
                let dist = Math.hypot(e.x - player.x, e.y - player.y);
                if (dist < parryRadius) {
                    e.hp -= pDmg;
                    if (e.type !== "boss") {
                        e.state = "stun"; e.stateTimer = 0;
                        let pushAngle = Math.atan2(e.y - player.y, e.x - player.x);
                        e.x += Math.cos(pushAngle) * 30; e.y += Math.sin(pushAngle) * 30;
                    }
                }
            });

            // 투사체 즉시 제거 (랙 방지)
            for (let i = projectiles.length - 1; i >= 0; i--) {
                let p = projectiles[i];
                if (Math.hypot(p.x - player.x, p.y - player.y) < parryRadius) {
                    projectiles.splice(i, 1);
                }
            }

            // 🦇 패링 성공 시 8% 확률로 흡혈 특수 공격
            if (Math.random() < 0.08) {
                player.hp = Math.min(player.maxHp, player.hp + 40);
                screenFlash = { timer: 15, color: "rgba(255, 0, 85, 0.3)" };
                effectRings.push({ x: player.x, y: player.y, radius: player.radius, maxRadius: 280, life: 20, maxLife: 20, color: "255, 0, 85" });
                enemies.forEach(e => {
                    if (Math.hypot(e.x - player.x, e.y - player.y) < 280) {
                        let vDmg = 120 * player.damageMult;
                        e.hp -= vDmg;
                        addDamageText(e.x, e.y - 20, "VAMPIRE!", "#ff0055", 30);
                    }
                });
                addDamageText(player.x, player.y - 50, "🦇 뱀파이어 블러드 특수기! (+40 HP) 🦇", "#ff0055", 50);
            }

            parryCombo++; comboTimer = 180;
            if (parryCombo >= 2) {
                let randomSkill = SKILL_POOL[Math.floor(Math.random() * SKILL_POOL.length)];
                randomSkill.action();
                addDamageText(player.x, player.y - 45, "⭐" + randomSkill.name + " 연계기!⭐", "#ffff00", 40);
                parryCombo = 0;
            }
        }

        function addDamageText(x, y, text, color, life=25) {
            if (damageTexts.length > 15) damageTexts.shift();
            damageTexts.push({ x, y, text: String(text), color, life: life });
        }

        function createParticles(x, y, color, count = 5) {
            if (particles.length > 40) return; // 파티클 최대 제한으로 렉 원인 차단
            for (let i = 0; i < count; i++) {
                particles.push({
                    x, y, vx: (Math.random() - 0.5) * 8, vy: (Math.random() - 0.5) * 8,
                    size: Math.random() * 3 + 2, color: color, life: 10 + Math.random() * 5
                });
            }
        }

        function openChest(chestIndex) {
            chests.splice(chestIndex, 1);
            isPaused = true; keys = {};
            
            let shuffled = [...UPGRADES].sort(() => 0.5 - Math.random());
            cardsContainer.innerHTML = "";
            shuffled.slice(0, 3).forEach(upg => {
                let card = document.createElement("div"); card.className = "card";
                card.innerHTML = `<h3>${upg.title}</h3><p>${upg.desc}</p>`;
                card.onclick = () => {
                    upg.action(); upgradeUI.style.display = "none"; isPaused = false;
                    addDamageText(player.x, player.y - 30, "✨능력치 상승!✨", "#ffff00");
                };
                cardsContainer.appendChild(card);
            });
            upgradeUI.style.display = "flex";
        }

        function update() {
            if (isPaused || isGameOver) return;

            if (player.hp <= 0 && !isGameOver) {
                player.hp = 0;
                isGameOver = true;
                document.getElementById("final-score").innerText = score;
                gameOverUI.style.display = "flex";
                return;
            }

            if (comboTimer > 0) { comboTimer--; if (comboTimer === 0) parryCombo = 0; }
            if (fireCooldown > 0) fireCooldown--;
            if (player.invincibleTimer > 0) player.invincibleTimer--;

            let moveX = 0, moveY = 0;
            if (keys["KeyW"]) moveY -= 1; if (keys["KeyS"]) moveY += 1;
            if (keys["KeyA"]) moveX -= 1; if (keys["KeyD"]) moveX += 1;
            if (moveX !== 0 && moveY !== 0) { moveX *= 0.7071; moveY *= 0.7071; }

            player.x += moveX * player.speed; player.y += moveY * player.speed;
            player.x = Math.max(player.radius, Math.min(canvas.width - player.radius, player.x));
            player.y = Math.max(player.radius, Math.min(canvas.height - player.radius, player.y));

            if (player.parryTimer > 0) { player.parryTimer--; if (player.parryTimer === 0) player.isParrying = false; }
            if (player.parryCooldown > 0) player.parryCooldown--;

            chests.forEach((chest, idx) => { if (Math.hypot(player.x - chest.x, player.y - chest.y) < player.radius + chest.radius) openChest(idx); });

            enemies.forEach((enemy) => {
                if (enemy.burnTimer > 0) {
                    enemy.burnTimer--;
                    if (enemy.burnTimer % 30 === 0) { enemy.hp -= 12 * player.damageMult; }
                }
                if (enemy.freezeTimer > 0) { enemy.freezeTimer--; return; }

                let dx = player.x - enemy.x; let dy = player.y - enemy.y; let dist = Math.hypot(dx, dy) || 1;
                enemy.stateTimer++;

                if (enemy.type === "melee" || enemy.type === "tank") {
                    let attackRange = enemy.type === "tank" ? 100 : 85;
                    if (enemy.state === "chase") {
                        enemy.x += (dx / dist) * enemy.speed; enemy.y += (dy / dist) * enemy.speed;
                        if (dist < attackRange) { enemy.state = "windup"; enemy.stateTimer = 0; }
                    } else if (enemy.state === "windup") {
                        if (enemy.stateTimer > 25) { enemy.state = "attack"; enemy.stateTimer = 0; }
                    } else if (enemy.state === "attack") {
                        if (player.isParrying && dist < attackRange + 30) { 
                            executeParry(enemy.x, enemy.y, false); 
                        } else if (enemy.stateTimer > 8) {
                            if (dist < attackRange + 15 && player.invincibleTimer <= 0) { 
                                let hitDmg = enemy.type === "tank" ? 22 : 12;
                                player.hp -= hitDmg; screenShake = 10;
                                addDamageText(player.x, player.y - 20, `-${hitDmg} HP`, "#ff0000");
                            }
                            enemy.state = "stun"; enemy.stateTimer = 0;
                        }
                    } else if (enemy.state === "stun") {
                        if (enemy.stateTimer > 35) { enemy.state = "chase"; enemy.stateTimer = 0; }
                    }
                } else if (enemy.type === "ranged") {
                    // 파란색 원거리 적 AI 및 공격 전조 표시
                    let idealDist = 200;
                    if (enemy.state === "chase") {
                        if (dist < idealDist - 20) { enemy.x -= (dx / dist) * enemy.speed; enemy.y -= (dy / dist) * enemy.speed; } 
                        else if (dist > idealDist + 20) { enemy.x += (dx / dist) * enemy.speed; enemy.y += (dy / dist) * enemy.speed; }
                        
                        // 공격 타이밍이 다가오면 '준비 상태(windup)'로 전환
                        if (enemy.stateTimer > 70) { enemy.state = "windup"; enemy.stateTimer = 0; }
                    } else if (enemy.state === "windup") {
                        // 멈춰 서서 에너지를 모으는 중 (이때 플레이어가 패링 준비를 해야 함)
                        if (enemy.stateTimer > 40) {
                            let projSpeed = 4.5;
                            projectiles.push({ x: enemy.x, y: enemy.y, type: "normal", vx: (dx / dist) * projSpeed, vy: (dy / dist) * projSpeed, radius: 7 });
                            enemy.state = "chase"; enemy.stateTimer = 0;
                        }
                    }
                } else if (enemy.type === "boss") {
                    if (enemy.state === "enter") {
                        enemy.y += 2; if (enemy.y > 100) { enemy.state = "chase"; enemy.stateTimer = 0; }
                    } else if (enemy.state === "chase") {
                        enemy.x += (dx / dist) * enemy.speed; enemy.y += (dy / dist) * enemy.speed;
                        if (enemy.stateTimer > 110) {
                            let patterns = ["spread_windup", "slam_windup"];
                            enemy.patternIndex = Math.floor(Math.random() * patterns.length);
                            enemy.state = patterns[enemy.patternIndex];
                            enemy.stateTimer = 0;
                        }
                    } else if (enemy.state === "spread_windup") {
                        if (enemy.stateTimer > 35) {
                            for(let i=0; i<8; i++) {
                                let angle = (Math.PI * 2 / 8) * i;
                                projectiles.push({ x: enemy.x, y: enemy.y, type: "boss_proj", vx: Math.cos(angle) * 4.5, vy: Math.sin(angle) * 4.5, radius: 8 });
                            }
                            enemy.state = "chase"; enemy.stateTimer = 0;
                        }
                    } else if (enemy.state === "slam_windup") {
                        if (enemy.stateTimer > 45) {
                            screenShake = 20;
                            if (dist < 150) { 
                                if (player.isParrying) {
                                    executeParry(enemy.x, enemy.y, true); 
                                } else if (player.invincibleTimer <= 0) { 
                                    player.hp -= 30;
                                    addDamageText(player.x, player.y - 20, "-30 HP", "#ff0000");
                                }
                            }
                            effectRings.push({ x: enemy.x, y: enemy.y, radius: enemy.radius, maxRadius: 150, life: 15, maxLife: 15, color: "255, 0, 85" });
                            enemy.state = "chase"; enemy.stateTimer = 0;
                        }
                    }
                }
            });

            for (let i = projectiles.length - 1; i >= 0; i--) {
                let p = projectiles[i];
                p.x += p.vx; p.y += p.vy;
                if (p.x < -20 || p.x > canvas.width + 20 || p.y < -20 || p.y > canvas.height + 20) { projectiles.splice(i, 1); continue; }
                
                let pDist = Math.hypot(player.x - p.x, player.y - p.y);
                if (pDist < player.radius + p.radius + 25) {
                    if (player.isParrying) {
                        executeParry(p.x, p.y, p.type === "boss_proj");
                    } else if (pDist < player.radius + p.radius && player.invincibleTimer <= 0) {
                        let dmg = p.type === "boss_proj" ? 20 : 10;
                        player.hp -= dmg;
                        screenShake = 6;
                        addDamageText(player.x, player.y - 20, `-${dmg} HP`, "#ff0055");
                        projectiles.splice(i, 1);
                    }
                }
            }

            let bossDiedThisFrame = false; let bossDeathPos = {x:0, y:0};
            enemies = enemies.filter(e => {
                if (e.hp <= 0) {
                    createParticles(e.x, e.y, "#ff3366", 8); 
                    score += (e.type === "boss" ? 2000 : 150);
                    if (player.vampireRate > 0) { player.hp = Math.min(player.maxHp, player.hp + player.vampireRate); }
                    if (e.type === "boss") { 
                        bossDiedThisFrame = true; 
                        bossDeathPos = {x: e.x, y: e.y}; 
                        isBossAlive = false; 
                    } else { 
                        stageKills++; 
                    }
                    return false;
                }
                return true;
            });

            if (bossDiedThisFrame) {
                stage++;
                chests.push({ x: bossDeathPos.x, y: bossDeathPos.y, radius: 20 });
                addDamageText(bossDeathPos.x, bossDeathPos.y - 30, "보물상자 등장!", "#ffff00");
                addDamageText(canvas.width/2, canvas.height/2, `STAGE ${stage} START!`, "#00ff88", 70);
                player.hp = Math.min(player.maxHp, player.hp + 40);
                stageKills = 0;
                nextBossTarget += 10;
            }

            if (!isBossAlive && stageKills >= nextBossTarget) { spawnBoss(); }

            if (screenShake > 0.5) screenShake *= 0.8;

            for (let i = particles.length - 1; i >= 0; i--) { let p = particles[i]; p.x += p.vx; p.y += p.vy; p.life--; if (p.life <= 0) particles.splice(i, 1); }
            for (let i = damageTexts.length - 1; i >= 0; i--) { let dt = damageTexts[i]; dt.y -= 0.6; dt.life--; if (dt.life <= 0) damageTexts.splice(i, 1); }
            for (let i = effectRings.length - 1; i >= 0; i--) { let r = effectRings[i]; r.radius += (r.maxRadius - r.radius) * 0.2; r.life--; if (r.life <= 0) effectRings.splice(i, 1); }
        }

        function draw() {
            ctx.save();
            if (screenShake > 0.5) ctx.translate((Math.random() - 0.5) * screenShake, (Math.random() - 0.5) * screenShake);
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            if (screenFlash.timer > 0) { ctx.fillStyle = screenFlash.color; ctx.fillRect(0, 0, canvas.width, canvas.height); screenFlash.timer--; }

            chests.forEach(chest => {
                ctx.fillStyle = "#ffcc00"; ctx.fillRect(chest.x - 15, chest.y - 10, 30, 20);
                ctx.beginPath(); ctx.arc(chest.x, chest.y, chest.radius + 5, 0, Math.PI*2);
                ctx.strokeStyle = "rgba(255, 204, 0, 0.5)"; ctx.lineWidth = 2; ctx.stroke();
            });

            effectRings.forEach(r => {
                ctx.beginPath(); ctx.arc(r.x, r.y, r.radius, 0, Math.PI * 2);
                ctx.strokeStyle = `rgba(${r.color}, ${r.life / r.maxLife})`; ctx.lineWidth = 6; ctx.stroke();
            });

            // 적 렌더링 및 공격 전조(공격 종류와 타이밍) 표시
            enemies.forEach(enemy => {
                ctx.beginPath(); ctx.arc(enemy.x, enemy.y, enemy.radius, 0, Math.PI * 2);
                
                if (enemy.type === "ranged") {
                    // 파란색 원거리 적
                    ctx.fillStyle = enemy.state === "windup" ? "#ffffff" : "#00bfff";
                } else if (enemy.type === "tank") {
                    ctx.fillStyle = "#3b82f6";
                } else if (enemy.type === "boss") {
                    ctx.fillStyle = enemy.state.includes("windup") ? "#ff0000" : "#880000";
                } else {
                    ctx.fillStyle = enemy.state === "windup" ? "#ffbb00" : "#ff4444";
                }
                ctx.fill();
                ctx.strokeStyle = "#ffffff"; ctx.lineWidth = 1.5; ctx.stroke();

                // 🔵 파란색 원거리 적 또는 보스가 공격을 준비할 때 머리 위에 경고 표시
                if (enemy.type === "ranged" && enemy.state === "windup") {
                    ctx.fillStyle = "#00ffff";
                    ctx.font = "bold 12px sans-serif";
                    ctx.textAlign = "center";
                    ctx.fillText("⚡ 레이저 장전!", enemy.x, enemy.y - enemy.radius - 12);
                    
                    // 사격 궤도 예고선 살짝 표시
                    ctx.strokeStyle = "rgba(0, 255, 255, 0.3)";
                    ctx.lineWidth = 1;
                    ctx.beginPath(); ctx.moveTo(enemy.x, enemy.y); ctx.lineTo(player.x, player.y); ctx.stroke();
                } else if (enemy.type === "boss" && enemy.state.includes("windup")) {
                    ctx.fillStyle = "#ff3300";
                    ctx.font = "bold 14px sans-serif";
                    ctx.textAlign = "center";
                    ctx.fillText(enemy.state === "spread_windup" ? "💥 탄막 폭격 준비!" : "⚡ 광역 내려찍기!", enemy.x, enemy.y - enemy.radius - 15);
                }

                let hpWidth = enemy.type === "boss" ? 60 : 30;
                ctx.fillStyle = "rgba(0,0,0,0.5)"; ctx.fillRect(enemy.x - hpWidth/2, enemy.y - enemy.radius - 6, hpWidth, 3);
                ctx.fillStyle = "#ff3366"; ctx.fillRect(enemy.x - hpWidth/2, enemy.y - enemy.radius - 6, Math.max(0, (enemy.hp / enemy.maxHp) * hpWidth), 3);
            });

            projectiles.forEach(p => {
                ctx.beginPath(); ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
                ctx.fillStyle = p.type === "boss_proj" ? "#ff4400" : "#00ffff";
                ctx.fill(); ctx.strokeStyle = "#ffffff"; ctx.lineWidth = 1.5; ctx.stroke();
            });

            ctx.beginPath(); ctx.arc(player.x, player.y, player.radius, 0, Math.PI * 2);
            ctx.fillStyle = player.isParrying ? "#00ffff" : "#3388ff";
            ctx.fill(); ctx.strokeStyle = "#ffffff"; ctx.lineWidth = 2; ctx.stroke();

            if (player.isParrying) {
                ctx.beginPath(); ctx.arc(player.x, player.y, player.radius + 15, 0, Math.PI * 2); 
                ctx.strokeStyle = "rgba(0, 255, 255, 0.8)"; ctx.lineWidth = 3; ctx.stroke();
            }

            particles.forEach(p => { ctx.beginPath(); ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2); ctx.fillStyle = p.color; ctx.fill(); });

            damageTexts.forEach(dt => {
                ctx.fillStyle = dt.color;
                ctx.font = "bold 14px sans-serif";
                ctx.textAlign = "center";
                ctx.fillText(dt.text, dt.x, dt.y);
            });

            ctx.restore();

            // UI 표시
            ctx.fillStyle = "rgba(255, 255, 255, 0.1)"; ctx.fillRect(20, 20, 200, 16);
            ctx.fillStyle = "#00ff88"; ctx.fillRect(20, 20, (Math.max(0, player.hp) / player.maxHp) * 200, 16);
            ctx.strokeStyle = "#fff"; ctx.strokeRect(20, 20, 200, 16);

            ctx.fillStyle = "#ffffff"; ctx.font = "bold 13px sans-serif";
            ctx.textAlign = "left";
            ctx.fillText(`HP: ${Math.max(0, Math.floor(player.hp))} / ${player.maxHp}`, 25, 33);
            ctx.fillText(`SCORE: ${score} | STAGE: ${stage}`, 20, 55);
            ctx.fillText(`BOSS KILLS TARGET | STAGE KILLS: ${stageKills} / ${nextBossTarget}`, 20, 75);
            
            let shiftReady = fireCooldown <= 0;
            ctx.fillStyle = shiftReady ? "#ff4400" : "#888888";
            ctx.fillText(`SHIFT (불공격) : ${shiftReady ? "READY!" : (fireCooldown/60).toFixed(1) + "s"}`, 20, 95);

            if (comboTimer > 0 && parryCombo > 0) {
                ctx.fillStyle = "#ffff00";
                ctx.fillText(`COMBO: ${parryCombo} 🔥`, 20, 115);
            }
        }

        function gameLoop() {
            update();
            draw();
            requestAnimationFrame(gameLoop);
        }

        initGame();
        spawnEnemy();
        gameLoop();
    </script>
</body>
</html>
"""

components.html(game_html, height=520)
