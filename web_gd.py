import http.server
import json
import os
import socket
import socketserver

PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LEVELS_FILE = os.path.join(BASE_DIR, "levels.json")


def get_default_levels():
    return {
        "Стартовый уровень": {
            "8,10": "spike",
            "13,10": "block", "14,10": "block", "14,9": "spike",
            "18,10": "portal_ship",
            "23,10": "spike", "24,10": "spike", "25,10": "spike",
            "24,2": "block", "24,3": "block",
            "29,10": "portal_cube",
            "34,10": "spike",
            "39,10": "goal",
        }
    }


def load_levels():
    if os.path.exists(LEVELS_FILE):
        try:
            with open(LEVELS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and data:
                    return data
        except Exception:
            pass
    data = get_default_levels()
    save_levels(data)
    return data


def save_levels(data):
    with open(LEVELS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


HTML_PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Cube Dash Mobile</title>
<style>
  * { box-sizing: border-box; user-select: none; -webkit-user-select: none; touch-action: none; }
  body { margin: 0; background: #161626; color: #fff; font-family: sans-serif; overflow: hidden; display: flex; flex-direction: column; height: 100vh; }
  #menuScreen { display: flex; flex-direction: column; align-items: center; padding: 15px; height: 100%; overflow-y: auto; touch-action: pan-y; }
  h1 { color: #00ffcc; margin: 10px 0 5px; font-size: 26px; text-align: center; }
  .sub { color: #a0a0c0; font-size: 13px; margin-bottom: 15px; text-align: center; }
  .btn-create { background: #00b894; color: #12121a; border: none; padding: 12px 22px; font-size: 16px; font-weight: bold; border-radius: 8px; margin-bottom: 15px; }
  #levelList { width: 100%; max-width: 600px; display: flex; flex-direction: column; gap: 8px; }
  .lvl-row { background: #2b2b40; padding: 10px 12px; border-radius: 8px; display: flex; align-items: center; justify-content: space-between; gap: 6px; }
  .lvl-name { font-weight: bold; font-size: 15px; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .btn-sm { border: none; padding: 8px 10px; border-radius: 6px; font-weight: bold; font-size: 12px; color: #fff; }
  .b-play { background: #00b894; color: #12121a; }
  .b-edit { background: #0984e3; }
  .b-del { background: #d63031; }
  #gameScreen { display: none; flex-direction: column; height: 100%; }
  #toolbar { background: #1e1e2e; padding: 6px; display: flex; flex-wrap: wrap; gap: 4px; align-items: center; justify-content: space-between; }
  .t-group { display: flex; flex-wrap: wrap; gap: 4px; }
  .t-btn { background: #2b2b40; color: #fff; border: 1px solid #3f3f5f; padding: 6px 8px; border-radius: 5px; font-size: 12px; font-weight: bold; }
  .t-btn.active { background: #1d4d4f; border-color: #00ffcc; color: #00ffcc; }
  #canvasWrap { position: relative; flex: 1; width: 100%; overflow: hidden; }
  canvas { display: block; width: 100%; height: 100%; background: #161626; }
  #camPad { position: absolute; bottom: 12px; right: 12px; display: grid; grid-template-columns: repeat(3, 42px); grid-template-rows: repeat(2, 42px); gap: 4px; }
  .cam-btn { background: rgba(30, 30, 46, 0.85); color: #00ffcc; border: 1px solid #00ffcc; border-radius: 8px; font-size: 18px; font-weight: bold; display: flex; align-items: center; justify-content: center; }
</style>
</head>
<body>
<div id="menuScreen">
  <h1>CUBE DASH MAKER</h1>
  <div class="sub">Мобильная версия (общие уровни с ПК)</div>
  <button class="btn-create" onclick="createNew()">+ СОЗДАТЬ УРОВЕНЬ</button>
  <div id="levelList">Загрузка уровней...</div>
</div>

<div id="gameScreen">
  <div id="toolbar">
    <div class="t-group" id="editTools">
      <button class="t-btn active" id="t_move" onclick="setTool('move')">Двигать</button>
      <button class="t-btn" id="t_block" onclick="setTool('block')">Блок</button>
      <button class="t-btn" id="t_spike" onclick="setTool('spike')">Шип</button>
      <button class="t-btn" id="t_portal_ship" onclick="setTool('portal_ship')">Самолёт</button>
      <button class="t-btn" id="t_portal_cube" onclick="setTool('portal_cube')">Куб</button>
      <button class="t-btn" id="t_goal" onclick="setTool('goal')">Финиш</button>
      <button class="t-btn" id="t_erase" onclick="setTool('erase')">Ластик</button>
      <button class="t-btn" style="background:#6c5ce7" onclick="publishLevel()">Выложить</button>
    </div>
    <div class="t-group">
      <button class="t-btn" id="playToggleBtn" style="background:#00b894;color:#12121a" onclick="toggleMode()">ИГРАТЬ</button>
      <button class="t-btn" style="background:#d63031" onclick="openMenu()">Меню</button>
    </div>
  </div>
  <div id="canvasWrap">
    <canvas id="cv"></canvas>
    <button id="jumpBtn" style="display:none;position:absolute;bottom:18px;right:18px;width:130px;height:75px;background:rgba(0,255,204,0.25);border:3px solid #00ffcc;border-radius:16px;color:#00ffcc;font-size:18px;font-weight:bold;" onpointerdown="if(!actionPressed)jumpJustPressed=true;actionPressed=true;if(won)resetPlayer();" onpointerup="actionPressed=false;" onpointerleave="actionPressed=false;">ПРЫЖОК</button>
    <div id="camPad">
      <div></div><div class="cam-btn" onpointerdown="camMove(0,-1)" onpointerup="camStop()">▲</div><div></div>
      <div class="cam-btn" onpointerdown="camMove(-1,0)" onpointerup="camStop()">◄</div>
      <div class="cam-btn" onpointerdown="camMove(0,1)" onpointerup="camStop()">▼</div>
      <div class="cam-btn" onpointerdown="camMove(1,0)" onpointerup="camStop()">►</div>
    </div>
  </div>
</div>
<script>
const GRID = 40;
const GRAVITY = 0.85, JUMP_FORCE = -13.5, SPEED = 6.5;
const SHIP_THRUST = -0.75, SHIP_GRAVITY = 0.65, SHIP_MAX_VY = 7.5;
const MAX_SKY_Y = -1200;

let savedLevels = {};
let currentName = "Новый уровень";
let level = new Map();
let screenState = "menu";
let tool = "move";
let camX = 0, camY = 0, camVX = 0, camVY = 0;
let actionPressed = false, won = false, deadTimer = 0;
let dragObj = null, dragOrigin = null, dragPos = {x:0, y:0};

const cv = document.getElementById("cv");
const ctx = cv.getContext("2d");
let W = 900, H = 440, FLOOR_Y = 400;

function resizeCanvas() {
  const wrap = document.getElementById("canvasWrap");
  W = cv.width = wrap.clientWidth || window.innerWidth;
  H = cv.height = wrap.clientHeight || (window.innerHeight - 50);
  FLOOR_Y = Math.floor((H - 20) / GRID) * GRID;
  if (FLOOR_Y < 200) FLOOR_Y = H - 30;
}
window.addEventListener("resize", resizeCanvas);

const player = { x: 80, y: 0, vy: 0, grounded: true, dead: false, mode: "cube" };

async function fetchLevels() {
  const res = await fetch("/api/levels");
  savedLevels = await res.json();
  renderMenu();
}

function renderMenu() {
  const list = document.getElementById("levelList");
  list.innerHTML = "";
  for (const name of Object.keys(savedLevels)) {
    const row = document.createElement("div");
    row.className = "lvl-row";
    const delBtn = name !== "Стартовый уровень"
      ? `<button class="btn-sm b-del" onclick="delLevel('${name.replace(/'/g, "\\'")}')">X</button>` : "";
    row.innerHTML = `
      <div class="lvl-name">${name}</div>
      <button class="btn-sm b-play" onclick="startLevel('${name.replace(/'/g, "\\'")}', 'play')">ИГРАТЬ</button>
      <button class="btn-sm b-edit" onclick="startLevel('${name.replace(/'/g, "\\'")}', 'edit')">Ред.</button>
      ${delBtn}
    `;
    list.appendChild(row);
  }
}

function openMenu() {
  screenState = "menu";
  document.getElementById("gameScreen").style.display = "none";
  document.getElementById("menuScreen").style.display = "flex";
  fetchLevels();
}

function createNew() {
  currentName = "Новый уровень";
  level.clear();
  openGame("edit");
  const gyGoal = Math.floor(FLOOR_Y / GRID) - 1;
  level.set(`20,${gyGoal}`, "goal");
}

function startLevel(name, mode) {
  currentName = name;
  level.clear();
  const raw = savedLevels[name] || {};
  const floorRow = Math.floor(FLOOR_Y / GRID) - 1;
  const shiftY = floorRow - 10;
  for (const [k, v] of Object.entries(raw)) {
    const [gx, gy] = k.split(",").map(Number);
    level.set(`${gx},${gy + shiftY}`, v);
  }
  openGame(mode);
}

async function delLevel(name) {
  if (!confirm(`Удалить «${name}»?`)) return;
  delete savedLevels[name];
  await fetch("/api/levels", { method: "POST", body: JSON.stringify(savedLevels) });
  renderMenu();
}

async function publishLevel() {
  if (![...level.values()].includes("goal")) {
    alert("Поставь ФИНИШ на уровень!");
    return;
  }
  const init = currentName === "Новый уровень" ? "" : currentName;
  const name = prompt("Название уровня:", init);
  if (!name || !name.trim()) return;
  const clean = name.trim();
  currentName = clean;
  const floorRow = Math.floor(FLOOR_Y / GRID) - 1;
  const shiftY = 10 - floorRow;
  const obj = {};
  for (const [k, v] of level.entries()) {
    const [gx, gy] = k.split(",").map(Number);
    obj[`${gx},${gy + shiftY}`] = v;
  }
  savedLevels[clean] = obj;
  await fetch("/api/levels", { method: "POST", body: JSON.stringify(savedLevels) });
  alert(`Уровень «${clean}» выложен!`);
}

function openGame(mode) {
  document.getElementById("menuScreen").style.display = "none";
  document.getElementById("gameScreen").style.display = "flex";
  resizeCanvas();
  screenState = mode;
  camX = 0; camY = 0; won = false;
  if (mode === "play") resetPlayer();
  syncUI();
}

function syncUI() {
  const isEdit = screenState === "edit";
  document.getElementById("editTools").style.display = isEdit ? "flex" : "none";
  document.getElementById("camPad").style.display = isEdit ? "grid" : "none"; document.getElementById("jumpBtn").style.display = isEdit ? "none" : "block";
  const btn = document.getElementById("playToggleBtn");
  btn.textContent = isEdit ? "ИГРАТЬ" : "РЕДАКТОР";
  btn.style.background = isEdit ? "#00b894" : "#ff7675";
}

function setTool(t) {
  tool = t;
  document.querySelectorAll("#editTools .t-btn").forEach(b => b.classList.remove("active"));
  const el = document.getElementById("t_" + t);
  if (el) el.classList.add("active");
}

function toggleMode() {
  if (screenState === "edit") {
    screenState = "play"; dragObj = null; resetPlayer();
  } else {
    screenState = "edit"; camX = 0; camY = 0; won = false;
  }
  syncUI();
}

function resetPlayer() {
  player.x = 80; player.y = FLOOR_Y - GRID;
  player.vy = 0; player.grounded = true; player.dead = false; player.mode = "cube";
  camX = 0; camY = 0; won = false; deadTimer = 0;
}

function camMove(dx, dy) { camVX = dx * 10; camVY = dy * 10; }
function camStop() { camVX = 0; camVY = 0; }
function screenToGrid(mx, my) {
  return [Math.floor((mx + camX) / GRID), Math.floor((my + camY) / GRID)];
}

function isValidCell(gx, gy) {
  const maxGy = Math.floor(FLOOR_Y / GRID) - 1;
  const minGy = Math.floor(MAX_SKY_Y / GRID);
  if (gx < 0 || gy < minGy || gy > maxGy) return false;
  if (gx === 2 && gy === maxGy) return false;
  return true;
}

cv.addEventListener("pointerdown", e => {
  const rect = cv.getBoundingClientRect();
  const mx = e.clientX - rect.left, my = e.clientY - rect.top;
  if (screenState === "play") { if (won) resetPlayer(); return; }
  if (screenState === "edit") {
    const [gx, gy] = screenToGrid(mx, my);
    const key = `${gx},${gy}`;
    if (tool === "move") {
      if (level.has(key)) {
        dragObj = level.get(key);
        level.delete(key);
        dragOrigin = key;
        dragPos = {x: mx, y: my};
      }
    } else if (isValidCell(gx, gy)) {
      if (tool === "erase") level.delete(key);
      else level.set(key, tool);
    }
  }
});

cv.addEventListener("pointermove", e => {
  if (screenState !== "edit" || e.buttons === 0) return;
  const rect = cv.getBoundingClientRect();
  const mx = e.clientX - rect.left, my = e.clientY - rect.top;
  if (tool === "move" && dragObj) {
    dragPos = {x: mx, y: my};
  } else if (tool !== "move") {
    const [gx, gy] = screenToGrid(mx, my);
    if (isValidCell(gx, gy)) {
      const key = `${gx},${gy}`;
      if (tool === "erase") level.delete(key);
      else level.set(key, tool);
    }
  }
});

window.addEventListener("pointerup", e => {
  actionPressed = false;
  if (screenState === "edit" && dragObj) {
    const rect = cv.getBoundingClientRect();
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    const [gx, gy] = screenToGrid(mx, my);
    const key = `${gx},${gy}`;
    if (isValidCell(gx, gy) && !level.has(key)) level.set(key, dragObj);
    else level.set(dragOrigin, dragObj);
    dragObj = null; dragOrigin = null;
  }
});

window.addEventListener("keydown", e => {
  if (e.code === "Space") { e.preventDefault(); actionPressed = true; if (won) resetPlayer(); }
  if (e.code === "ArrowRight") camVX = 10;
  if (e.code === "ArrowLeft") camVX = -10;
  if (e.code === "ArrowUp") camVY = -10;
  if (e.code === "ArrowDown") camVY = 10;
});
window.addEventListener("keyup", e => {
  if (e.code === "Space") actionPressed = false;
  if (["ArrowRight","ArrowLeft"].includes(e.code)) camVX = 0;
  if (["ArrowUp","ArrowDown"].includes(e.code)) camVY = 0;
});

function collide(a, b) {
  return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
}

function update() {
  if (screenState === "menu") return;
  if (screenState === "edit") {
    camX = Math.max(0, camX + camVX);
    camY = Math.min(0, Math.max(MAX_SKY_Y, camY + camVY));
    return;
  }
  if (won) return;
  if (player.dead) {
    deadTimer += 16;
    if (deadTimer >= 300) resetPlayer();
    return;
  }

  if (player.mode === "cube") {
    if (actionPressed && player.grounded) { player.vy = JUMP_FORCE; player.grounded = false; }
    player.vy += GRAVITY;
  } else {
    player.vy += actionPressed ? SHIP_THRUST : SHIP_GRAVITY;
    player.vy = Math.max(-SHIP_MAX_VY, Math.min(SHIP_MAX_VY, player.vy));
  }

  player.x += SPEED;
  let pBox = { x: player.x + 3, y: player.y + 3, w: GRID - 6, h: GRID - 6 };
  for (const [k, obj] of level.entries()) {
    if (obj !== "block") continue;
    const [gx, gy] = k.split(",").map(Number);
    if (collide(pBox, { x: gx*GRID, y: gy*GRID, w: GRID, h: GRID })) { player.dead = true; return; }
  }

  player.y += player.vy;
  player.grounded = false;
  if (player.y + GRID >= FLOOR_Y) { player.y = FLOOR_Y - GRID; player.vy = 0; player.grounded = true; }
  if (player.y < MAX_SKY_Y) { player.y = MAX_SKY_Y; if (player.vy < 0) player.vy = 0; }

  pBox = { x: player.x + 3, y: player.y, w: GRID - 6, h: GRID };
  for (const [k, obj] of level.entries()) {
    const [gx, gy] = k.split(",").map(Number);
    const ox = gx * GRID, oy = gy * GRID;
    if (obj === "block") {
      if (collide(pBox, { x: ox, y: oy, w: GRID, h: GRID })) {
        if (player.vy > 0) { player.y = oy - GRID; player.vy = 0; player.grounded = true; }
        else if (player.vy < 0) {
          if (player.mode === "ship") { player.y = oy + GRID; player.vy = 0; }
          else { player.dead = true; return; }
        }
      }
    } else if (obj === "pad_yellow") {
      if (collide(pBox, { x: ox + 4, y: oy + GRID - 14, w: GRID - 8, h: 14 })) {
        player.vy = JUMP_FORCE * 1.45;
        player.grounded = false;
      }
    } else if (obj === "pad_yellow") {
    ctx.fillStyle = "#ffd32a";
    ctx.strokeStyle = hl ? "#00ffcc" : "#fff200";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(sx + GRID/2, sy + GRID, GRID/2 - 4, Math.PI, 0);
    ctx.closePath(); ctx.fill(); ctx.stroke();
  } else if (obj === "spike") {
      if (collide(pBox, { x: ox + 12, y: oy + 14, w: GRID - 24, h: GRID - 14 })) { player.dead = true; return; }
    } else if (obj === "portal_ship") {
      if (collide(pBox, { x: ox + 8, y: oy, w: GRID - 16, h: GRID })) player.mode = "ship";
    } else if (obj === "portal_cube") {
      if (collide(pBox, { x: ox + 8, y: oy, w: GRID - 16, h: GRID })) player.mode = "cube";
    } else if (obj === "goal") {
      if (collide(pBox, { x: ox, y: oy, w: GRID, h: GRID })) { won = true; return; }
    }
  }

  camX = Math.max(0, player.x - W * 0.25);
  const targetCY = Math.min(0, Math.max(MAX_SKY_Y, player.y - H * 0.45));
  camY += (targetCY - camY) * 0.15;
}

function drawObj(sx, sy, obj, hl=false) {
  if (obj === "block") {
    ctx.fillStyle = "#2d3436"; ctx.fillRect(sx, sy, GRID, GRID);
    ctx.strokeStyle = hl ? "#00ffcc" : "#74b9ff"; ctx.lineWidth = 2; ctx.strokeRect(sx, sy, GRID, GRID);
  } else if (obj === "spike") {
    ctx.fillStyle = "#ff4757"; ctx.beginPath();
    ctx.moveTo(sx + GRID/2, sy + 4); ctx.lineTo(sx + GRID - 3, sy + GRID); ctx.lineTo(sx + 3, sy + GRID);
    ctx.closePath(); ctx.fill(); ctx.strokeStyle = hl ? "#00ffcc" : "#fff"; ctx.stroke();
  } else if (obj === "portal_ship" || obj === "portal_cube") {
    const isShip = obj === "portal_ship";
    ctx.fillStyle = isShip ? "#4a154b" : "#0b4619";
    ctx.strokeStyle = isShip ? "#ff6b81" : "#2ed573"; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.ellipse(sx + GRID/2, sy + GRID/2, GRID/2 - 6, GRID/2 - 2, 0, 0, Math.PI*2); ctx.fill(); ctx.stroke();
    ctx.fillStyle = ctx.strokeStyle; ctx.font = "bold 9px sans-serif"; ctx.textAlign = "center";
    ctx.fillText(isShip ? "САМ" : "КУБ", sx + GRID/2, sy + GRID/2 + 3);
  } else if (obj === "goal") {
    ctx.fillStyle = "#165b54"; ctx.fillRect(sx, sy, GRID, GRID);
    ctx.strokeStyle = "#00ffcc"; ctx.strokeRect(sx, sy, GRID, GRID);
    ctx.fillStyle = "#00ffcc"; ctx.font = "bold 9px sans-serif"; ctx.textAlign = "center";
    ctx.fillText("ФИНИШ", sx + GRID/2, sy + GRID/2 + 3);
  }
}

function draw() {
  if (screenState === "menu") return;
  ctx.clearRect(0, 0, W, H);
  if (screenState === "edit") {
    ctx.strokeStyle = "#25253d"; ctx.lineWidth = 1;
    for (let c = Math.floor(camX/GRID); c <= Math.floor((camX+W)/GRID)+1; c++) {
      ctx.beginPath(); ctx.moveTo(c*GRID - camX, 0); ctx.lineTo(c*GRID - camX, H); ctx.stroke();
    }
    for (let r = Math.floor(camY/GRID); r <= Math.floor((camY+H)/GRID)+1; r++) {
      ctx.beginPath(); ctx.moveTo(0, r*GRID - camY); ctx.lineTo(W, r*GRID - camY); ctx.stroke();
    }
    ctx.strokeStyle = "#00ffcc"; ctx.lineWidth = 2;
    ctx.strokeRect(80 - camX, FLOOR_Y - GRID - camY, GRID, GRID);
  }
  const fy = FLOOR_Y - camY;
  if (fy < H) {
    ctx.fillStyle = "#0f0f1a"; ctx.fillRect(0, fy, W, H - fy);
    ctx.strokeStyle = "#00ffcc"; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(0, fy); ctx.lineTo(W, fy); ctx.stroke();
  }
  for (const [k, obj] of level.entries()) {
    const [gx, gy] = k.split(",").map(Number);
    const sx = gx * GRID - camX, sy = gy * GRID - camY;
    if (sx + GRID < 0 || sx > W || sy + GRID < 0 || sy > H) continue;
    drawObj(sx, sy, obj);
  }
  if (screenState === "edit" && dragObj) drawObj(dragPos.x - GRID/2, dragPos.y - GRID/2, dragObj, true);
  if (screenState === "play" && !player.dead) {
    const px = player.x - camX, py = player.y - camY;
    if (player.mode === "cube") {
      ctx.fillStyle = "#ffeaa7"; ctx.fillRect(px, py, GRID, GRID);
      ctx.strokeStyle = "#fdcb6e"; ctx.lineWidth = 3; ctx.strokeRect(px, py, GRID, GRID);
      ctx.fillStyle = "#2d3436"; ctx.fillRect(px+22, py+10, 6, 6); ctx.fillRect(px+31, py+10, 6, 6); ctx.fillRect(px+22, py+22, 15, 4);
    } else {
      ctx.fillStyle = "#ff6b81"; ctx.beginPath();
      ctx.moveTo(px+2, py+22); ctx.lineTo(px+12, py+36); ctx.lineTo(px+34, py+36); ctx.lineTo(px+GRID, py+24); ctx.lineTo(px+24, py+18);
      ctx.closePath(); ctx.fill();
      ctx.fillStyle = "#ffeaa7"; ctx.fillRect(px+14, py+10, 14, 14);
    }
  }
  if (won) {
    ctx.fillStyle = "rgba(18,18,26,0.9)"; ctx.fillRect(W*0.15, H/2 - 60, W*0.7, 120);
    ctx.strokeStyle = "#00ffcc"; ctx.lineWidth = 3; ctx.strokeRect(W*0.15, H/2 - 60, W*0.7, 120);
    ctx.fillStyle = "#00ffcc"; ctx.font = "bold 22px sans-serif"; ctx.textAlign = "center";
    ctx.fillText("УРОВЕНЬ ПРОЙДЕН!", W/2, H/2 - 15);
    ctx.fillStyle = "#fff"; ctx.font = "13px sans-serif";
    ctx.fillText("Нажми на экран, чтобы сыграть снова", W/2, H/2 + 25);
  }
}

function loop() { update(); draw(); requestAnimationFrame(loop); }
fetchLevels(); loop();
</script>
</body>
</html>
"""


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/levels":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(load_levels(), ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))

    def do_POST(self):
        if self.path == "/api/levels":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            save_levels(json.loads(body))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")


