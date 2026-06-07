"""
SQLite database layer for Family Tree application.
"""
import os
import sqlite3
import sys
import json
from pathlib import Path
from datetime import datetime

# Fix Thai/Unicode output on Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH = Path(os.environ.get("DB_PATH", str(Path(__file__).parent / "family_tree.db")))


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                username     TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                full_name    TEXT NOT NULL,
                role         TEXT NOT NULL DEFAULT 'user' CHECK(role IN ('admin','user')),
                is_active    INTEGER NOT NULL DEFAULT 1,
                last_login   TEXT,
                created_at   TEXT DEFAULT (datetime('now','localtime')),
                created_by   INTEGER REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER REFERENCES users(id),
                username    TEXT,
                action      TEXT NOT NULL,
                table_name  TEXT,
                record_id   INTEGER,
                old_data    TEXT,
                new_data    TEXT,
                ip_address  TEXT,
                timestamp   TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_log(timestamp);
            CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id);

            CREATE TABLE IF NOT EXISTS members (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name  TEXT NOT NULL,
                last_name   TEXT NOT NULL,
                nickname    TEXT,
                gender      TEXT CHECK(gender IN ('ชาย','หญิง','อื่นๆ')),
                birth_date  TEXT,
                death_date  TEXT,
                birth_place TEXT,
                occupation  TEXT,
                notes       TEXT,
                photo_path  TEXT,
                created_at   TEXT DEFAULT (datetime('now','localtime')),
                created_by   INTEGER REFERENCES users(id),
                updated_at   TEXT DEFAULT (datetime('now','localtime')),
                updated_by   INTEGER REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS relationships (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                person1_id  INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
                person2_id  INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
                rel_type    TEXT NOT NULL CHECK(rel_type IN ('spouse','parent-child')),
                -- for parent-child: person1=parent, person2=child
                -- for spouse: bidirectional
                married_date TEXT,
                divorced_date TEXT,
                notes       TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_rel_p1 ON relationships(person1_id);
            CREATE INDEX IF NOT EXISTS idx_rel_p2 ON relationships(person2_id);

            CREATE TABLE IF NOT EXISTS member_names (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id   INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
                lang        TEXT NOT NULL,
                first_name  TEXT,
                last_name   TEXT,
                nickname    TEXT,
                UNIQUE(member_id, lang)
            );

            CREATE INDEX IF NOT EXISTS idx_mnames_mid ON member_names(member_id);
        """)

        # ── migrate: add new columns if they don't exist yet ──────────────────
        _add_col_if_missing(conn, 'members', 'address',  'TEXT')
        _add_col_if_missing(conn, 'members', 'phone',    'TEXT')
        _add_col_if_missing(conn, 'members', 'line_id',  'TEXT')
        _add_col_if_missing(conn, 'members', 'email',    'TEXT')


def _add_col_if_missing(conn, table: str, col: str, col_type: str):
    existing = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    if col not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")


# ─── User Management ─────────────────────────────────────────────────────────

import hashlib, secrets

def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{h}"

def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, h = stored.split(':', 1)
        return hashlib.sha256((salt + password).encode()).hexdigest() == h
    except Exception:
        return False

def create_user(username: str, password: str, full_name: str,
                role: str = 'user', created_by: int = None) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO users (username, password_hash, full_name, role, created_by) VALUES (?,?,?,?,?)",
            (username, _hash_password(password), full_name, role, created_by)
        )
        return cur.lastrowid

def authenticate_user(username: str, password: str):
    """Return user row if credentials valid and active, else None."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username=? AND is_active=1", (username,)
        ).fetchone()
    if row and _verify_password(password, row['password_hash']):
        with get_conn() as conn:
            conn.execute("UPDATE users SET last_login=datetime('now','localtime') WHERE id=?", (row['id'],))
        return row
    return None

def get_user(user_id: int):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()

def list_users():
    with get_conn() as conn:
        return conn.execute(
            "SELECT u.*, c.username AS created_by_name FROM users u "
            "LEFT JOIN users c ON c.id=u.created_by ORDER BY u.id"
        ).fetchall()

def update_user(user_id: int, **kwargs):
    if 'password' in kwargs:
        kwargs['password_hash'] = _hash_password(kwargs.pop('password'))
    sets = ', '.join(f"{k}=?" for k in kwargs)
    with get_conn() as conn:
        conn.execute(f"UPDATE users SET {sets} WHERE id=?", list(kwargs.values()) + [user_id])

def ensure_default_admin():
    """Create default admin account if no users exist."""
    with get_conn() as conn:
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count == 0:
        create_user('admin', 'admin1234', 'ผู้ดูแลระบบ', role='admin')
        print("[OK] สร้าง admin เริ่มต้น: username=admin  password=admin1234")

# ─── Audit Log ────────────────────────────────────────────────────────────────

def write_audit(user_id, username, action, table_name=None, record_id=None,
                old_data=None, new_data=None, ip_address=None):
    old_json = json.dumps(old_data, ensure_ascii=False) if old_data else None
    new_json = json.dumps(new_data, ensure_ascii=False) if new_data else None
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO audit_log (user_id,username,action,table_name,record_id,old_data,new_data,ip_address) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (user_id, username, action, table_name, record_id, old_json, new_json, ip_address)
        )

def list_audit(limit=100):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()

# ─── CRUD ────────────────────────────────────────────────────────────────────

def add_member(**kwargs) -> int:
    cols = [k for k in kwargs if kwargs[k] is not None]
    vals = [kwargs[k] for k in cols]
    sql = f"INSERT INTO members ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
    with get_conn() as conn:
        cur = conn.execute(sql, vals)
        return cur.lastrowid


def update_member(member_id: int, **kwargs):
    kwargs['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sets = ', '.join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [member_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE members SET {sets} WHERE id=?", vals)


def delete_member(member_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM members WHERE id=?", (member_id,))


def get_member(member_id: int):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM members WHERE id=?", (member_id,)).fetchone()


def list_members():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM members ORDER BY id").fetchall()


def add_relationship(person1_id, person2_id, rel_type, **kwargs):
    cols = ['person1_id', 'person2_id', 'rel_type'] + list(kwargs.keys())
    vals = [person1_id, person2_id, rel_type] + list(kwargs.values())
    sql = f"INSERT INTO relationships ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
    with get_conn() as conn:
        cur = conn.execute(sql, vals)
        return cur.lastrowid


def delete_relationship(rel_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM relationships WHERE id=?", (rel_id,))


def get_children(parent_id: int):
    with get_conn() as conn:
        return conn.execute("""
            SELECT m.* FROM members m
            JOIN relationships r ON r.person2_id = m.id
            WHERE r.person1_id=? AND r.rel_type='parent-child'
            ORDER BY m.birth_date, m.id
        """, (parent_id,)).fetchall()


def get_parents(child_id: int):
    with get_conn() as conn:
        return conn.execute("""
            SELECT m.* FROM members m
            JOIN relationships r ON r.person1_id = m.id
            WHERE r.person2_id=? AND r.rel_type='parent-child'
        """, (child_id,)).fetchall()


def get_spouses(member_id: int):
    with get_conn() as conn:
        return conn.execute("""
            SELECT m.*, r.married_date, r.divorced_date FROM members m
            JOIN relationships r ON (
                (r.person1_id=? AND r.person2_id=m.id) OR
                (r.person2_id=? AND r.person1_id=m.id)
            )
            WHERE r.rel_type='spouse'
        """, (member_id, member_id)).fetchall()


def get_roots():
    """
    Return one representative per independent family line.
    A person qualifies if:
      1. They have no recorded parent, AND
      2. None of their spouses have a recorded parent (i.e. not a married-in spouse)
         OR they have children (making them the family's anchor).
    For spouse pairs both qualifying, keep the one with smaller id.
    """
    with get_conn() as conn:
        no_parent_ids = {r['id'] for r in conn.execute("""
            SELECT id FROM members
            WHERE id NOT IN (
                SELECT person2_id FROM relationships WHERE rel_type='parent-child'
            )
        """).fetchall()}

        has_parent_ids = {r['id'] for r in conn.execute("""
            SELECT DISTINCT person2_id AS id FROM relationships WHERE rel_type='parent-child'
        """).fetchall()}

        def spouse_ids(mid):
            return {r[0] for r in conn.execute("""
                SELECT CASE WHEN person1_id=? THEN person2_id ELSE person1_id END
                FROM relationships WHERE rel_type='spouse'
                AND (person1_id=? OR person2_id=?)
            """, (mid, mid, mid)).fetchall()}

        def has_children(mid):
            return conn.execute(
                "SELECT 1 FROM relationships WHERE person1_id=? AND rel_type='parent-child' LIMIT 1",
                (mid,)
            ).fetchone() is not None

        filtered = []
        for rid in sorted(no_parent_ids):
            spouses = spouse_ids(rid)
            if not spouses:
                filtered.append(rid)
                continue
            # If ANY spouse has a parent, this person is "married-in" → skip as root
            if any(s in has_parent_ids for s in spouses):
                continue
            # All spouses also have no parent → deduplicate by keeping smallest id
            if any(s < rid for s in spouses):
                continue
            filtered.append(rid)

        if not filtered:
            return []
        placeholders = ','.join('?' * len(filtered))
        return conn.execute(
            f"SELECT * FROM members WHERE id IN ({placeholders}) ORDER BY birth_date, id",
            filtered
        ).fetchall()


# ─── Multilingual names ───────────────────────────────────────────────────────

def set_member_name(member_id: int, lang: str,
                    first_name: str = None, last_name: str = None,
                    nickname: str = None):
    """Upsert a language variant for a member."""
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO member_names (member_id, lang, first_name, last_name, nickname)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(member_id, lang) DO UPDATE SET
                first_name = excluded.first_name,
                last_name  = excluded.last_name,
                nickname   = excluded.nickname
        """, (member_id, lang, first_name, last_name, nickname))


def delete_member_name(member_id: int, lang: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM member_names WHERE member_id=? AND lang=?",
                     (member_id, lang))


def get_member_names(member_id: int) -> dict:
    """Return {lang: {first_name, last_name, nickname}} for all language variants."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM member_names WHERE member_id=?", (member_id,)
        ).fetchall()
    return {r['lang']: dict(r) for r in rows}


def get_display_name(member: dict, lang: str = 'th') -> dict:
    """
    Return {'first_name', 'last_name', 'nickname'} for the given language.
    Falls back to primary (Thai) if no translation exists.
    `member` can be a DB row dict or a tree node dict that may already contain
    pre-fetched `_names` key from build_tree_lang.
    """
    names = member.get('_names', {})
    variant = names.get(lang)
    if variant and (variant.get('first_name') or variant.get('last_name')):
        return {
            'first_name': variant['first_name'] or member['first_name'],
            'last_name':  variant['last_name']  or member['last_name'],
            'nickname':   variant['nickname']   or member.get('nickname') or '',
        }
    return {
        'first_name': member['first_name'],
        'last_name':  member['last_name'],
        'nickname':   member.get('nickname') or '',
    }


def build_tree(member_id: int, depth=0) -> dict:
    m = get_member(member_id)
    if not m:
        return {}
    node = dict(m)
    node['depth'] = depth
    node['_names'] = get_member_names(member_id)
    spouses_raw = get_spouses(member_id)
    node['spouses'] = []
    for s in spouses_raw:
        sd = dict(s)
        sd['_names'] = get_member_names(s['id'])
        node['spouses'].append(sd)
    node['children'] = [build_tree(c['id'], depth + 1) for c in get_children(member_id)]
    return node


def seed_sample_data(force=False):
    """Insert sample Thai family data for demonstration."""
    with get_conn() as conn:
        count = conn.execute("SELECT COUNT(*) FROM members").fetchone()[0]
    if count > 0 and not force:
        print("[SKIP] มีข้อมูลอยู่แล้ว ใช้ force=True เพื่อรีเซ็ต")
        return
    if force:
        with get_conn() as conn:
            conn.execute("DELETE FROM relationships")
            conn.execute("DELETE FROM members")
            conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('members','relationships')")
    # Generation 1
    g1f = add_member(first_name="สมชาย", last_name="ใจดี", nickname="ปู่", gender="ชาย",
                     birth_date="2480-01-15", death_date="2550-06-20", birth_place="เชียงใหม่",
                     occupation="เกษตรกร")
    g1m = add_member(first_name="สมหญิง", last_name="ใจดี", nickname="ย่า", gender="หญิง",
                     birth_date="2483-03-22", death_date="2555-11-10", birth_place="เชียงใหม่",
                     occupation="แม่บ้าน")
    add_relationship(g1f, g1m, 'spouse', married_date="2503-04-10")

    # Generation 2
    g2s1 = add_member(first_name="วิชัย", last_name="ใจดี", nickname="พ่อ", gender="ชาย",
                      birth_date="2505-07-14", birth_place="เชียงใหม่", occupation="ครู")
    g2s1w = add_member(first_name="สมใจ", last_name="ใจดี", nickname="แม่", gender="หญิง",
                       birth_date="2508-09-01", birth_place="ลำปาง", occupation="พยาบาล")
    add_relationship(g1f, g2s1, 'parent-child')
    add_relationship(g1m, g2s1, 'parent-child')
    add_relationship(g2s1, g2s1w, 'spouse', married_date="2530-02-14")

    g2s2 = add_member(first_name="วิไล", last_name="ใจดี", nickname="อา", gender="หญิง",
                      birth_date="2508-12-05", birth_place="เชียงใหม่", occupation="นักธุรกิจ")
    g2s2h = add_member(first_name="ประสิทธิ์", last_name="มีสุข", nickname="ลุงป้อม", gender="ชาย",
                       birth_date="2505-08-30", birth_place="กรุงเทพฯ", occupation="วิศวกร")
    add_relationship(g1f, g2s2, 'parent-child')
    add_relationship(g1m, g2s2, 'parent-child')
    add_relationship(g2s2, g2s2h, 'spouse', married_date="2532-11-20")

    # Generation 3
    g3c1 = add_member(first_name="ณัฐพล", last_name="ใจดี", nickname="เบส", gender="ชาย",
                      birth_date="2532-05-20", birth_place="เชียงใหม่", occupation="โปรแกรมเมอร์")
    add_relationship(g2s1, g3c1, 'parent-child')
    add_relationship(g2s1w, g3c1, 'parent-child')

    g3c2 = add_member(first_name="สุดา", last_name="ใจดี", nickname="น้องตู่", gender="หญิง",
                      birth_date="2535-08-12", birth_place="เชียงใหม่", occupation="นักออกแบบ")
    add_relationship(g2s1, g3c2, 'parent-child')
    add_relationship(g2s1w, g3c2, 'parent-child')

    g3c3 = add_member(first_name="ปิยะ", last_name="มีสุข", nickname="โบ้", gender="ชาย",
                      birth_date="2533-03-17", birth_place="กรุงเทพฯ", occupation="แพทย์")
    add_relationship(g2s2, g3c3, 'parent-child')
    add_relationship(g2s2h, g3c3, 'parent-child')

    print("[OK] สร้างข้อมูลตัวอย่างเรียบร้อยแล้ว")
