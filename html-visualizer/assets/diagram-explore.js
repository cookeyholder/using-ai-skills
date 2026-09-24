/* 結構圖探索層＋浮動說明窗 — 與 diagram-explore.css 成對，整段內嵌進頁面 body 結尾前的 script 標籤裡。
 * （本檔任何地方都不能出現 script 的結尾標籤字樣，否則內嵌時瀏覽器會在那裡把腳本切斷。）
 *
 * 作者只要：① 圖包在 div.xp[data-explore] 裡；② svg 加 class xplore；
 * ③ 每個節點 g.node[data-id][data-kind][data-title] 內含 rect.box；
 * ④ 每條線 g.edge[data-from][data-to][data-label] 內含 path.hit（透明寬）與 path.ln；
 * ⑤ 線的標籤 g.elabel（文字＝data-label 才能一起變亮）；圖例項 g.lg[data-kind]；
 * ⑥ 選配：容器內 script[type=application/json].xp-views，內容 [{id,label,focus:[ids],note}]；
 * ⑦ 選配：每格的說明寫成 template[data-detail="<節點 id>"]（可加 data-tag="等你拍板" 之類的標籤），
 *    裡面寫一般 HTML；圖外的元素加 data-detail-open="<id>" 也能開同一個窗（id 對到 template 即可）。
 * 點一格 → 浮動窗上半是這格的說明（沒寫就只有連線資訊），下半是上下游與追線按鈕。
 * 窗可拖、可換邊、開在所點格子的對面；點窗外任何地方、按 esc 或 ✕ 關閉；手機（≤760px）變底部抽屜。
 * 深連結：#focus=id / #focus=id&reach=up|down / #route=a~b / #view=id（只作用在第一張圖）。
 */
(function () {
  const SVGNS = "http://www.w3.org/2000/svg";
  const HINT =
    "點一格看說明與上下游；<kbd>shift</kbd>＋點第二格找兩格之間的路徑；點圖例可暫時藏掉一類；<kbd>esc</kbd> 關閉";
  const esc = (s) =>
    String(s).replace(
      /[&<>"]/g,
      (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c],
    );

  // ── 全頁共用的浮動說明窗 ─────────────────────────
  const panel = document.createElement("aside");
  panel.className = "xp-panel";
  panel.hidden = true;
  panel.setAttribute("aria-label", "說明");
  panel.innerHTML =
    '<div class="xp-grip" title="按住拖曳"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="9" cy="6" r="1"/><circle cx="15" cy="6" r="1"/><circle cx="9" cy="12" r="1"/><circle cx="15" cy="12" r="1"/><circle cx="9" cy="18" r="1"/><circle cx="15" cy="18" r="1"/></svg>按住這裡拖曳</div>' +
    '<button class="xp-ibtn xp-flip" type="button" title="換到另一邊" aria-label="換到另一邊"><svg viewBox="0 0 24 24"><path d="M8 3 4 7l4 4"/><path d="M4 7h16"/><path d="m16 21 4-4-4-4"/><path d="M20 17H4"/></svg></button>' +
    '<button class="xp-ibtn xp-close" type="button" aria-label="關閉"><svg viewBox="0 0 24 24"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg></button>' +
    '<span class="xp-tag"></span><h3 class="xp-title"></h3><div class="xp-body"></div><div class="xp-nav"></div>';
  document.body.appendChild(panel);
  const pTag = panel.querySelector(".xp-tag");
  const pTitle = panel.querySelector(".xp-title");
  const pBody = panel.querySelector(".xp-body");
  const pNav = panel.querySelector(".xp-nav");
  let owner = null; // 目前佔用窗的那張圖（instance），圖外開窗時為 null
  let navHandler = null;

  const isSheet = () => window.innerWidth <= 760;
  let userMoved = false;
  function resetPos() {
    ["left", "right", "top", "bottom", "height"].forEach(
      (k) => (panel.style[k] = ""),
    );
  }
  function setSide(side) {
    resetPos();
    if (side === "left") {
      panel.style.left = "18px";
      panel.style.right = "auto";
    }
    userMoved = false;
  }
  function place(anchor) {
    if (isSheet()) return resetPos();
    const ar = anchor ? anchor.getBoundingClientRect() : null;
    const side =
      ar && ar.left + ar.width / 2 > window.innerWidth / 2 ? "left" : "right";
    if (!userMoved) return setSide(side);
    if (!ar) return;
    const pr = panel.getBoundingClientRect();
    const overlap = !(
      ar.right < pr.left ||
      ar.left > pr.right ||
      ar.bottom < pr.top ||
      ar.top > pr.bottom
    );
    if (overlap) setSide(side);
  }
  function findTemplate(id, scope) {
    const sel = 'template[data-detail="' + CSS.escape(id) + '"]';
    return (scope && scope.querySelector(sel)) || document.querySelector(sel);
  }
  // 開窗：title、tag、說明（template 或 fallback 字串）、下半部導覽（HTML 字串＋點擊處理）
  function openPanel(o) {
    pTag.textContent = o.tag || "";
    pTag.hidden = !o.tag;
    pTitle.textContent = o.title || "";
    pBody.textContent = "";
    if (o.template) pBody.appendChild(o.template.content.cloneNode(true));
    else if (o.fallback)
      pBody.innerHTML = '<p class="xp-dim">' + o.fallback + "</p>";
    pNav.innerHTML = o.nav || "";
    pNav.hidden = !o.nav;
    navHandler = o.onNav || null;
    // 換到另一張圖（或圖外開窗）時，把前一張圖的聚焦變暗清掉
    if (owner && owner !== (o.owner || null)) owner.reset();
    owner = o.owner || null;
    const wasHidden = panel.hidden;
    panel.hidden = false;
    if (wasHidden) panel.scrollTop = 0;
    place(o.anchor || null);
  }
  function closePanel() {
    if (panel.hidden) return;
    panel.hidden = true;
    const o = owner;
    owner = null;
    navHandler = null;
    if (o) o.reset();
  }
  pNav.addEventListener("click", (ev) => {
    const b = ev.target.closest("button");
    if (b && navHandler) navHandler(b);
  });
  panel.querySelector(".xp-close").addEventListener("click", closePanel);
  panel.querySelector(".xp-flip").addEventListener("click", () => {
    const pr = panel.getBoundingClientRect();
    setSide(pr.left + pr.width / 2 > window.innerWidth / 2 ? "left" : "right");
  });
  const grip = panel.querySelector(".xp-grip");
  let drag = null;
  grip.addEventListener("pointerdown", (ev) => {
    if (isSheet()) return;
    const r = panel.getBoundingClientRect();
    drag = { dx: ev.clientX - r.left, dy: ev.clientY - r.top, h: r.height };
    Object.assign(panel.style, {
      left: r.left + "px",
      top: r.top + "px",
      right: "auto",
      bottom: "auto",
      height: r.height + "px",
    });
    panel.classList.add("dragging");
    grip.setPointerCapture(ev.pointerId);
    ev.preventDefault();
  });
  grip.addEventListener("pointermove", (ev) => {
    if (!drag) return;
    const w = panel.offsetWidth;
    const x = Math.min(
      Math.max(ev.clientX - drag.dx, 8),
      window.innerWidth - w - 8,
    );
    const y = Math.min(
      Math.max(ev.clientY - drag.dy, 8),
      window.innerHeight - 120,
    );
    panel.style.left = x + "px";
    panel.style.top = y + "px";
    panel.style.height =
      Math.max(220, Math.min(drag.h, window.innerHeight - y - 24)) + "px";
  });
  const endDrag = () => {
    if (!drag) return;
    drag = null;
    userMoved = true;
    panel.classList.remove("dragging");
  };
  grip.addEventListener("pointerup", endDrag);
  grip.addEventListener("pointercancel", endDrag);
  // 窗開著時把視窗縮到手機寬：清掉桌機留下的座標，抽屜才不會往右凸出
  window.addEventListener("resize", () => {
    if (!panel.hidden && isSheet()) {
      resetPos();
      userMoved = false;
    }
  });
  // 點窗外任何地方就關。例外：窗本身、開窗按鈕、章節列、圖例、風格設定面板（在這些地方操作不該把窗關掉）；
  // 節點與線的點擊自己 stopPropagation，換格不會先關再開。
  // 用事件發生當下的路徑判斷：窗裡的按鈕按下去會重畫導覽區，按鈕本身已被移除，
  // 用 ev.target.closest 會找不到它屬於窗、誤判成點窗外而把窗關掉。
  // 評論工具：在窗裡選字留言時，按「評論」不該把窗關掉
  const KEEP =
    ".xp-panel, [data-detail-open], .xp-views, svg.xplore .lg, .vt-tw-root, .vt-comment-trigger, .vt-comment-popup";
  document.addEventListener("click", (ev) => {
    if (panel.hidden) return;
    if (ev.composedPath().some((el) => el.matches && el.matches(KEEP))) return;
    closePanel();
  });
  document.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape") {
      if (!panel.hidden) closePanel();
      else instances.forEach((i) => i.reset());
    }
  });
  // 圖外元素開窗（例如規格頁的「規則一」「規則二」按鈕）
  document.querySelectorAll("[data-detail-open]").forEach((b) => {
    b.addEventListener("click", () => {
      const id = b.getAttribute("data-detail-open");
      const t = findTemplate(id, null);
      if (!t)
        return console.error(
          "data-detail-open 找不到對應的 template[data-detail]",
          id,
        );
      instances.forEach((i) => i.clear());
      openPanel({
        title: t.getAttribute("data-title") || id,
        tag: t.getAttribute("data-tag") || "",
        template: t,
        anchor: b,
      });
    });
  });

  // ── 每張圖 ─────────────────────────────────────
  function setup(root, idx) {
    const svg = root.querySelector("svg.xplore");
    if (!svg) return null;
    let views = [];
    const vj = root.querySelector("script.xp-views");
    if (vj) {
      try {
        views = JSON.parse(vj.textContent);
      } catch (e) {
        console.error("xp-views JSON 壞了", e);
      }
    }
    const fig = svg.closest(".figure") || svg;
    const main = document.createElement("div");
    main.className = "xp-main";
    fig.parentNode.insertBefore(main, fig);
    const viewsBar = document.createElement("div");
    viewsBar.className = "xp-views";
    const hintEl = document.createElement("div");
    hintEl.className = "xp-hint";
    hintEl.innerHTML = HINT;
    const noteEl = document.createElement("div");
    noteEl.className = "xp-note";
    main.append(viewsBar, hintEl, noteEl, fig);
    if (!views.length) viewsBar.remove();
    const uid = "xp" + idx + "-hot";
    let defs = svg.querySelector("defs");
    if (!defs) {
      defs = document.createElementNS(SVGNS, "defs");
      svg.insertBefore(defs, svg.firstChild);
    }
    const mk = document.createElementNS(SVGNS, "marker");
    mk.setAttribute("id", uid);
    mk.setAttribute("markerWidth", "8");
    mk.setAttribute("markerHeight", "6");
    mk.setAttribute("refX", "7");
    mk.setAttribute("refY", "3");
    mk.setAttribute("orient", "auto");
    const poly = document.createElementNS(SVGNS, "polygon");
    poly.setAttribute("points", "0 0, 8 3, 0 6");
    poly.setAttribute("class", "ordbg");
    mk.appendChild(poly);
    defs.appendChild(mk);

    const nodes = [...svg.querySelectorAll(".node")],
      edges = [...svg.querySelectorAll(".edge")];
    const byId = Object.fromEntries(nodes.map((n) => [n.dataset.id, n]));
    const out = {},
      inn = {};
    nodes.forEach((n) => {
      out[n.dataset.id] = [];
      inn[n.dataset.id] = [];
    });
    const bad = [];
    edges.forEach((e) => {
      if (!byId[e.dataset.from] || !byId[e.dataset.to]) {
        bad.push(e.dataset.from + "→" + e.dataset.to);
        return;
      }
      out[e.dataset.from].push(e);
      inn[e.dataset.to].push(e);
    });
    if (bad.length)
      console.error("探索層：這些線的端點沒有對應的 data-id", bad);
    const labelOf = {};
    svg.querySelectorAll(".elabel").forEach((g) => {
      labelOf[g.textContent.trim()] = g;
    });
    edges.forEach((e) => {
      e._label = labelOf[(e.dataset.label || "").trim()] || null;
    });

    const state = { focus: null, mode: "focus", view: null };
    const title = (id) => byId[id].dataset.title || id;
    function clear() {
      svg.classList.remove("has-focus");
      nodes.forEach((n) => {
        n.classList.remove("on", "is-focus");
        n.querySelectorAll(".ordwrap").forEach((x) => x.remove());
      });
      edges.forEach((e) => {
        e.classList.remove("on");
        e.querySelector(".ln").style.markerEnd = "";
        e._label && e._label.classList.remove("on");
      });
    }
    const lightNodes = (ids) =>
      ids.forEach((id) => byId[id] && byId[id].classList.add("on"));
    function lightEdge(e) {
      e.classList.add("on");
      e.querySelector(".ln").style.markerEnd = "url(#" + uid + ")";
      e._label && e._label.classList.add("on");
    }
    function reach(id, dir) {
      const seen = new Set([id]),
        q = [id],
        es = [];
      while (q.length) {
        const c = q.shift();
        (dir === "down" ? out[c] : inn[c]).forEach((e) => {
          es.push(e);
          const n = dir === "down" ? e.dataset.to : e.dataset.from;
          if (!seen.has(n)) {
            seen.add(n);
            q.push(n);
          }
        });
      }
      return { nodes: [...seen], edges: es };
    }
    function path(a, b) {
      const prev = { [a]: null },
        q = [a];
      while (q.length) {
        const c = q.shift();
        if (c === b) break;
        for (const e of out[c]) {
          const n = e.dataset.to;
          if (!(n in prev)) {
            prev[n] = { from: c, edge: e };
            q.push(n);
          }
        }
      }
      if (!(b in prev)) return null;
      const steps = [];
      let c = b;
      while (prev[c]) {
        steps.unshift(prev[c]);
        c = prev[c].from;
      }
      return steps;
    }
    const setHash = (h) => {
      if (idx === 0)
        history.replaceState(
          null,
          "",
          h ? "#" + h : location.pathname + location.search,
        );
    };
    function order(id, i) {
      const r = byId[id].querySelector(".box");
      const x = +r.getAttribute("x") || 0,
        y = +r.getAttribute("y") || 0;
      const g = document.createElementNS(SVGNS, "g");
      g.setAttribute("class", "ordwrap");
      g.innerHTML =
        '<circle class="ordbg" cx="' +
        x +
        '" cy="' +
        y +
        '" r="9"/><text class="ord" x="' +
        x +
        '" y="' +
        (y + 3.5) +
        '" text-anchor="middle">' +
        i +
        "</text>";
      byId[id].appendChild(g);
    }
    function setActiveView(id) {
      viewsBar
        .querySelectorAll("button")
        .forEach((b) => b.classList.toggle("active", b.dataset.view === id));
    }
    const btn = (act, text, extra) =>
      '<button type="button" data-act="' +
      act +
      '"' +
      (extra || "") +
      ">" +
      text +
      "</button>";
    function onNav(b) {
      const a = b.dataset.act;
      if (a === "clear") closePanel();
      else if (a === "up" || a === "down") showReach(state.focus, a);
      else if (a === "back") showFocus(state.focus);
      else if (a === "route") {
        state.mode = "route";
        b.classList.add("active");
        noteEl.textContent = "現在點第二格。";
      } else if (a === "rev") showRoute(b.dataset.a, b.dataset.b);
      else if (a === "prev" || a === "next") {
        const i = views.findIndex((v) => v.id === state.view);
        showView(
          views[(i + (a === "next" ? 1 : views.length - 1)) % views.length],
        );
      }
    }
    function open(o) {
      openPanel(Object.assign({ owner: api, onNav }, o));
    }
    function showFocus(id, anchor) {
      clear();
      state.focus = id;
      state.view = null;
      setActiveView(null);
      svg.classList.add("has-focus");
      byId[id].classList.add("on", "is-focus");
      const up = inn[id].map((e) => e.dataset.from),
        down = out[id].map((e) => e.dataset.to);
      lightNodes(up.concat(down));
      inn[id].concat(out[id]).forEach(lightEdge);
      const t = findTemplate(id, root);
      noteEl.textContent = "";
      open({
        title: title(id),
        tag: t ? t.getAttribute("data-tag") || "" : "",
        template: t,
        fallback: t ? "" : "這格沒有另外寫說明，下面是它直接相連的格子。",
        anchor: anchor || byId[id],
        nav:
          '<div class="xp-row">上游 ' +
          up.length +
          "：" +
          (esc(up.map(title).join("、")) || "—") +
          "</div>" +
          '<div class="xp-row">下游 ' +
          down.length +
          "：" +
          (esc(down.map(title).join("、")) || "—") +
          "</div>" +
          '<div class="xp-btns">' +
          btn("up", "往上游追到底") +
          btn("down", "往下游追到底") +
          btn("route", "從這裡找路徑…") +
          btn("clear", "清除") +
          "</div>",
      });
      setHash("focus=" + id);
    }
    function showReach(id, dir) {
      clear();
      svg.classList.add("has-focus");
      byId[id].classList.add("on", "is-focus");
      const r = reach(id, dir);
      lightNodes(r.nodes);
      r.edges.forEach(lightEdge);
      const others = r.nodes.filter((n) => n !== id);
      pNav.innerHTML =
        '<div class="xp-row"><b>' +
        (dir === "down" ? "下游" : "上游") +
        "全部 " +
        others.length +
        " 格</b>（沿箭頭可達、只看圖上畫出來的關係）</div>" +
        '<div class="xp-row">' +
        (esc(others.map(title).join("、")) || "—") +
        "</div>" +
        '<div class="xp-btns">' +
        btn("back", "回到相鄰") +
        btn("clear", "清除") +
        "</div>";
      setHash("focus=" + id + "&reach=" + dir);
    }
    function showRoute(a, b) {
      const st = path(a, b);
      clear();
      state.view = null;
      state.mode = "focus";
      setActiveView(null);
      svg.classList.add("has-focus");
      noteEl.textContent = "";
      if (!st) {
        byId[a].classList.add("on");
        byId[b].classList.add("on");
        open({
          title: title(a) + " → " + title(b),
          fallback: "圖上沒有這個方向的路徑。",
          anchor: byId[b],
          nav:
            '<div class="xp-btns">' +
            btn(
              "rev",
              "反向找",
              ' data-a="' + esc(b) + '" data-b="' + esc(a) + '"',
            ) +
            btn("clear", "清除") +
            "</div>",
        });
        return;
      }
      byId[a].classList.add("on", "is-focus");
      order(a, 1);
      st.forEach((s, i) => {
        lightEdge(s.edge);
        byId[s.edge.dataset.to].classList.add("on");
        order(s.edge.dataset.to, i + 2);
      });
      open({
        title: title(a) + " → " + title(b),
        fallback: st.length + " 步，最短有向路徑",
        anchor: byId[b],
        nav:
          "<ol>" +
          st
            .map(
              (s) =>
                "<li>" +
                esc(title(s.from)) +
                ' <span class="xp-dim">' +
                esc(
                  s.edge.dataset.label ? "—" + s.edge.dataset.label + "→" : "→",
                ) +
                "</span> " +
                esc(title(s.edge.dataset.to)) +
                "</li>",
            )
            .join("") +
          '</ol><div class="xp-btns">' +
          btn("clear", "清除") +
          "</div>",
      });
      setHash("route=" + a + "~" + b);
    }
    function showView(v) {
      clear();
      state.view = v.id;
      svg.classList.add("has-focus");
      lightNodes(v.focus);
      const set = new Set(v.focus);
      edges.forEach((e) => {
        if (set.has(e.dataset.from) && set.has(e.dataset.to)) lightEdge(e);
      });
      setActiveView(v.id);
      noteEl.textContent = v.note || "";
      open({
        title: v.label,
        fallback: "這一章點亮 " + v.focus.length + " 格",
        anchor: viewsBar,
        nav:
          "<ul>" +
          v.focus
            .filter((id) => byId[id])
            .map((id) => "<li>" + esc(title(id)) + "</li>")
            .join("") +
          "</ul>" +
          '<div class="xp-btns">' +
          btn("prev", "上一章") +
          btn("next", "下一章") +
          btn("clear", "清除") +
          "</div>",
      });
      setHash("view=" + v.id);
    }
    function reset() {
      clear();
      state.focus = null;
      state.view = null;
      state.mode = "focus";
      setActiveView(null);
      noteEl.textContent = "";
      setHash("");
    }

    views.forEach((v) => {
      const b = document.createElement("button");
      b.type = "button";
      b.dataset.view = v.id;
      b.textContent = v.label;
      b.addEventListener("click", () => showView(v));
      viewsBar.appendChild(b);
    });
    nodes.forEach((n) => {
      n.setAttribute("tabindex", "0");
      n.setAttribute("role", "button");
      n.addEventListener("click", (ev) => {
        ev.stopPropagation();
        const id = n.dataset.id;
        if (
          (ev.shiftKey || state.mode === "route") &&
          state.focus &&
          state.focus !== id &&
          owner === api
        ) {
          state.mode = "focus";
          showRoute(state.focus, id);
        } else showFocus(id, n);
      });
      n.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter" || ev.key === " ") {
          ev.preventDefault();
          n.click();
        }
      });
    });
    edges.forEach((e) => {
      e.addEventListener("click", (ev) => {
        ev.stopPropagation();
        clear();
        state.view = null;
        setActiveView(null);
        svg.classList.add("has-focus");
        lightEdge(e);
        byId[e.dataset.from].classList.add("on");
        byId[e.dataset.to].classList.add("on");
        open({
          title: title(e.dataset.from) + " → " + title(e.dataset.to),
          fallback: esc(e.dataset.label || "（無標籤）"),
          anchor: e,
          nav: '<div class="xp-btns">' + btn("clear", "清除") + "</div>",
        });
      });
    });
    svg.querySelectorAll(".lg").forEach((l) => {
      l.addEventListener("click", () => {
        const k = l.dataset.kind;
        l.classList.toggle("off");
        const off = l.classList.contains("off");
        nodes.forEach((n) => {
          if (n.dataset.kind === k) n.classList.toggle("off", off);
        });
      });
    });
    const api = {
      applyHash() {
        const h = new URLSearchParams(location.hash.slice(1));
        if (h.get("view")) {
          const v = views.find((v) => v.id === h.get("view"));
          v ? showView(v) : reset();
        } else if (h.get("route")) {
          const [a, b] = h.get("route").split("~");
          byId[a] && byId[b] ? showRoute(a, b) : reset();
        } else if (h.get("focus") && byId[h.get("focus")]) {
          showFocus(h.get("focus"));
          if (h.get("reach")) showReach(h.get("focus"), h.get("reach"));
        }
      },
      reset,
      clear,
    };
    return api;
  }

  const instances = [...document.querySelectorAll("[data-explore]")]
    .map(setup)
    .filter(Boolean);
  if (!instances.length) return;
  instances[0].applyHash();
  window.addEventListener("hashchange", () => instances[0].applyHash());
})();
