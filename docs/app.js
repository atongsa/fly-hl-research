const cfg = window.FLYHL_CONFIG || {};

function badge(el, text, kind) {
  el.innerHTML = `<span class="badge ${kind}">${text}</span>`;
}

async function postInfo(body) {
  const res = await fetch(cfg.infoUrl || "https://api.hyperliquid.xyz/info", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error("info " + res.status);
  return res.json();
}

function drawFly(pShort) {
  const c = document.getElementById("fly");
  const ctx = c.getContext("2d");
  const w = c.width, h = c.height;
  ctx.clearRect(0, 0, w, h);
  ctx.strokeStyle = "#2a2b36";
  for (let x = 40; x < w; x += 40) {
    ctx.beginPath(); ctx.moveTo(x, 20); ctx.lineTo(x, h - 20); ctx.stroke();
  }
  const layers = ["R1-8", "L1-2", "T4/T5", "LC", "GF"];
  const p = Math.max(0, Math.min(1, pShort || 0));
  layers.forEach((name, i) => {
    const x = 70 + i * 110;
    const y = h / 2 + Math.sin(Date.now() / 400 + i) * 8;
    const r = 16 + p * 10;
    ctx.beginPath();
    ctx.fillStyle = i === layers.length - 1
      ? `rgba(232, 93, 76, ${0.25 + p * 0.6})`
      : `rgba(110, 231, 183, ${0.15 + (1 - Math.abs(i / 4 - p)) * 0.4})`;
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#e8e6de";
    ctx.font = "12px ui-sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(name, x, y + 36);
    if (i < layers.length - 1) {
      ctx.strokeStyle = `rgba(232, 93, 76, ${0.2 + p * 0.5})`;
      ctx.beginPath();
      ctx.moveTo(x + r, y);
      ctx.lineTo(x + 110 - r, y);
      ctx.stroke();
    }
  });
}

async function refresh() {
  const err = document.getElementById("err");
  err.textContent = "";
  try {
    const state = await fetch(cfg.stateUrl || "./live-state.json", { cache: "no-store" }).then((r) => r.json());
    document.getElementById("mode").textContent = state.mode || "idle";
    const act = (state.decision && state.decision.action) || "idle";
    badge(document.getElementById("action"), act, act === "short" ? "short" : act === "flat" ? "flat" : "idle");
    const ps = state.decision ? state.decision.p_short : 0;
    document.getElementById("pshort").textContent = ps != null ? Number(ps).toFixed(3) : "\u2014";
    document.getElementById("updated").textContent = state.updated || "\u2014";
    const ev = (state.execution && state.execution.event) || (state.paper && state.paper.last_event) || state.note || "\u2014";
    document.getElementById("event").textContent = ev;
    drawFly(ps);
  } catch (e) {
    err.textContent = "local state: " + e.message;
    drawFly(0);
  }
  try {
    const data = await postInfo({ type: "metaAndAssetCtxs" });
    const uni = data[0].universe || [];
    const idx = uni.findIndex((u) => u.name === (cfg.coin || "BTC"));
    if (idx >= 0) {
      const ctx = data[1][idx];
      document.getElementById("mark").textContent = ctx.markPx;
      document.getElementById("funding").textContent = ctx.funding;
      document.getElementById("oi").textContent = ctx.openInterest;
    }
  } catch (e) {
    err.textContent = (err.textContent ? err.textContent + " \u00b7 " : "") + "HL public: " + e.message;
  }
  const acct = cfg.publicAccount;
  document.getElementById("acct").textContent = acct || "(set docs/config.js)";
  if (acct) {
    try {
      const us = await postInfo({ type: "clearinghouseState", user: acct });
      const pos = (us.assetPositions || []).find((p) => p.position && p.position.coin === (cfg.coin || "BTC"));
      document.getElementById("szi").textContent = pos ? pos.position.szi : "0";
    } catch (e) {
      document.getElementById("szi").textContent = "n/a";
    }
  }
}

refresh();
setInterval(refresh, 15000);
setInterval(() => {
  const el = document.getElementById("pshort");
  drawFly(parseFloat(el.textContent) || 0);
}, 80);
