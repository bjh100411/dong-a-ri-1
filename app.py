import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Action Roguelite", page_icon="⚔️", layout="centered")

st.title("⚔️ 멀티 스테이지 & 보스 액션")
st.caption("WASD : 이동 | Spacebar : 패링 | Shift : 특수 불공격(쿨타임) | 보물상자 획득 시 패시브 선택")

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
        /* 레벨업/패시브 선택 UI */
        #upgrade-ui {
            display: none;
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.75);
            border-radius: 12px;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 10;
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
        
        <!-- 패시브 선택 창 -->
        <div id="upgrade-ui">
            <h2>보상 선택</h2>
            <div class="upgrade-cards" id="cards-container">
                <!-- 자바스크립트에서 카드 생성 -->
            </div>
        </div>
    </div>

    <script>
        const canvas = document.getElementById("gameCanvas");
        const ctx = canvas.getContext("2d");
        const upgradeUI = document.getElementById("upgrade-ui");
        const cardsContainer = document.getElementById("cards-container");

        let keys = {};
        window.addEventListener("keydown", (e) => {
            if (isPaused) return; // 일시정지 시 입력 무시
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

        // 플레이어 객체 (스탯 추가)
        let player = {
            x: 400, y: 250,
            radius: 18,
            speed: 3.8,
            vx: 0, vy: 0,
            hp: 100, maxHp: 100,
            isParrying: false,
            parryTimer: 0, parryCooldown: 0,
            damageMult: 1.0 // 공격력 배율
        };

        // 게임 상태 관리
        let isPaused = false;
        let enemies = [];
        let projectiles = [];
        let particles = [];
        let damageTexts = [];
        let fireRings = [];
        let chests = [];
        let screenShake = 0;
        let score = 0;
        
        // 스테이지 및 킬 카운트 시스템
        let stage = 1;
        let stageKills = 0;
        let nextBossTarget = 30; // 30, 60, 90마리마다 보스 등장
        let isBossAlive = false;

        let parryCombo = 0;
        let comboTimer = 0;
        let fireCooldown = 0;
        let baseFireCooldown = 300; // 쿨타임 감소 패시브를 위한 기본값

        // 패시브 옵션 풀
        const UPGRADES = [
            { id: "dmg", title: "⚔️ 공격력 증가", desc: "모든 피해량 25% 증가", action: () => { player.damageMult += 0.25; } },
            { id: "spd", title: "👟 속도 증가", desc: "이동 속도 15% 증가", action: () => { player.speed *= 1.15; } },
            { id: "hp", title: "❤️ 체력 강화", desc: "최대 체력 +50 및 100% 회복", action: () => { player.maxHp += 50; player.hp = player.maxHp; } },
            { id: "cool", title: "⏳ 쿨타임 감소", desc: "Shift 불공격 쿨타임 20% 감소", action: () => { baseFireCooldown *= 0.8; } },
            { id: "heal", title: "🧪 즉시 회복", desc: "체력 50 회복 (최대치 초과 불가)", action: () => { player.hp = Math.min(player.maxHp, player.hp + 50); } }
        ];

        // 자동 발동 스킬 풀 (빙결 시간 1초(60프레임)로 조정)
        const SKILL_POOL = [
            {
                name: "⚡천둥 벼락",
                action: () => {
                    enemies.forEach(e => {
                        let dmg = 70 * player.damageMult;
                        e.hp -= dmg;
                        addDamageText(e.x, e.y - 20, Math.floor(dmg), "#00ffff");
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
                            let dmg = 90 * player.damageMult;
                            e.hp -= dmg;
                            if (e.type !== "boss") {
                                e.x += (dx / dist) * 120;
                                e.y += (dy / dist) * 120;
                            }
                            addDamageText(e.x, e.y - 20, Math.floor(dmg), "#ff5500");
                            createParticles(e.x, e.y, "#ff5500", 15);
                        }
                    });
                }
            },
            {
                name: "❄️빙결 파동",
                action: () => {
                    enemies.forEach(e => {
                        let dmg = 40 * player.damageMult;
                        e.hp -= dmg;
                        if (e.type !== "boss") e.freezeTimer = 60; // 1초 빙결 적용
                        else e.freezeTimer = 20; // 보스는 빙결 저항
                        addDamageText(e.x, e.y - 20, Math.floor(dmg), "#88ffff");
                        createParticles(e.x, e.y, "#88ffff", 10);
                    });
                }
            }
        ];

        function spawnEnemy() {
            if (isPaused) return;
            // 스테이지가 오를수록 동시 스폰량 증가
            let maxEnemies = 10 + (stage * 2); 
            if (enemies.length >= maxEnemies || isBossAlive) return;

            let x, y;
            if (Math.random() < 0.5) {
                x = Math.random() < 0.5 ? -20 : canvas.width + 20;
                y = Math.random() * canvas.height;
            } else {
                x = Math.random() * canvas.width;
                y = Math.random() < 0.5 ? -20 : canvas.height + 20;
            }

            let isRanged = Math.random() < 0.4;
            // 스테이지 비례 체력 증가
            let hpMult = 1 + (stage - 1) * 0.4;
            
            enemies.push({
                x: x, y: y,
                type: isRanged ? "ranged" : "melee",
                radius: isRanged ? 14 : 16,
                hp: (isRanged ? 80 : 120) * hpMult,
                maxHp: (isRanged ? 80 : 120) * hpMult,
                speed: isRanged ? 1.1 : (1.5 + stage * 0.1),
                state: "chase", stateTimer: 0,
                freezeTimer: 0, burnTimer: 0
            });
        }
        setInterval(spawnEnemy, 1500);

        function spawnBoss() {
            isBossAlive = true;
            addDamageText(canvas.width/2, canvas.height/2, "⚠️ WARNING: BOSS INCOMING ⚠️", "#ff0000", 120);
            screenShake = 30;

            let hpMult = 1 + (stage - 1) * 0.8;
            enemies.push({
                x: canvas.width / 2, y: -50,
                type: "boss",
                radius: 35,
                hp: 1200 * hpMult,
                maxHp: 1200 * hpMult,
                speed: 1.6,
                state: "enter", stateTimer: 0,
                freezeTimer: 0, burnTimer: 0
            });
        }

        function triggerParry() {
            if (player.parryCooldown <= 0) {
                player.isParrying = true;
                player.parryTimer = 16;
                player.parryCooldown = 30;
            }
        }

        function triggerFireAttack() {
            fireCooldown = baseFireCooldown; 
            screenShake = 18;
            fireRings.push({ x: player.x, y: player.y, radius: player.radius, maxRadius: 280, life: 25 });
            createParticles(player.x, player.y, "#ff4400", 50);
            
            let dmg = 50 * player.damageMult;
            enemies.forEach(e => {
                let dist = Math.hypot(e.x - player.x, e.y - player.y);
                if (dist < 280) {
                    e.hp -= dmg; 
                    e.burnTimer = 240;
                    addDamageText(e.x, e.y - 20, "FIRE! " + Math.floor(-dmg), "#ffaa00");
                }
            });
            addDamageText(player.x, player.y - 45, "🔥파이어 스톰!🔥", "#ff4400");
        }

        function onParrySuccess() {
            parryCombo++;
            comboTimer = 90;

            if (parryCombo % 2 === 0) {
                let randomSkill = SKILL_POOL[Math.floor(Math.random() * SKILL_POOL.length)];
                randomSkill.action();
                addDamageText(player.x, player.y - 35, randomSkill.name + " 연계기!", "#ffffff");
            }
        }

        function addDamageText(x, y, text, color, life=40) {
            damageTexts.push({ x, y, text, color, life: life, opacity: 1 });
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

        // 보물상자 열기 (게임 멈춤 및 UI 표시)
        function openChest(chestIndex) {
            chests.splice(chestIndex, 1);
            isPaused = true;
            keys = {}; // 입력 초기화
            
            // 3가지 랜덤 패시브 선택
            let shuffled = [...UPGRADES].sort(() => 0.5 - Math.random());
            let selectedUpgrades = shuffled.slice(0, 3);
            
            cardsContainer.innerHTML = "";
            selectedUpgrades.forEach(upg => {
                let card = document.createElement("div");
                card.className = "card";
                card.innerHTML = `<h3>${upg.title}</h3><p>${upg.desc}</p>`;
                card.onclick = () => {
                    upg.action();
                    upgradeUI.style.display = "none";
                    isPaused = false;
                    addDamageText(player.x, player.y - 30, "✨능력치 상승!✨", "#ffff00");
                };
                cardsContainer.appendChild(card);
            });
            
            upgradeUI.style.display = "flex";
        }

        function update() {
            if (isPaused) return;

            if (comboTimer > 0) {
                comboTimer--;
                if (comboTimer === 0) parryCombo = 0;
            }
            if (fireCooldown > 0) fireCooldown--;

            // 1. 플레이어 이동
            let moveX = 0, moveY = 0;
            if (keys["KeyW"]) moveY -= 1;
            if (keys["KeyS"]) moveY += 1;
            if (keys["KeyA"]) moveX -= 1;
            if (keys["KeyD"]) moveX += 1;

            if (moveX !== 0 && moveY !== 0) {
                moveX *= 0.7071; moveY *= 0.7071;
            }

            player.x += moveX * player.speed;
            player.y += moveY * player.speed;

            player.x += player.vx; player.y += player.vy;
            player.vx *= 0.82; player.vy *= 0.82;

            player.x = Math.max(player.radius, Math.min(canvas.width - player.radius, player.x));
            player.y = Math.max(player.radius, Math.min(canvas.height - player.radius, player.y));

            if (player.parryTimer > 0) {
                player.parryTimer--;
                if (player.parryTimer === 0) player.isParrying = false;
            }
            if (player.parryCooldown > 0) player.parryCooldown--;

            // 상자 충돌 확인
            chests.forEach((chest, idx) => {
                if (Math.hypot(player.x - chest.x, player.y - chest.y) < player.radius + chest.radius) {
                    openChest(idx);
                }
            });

            // 2. 적 행동 제어
            enemies.forEach((enemy) => {
                if (enemy.burnTimer > 0) {
                    enemy.burnTimer--;
                    if (enemy.burnTimer % 30 === 0) {
                        let bDmg = 15 * player.damageMult;
                        enemy.hp -= bDmg;
                        addDamageText(enemy.x, enemy.y - 10, Math.floor(-bDmg), "#ff4400");
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
                        if (dist < 85) { enemy.state = "windup"; enemy.stateTimer = 0; }
                    } else if (enemy.state === "windup") {
                        if (enemy.stateTimer > 25) { enemy.state = "attack"; enemy.stateTimer = 0; }
                    } else if (enemy.state === "attack") {
                        if (player.isParrying && dist < 120) { 
                            screenShake = 18; score += 200;
                            let pushAngle = Math.atan2(dy, dx);
                            player.vx = Math.cos(pushAngle) * 26; player.vy = Math.sin(pushAngle) * 26;
                            createParticles(player.x, player.y, "#00ffff", 25);
                            let pDmg = 40 * player.damageMult;
                            enemy.hp -= pDmg;
                            addDamageText(enemy.x, enemy.y - 15, "PARRY! " + Math.floor(-pDmg), "#00ffff");
                            enemy.state = "stun"; enemy.stateTimer = 0;
                            onParrySuccess();
                        } else if (enemy.stateTimer > 8) {
                            if (dist < 90) { 
                                player.hp = Math.max(0, player.hp - 15); screenShake = 10;
                                addDamageText(player.x, player.y - 20, "-15 HP", "#ff0000");
                                player.vx = (dx / dist) * 10; player.vy = (dy / dist) * 10;
                            }
                            enemy.state = "stun"; enemy.stateTimer = 0;
                        }
                    } else if (enemy.state === "stun") {
                        if (enemy.stateTimer > 40) { enemy.state = "chase"; enemy.stateTimer = 0; }
                    }
                } else if (enemy.type === "ranged") {
                    let idealDist = 220;
                    if (enemy.state === "chase") {
                        if (dist < idealDist - 30) {
                            enemy.x -= (dx / dist) * enemy.speed; enemy.y -= (dy / dist) * enemy.speed;
                        } else if (dist > idealDist + 30) {
                            enemy.x += (dx / dist) * enemy.speed; enemy.y += (dy / dist) * enemy.speed;
                        }
                        if (enemy.stateTimer > 70) { enemy.state = "windup"; enemy.stateTimer = 0; }
                    } else if (enemy.state === "windup") {
                        if (enemy.stateTimer > 35) {
                            let projSpeed = 5.5;
                            projectiles.push({
                                x: enemy.x, y: enemy.y, type: "normal",
                                vx: (dx / dist) * projSpeed, vy: (dy / dist) * projSpeed, radius: 7
                            });
                            enemy.state = "chase"; enemy.stateTimer = 0;
                        }
                    }
                } else if (enemy.type === "boss") {
                    // 보스 패턴
                    if (enemy.state === "enter") {
                        enemy.y += 2;
                        if (enemy.y > 100) { enemy.state = "chase"; enemy.stateTimer = 0; }
                    } else if (enemy.state === "chase") {
                        enemy.x += (dx / dist) * enemy.speed;
                        enemy.y += (dy / dist) * enemy.speed;
                        
                        if (enemy.stateTimer > 150) {
                            enemy.state = Math.random() < 0.5 ? "spread_windup" : "slam_windup";
                            enemy.stateTimer = 0;
                        }
                    } else if (enemy.state === "spread_windup") {
                        if (enemy.stateTimer > 40) {
                            // 원형 탄막
                            for(let i=0; i<12; i++) {
                                let angle = (Math.PI * 2 / 12) * i;
                                projectiles.push({
                                    x: enemy.x, y: enemy.y, type: "boss_proj",
                                    vx: Math.cos(angle) * 5, vy: Math.sin(angle) * 5, radius: 9
                                });
                            }
                            enemy.state = "chase"; enemy.stateTimer = 0;
                        }
                    } else if (enemy.state === "slam_windup") {
                        if (enemy.stateTimer > 60) {
                            screenShake = 25;
                            if (dist < 150) { // 광역 데미지
                                if (player.isParrying) {
                                    score += 1000;
                                    let pDmg = 150 * player.damageMult;
                                    enemy.hp -= pDmg;
                                    addDamageText(enemy.x, enemy.y - 20, "BOSS PARRY! " + Math.floor(-pDmg), "#00ffff");
                                    onParrySuccess();
                                } else {
                                    player.hp = Math.max(0, player.hp - 35);
                                    addDamageText(player.x, player.y - 20, "-35 HP", "#ff0000");
                                }
                            }
                            createParticles(enemy.x, enemy.y, "#ff0055", 40);
                            fireRings.push({ x: enemy.x, y: enemy.y, radius: enemy.radius, maxRadius: 150, life: 15 });
                            enemy.state = "chase"; enemy.stateTimer = 0;
                        }
                    }
                }
            });

            // 3. 투사체
            projectiles.forEach((p, pIdx) => {
                p.x += p.vx; p.y += p.vy;
                if (p.x < -20 || p.x > canvas.width + 20 || p.y < -20 || p.y > canvas.height + 20) {
                    projectiles.splice(pIdx, 1); return;
                }
                let pDist = Math.hypot(player.x - p.x, player.y - p.y);
                if (pDist < player.radius + p.radius + 35) {
                    if (player.isParrying) {
                        screenShake = 16; score += 150;
                        createParticles(p.x, p.y, "#00ffff", 25);
                        addDamageText(player.x, player.y - 25, "PARRY!", "#00ffff");
                        projectiles.splice(pIdx, 1);
                        onParrySuccess();
                    } else if (pDist < player.radius + p.radius) {
                        let dmg = p.type === "boss_proj" ? 20 : 12;
                        player.hp = Math.max(0, player.hp - dmg);
                        screenShake = 8;
                        addDamageText(player.x, player.y - 20, `-${dmg} HP`, "#ff0055");
                        createParticles(p.x, p.y, "#ff0055", 10);
                        projectiles.splice(pIdx, 1);
                    }
                }
            });

            // 적 사망 처리 (스테이지 로직 포함)
            let bossDiedThisFrame = false;
            let bossDeathPos = {x:0, y:0};

            enemies = enemies.filter(e => {
                if (e.hp <= 0) {
                    createParticles(e.x, e.y, "#ff3366", 20);
                    score += (e.type === "boss" ? 2000 : 120);
                    
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

            // 보스 처치 시 보물상자 드랍
            if (bossDiedThisFrame) {
                chests.push({ x: bossDeathPos.x, y: bossDeathPos.y, radius: 20 });
                addDamageText(bossDeathPos.x, bossDeathPos.y - 30, "보물상자 등장!", "#ffff00");
            }

            // 보스 스폰 조건 체크
            if (!isBossAlive && stageKills >= nextBossTarget) {
                nextBossTarget += 30; // 다음 보스 목표 갱신
                spawnBoss();
            }

            // 100마리 처치 시 다음 스테이지 진행
            if (stageKills >= 100) {
                stage++;
                stageKills = 0;
                nextBossTarget = 30;
                addDamageText(canvas.width/2, canvas.height/2, `STAGE ${stage} START!`, "#00ff88", 100);
                player.hp = Math.min(player.maxHp, player.hp + 30); // 스테이지 클리어 보너스 힐
            }

            if (screenShake > 0) screenShake *= 0.85;

            particles.forEach((p, i) => { p.x += p.vx; p.y += p.vy; p.life--; if (p.life <= 0) particles.splice(i, 1); });
            damageTexts.forEach((dt, i) => { dt.y -= 0.8; dt.life--; if (dt.life <= 0) damageTexts.splice(i, 1); });
            fireRings.forEach((r, i) => { r.radius += (r.maxRadius - r.radius) * 0.2; r.life--; if (r.life <= 0) fireRings.splice(i, 1); });
        }

        function draw() {
            ctx.save();
            if (screenShake > 0.5) ctx.translate((Math.random() - 0.5) * screenShake, (Math.random() - 0.5) * screenShake);
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // 격자 배경
            ctx.strokeStyle = "#1f1f2e"; ctx.lineWidth = 1;
            for (let x = 0; x < canvas.width; x += 40) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke(); }
            for (let y = 0; y < canvas.height; y += 40) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke(); }

            // 보물상자 그리기
            chests.forEach(chest => {
                ctx.fillStyle = "#ffcc00";
                ctx.fillRect(chest.x - 15, chest.y - 10, 30, 20);
                ctx.fillStyle = "#aa7700";
                ctx.fillRect(chest.x - 15, chest.y - 2, 30, 4);
                ctx.beginPath();
                ctx.arc(chest.x, chest.y - 10, 15, Math.PI, 0);
                ctx.fill();
                // 빛나는 효과
                ctx.beginPath();
                ctx.arc(chest.x, chest.y, chest.radius + 5 + Math.sin(Date.now()/100)*5, 0, Math.PI*2);
                ctx.strokeStyle = "rgba(255, 204, 0, 0.5)"; ctx.lineWidth = 3; ctx.stroke();
            });

            fireRings.forEach(r => {
                ctx.beginPath(); ctx.arc(r.x, r.y, r.radius, 0, Math.PI * 2);
                ctx.strokeStyle = `rgba(255, 68, 0, ${r.life / 25})`; ctx.lineWidth = 10; ctx.stroke();
            });

            enemies.forEach(enemy => {
                ctx.beginPath(); ctx.arc(enemy.x, enemy.y, enemy.radius, 0, Math.PI * 2);
                if (enemy.freezeTimer > 0) ctx.fillStyle = "#00e5ff"; 
                else if (enemy.burnTimer > 0 && Math.random() > 0.5) ctx.fillStyle = "#ff5500"; 
                else if (enemy.type === "boss") {
                    ctx.fillStyle = enemy.state === "slam_windup" ? "#ff0000" : "#880000";
                }
                else if (enemy.type === "melee") {
                    if (enemy.state === "chase") ctx.fillStyle = "#ff4444";
                    else if (enemy.state === "windup") ctx.fillStyle = "#ffbb00";
                    else if (enemy.state === "attack") ctx.fillStyle = "#ff0055";
                    else ctx.fillStyle = "#555566";
                } else {
                    if (enemy.state === "chase") ctx.fillStyle = "#a855f7"; 
                    else if (enemy.state === "windup") ctx.fillStyle = "#ff9900"; 
                    else ctx.fillStyle = "#555566";
                }
                ctx.fill();
                ctx.strokeStyle = enemy.type === "boss" ? "#ffaa00" : (enemy.type === "ranged" ? "#e9d5ff" : "#ffffff");
                ctx.lineWidth = enemy.type === "boss" ? 3 : 1.5; ctx.stroke();

                // HP 바
                let hpWidth = enemy.type === "boss" ? 60 : 30;
                ctx.fillStyle = "rgba(0,0,0,0.5)";
                ctx.fillRect(enemy.x - hpWidth/2, enemy.y - enemy.radius - 8, hpWidth, 4);
                ctx.fillStyle = "#ff3366";
                ctx.fillRect(enemy.x - hpWidth/2, enemy.y - enemy.radius - 8, Math.max(0, (enemy.hp / enemy.maxHp) * hpWidth), 4);
            });

            projectiles.forEach(p => {
                ctx.beginPath(); ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
                ctx.fillStyle = p.type === "boss_proj" ? "#ff4400" : "#ff00cc";
                ctx.fill(); ctx.strokeStyle = "#ffffff"; ctx.lineWidth = 2; ctx.stroke();
            });

            // 플레이어
            ctx.beginPath(); ctx.arc(player.x, player.y, player.radius, 0, Math.PI * 2);
            ctx.fillStyle = player.isParrying ? "#00ffff" : "#3388ff";
            ctx.fill(); ctx.strokeStyle = "#ffffff"; ctx.lineWidth = 2; ctx.stroke();

            if (player.isParrying) {
                ctx.beginPath(); ctx.arc(player.x, player.y, player.radius + 18, 0, Math.PI * 2); 
                ctx.strokeStyle = "rgba(0, 255, 255, 0.8)"; ctx.lineWidth = 4; ctx.stroke();
            }

            particles.forEach(p => {
                ctx.beginPath(); ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                ctx.fillStyle = p.color; ctx.fill();
            });

            damageTexts.forEach(dt => {
                ctx.fillStyle = dt.color;
                ctx.font = dt.text.includes("STAGE") || dt.text.includes("BOSS") ? "bold 24px sans-serif" : "bold 15px sans-serif";
                ctx.textAlign = "center";
                ctx.globalAlpha = Math.min(1, dt.life / 20);
                ctx.fillText(dt.text, dt.x, dt.y);
                ctx.globalAlpha = 1;
                ctx.textAlign = "left";
            });

            ctx.restore();

            // HUD
            ctx.fillStyle = "rgba(255, 255, 255, 0.1)"; ctx.fillRect(20, 20, 200, 16);
            ctx.fillStyle = "#00ff88"; ctx.fillRect(20, 20, (player.hp / player.maxHp) * 200, 16);
            ctx.strokeStyle = "#fff"; ctx.strokeRect(20, 20, 200, 16);

            ctx.fillStyle = "#ffffff"; ctx.font = "bold 13px sans-serif";
            ctx.fillText(`HP: ${Math.floor(player.hp)} / ${player.maxHp}`, 25, 33);
            ctx.fillText(`SCORE: ${score} | STAGE: ${stage}`, 20, 55);
            
            // 프로그레스 바 (스테이지 진행도)
            ctx.fillText(`KILLS: ${stageKills} / 100`, 20, 75);
            ctx.fillStyle = "rgba(255, 255, 255, 0.2)"; ctx.fillRect(130, 65, 90, 10);
            ctx.fillStyle = "#a855f7"; ctx.fillRect(130, 65, (stageKills / 100) * 90, 10);
            
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
        gameLoop();
    </script>
</body>
</html>
"""

components.html(game_html, height=520)
