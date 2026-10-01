import json
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
UPLOAD_DIR = ROOT / "uploads"
DB_PATH = DATA_DIR / "kanwood.db"

DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_UPLOAD = 8 * 1024 * 1024
SHIPPING_FREE_ABOVE = 25000
SHIPPING_FEE = 499

CATEGORIES = [
    {"slug": "home", "name": "Home Furniture", "image": "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&w=800&q=80"},
    {"slug": "office", "name": "Office Furniture", "image": "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=800&q=80"},
    {"slug": "workstation", "name": "Workstation", "image": "https://images.unsplash.com/photo-1524758631624-e2822e304c36?auto=format&fit=crop&w=800&q=80"},
    {"slug": "institutional", "name": "Institutional", "image": "https://images.unsplash.com/photo-1497366811353-6870744d04b2?auto=format&fit=crop&w=800&q=80"},
    {"slug": "patio", "name": "Patio Furniture", "image": "https://images.unsplash.com/photo-1600585154340-0ef3c08c08be?auto=format&fit=crop&w=800&q=80"},
    {"slug": "restaurant", "name": "Restaurant Furniture", "image": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80"},
    {"slug": "lockers", "name": "Storage Lockers", "image": "https://images.unsplash.com/photo-1567016546188-7500fe80a8c4?auto=format&fit=crop&w=800&q=80"},
    {"slug": "cabinets", "name": "Cabinets & Wardrobes", "image": "https://images.unsplash.com/photo-1595428774223-ef3341051a51?auto=format&fit=crop&w=800&q=80"},
]

SEED_PRODUCTS = [
    {
        "slug": "heritage-lounge-sofa",
        "name": "Heritage Lounge Sofa",
        "dim": "2100x900x850 mm",
        "price": 48900,
        "stock": 12,
        "category": "home",
        "colors": ["coka", "red", "gold"],
        "image": "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&w=1200&q=80",
        "thumbs": [
            "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?auto=format&fit=crop&w=800&q=80",
        ],
        "specs": ["Solid teak frame", "High-density foam", "Premium fabric upholstery", "Made in India"],
        "description": "Comfort-first lounge sofa for living rooms. Solid teak frame with premium fabric.",
    },
    {
        "slug": "executive-office-desk",
        "name": "Executive Office Desk",
        "dim": "1600x800x750 mm",
        "price": 32400,
        "stock": 18,
        "category": "office",
        "colors": ["coka", "gold"],
        "image": "https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?auto=format&fit=crop&w=1200&q=80",
        "thumbs": [
            "https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1524758631624-e2822e304c36?auto=format&fit=crop&w=800&q=80",
        ],
        "specs": ["Engineered wood + veneer", "Cable management", "Soft-close drawers", "Scratch-resistant top"],
        "description": "Executive desk with cable management and soft-close drawers.",
    },
    {
        "slug": "teak-dining-collection",
        "name": "Teak Dining Collection",
        "dim": "1800x900x760 mm",
        "price": 54200,
        "stock": 8,
        "category": "home",
        "colors": ["coka", "gold", "yellow"],
        "image": "https://images.unsplash.com/photo-1617806118233-18e1de247200?auto=format&fit=crop&w=1200&q=80",
        "thumbs": [
            "https://images.unsplash.com/photo-1617806118233-18e1de247200?auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1600585154340-0ef3c08c08be?auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1506439773649-6e0eb8cfb237?auto=format&fit=crop&w=800&q=80",
        ],
        "specs": ["6-seater teak table", "Cushioned chairs", "Natural wood grain", "Indoor use"],
        "description": "Six-seater teak dining set with cushioned chairs.",
    },
    {
        "slug": "modular-workstation",
        "name": "Modular Workstation",
        "dim": "1200x600x750 mm",
        "price": 18700,
        "stock": 24,
        "category": "workstation",
        "colors": ["coka", "red"],
        "image": "https://images.unsplash.com/photo-1524758631624-e2822e304c36?auto=format&fit=crop&w=1200&q=80",
        "thumbs": [
            "https://images.unsplash.com/photo-1524758631624-e2822e304c36?auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1497366811353-6870744d04b2?auto=format&fit=crop&w=800&q=80",
        ],
        "specs": ["Modular partitions", "Powder-coated steel", "Wire raceway", "Office / institutional"],
        "description": "Modular workstation for offices and institutions.",
    },
]

app = Flask(
    __name__,
    template_folder=str(ROOT / "templates"),
    static_folder=None,
)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "kanwood-interiors-shop-secret")
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASSWORD", "kanwood2025")


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def slugify(text):
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s or ("item-" + uuid.uuid4().hex[:8])


def dumps(val):
    return json.dumps(val if val is not None else [], ensure_ascii=False)


def loads(val, default=None):
    if default is None:
        default = []
    if not val:
        return default
    try:
        return json.loads(val)
    except (TypeError, ValueError):
        return default


def cat_name(slug):
    for c in CATEGORIES:
        if c["slug"] == slug:
            return c["name"]
    return slug or ""


def ensure_column(db, table, column, decl):
    cols = {r["name"] for r in db.execute("PRAGMA table_info(" + table + ")")}
    if column not in cols:
        db.execute("ALTER TABLE " + table + " ADD COLUMN " + column + " " + decl)


def product_public(row):
    thumbs = loads(row["thumbs"])
    image = row["image"] or (thumbs[0] if thumbs else "")
    stock = row["stock"] if "stock" in row.keys() else 0
    return {
        "id": row["id"],
        "slug": row["slug"],
        "name": row["name"],
        "dim": row["dim"] or "",
        "price": row["price"] or 0,
        "stock": stock or 0,
        "in_stock": (stock or 0) > 0,
        "category": row["category"],
        "category_name": cat_name(row["category"]),
        "colors": loads(row["colors"]),
        "image": image,
        "thumbs": thumbs or ([image] if image else []),
        "specs": loads(row["specs"]),
        "description": row["description"] or "",
    }


def customer_public(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "phone": row["phone"] or "",
        "address": row["address"] or "",
        "city": row["city"] or "",
        "pincode": row["pincode"] or "",
    }


def current_customer():
    cid = session.get("customer_id")
    if not cid:
        return None
    return get_db().execute("SELECT * FROM customers WHERE id = ?", (cid,)).fetchone()


def init_db():
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            dim TEXT,
            price INTEGER DEFAULT 0,
            stock INTEGER DEFAULT 0,
            category TEXT NOT NULL,
            colors TEXT,
            image TEXT,
            thumbs TEXT,
            specs TEXT,
            description TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            address TEXT,
            city TEXT,
            pincode TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS cart_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            qty INTEGER NOT NULL DEFAULT 1,
            UNIQUE(customer_id, product_id),
            FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE CASCADE,
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            customer_id INTEGER,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            city TEXT,
            pincode TEXT,
            items TEXT NOT NULL,
            subtotal INTEGER DEFAULT 0,
            shipping INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0,
            payment_method TEXT,
            payment_status TEXT DEFAULT 'pending',
            status TEXT DEFAULT 'placed',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS enquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            product_slug TEXT,
            product_name TEXT,
            qty INTEGER DEFAULT 1,
            items TEXT,
            message TEXT,
            source TEXT,
            status TEXT DEFAULT 'new',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
        """
    )
    ensure_column(db, "products", "stock", "INTEGER DEFAULT 0")
    row = db.execute("SELECT id FROM admin_users WHERE username = ?", (ADMIN_USER,)).fetchone()
    if not row:
        db.execute(
            "INSERT INTO admin_users (username, password_hash) VALUES (?, ?)",
            (ADMIN_USER, generate_password_hash(ADMIN_PASS)),
        )
    count = db.execute("SELECT COUNT(*) AS n FROM products").fetchone()["n"]
    if count == 0:
        for p in SEED_PRODUCTS:
            db.execute(
                """INSERT INTO products
                   (slug, name, dim, price, stock, category, colors, image, thumbs, specs, description, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    p["slug"],
                    p["name"],
                    p["dim"],
                    p["price"],
                    p["stock"],
                    p["category"],
                    dumps(p["colors"]),
                    p["image"],
                    dumps(p["thumbs"]),
                    dumps(p["specs"]),
                    p["description"],
                    now_iso(),
                ),
            )
    db.commit()


def save_upload(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    name = secure_filename(file_storage.filename)
    ext = Path(name).suffix.lower()
    if ext not in ALLOWED_EXT:
        return None
    fname = uuid.uuid4().hex + ext
    dest = UPLOAD_DIR / fname
    file_storage.save(dest)
    return "/uploads/" + fname


def parse_lines(text):
    return [ln.strip() for ln in (text or "").splitlines() if ln.strip()]


def parse_colors(text):
    raw = [c.strip().lower() for c in (text or "").replace(",", " ").split() if c.strip()]
    allowed = {"coka", "red", "gold", "yellow"}
    return [c for c in raw if c in allowed] or ["coka"]


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login", next=request.path))
        return fn(*args, **kwargs)

    return wrapper


def api_customer_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_customer():
            return jsonify({"ok": False, "error": "Please login."}), 401
        return fn(*args, **kwargs)

    return wrapper


def json_body():
    return request.get_json(silent=True) or {}


def valid_email(email):
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or ""))


def shipping_for(subtotal):
    return 0 if subtotal >= SHIPPING_FREE_ABOVE else (SHIPPING_FEE if subtotal else 0)


def cart_payload(customer_id):
    db = get_db()
    rows = db.execute(
        """SELECT c.qty, p.* FROM cart_items c
           JOIN products p ON p.id = c.product_id
           WHERE c.customer_id = ? ORDER BY c.id""",
        (customer_id,),
    ).fetchall()
    items = []
    subtotal = 0
    for r in rows:
        p = product_public(r)
        qty = r["qty"]
        line = qty * p["price"]
        subtotal += line
        items.append({
            "slug": p["slug"],
            "name": p["name"],
            "price": p["price"],
            "img": p["image"],
            "dim": p["dim"],
            "qty": qty,
            "stock": p["stock"],
            "line": line,
        })
    ship = shipping_for(subtotal)
    return {"items": items, "count": sum(x["qty"] for x in items), "subtotal": subtotal, "shipping": ship, "total": subtotal + ship}


def order_public(row):
    return {
        "id": row["id"],
        "code": row["code"],
        "name": row["name"],
        "email": row["email"],
        "phone": row["phone"],
        "address": row["address"],
        "city": row["city"] or "",
        "pincode": row["pincode"] or "",
        "items": loads(row["items"]),
        "subtotal": row["subtotal"],
        "shipping": row["shipping"],
        "total": row["total"],
        "payment_method": row["payment_method"],
        "payment_status": row["payment_status"],
        "status": row["status"],
        "created_at": row["created_at"],
    }


@app.before_request
def _ensure_db():
    init_db()


@app.route("/health")
@app.route("/api/health")
def api_health():
    return jsonify({"ok": True, "app": "kanwood-shop"})


@app.route("/api/categories")
def api_categories():
    db = get_db()
    counts = {
        r["category"]: r["n"]
        for r in db.execute("SELECT category, COUNT(*) AS n FROM products GROUP BY category")
    }
    out = []
    for c in CATEGORIES:
        item = dict(c)
        item["count"] = counts.get(c["slug"], 0)
        out.append(item)
    return jsonify(out)


@app.route("/api/products")
def api_products():
    db = get_db()
    cat = (request.args.get("category") or "").strip()
    q = (request.args.get("q") or "").strip()
    sql = "SELECT * FROM products WHERE 1=1"
    args = []
    if cat:
        sql += " AND category = ?"
        args.append(cat)
    if q:
        sql += " AND (name LIKE ? OR dim LIKE ? OR description LIKE ?)"
        like = "%" + q + "%"
        args.extend([like, like, like])
    sql += " ORDER BY id DESC"
    rows = db.execute(sql, args).fetchall()
    return jsonify([product_public(r) for r in rows])


@app.route("/api/products/<slug>")
def api_product(slug):
    db = get_db()
    row = db.execute("SELECT * FROM products WHERE slug = ?", (slug,)).fetchone()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify(product_public(row))


@app.route("/api/auth/me")
def api_me():
    row = current_customer()
    if not row:
        return jsonify({"user": None})
    return jsonify({"user": customer_public(row)})


@app.route("/api/auth/register", methods=["POST"])
def api_register():
    data = json_body()
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    phone = (data.get("phone") or "").strip()
    password = data.get("password") or ""
    if not name or not email or not password:
        return jsonify({"ok": False, "error": "Name, email and password are required."}), 400
    if not valid_email(email):
        return jsonify({"ok": False, "error": "Enter a valid email."}), 400
    if len(password) < 4:
        return jsonify({"ok": False, "error": "Password must be at least 4 characters."}), 400
    db = get_db()
    if db.execute("SELECT id FROM customers WHERE email = ?", (email,)).fetchone():
        return jsonify({"ok": False, "error": "This email is already registered."}), 400
    db.execute(
        """INSERT INTO customers (name, email, phone, password_hash, address, city, pincode, created_at)
           VALUES (?, ?, ?, ?, '', '', '', ?)""",
        (name, email, phone, generate_password_hash(password), now_iso()),
    )
    db.commit()
    row = db.execute("SELECT * FROM customers WHERE email = ?", (email,)).fetchone()
    session["customer_id"] = row["id"]
    return jsonify({"ok": True, "user": customer_public(row)})


@app.route("/api/auth/login", methods=["POST"])
def api_login():
    data = json_body()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    db = get_db()
    row = db.execute("SELECT * FROM customers WHERE email = ?", (email,)).fetchone()
    if not row or not check_password_hash(row["password_hash"], password):
        return jsonify({"ok": False, "error": "Wrong email or password."}), 400
    session["customer_id"] = row["id"]
    guest = data.get("cart") if isinstance(data.get("cart"), list) else []
    for it in guest:
        slug = (it.get("slug") or "").strip()
        try:
            qty = max(1, int(it.get("qty") or 1))
        except (TypeError, ValueError):
            qty = 1
        prow = db.execute("SELECT * FROM products WHERE slug = ?", (slug,)).fetchone()
        if not prow:
            continue
        existing = db.execute(
            "SELECT qty FROM cart_items WHERE customer_id = ? AND product_id = ?",
            (row["id"], prow["id"]),
        ).fetchone()
        stock = prow["stock"] or 0
        if existing:
            new_qty = min(stock, existing["qty"] + qty) if stock else existing["qty"] + qty
            db.execute(
                "UPDATE cart_items SET qty = ? WHERE customer_id = ? AND product_id = ?",
                (max(1, new_qty), row["id"], prow["id"]),
            )
        else:
            db.execute(
                "INSERT INTO cart_items (customer_id, product_id, qty) VALUES (?, ?, ?)",
                (row["id"], prow["id"], min(qty, stock) if stock else qty),
            )
    db.commit()
    return jsonify({"ok": True, "user": customer_public(row), "cart": cart_payload(row["id"])})


@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    session.pop("customer_id", None)
    return jsonify({"ok": True})


@app.route("/api/auth/profile", methods=["POST"])
@api_customer_required
def api_profile():
    data = json_body()
    me = current_customer()
    name = (data.get("name") or me["name"]).strip()
    phone = (data.get("phone") if data.get("phone") is not None else me["phone"] or "").strip()
    address = (data.get("address") if data.get("address") is not None else me["address"] or "").strip()
    city = (data.get("city") if data.get("city") is not None else me["city"] or "").strip()
    pincode = (data.get("pincode") if data.get("pincode") is not None else me["pincode"] or "").strip()
    db = get_db()
    db.execute(
        "UPDATE customers SET name=?, phone=?, address=?, city=?, pincode=? WHERE id=?",
        (name, phone, address, city, pincode, me["id"]),
    )
    db.commit()
    row = db.execute("SELECT * FROM customers WHERE id = ?", (me["id"],)).fetchone()
    return jsonify({"ok": True, "user": customer_public(row)})


@app.route("/api/cart")
def api_cart_get():
    me = current_customer()
    if not me:
        return jsonify({"items": [], "count": 0, "subtotal": 0, "shipping": 0, "total": 0, "guest": True})
    return jsonify(cart_payload(me["id"]))


@app.route("/api/cart", methods=["POST"])
@api_customer_required
def api_cart_add():
    data = json_body()
    slug = (data.get("slug") or "").strip()
    try:
        qty = max(1, int(data.get("qty") or 1))
    except (TypeError, ValueError):
        qty = 1
    db = get_db()
    me = current_customer()
    prow = db.execute("SELECT * FROM products WHERE slug = ?", (slug,)).fetchone()
    if not prow:
        return jsonify({"ok": False, "error": "Product not found."}), 404
    stock = prow["stock"] or 0
    if stock < 1:
        return jsonify({"ok": False, "error": "Out of stock."}), 400
    existing = db.execute(
        "SELECT qty FROM cart_items WHERE customer_id = ? AND product_id = ?",
        (me["id"], prow["id"]),
    ).fetchone()
    new_qty = (existing["qty"] if existing else 0) + qty
    if new_qty > stock:
        return jsonify({"ok": False, "error": "Only " + str(stock) + " in stock."}), 400
    if existing:
        db.execute(
            "UPDATE cart_items SET qty = ? WHERE customer_id = ? AND product_id = ?",
            (new_qty, me["id"], prow["id"]),
        )
    else:
        db.execute(
            "INSERT INTO cart_items (customer_id, product_id, qty) VALUES (?, ?, ?)",
            (me["id"], prow["id"], new_qty),
        )
    db.commit()
    return jsonify({"ok": True, "cart": cart_payload(me["id"])})


@app.route("/api/cart", methods=["PUT"])
@api_customer_required
def api_cart_update():
    data = json_body()
    slug = (data.get("slug") or "").strip()
    try:
        qty = int(data.get("qty") or 0)
    except (TypeError, ValueError):
        qty = 0
    db = get_db()
    me = current_customer()
    prow = db.execute("SELECT * FROM products WHERE slug = ?", (slug,)).fetchone()
    if not prow:
        return jsonify({"ok": False, "error": "Product not found."}), 404
    if qty < 1:
        db.execute("DELETE FROM cart_items WHERE customer_id = ? AND product_id = ?", (me["id"], prow["id"]))
    else:
        stock = prow["stock"] or 0
        if qty > stock:
            return jsonify({"ok": False, "error": "Only " + str(stock) + " in stock."}), 400
        db.execute(
            """INSERT INTO cart_items (customer_id, product_id, qty) VALUES (?, ?, ?)
               ON CONFLICT(customer_id, product_id) DO UPDATE SET qty=excluded.qty""",
            (me["id"], prow["id"], qty),
        )
    db.commit()
    return jsonify({"ok": True, "cart": cart_payload(me["id"])})


@app.route("/api/enquiries", methods=["POST"])
def api_enquiry():
    data = request.get_json(silent=True) or request.form
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    phone = (data.get("phone") or "").strip()
    message = (data.get("message") or "").strip()
    product_slug = (data.get("product_slug") or data.get("product") or "").strip()
    product_name = (data.get("product_name") or "").strip()
    source = (data.get("source") or "contact").strip()[:40]
    try:
        qty = max(1, int(data.get("qty") or 1))
    except (TypeError, ValueError):
        qty = 1
    items = data.get("items")
    if isinstance(items, str):
        try:
            items = json.loads(items)
        except ValueError:
            items = []
    if not isinstance(items, list):
        items = []
    if not name or not email or not phone:
        return jsonify({"ok": False, "error": "Name, email and phone are required."}), 400
    if not valid_email(email):
        return jsonify({"ok": False, "error": "Enter a valid email."}), 400
    db = get_db()
    if product_slug and not product_name:
        prow = db.execute("SELECT name FROM products WHERE slug = ?", (product_slug,)).fetchone()
        if prow:
            product_name = prow["name"]
    db.execute(
        """INSERT INTO enquiries
           (name, email, phone, product_slug, product_name, qty, items, message, source, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', ?)""",
        (name, email, phone, product_slug, product_name, qty, dumps(items), message, source, now_iso()),
    )
    db.commit()
    return jsonify({"ok": True, "message": "Enquiry received. We will contact you shortly."})


def place_order(me, data):
    db = get_db()
    name = (data.get("name") or (me["name"] if me else "")).strip()
    email = (data.get("email") or (me["email"] if me else "")).strip().lower()
    phone = (data.get("phone") or (me["phone"] if me else "")).strip()
    address = (data.get("address") or "").strip()
    city = (data.get("city") or "").strip()
    pincode = (data.get("pincode") or "").strip()
    method = (data.get("payment_method") or "cod").strip().lower()
    if method not in {"cod", "card", "upi"}:
        method = "cod"
    if not name or not email or not phone or not address:
        return None, "Name, email, phone and address are required."
    if not valid_email(email):
        return None, "Enter a valid email."
    if pincode and not re.match(r"^\d{6}$", pincode):
        return None, "Enter a valid 6-digit pincode."
    cart = cart_payload(me["id"])
    if not cart["items"]:
        return None, "Your cart is empty."
    for it in cart["items"]:
        prow = db.execute("SELECT stock, name FROM products WHERE slug = ?", (it["slug"],)).fetchone()
        if not prow or (prow["stock"] or 0) < it["qty"]:
            return None, (prow["name"] if prow else it["name"]) + " is out of stock."
    code = "KW" + datetime.now(timezone.utc).strftime("%y%m%d") + uuid.uuid4().hex[:6].upper()
    if method == "cod":
        pay_status = "cod"
        status = "placed"
    else:
        pay_status = "pending"
        status = "awaiting_payment"
    db.execute(
        """INSERT INTO orders
           (code, customer_id, name, email, phone, address, city, pincode, items, subtotal, shipping, total,
            payment_method, payment_status, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            code, me["id"], name, email, phone, address, city, pincode, dumps(cart["items"]),
            cart["subtotal"], cart["shipping"], cart["total"], method, pay_status, status, now_iso(),
        ),
    )
    if method == "cod":
        for it in cart["items"]:
            db.execute("UPDATE products SET stock = stock - ? WHERE slug = ? AND stock >= ?", (it["qty"], it["slug"], it["qty"]))
        db.execute("DELETE FROM cart_items WHERE customer_id = ?", (me["id"],))
        db.execute("UPDATE customers SET phone=?, address=?, city=?, pincode=? WHERE id=?", (phone, address, city, pincode, me["id"]))
    db.commit()
    row = db.execute("SELECT * FROM orders WHERE code = ?", (code,)).fetchone()
    return order_public(row), None


@app.route("/api/orders", methods=["POST"])
@api_customer_required
def api_order_create():
    me = current_customer()
    order, err = place_order(me, json_body())
    if err:
        return jsonify({"ok": False, "error": err}), 400
    return jsonify({"ok": True, "order": order})


@app.route("/api/orders")
@api_customer_required
def api_orders():
    me = current_customer()
    rows = get_db().execute(
        "SELECT * FROM orders WHERE customer_id = ? ORDER BY id DESC", (me["id"],)
    ).fetchall()
    return jsonify([order_public(r) for r in rows])


@app.route("/api/orders/<code>")
@api_customer_required
def api_order(code):
    me = current_customer()
    row = get_db().execute(
        "SELECT * FROM orders WHERE code = ? AND customer_id = ?", (code, me["id"])
    ).fetchone()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify(order_public(row))


@app.route("/api/orders/<code>/pay", methods=["POST"])
@api_customer_required
def api_pay(code):
    me = current_customer()
    db = get_db()
    row = db.execute("SELECT * FROM orders WHERE code = ? AND customer_id = ?", (code, me["id"])).fetchone()
    if not row:
        return jsonify({"ok": False, "error": "Order not found."}), 404
    if row["payment_status"] == "paid":
        return jsonify({"ok": True, "order": order_public(row)})
    data = json_body()
    method = row["payment_method"]
    if method == "card":
        card = re.sub(r"\D", "", data.get("card") or "")
        if len(card) < 12:
            return jsonify({"ok": False, "error": "Enter a valid card number (demo)."}), 400
        if card.endswith("0000"):
            return jsonify({"ok": False, "error": "Demo payment declined. Try another card."}), 400
    elif method == "upi":
        upi = (data.get("upi") or "").strip()
        if "@" not in upi:
            return jsonify({"ok": False, "error": "Enter a valid UPI ID (demo)."}), 400
    elif method == "cod":
        return jsonify({"ok": True, "order": order_public(row)})
    items = loads(row["items"])
    for it in items:
        prow = db.execute("SELECT stock, name FROM products WHERE slug = ?", (it.get("slug"),)).fetchone()
        if not prow or (prow["stock"] or 0) < int(it.get("qty") or 1):
            return jsonify({"ok": False, "error": (prow["name"] if prow else "Item") + " is out of stock."}), 400
    for it in items:
        db.execute(
            "UPDATE products SET stock = stock - ? WHERE slug = ? AND stock >= ?",
            (int(it.get("qty") or 1), it.get("slug"), int(it.get("qty") or 1)),
        )
    db.execute(
        "UPDATE orders SET payment_status = 'paid', status = 'paid' WHERE id = ?",
        (row["id"],),
    )
    db.execute("DELETE FROM cart_items WHERE customer_id = ?", (me["id"],))
    db.commit()
    row = db.execute("SELECT * FROM orders WHERE id = ?", (row["id"],)).fetchone()
    return jsonify({"ok": True, "order": order_public(row)})


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin"):
        return redirect(url_for("admin_home"))
    error = ""
    if request.method == "POST":
        user = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        db = get_db()
        row = db.execute("SELECT * FROM admin_users WHERE username = ?", (user,)).fetchone()
        if row and check_password_hash(row["password_hash"], password):
            session["admin"] = row["username"]
            nxt = request.args.get("next") or url_for("admin_home")
            if not str(nxt).startswith("/admin"):
                nxt = url_for("admin_home")
            return redirect(nxt)
        error = "Invalid username or password."
    return render_template("admin/login.html", error=error)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))


@app.route("/admin")
@app.route("/admin/")
@login_required
def admin_home():
    db = get_db()
    stats = {
        "products": db.execute("SELECT COUNT(*) AS n FROM products").fetchone()["n"],
        "orders": db.execute("SELECT COUNT(*) AS n FROM orders").fetchone()["n"],
        "customers": db.execute("SELECT COUNT(*) AS n FROM customers").fetchone()["n"],
        "low": db.execute("SELECT COUNT(*) AS n FROM products WHERE stock < 5").fetchone()["n"],
    }
    recent = db.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 8").fetchall()
    return render_template("admin/dashboard.html", stats=stats, recent=recent)


@app.route("/admin/products")
@login_required
def admin_products():
    db = get_db()
    rows = db.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    products = [product_public(r) for r in rows]
    return render_template("admin/products.html", products=products)


@app.route("/admin/products/new", methods=["GET", "POST"])
@login_required
def admin_product_new():
    if request.method == "POST":
        err = save_product(None)
        if not err:
            flash("Product created.", "ok")
            return redirect(url_for("admin_products"))
        flash(err, "err")
    return render_template("admin/product_form.html", product=None, categories=CATEGORIES, title="Add product")


@app.route("/admin/products/<int:pid>/edit", methods=["GET", "POST"])
@login_required
def admin_product_edit(pid):
    db = get_db()
    row = db.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
    if not row:
        flash("Product not found.", "err")
        return redirect(url_for("admin_products"))
    if request.method == "POST":
        err = save_product(row)
        if not err:
            flash("Product updated.", "ok")
            return redirect(url_for("admin_products"))
        flash(err, "err")
        row = db.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
    product = product_public(row)
    product["specs_text"] = "\n".join(product["specs"])
    product["thumbs_text"] = "\n".join(product["thumbs"])
    product["colors_text"] = " ".join(product["colors"])
    return render_template("admin/product_form.html", product=product, categories=CATEGORIES, title="Edit product")


@app.route("/admin/products/<int:pid>/delete", methods=["POST"])
@login_required
def admin_product_delete(pid):
    db = get_db()
    db.execute("DELETE FROM products WHERE id = ?", (pid,))
    db.commit()
    flash("Product deleted.", "ok")
    return redirect(url_for("admin_products"))


def unique_slug(db, base, pid=None):
    slug = slugify(base)
    i = 2
    while True:
        row = db.execute("SELECT id FROM products WHERE slug = ?", (slug,)).fetchone()
        if not row or (pid and row["id"] == pid):
            return slug
        slug = slugify(base) + "-" + str(i)
        i += 1


def save_product(existing):
    name = (request.form.get("name") or "").strip()
    if not name:
        return "Name is required."
    category = (request.form.get("category") or "").strip()
    if category not in {c["slug"] for c in CATEGORIES}:
        return "Choose a valid category."
    try:
        price = max(0, int(request.form.get("price") or 0))
    except (TypeError, ValueError):
        return "Price must be a number."
    try:
        stock = max(0, int(request.form.get("stock") or 0))
    except (TypeError, ValueError):
        return "Stock must be a number."
    dim = (request.form.get("dim") or "").strip()
    description = (request.form.get("description") or "").strip()
    specs = parse_lines(request.form.get("specs"))
    colors = parse_colors(request.form.get("colors"))
    image_url = (request.form.get("image") or "").strip()
    thumbs = parse_lines(request.form.get("thumbs"))
    uploaded = save_upload(request.files.get("photo"))
    extra_urls = []
    for f in request.files.getlist("photos"):
        u = save_upload(f)
        if u:
            extra_urls.append(u)
    if uploaded:
        image_url = uploaded
        thumbs = [uploaded] + [t for t in thumbs if t != uploaded]
    if extra_urls:
        thumbs = thumbs + extra_urls
    if not image_url and thumbs:
        image_url = thumbs[0]
    if image_url and image_url not in thumbs:
        thumbs = [image_url] + thumbs
    db = get_db()
    slug_in = (request.form.get("slug") or "").strip() or name
    slug = unique_slug(db, slug_in, existing["id"] if existing else None)
    if existing:
        db.execute(
            """UPDATE products SET slug=?, name=?, dim=?, price=?, stock=?, category=?, colors=?,
               image=?, thumbs=?, specs=?, description=? WHERE id=?""",
            (slug, name, dim, price, stock, category, dumps(colors), image_url, dumps(thumbs), dumps(specs), description, existing["id"]),
        )
    else:
        db.execute(
            """INSERT INTO products
               (slug, name, dim, price, stock, category, colors, image, thumbs, specs, description, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (slug, name, dim, price, stock, category, dumps(colors), image_url, dumps(thumbs), dumps(specs), description, now_iso()),
        )
    db.commit()
    return None


@app.route("/admin/orders")
@login_required
def admin_orders():
    db = get_db()
    status = (request.args.get("status") or "").strip()
    sql = "SELECT * FROM orders"
    args = []
    if status:
        sql += " WHERE status = ?"
        args.append(status)
    sql += " ORDER BY id DESC"
    rows = db.execute(sql, args).fetchall()
    orders = []
    for r in rows:
        d = dict(r)
        d["items_list"] = loads(r["items"])
        orders.append(d)
    return render_template("admin/orders.html", orders=orders, status=status)


@app.route("/admin/orders/<int:oid>/status", methods=["POST"])
@login_required
def admin_order_status(oid):
    status = (request.form.get("status") or "placed").strip()
    if status not in {"placed", "awaiting_payment", "paid", "packed", "shipped", "delivered", "cancelled"}:
        status = "placed"
    db = get_db()
    db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, oid))
    db.commit()
    flash("Order updated.", "ok")
    return redirect(url_for("admin_orders"))


@app.route("/admin/enquiries")
@login_required
def admin_enquiries():
    db = get_db()
    status = (request.args.get("status") or "").strip()
    sql = "SELECT * FROM enquiries"
    args = []
    if status:
        sql += " WHERE status = ?"
        args.append(status)
    sql += " ORDER BY id DESC"
    rows = db.execute(sql, args).fetchall()
    items = []
    for r in rows:
        d = dict(r)
        d["items_list"] = loads(r["items"])
        items.append(d)
    return render_template("admin/enquiries.html", enquiries=items, status=status)


@app.route("/admin/enquiries/<int:eid>/status", methods=["POST"])
@login_required
def admin_enquiry_status(eid):
    status = (request.form.get("status") or "new").strip()
    if status not in {"new", "contacted", "closed"}:
        status = "new"
    db = get_db()
    db.execute("UPDATE enquiries SET status = ? WHERE id = ?", (status, eid))
    db.commit()
    flash("Enquiry updated.", "ok")
    return redirect(url_for("admin_enquiries"))


@app.route("/admin/categories")
@login_required
def admin_categories():
    db = get_db()
    counts = {
        r["category"]: r["n"]
        for r in db.execute("SELECT category, COUNT(*) AS n FROM products GROUP BY category")
    }
    cats = []
    for c in CATEGORIES:
        item = dict(c)
        item["count"] = counts.get(c["slug"], 0)
        cats.append(item)
    return render_template("admin/categories.html", categories=cats)


SKIP_STATIC = {"api", "admin", "uploads", "templates", "data", "__pycache__"}
SKIP_FILES = {"app.py", "requirements.txt", ".gitignore", "start.sh"}


@app.route("/product/<slug>.html")
def legacy_pdp(slug):
    return redirect("/item.html?slug=" + slug)


@app.route("/")
def serve_index():
    return send_from_directory(ROOT, "index.html")


@app.route("/<path:path>")
def serve_static(path):
    first = path.split("/", 1)[0]
    name = Path(path).name
    if first in SKIP_STATIC or name in SKIP_FILES:
        return jsonify({"error": "Not found"}), 404
    try:
        target = (ROOT / path).resolve()
        target.relative_to(ROOT)
    except ValueError:
        return jsonify({"error": "Not found"}), 404
    if target.is_file():
        return send_from_directory(ROOT, path)
    if (target / "index.html").is_file():
        return send_from_directory(target, "index.html")
    return ("Not found", 404)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
