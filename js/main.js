const FALLBACK_PRODUCTS = [
  {
    id: 1, slug: "heritage-lounge-sofa", name: "Heritage Lounge Sofa", dim: "2100x900x850 mm",
    price: 48900, stock: 12, category: "home", category_name: "Home Furniture", colors: ["coka", "red", "gold"],
    image: "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&w=1200&q=80",
    thumbs: [
      "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&w=800&q=80",
      "https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?auto=format&fit=crop&w=800&q=80",
      "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?auto=format&fit=crop&w=800&q=80"
    ],
    specs: ["Solid teak frame", "High-density foam", "Premium fabric upholstery", "Made in India"],
    description: "Comfort-first lounge sofa for living rooms."
  },
  {
    id: 2, slug: "executive-office-desk", name: "Executive Office Desk", dim: "1600x800x750 mm",
    price: 32400, stock: 18, category: "office", category_name: "Office Furniture", colors: ["coka", "gold"],
    image: "https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?auto=format&fit=crop&w=1200&q=80",
    thumbs: [
      "https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?auto=format&fit=crop&w=800&q=80",
      "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=800&q=80",
      "https://images.unsplash.com/photo-1524758631624-e2822e304c36?auto=format&fit=crop&w=800&q=80"
    ],
    specs: ["Engineered wood + veneer", "Cable management", "Soft-close drawers", "Scratch-resistant top"],
    description: "Executive desk with cable management."
  },
  {
    id: 3, slug: "teak-dining-collection", name: "Teak Dining Collection", dim: "1800x900x760 mm",
    price: 54200, stock: 8, category: "home", category_name: "Home Furniture", colors: ["coka", "gold", "yellow"],
    image: "https://images.unsplash.com/photo-1617806118233-18e1de247200?auto=format&fit=crop&w=1200&q=80",
    thumbs: [
      "https://images.unsplash.com/photo-1617806118233-18e1de247200?auto=format&fit=crop&w=800&q=80",
      "https://images.unsplash.com/photo-1600585154340-0ef3c08c08be?auto=format&fit=crop&w=800&q=80",
      "https://images.unsplash.com/photo-1506439773649-6e0eb8cfb237?auto=format&fit=crop&w=800&q=80"
    ],
    specs: ["6-seater teak table", "Cushioned chairs", "Natural wood grain", "Indoor use"],
    description: "Six-seater teak dining set."
  },
  {
    id: 4, slug: "modular-workstation", name: "Modular Workstation", dim: "1200x600x750 mm",
    price: 18700, stock: 24, category: "workstation", category_name: "Workstation", colors: ["coka", "red"],
    image: "https://images.unsplash.com/photo-1524758631624-e2822e304c36?auto=format&fit=crop&w=1200&q=80",
    thumbs: [
      "https://images.unsplash.com/photo-1524758631624-e2822e304c36?auto=format&fit=crop&w=800&q=80",
      "https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=800&q=80",
      "https://images.unsplash.com/photo-1497366811353-6870744d04b2?auto=format&fit=crop&w=800&q=80"
    ],
    specs: ["Modular partitions", "Powder-coated steel", "Wire raceway", "Office / institutional"],
    description: "Modular workstation for offices."
  }
];

const LEGACY = { sofa: "heritage-lounge-sofa", desk: "executive-office-desk", dining: "teak-dining-collection", station: "modular-workstation" };
const GUEST_KEY = "kanwood_shop_guest_cart";

let CATALOGUE = FALLBACK_PRODUCTS.slice();
let ME = null;
let CART = { items: [], count: 0, subtotal: 0, shipping: 0, total: 0 };

async function apiGet(path) {
  const res = await fetch(path, { credentials: "same-origin" });
  if (!res.ok) throw new Error("api");
  return res.json();
}

async function apiSend(path, method, body) {
  const res = await fetch(path, {
    method,
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

function money(n) {
  return "₹" + Number(n || 0).toLocaleString("en-IN");
}

function guestCart() {
  try { return JSON.parse(localStorage.getItem(GUEST_KEY) || "[]"); } catch (e) { return []; }
}

function saveGuest(items) {
  localStorage.setItem(GUEST_KEY, JSON.stringify(items));
}

function findProduct(slug) {
  const s = LEGACY[slug] || slug;
  return CATALOGUE.find((p) => p.slug === s);
}

function paintCount() {
  const n = CART.count || 0;
  document.querySelectorAll("[data-cart-count]").forEach((el) => { el.textContent = String(n); });
}

function guestSummary() {
  const items = guestCart();
  const sub = items.reduce((s, x) => s + x.price * x.qty, 0);
  const ship = sub >= 25000 || !sub ? 0 : 499;
  return { items, count: items.reduce((s, x) => s + x.qty, 0), subtotal: sub, shipping: ship, total: sub + ship };
}

async function refreshCart() {
  if (ME) {
    try { CART = await apiGet("/api/cart"); } catch (e) { CART = { items: [], count: 0, subtotal: 0, shipping: 0, total: 0 }; }
  } else {
    CART = guestSummary();
  }
  paintCount();
  return CART;
}

async function addToCart(slug, qty) {
  const p = findProduct(slug);
  if (!p) return { ok: false, error: "Product not found." };
  const q = Math.max(1, Number(qty) || 1);
  if (ME) {
    const data = await apiSend("/api/cart", "POST", { slug: p.slug, qty: q });
    CART = data.cart;
    paintCount();
    return data;
  }
  const items = guestCart();
  const found = items.find((x) => x.slug === p.slug);
  const next = (found ? found.qty : 0) + q;
  if (p.stock && next > p.stock) throw new Error("Only " + p.stock + " in stock.");
  if (found) found.qty = next;
  else items.push({ slug: p.slug, name: p.name, price: p.price, img: p.image, dim: p.dim, qty: q, stock: p.stock });
  saveGuest(items);
  CART = guestSummary();
  paintCount();
  return { ok: true, cart: CART };
}

function dotsHtml(colors) {
  return (colors || []).map((c) => `<span class="dot ${c}"></span>`).join("");
}

function cardHtml(p, root) {
  const r = root || "";
  const stock = p.in_stock === false || p.stock === 0
    ? '<p class="stock-out">Out of stock</p>'
    : '<p class="stock-ok">In stock' + (p.stock ? " · " + p.stock : "") + "</p>";
  return `
    <a class="pcard" data-cat="${p.category}" href="${r}item.html?slug=${encodeURIComponent(p.slug)}">
      <img src="${p.image}" alt="${p.name}">
      <div class="body">
        <h3>${p.name}</h3>
        <p class="dim">${p.dim || p.category_name || ""}</p>
        <p class="price">${money(p.price)} MRP</p>
        ${stock}
        <div class="swatches">${dotsHtml(p.colors)}</div>
        <span class="btn btn-line" style="width:100%;">View Details</span>
      </div>
    </a>`;
}

function renderCart() {
  const box = document.getElementById("cartItems");
  const empty = document.getElementById("cartEmpty");
  const layout = document.getElementById("cartLayout");
  if (!box) return;
  const items = CART.items || [];
  if (!items.length) {
    if (empty) empty.style.display = "block";
    if (layout) layout.style.display = "none";
    return;
  }
  if (empty) empty.style.display = "none";
  if (layout) layout.style.display = "grid";
  box.innerHTML = items.map((x) => `
    <div class="item" data-slug="${x.slug}">
      <img src="${x.img}" alt="${x.name}">
      <div>
        <h3>${x.name}</h3>
        <p class="dim">${x.dim || ""}</p>
        <div class="qty">
          <button type="button" data-minus>-</button>
          <input value="${x.qty}" readonly>
          <button type="button" data-plus>+</button>
        </div>
      </div>
      <div class="rm">
        <b>${money(x.price * x.qty)}</b>
        <button type="button" class="btn btn-line" data-rm style="margin-top:8px;">Remove</button>
      </div>
    </div>`).join("");
  const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
  set("subTotal", money(CART.subtotal));
  set("shipFee", CART.shipping ? money(CART.shipping) : "Free");
  set("grandTotal", money(CART.total));
}

async function setCartQty(slug, qty) {
  if (ME) {
    const data = await apiSend("/api/cart", "PUT", { slug, qty });
    CART = data.cart;
  } else {
    let items = guestCart();
    if (qty < 1) items = items.filter((x) => x.slug !== slug);
    else {
      const it = items.find((x) => x.slug === slug);
      if (it) it.qty = qty;
    }
    saveGuest(items);
    CART = guestSummary();
  }
  paintCount();
  renderCart();
}

function bindCart() {
  const box = document.getElementById("cartItems");
  if (!box) return;
  box.addEventListener("click", async (e) => {
    const row = e.target.closest(".item");
    if (!row) return;
    const it = (CART.items || []).find((x) => x.slug === row.dataset.slug);
    if (!it) return;
    try {
      if (e.target.closest("[data-plus]")) await setCartQty(it.slug, it.qty + 1);
      if (e.target.closest("[data-minus]")) await setCartQty(it.slug, Math.max(1, it.qty - 1));
      if (e.target.closest("[data-rm]")) await setCartQty(it.slug, 0);
    } catch (err) {
      showNote(document.getElementById("cartNote"), err.message);
    }
  });
  const go = document.getElementById("goCheckout");
  go && go.addEventListener("click", (e) => {
    if (!ME) {
      e.preventDefault();
      const root = document.body.dataset.root || "";
      location.href = root + "user/login.html?next=checkout.html";
    }
  });
}

function bindMenu() {
  const burger = document.querySelector(".burger");
  const nav = document.querySelector(".nav");
  const overlay = document.querySelector(".nav-overlay");
  const close = () => {
    nav && nav.classList.remove("open");
    overlay && overlay.classList.remove("show");
    document.body.classList.remove("menu-open");
  };
  burger && burger.addEventListener("click", () => {
    nav && nav.classList.toggle("open");
    overlay && overlay.classList.toggle("show");
    document.body.classList.toggle("menu-open");
  });
  overlay && overlay.addEventListener("click", close);
  const navClose = document.querySelector(".nav-close");
  navClose && navClose.addEventListener("click", close);
  document.querySelectorAll(".has-drop").forEach((item) => {
    const trigger = item.querySelector(":scope > a");
    trigger && trigger.addEventListener("click", (e) => {
      e.preventDefault();
      const wasOpen = item.classList.contains("open");
      document.querySelectorAll(".has-drop").forEach((x) => x.classList.remove("open"));
      if (!wasOpen) item.classList.add("open");
    });
  });
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".has-drop")) {
      document.querySelectorAll(".has-drop").forEach((x) => x.classList.remove("open"));
    }
  });
}

function bindSlider() {
  const slides = document.querySelector(".slides");
  if (!slides) return;
  const n = slides.children.length;
  let i = 0;
  const dots = document.querySelectorAll(".dots button");
  const go = (k) => {
    i = (k + n) % n;
    slides.style.transform = "translateX(-" + i * 100 + "%)";
    dots.forEach((d, idx) => d.classList.toggle("on", idx === i));
  };
  dots.forEach((d, idx) => d.addEventListener("click", () => go(idx)));
  setInterval(() => go(i + 1), 4500);
}

function bindPdp() {
  const add = document.querySelector("[data-add]");
  const buy = document.querySelector("[data-buy]");
  const qty = document.getElementById("qty");
  const id = document.body.dataset.product;
  if (!id && !document.body.dataset.item) return;
  document.querySelectorAll("[data-minus]").forEach((b) => b.addEventListener("click", () => {
    if (qty) qty.value = Math.max(1, Number(qty.value) - 1);
  }));
  document.querySelectorAll("[data-plus]").forEach((b) => b.addEventListener("click", () => {
    if (qty) qty.value = Number(qty.value) + 1;
  }));
  add && add.addEventListener("click", async () => {
    const slug = document.body.dataset.slug || LEGACY[id] || id;
    try {
      await addToCart(slug, qty ? qty.value : 1);
      add.textContent = "Added to cart";
      setTimeout(() => { add.textContent = "Add to Cart"; }, 1200);
    } catch (err) {
      add.textContent = err.message;
      setTimeout(() => { add.textContent = "Add to Cart"; }, 1800);
    }
  });
  buy && buy.addEventListener("click", async () => {
    const slug = document.body.dataset.slug || LEGACY[id] || id;
    try {
      await addToCart(slug, qty ? qty.value : 1);
      location.href = (document.body.dataset.root || "") + "cart.html";
    } catch (err) {
      buy.textContent = err.message;
    }
  });
  const main = document.querySelector(".gallery img.main");
  document.querySelectorAll(".thumbs img").forEach((img) => {
    img.addEventListener("click", () => {
      document.querySelectorAll(".thumbs img").forEach((t) => t.classList.remove("on"));
      img.classList.add("on");
      if (main) main.src = img.src;
    });
  });
}

function showNote(el, msg, ok) {
  if (!el) return;
  el.textContent = msg;
  el.classList.add("show");
  el.classList.toggle("ok", !!ok);
}

function nextAfterLogin() {
  const n = new URLSearchParams(location.search).get("next") || "";
  if (n === "checkout.html" || n === "cart.html") return "../" + n;
  return "account.html";
}

function bindAuth() {
  const tabs = document.querySelectorAll(".toggle button");
  const login = document.getElementById("loginForm");
  const reg = document.getElementById("regForm");
  const note = document.getElementById("authNote");
  const root = document.body.dataset.root || "";
  const box = document.getElementById("accountBox");

  if (box) {
    if (!ME) {
      location.replace(root + "user/login.html");
      return;
    }
    const fill = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
    const val = (id, v) => { const el = document.getElementById(id); if (el) el.value = v || ""; };
    fill("accName", ME.name);
    fill("accEmail", ME.email);
    fill("accPhone", ME.phone || "—");
    val("pfName", ME.name);
    val("pfPhone", ME.phone);
    val("pfAddress", ME.address);
    val("pfCity", ME.city);
    val("pfPin", ME.pincode);
    const out = document.getElementById("logoutBtn");
    out && out.addEventListener("click", async () => {
      await apiSend("/api/auth/logout", "POST", {});
      location.href = root + "user/login.html";
    });
    const pf = document.getElementById("profileForm");
    pf && pf.addEventListener("submit", async (e) => {
      e.preventDefault();
      try {
        const data = await apiSend("/api/auth/profile", "POST", {
          name: document.getElementById("pfName").value.trim(),
          phone: document.getElementById("pfPhone").value.trim(),
          address: document.getElementById("pfAddress").value.trim(),
          city: document.getElementById("pfCity").value.trim(),
          pincode: document.getElementById("pfPin").value.trim()
        });
        ME = data.user;
        fill("accName", ME.name);
        fill("accPhone", ME.phone || "—");
        showNote(document.getElementById("pfNote"), "Saved.", true);
      } catch (err) {
        showNote(document.getElementById("pfNote"), err.message);
      }
    });
    loadOrders();
    return;
  }

  if (login && ME) {
    location.replace(root + "user/" + (new URLSearchParams(location.search).get("next") === "checkout.html" ? "../checkout.html" : "account.html"));
    return;
  }

  tabs.forEach((t) => t.addEventListener("click", () => {
    tabs.forEach((x) => x.classList.remove("on"));
    t.classList.add("on");
    const mode = t.dataset.tab;
    if (login) login.style.display = mode === "login" ? "block" : "none";
    if (reg) reg.style.display = mode === "reg" ? "block" : "none";
    if (note) { note.classList.remove("show"); note.textContent = ""; }
  }));

  login && login.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const data = await apiSend("/api/auth/login", "POST", {
        email: document.getElementById("loginEmail").value.trim().toLowerCase(),
        password: document.getElementById("loginPass").value,
        cart: guestCart()
      });
      saveGuest([]);
      ME = data.user;
      showNote(note, "Logged in. Redirecting...", true);
      setTimeout(() => { location.href = nextAfterLogin(); }, 400);
    } catch (err) {
      showNote(note, err.message);
    }
  });

  reg && reg.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const data = await apiSend("/api/auth/register", "POST", {
        name: document.getElementById("regName").value.trim(),
        email: document.getElementById("regEmail").value.trim().toLowerCase(),
        phone: document.getElementById("regPhone").value.trim(),
        password: document.getElementById("regPass").value
      });
      if (guestCart().length) {
        await apiSend("/api/auth/login", "POST", {
          email: data.user.email,
          password: document.getElementById("regPass").value,
          cart: guestCart()
        });
        saveGuest([]);
      }
      showNote(note, "Account created. Redirecting...", true);
      setTimeout(() => { location.href = nextAfterLogin(); }, 400);
    } catch (err) {
      showNote(note, err.message);
    }
  });
}

async function loadOrders() {
  const box = document.getElementById("orderList");
  if (!box) return;
  try {
    const list = await apiGet("/api/orders");
    if (!list.length) {
      box.innerHTML = '<p class="dim">No orders yet.</p>';
      return;
    }
    const root = document.body.dataset.root || "";
    box.innerHTML = list.map((o) => `
      <a class="order-row" href="${root}order.html?code=${encodeURIComponent(o.code)}">
        <b>${o.code}</b> · ${money(o.total)}
        <div class="dim">${o.status} · ${o.payment_status} · ${(o.created_at || "").slice(0, 10)}</div>
      </a>`).join("");
  } catch (e) {
    box.innerHTML = '<p class="dim">Could not load orders.</p>';
  }
}

function bindPin() {
  const open = document.querySelector("[data-pin]");
  const apply = document.getElementById("pinApply");
  const input = document.getElementById("pinInput");
  const out = document.getElementById("pinOut");
  if (!apply) return;
  apply.addEventListener("click", () => {
    const v = (input && input.value || "").trim();
    if (!/^\d{6}$/.test(v)) {
      if (out) out.textContent = "Enter a valid 6-digit pincode.";
      return;
    }
    if (out) out.textContent = "Deliver to " + v + " — usually 5–7 days.";
    if (open) open.textContent = "Deliver to " + v;
  });
}

function bindSearch() {
  document.querySelectorAll("form.search").forEach((f) => {
    f.addEventListener("submit", (e) => {
      e.preventDefault();
      const root = document.body.dataset.root || "";
      const q = (f.querySelector("input") && f.querySelector("input").value || "").trim();
      location.href = root + "product.html" + (q ? "?q=" + encodeURIComponent(q) : "");
    });
  });
}

function bindCatFilter() {
  const boxes = document.querySelectorAll(".cat-filter");
  const grid = document.querySelector(".prod-grid");
  if (!boxes.length || !grid) return;
  let empty = document.getElementById("catEmpty");
  if (!empty) {
    empty = document.createElement("p");
    empty.id = "catEmpty";
    empty.style.cssText = "grid-column:1/-1;padding:28px 8px;color:var(--mute);";
    empty.textContent = "No products in this category yet.";
    grid.appendChild(empty);
  }
  const fromHash = () => {
    const h = (location.hash || "").replace("#", "");
    if (!h) return;
    boxes.forEach((b) => { b.checked = b.value === h; });
  };
  const apply = () => {
    const cards = document.querySelectorAll(".pcard[data-cat]");
    const on = Array.from(boxes).filter((b) => b.checked).map((b) => b.value);
    let n = 0;
    cards.forEach((c) => {
      const ok = on.includes(c.dataset.cat);
      c.style.display = ok ? "" : "none";
      if (ok) n += 1;
    });
    if (empty) empty.style.display = n ? "none" : "block";
  };
  boxes.forEach((b) => b.addEventListener("change", () => {
    const on = Array.from(boxes).filter((x) => x.checked).map((x) => x.value);
    if (on.length === 1) history.replaceState(null, "", "#" + on[0]);
    else history.replaceState(null, "", location.pathname + location.search);
    apply();
  }));
  fromHash();
  apply();
  window.addEventListener("hashchange", () => { fromHash(); apply(); });
  window.__applyCatFilter = apply;
}

function fillListing() {
  const grid = document.querySelector(".prod-grid");
  if (!grid) return;
  const params = new URLSearchParams(location.search);
  const q = (params.get("q") || "").toLowerCase();
  const list = CATALOGUE.filter((p) => {
    if (!q) return true;
    return (p.name + " " + (p.dim || "") + " " + (p.description || "")).toLowerCase().includes(q);
  });
  grid.innerHTML = list.map((p) => cardHtml(p, "")).join("");
  if (window.__applyCatFilter) window.__applyCatFilter();
  else bindCatFilter();
}

function fillFeatured() {
  const grid = document.getElementById("featuredGrid");
  if (!grid) return;
  grid.innerHTML = CATALOGUE.slice(0, 8).map((p) => cardHtml(p, "")).join("");
}

function fillContactProducts() {
  const sel = document.getElementById("contactProduct");
  if (!sel) return;
  const keep = sel.value;
  const extra = Array.from(sel.querySelectorAll("option[data-static]"));
  sel.innerHTML = '<option value="">Choose a model (optional)</option>';
  CATALOGUE.forEach((p) => {
    const o = document.createElement("option");
    o.value = p.slug;
    o.textContent = p.name + " — " + p.category_name;
    sel.appendChild(o);
  });
  extra.forEach((o) => sel.appendChild(o));
  if (keep) sel.value = keep;
}

function bindContact() {
  const form = document.getElementById("contactForm");
  if (!form) return;
  const ta = form.querySelector("textarea");
  const wc = document.getElementById("wc");
  ta && ta.addEventListener("input", () => {
    const n = ta.value.trim() ? ta.value.trim().split(/\s+/).length : 0;
    if (wc) wc.textContent = n;
  });
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const note = document.getElementById("authNote");
    const slug = (document.getElementById("contactProduct") || {}).value || "";
    const p = findProduct(slug);
    try {
      const data = await apiSend("/api/enquiries", "POST", {
        name: document.getElementById("cName").value.trim(),
        email: document.getElementById("cEmail").value.trim(),
        phone: document.getElementById("cPhone").value.trim(),
        message: document.getElementById("cMsg").value.trim(),
        product_slug: p ? p.slug : "",
        product_name: p ? p.name : slug,
        source: "contact"
      });
      showNote(note, data.message || "Thank you.", true);
      form.reset();
      if (wc) wc.textContent = "0";
    } catch (err) {
      showNote(note, err.message);
    }
  });
}

function pdpHtml(p) {
  const thumbs = (p.thumbs && p.thumbs.length ? p.thumbs : [p.image]).filter(Boolean);
  const specs = p.specs && p.specs.length ? p.specs : [];
  const out = !p.stock;
  return `
    <div class="pdp">
      <div class="gallery">
        <img class="main" src="${p.image}" alt="${p.name}">
        <div class="thumbs">
          ${thumbs.map((t, i) => `<img class="${i===0?"on":""}" src="${t}" alt="">`).join("")}
        </div>
      </div>
      <div class="pdp-info">
        <h1>${p.name}</h1>
        <p class="dim">${p.category_name || ""} · ${p.dim || ""}</p>
        <p class="mrp">${money(p.price)} <small>MRP</small></p>
        <p class="${out ? "stock-out" : "stock-ok"}">${out ? "Out of stock" : "In stock · " + p.stock + " available"}</p>
        <div class="badges">${specs.slice(0,3).map((s) => `<span>${s}</span>`).join("")}<span>Made in India</span></div>
        <div class="swatches">${dotsHtml(p.colors)}</div>
        ${p.description ? `<p class="dim" style="margin:10px 0;">${p.description}</p>` : ""}
        <div class="qty">
          <button type="button" data-minus>-</button>
          <input id="qty" value="1">
          <button type="button" data-plus>+</button>
        </div>
        <div class="actions">
          <button class="btn btn-red" type="button" data-add ${out ? "disabled" : ""}>Add to Cart</button>
          <button class="btn btn-dark" type="button" data-buy ${out ? "disabled" : ""}>Buy Now</button>
        </div>
        <div class="feats">
          <h3>Highlights</h3>
          <ul>${specs.map((s) => `<li>${s}</li>`).join("") || "<li>Made in India</li>"}</ul>
        </div>
        <div class="spec">
          <h3>Specifications</h3>
          <ul>
            <li>Dimensions: ${p.dim || "—"}</li>
            <li>Category: ${p.category_name || p.category}</li>
            <li>Finish: ${(p.colors || []).join(" / ") || "—"}</li>
            <li>Stock: ${p.stock}</li>
          </ul>
        </div>
      </div>
    </div>`;
}

async function fillPdp() {
  const mount = document.getElementById("pdpMount");
  if (!mount) return;
  const params = new URLSearchParams(location.search);
  let slug = params.get("slug") || "";
  if (!slug && document.body.dataset.product) slug = LEGACY[document.body.dataset.product] || document.body.dataset.product;
  let p = findProduct(slug);
  if (!p && slug) {
    try { p = await apiGet("/api/products/" + encodeURIComponent(slug)); } catch (e) { p = null; }
  }
  if (!p) {
    mount.innerHTML = '<p class="dim">Product not found. <a href="product.html">Back to shop</a></p>';
    return;
  }
  document.body.dataset.slug = p.slug;
  document.title = p.name + " | Kanwood Interiors";
  const crumb = document.getElementById("crumbName");
  if (crumb) crumb.textContent = p.name;
  mount.innerHTML = pdpHtml(p);
  bindPdp();
}

function bindCheckout() {
  const form = document.getElementById("checkForm");
  if (!form) return;
  if (!ME) {
    location.replace("user/login.html?next=checkout.html");
    return;
  }
  const items = CART.items || [];
  if (!items.length) {
    location.replace("cart.html");
    return;
  }
  document.getElementById("ckName").value = ME.name || "";
  document.getElementById("ckEmail").value = ME.email || "";
  document.getElementById("ckPhone").value = ME.phone || "";
  document.getElementById("ckAddress").value = ME.address || "";
  document.getElementById("ckCity").value = ME.city || "";
  document.getElementById("ckPin").value = ME.pincode || "";
  document.getElementById("ckItems").innerHTML = items.map((x) =>
    `<div class="sum-row"><span>${x.name} × ${x.qty}</span><b>${money(x.price * x.qty)}</b></div>`
  ).join("");
  document.getElementById("ckSub").textContent = money(CART.subtotal);
  document.getElementById("ckShip").textContent = CART.shipping ? money(CART.shipping) : "Free";
  document.getElementById("ckTotal").textContent = money(CART.total);
  const payInputs = form.querySelectorAll('input[name="pay"]');
  const togglePay = () => {
    const v = (form.querySelector('input[name="pay"]:checked') || {}).value;
    document.getElementById("upiBox").style.display = v === "upi" ? "block" : "none";
    document.getElementById("cardBox").style.display = v === "card" ? "block" : "none";
  };
  payInputs.forEach((i) => i.addEventListener("change", togglePay));
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const note = document.getElementById("ckNote");
    const method = (form.querySelector('input[name="pay"]:checked') || {}).value || "cod";
    try {
      const data = await apiSend("/api/orders", "POST", {
        name: document.getElementById("ckName").value.trim(),
        email: document.getElementById("ckEmail").value.trim(),
        phone: document.getElementById("ckPhone").value.trim(),
        address: document.getElementById("ckAddress").value.trim(),
        city: document.getElementById("ckCity").value.trim(),
        pincode: document.getElementById("ckPin").value.trim(),
        payment_method: method
      });
      let order = data.order;
      if (method === "upi" || method === "card") {
        const pay = await apiSend("/api/orders/" + order.code + "/pay", "POST", {
          upi: document.getElementById("ckUpi").value.trim(),
          card: document.getElementById("ckCard").value.trim()
        });
        order = pay.order;
      }
      location.href = "order.html?code=" + encodeURIComponent(order.code);
    } catch (err) {
      showNote(note, err.message);
    }
  });
}

async function fillOrder() {
  const mount = document.getElementById("orderMount");
  if (!mount) return;
  if (!ME) {
    location.replace("user/login.html");
    return;
  }
  const code = new URLSearchParams(location.search).get("code") || "";
  if (!code) {
    mount.innerHTML = '<p class="dim">Missing order. <a href="user/account.html">Account</a></p>';
    return;
  }
  try {
    const o = await apiGet("/api/orders/" + encodeURIComponent(code));
    document.title = o.code + " | Kanwood Interiors";
    mount.innerHTML = `
      <div class="cart-layout">
        <div class="cart-box">
          <h3>Thank you, ${o.name}</h3>
          <p style="margin:8px 0;">Order <b>${o.code}</b></p>
          <p class="dim">${o.status} · payment ${o.payment_status} · ${o.payment_method}</p>
          <ul class="spec" style="margin-top:12px;">
            ${(o.items || []).map((x) => `<li>${x.name} × ${x.qty} — ${money(x.price * x.qty)}</li>`).join("")}
          </ul>
          <p style="margin-top:12px;">${o.address}${o.city ? ", " + o.city : ""} ${o.pincode || ""}</p>
        </div>
        <aside class="summary">
          <div class="sum-row"><span>Subtotal</span><b>${money(o.subtotal)}</b></div>
          <div class="sum-row"><span>Delivery</span><b>${o.shipping ? money(o.shipping) : "Free"}</b></div>
          <div class="sum-row" style="border-top:1px solid var(--line);padding-top:10px;font-size:16px;"><span>Total</span><b>${money(o.total)}</b></div>
          <a class="btn btn-red" href="product.html" style="width:100%;margin-top:14px;">Continue shopping</a>
        </aside>
      </div>`;
  } catch (e) {
    mount.innerHTML = '<p class="dim">Order not found. <a href="user/account.html">Account</a></p>';
  }
}

function chrome(root, active) {
  const r = root || "";
  const accHref = ME ? r + "user/account.html" : r + "user/login.html";
  const accLabel = ME ? ME.name.split(" ")[0] : "Login";
  return `
  <div class="topbar"><div class="wrap">
    <span>Free delivery on orders ₹25,000+ · 30-day returns</span>
    <span><a href="mailto:kanwoodinteriors@gmail.com">kanwoodinteriors@gmail.com</a> · <a href="tel:+919811167816">+91 98111 67816</a></span>
  </div></div>
  <header class="header">
    <div class="wrap head-row">
      <a class="logo" href="${r}index.html">
        <div class="logo-mark">K</div>
        <div><strong>Kanwood</strong><span>Interiors · Shop</span></div>
      </a>
      <form class="search" action="${r}product.html">
        <input type="search" name="q" placeholder="Search sofa, desk, dining, workstation...">
        <button type="submit">Search</button>
      </form>
      <div class="head-acts">
        <a class="icon" href="${r}product.html"><b>Store</b>Shop</a>
        <a class="icon" href="${accHref}"><b>${accLabel}</b>Account</a>
        <a class="icon" href="${r}cart.html"><b>Cart</b><span>Bag</span><span class="cart-count" data-cart-count>0</span></a>
        <button class="burger" aria-label="Open menu"><span></span><span></span><span></span></button>
      </div>
    </div>
    <nav class="nav"><div class="wrap"><ul>
      <li><a class="${active==="home"?"active":""}" href="${r}index.html">Home</a></li>
      <li class="has-drop">
        <a class="${active==="product"?"active":""}" href="${r}product.html">Product <span class="caret">▾</span></a>
        <ul class="drop">
          <li><a href="${r}product.html">View All</a></li>
          <li><a href="${r}product.html#home">Home Furniture</a></li>
          <li><a href="${r}product.html#office">Office Furniture</a></li>
          <li><a href="${r}product.html#workstation">Workstation</a></li>
          <li><a href="${r}product.html#institutional">Institutional</a></li>
          <li><a href="${r}product.html#patio">Patio Furniture</a></li>
          <li><a href="${r}product.html#restaurant">Restaurant Furniture</a></li>
          <li><a href="${r}product.html#lockers">Storage Lockers</a></li>
          <li><a href="${r}product.html#cabinets">Cabinets &amp; Wardrobes</a></li>
        </ul>
      </li>
      <li><a class="${active==="about"?"active":""}" href="${r}about.html">About Us</a></li>
      <li><a href="${r}about.html#authenticity">Check Authenticity</a></li>
      <li class="has-drop">
        <a class="${["contact","enquiry","service","dealer","stores"].includes(active)?"active":""}" href="${r}contact.html">Contact Us <span class="caret">▾</span></a>
        <ul class="drop">
          <li><a href="${r}contact.html">General Enquiry</a></li>
          <li><a href="${r}contact.html#after-sales">After Sales Service</a></li>
          <li><a href="${r}contact.html#dealer">Dealer &amp; Price</a></li>
          <li><a href="${r}contact.html#distributorship">Distributorship Enquiry</a></li>
          <li><a href="${r}contact.html#outlets">Company Stores</a></li>
          <li><a href="${r}about.html">Careers</a></li>
        </ul>
      </li>
      <li><a class="${active==="cart"?"active":""}" href="${r}cart.html">Wishlist / Cart</a></li>
    </ul></div>
    <button class="nav-close" type="button" aria-label="Close menu">×</button>
    </nav>
  </header>
  <form class="search mob-search" action="${r}product.html">
    <input type="search" name="q" placeholder="Search sofa, desk, dining...">
    <button type="submit">Search</button>
  </form>
  <div class="nav-overlay"></div>`;
}

function foot(root) {
  const r = root || "";
  return `
  <footer class="foot"><div class="wrap">
    <div class="foot-grid">
      <div>
        <h4>Kanwood Interiors</h4>
        <p>Sister company of Bakshi Steel Ind. since 1960. Manufacturer and dealer of office furniture and interiors. Est. 2025.</p>
      </div>
      <div>
        <h4>Company</h4>
        <ul>
          <li><a href="${r}about.html">About Us</a></li>
          <li><a href="${r}contact.html">Contact Us</a></li>
          <li><a href="${r}product.html">Products</a></li>
          <li><a href="${r}about.html#authenticity">Check Authenticity</a></li>
        </ul>
      </div>
      <div>
        <h4>Shop</h4>
        <ul>
          <li><a href="${r}product.html">View All</a></li>
          <li><a href="${r}cart.html">Cart</a></li>
          <li><a href="${r}user/login.html">Login</a></li>
          <li><a href="${r}checkout.html">Checkout</a></li>
        </ul>
      </div>
      <div>
        <h4>Get in touch</h4>
        <ul>
          <li><a href="mailto:kanwoodinteriors@gmail.com">kanwoodinteriors@gmail.com</a></li>
          <li><a href="tel:+919811167816">+91 98111 67816</a></li>
          <li>Bakshi Steel Ind. lineage · India</li>
        </ul>
      </div>
    </div>
    <div class="foot-end"><span>Established 2025 · Bakshi Steel Ind. since 1960</span><span>© 2026 Kanwood Interiors</span></div>
  </div></footer>
  <nav class="mobnav">
    <a class="${document.body.dataset.page==="home"?"active":""}" href="${r}index.html"><b>⌂</b>Home</a>
    <a class="${document.body.dataset.page==="product"?"active":""}" href="${r}product.html"><b>□</b>Shop</a>
    <a class="${document.body.dataset.page==="cart"?"active":""}" href="${r}cart.html"><b>▣</b>Cart</a>
    <a class="${document.body.dataset.page==="login"?"active":""}" href="${r}user/login.html"><b>○</b>Account</a>
    <a class="${document.body.dataset.page==="contact"?"active":""}" href="${r}contact.html"><b>☎</b>Contact</a>
  </nav>`;
}

async function loadCatalogue() {
  try {
    const list = await apiGet("/api/products");
    if (Array.isArray(list) && list.length) CATALOGUE = list;
  } catch (e) {
    CATALOGUE = FALLBACK_PRODUCTS.slice();
  }
}

async function loadMe() {
  try {
    const data = await apiGet("/api/auth/me");
    ME = data.user || null;
  } catch (e) {
    ME = null;
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  const root = document.body.dataset.root || "";
  const page = document.body.dataset.page || "";
  await loadMe();
  await loadCatalogue();
  await refreshCart();
  const mountH = document.getElementById("siteHead");
  const mountF = document.getElementById("siteFoot");
  if (mountH) mountH.outerHTML = chrome(root, page);
  if (mountF) mountF.outerHTML = foot(root);
  paintCount();
  bindMenu();
  bindSlider();
  bindAuth();
  bindPin();
  bindSearch();
  fillFeatured();
  fillListing();
  fillContactProducts();
  bindContact();
  bindCart();
  renderCart();
  bindCheckout();
  await fillPdp();
  await fillOrder();
  if (!document.body.dataset.item) bindPdp();
});
