"""
Family Tree — Web UI
Run: python web_ui.py  →  http://localhost:8888

Roles
  admin : full CRUD on members, relationships, users; view audit log
  user  : read-only (tree + member list)
"""
import cgi
import json
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

import database as db
from database import (
    init_db, ensure_default_admin,
    add_member, update_member, delete_member, get_member, list_members,
    add_relationship, delete_relationship, get_roots, build_tree,
    get_children, get_spouses, get_parents, get_conn,
    create_user, update_user, list_users, get_user,
    authenticate_user, write_audit, list_audit,
)
from export_excel import export_excel
from date_utils import (display_date, display_year,
                        date_field_html, parse_date_from_form)
from tree_render import render_tree_page
from database import (set_member_name, get_member_names, get_display_name,
                      delete_member_name)
from i18n import (t, LANGUAGES, DEFAULT_LANG, get_lang_from_request,
                  set_lang_cookie, format_date, format_year_only)
from photo_utils import (save_photo, delete_photo, validate_path,
                         PhotoError, PHOTO_DIR, photo_url)
import auth

import os as _os
PORT = int(_os.environ.get("PORT", 8888))

# ─── Shared HTML pieces ──────────────────────────────────────────────────────

CSS = """
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Family Tree</title>
<link href="https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
/* ── Themes (CSS variables) ───────────────────────────────────────────────── */
:root {
  --green:#2D6A4F; --green-dark:#1A472A; --green-mid:#40916C;
  --green-light:#D8F3DC; --accent:#52B788;
  --red:#E74C3C; --yellow:#F39C12; --blue:#2980B9;
  --bg:#ffffff; --card:#ffffff; --border:#D5E8DC;
  --text:#1a1a2e; --muted:#6c757d;
  --nav-bg:#1A472A; --nav-link:#B7E4C7;
  --node-bg:#fff; --node-border:#40916C;
  --bg-pattern: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%2340916C' fill-opacity='0.04'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
}
body.theme-ocean {
  --green:#1A6B8A; --green-dark:#0D4F6C; --green-mid:#2980B9;
  --green-light:#D6EAF8; --accent:#5DADE2;
  --border:#BEE3F8; --nav-bg:#0D4F6C; --nav-link:#A9D6E5;
  --node-border:#2980B9;
  --bg-pattern: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none'%3E%3Cg fill='%232980B9' fill-opacity='0.04'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
}
body.theme-sunset {
  --green:#8B4513; --green-dark:#5D3A1A; --green-mid:#CA6F1E;
  --green-light:#FDEBD0; --accent:#E59866;
  --border:#F5CBA7; --nav-bg:#5D3A1A; --nav-link:#F5CBA7;
  --node-border:#CA6F1E;
  --bg-pattern: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none'%3E%3Cg fill='%23CA6F1E' fill-opacity='0.04'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
}
body.theme-classic {
  --green:#555; --green-dark:#333; --green-mid:#777;
  --green-light:#F0F0F0; --accent:#888;
  --border:#DDD; --nav-bg:#333; --nav-link:#CCC;
  --node-border:#777;
  --bg-pattern: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none'%3E%3Cg fill='%23777' fill-opacity='0.04'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
}

*{box-sizing:border-box;margin:0;padding:0}
body {
  font-family:'Sarabun',sans-serif;
  background-color:#fff;
  background-image: var(--bg-pattern);
  color:var(--text);font-size:15px;min-height:100vh;
}

/* ── Navbar ── */
.navbar{background:var(--nav-bg);color:#fff;padding:0 24px;display:flex;align-items:center;
        gap:4px;height:56px;position:sticky;top:0;z-index:100;box-shadow:0 2px 8px #0003}
.navbar .brand{font-size:20px;font-weight:700;color:#fff;margin-right:16px;text-decoration:none;white-space:nowrap}
.navbar a{color:var(--nav-link);text-decoration:none;padding:6px 12px;border-radius:6px;font-size:14px;
          transition:.15s;white-space:nowrap}
.navbar a:hover{background:rgba(255,255,255,.15);color:#fff}
.navbar .spacer{flex:1}
.navbar .user-badge{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--nav-link)}
.navbar .user-badge .role{background:rgba(255,255,255,.2);padding:2px 8px;border-radius:10px;
                          font-size:11px;font-weight:600;letter-spacing:.5px}
.navbar .user-badge .role.admin{background:#E74C3C}

/* ── Layout ── */
.container{max-width:1280px;margin:0 auto;padding:28px 20px}
.page-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:24px;flex-wrap:wrap;gap:12px}
.page-title{font-size:22px;font-weight:700;color:var(--green-dark)}
.page-title span{font-size:26px;margin-right:8px}

/* ── Cards ── */
.card{background:var(--card);border-radius:14px;box-shadow:0 2px 16px #0001;
      border:1px solid var(--border);padding:24px;margin-bottom:20px}
.card-title{font-size:16px;font-weight:700;color:var(--green-dark);margin-bottom:16px;
            padding-bottom:10px;border-bottom:2px solid var(--green-light)}

/* ── Buttons ── */
.btn{display:inline-flex;align-items:center;gap:6px;padding:8px 18px;border-radius:8px;
     border:none;cursor:pointer;font-size:14px;font-family:inherit;text-decoration:none;
     font-weight:600;transition:.15s;white-space:nowrap}
.btn:hover{filter:brightness(.9);transform:translateY(-1px)}
.btn:active{transform:translateY(0)}
.btn-primary{background:var(--green);color:#fff}
.btn-danger{background:var(--red);color:#fff}
.btn-warning{background:var(--yellow);color:#fff}
.btn-info{background:var(--blue);color:#fff}
.btn-gray{background:#ecf0f1;color:#333;border:1px solid #ddd}
.btn-sm{padding:5px 12px;font-size:13px;border-radius:6px}
.btn-icon{padding:6px 10px}

/* ── Tables ── */
.table-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:14px}
th{background:var(--green-dark);color:#fff;padding:10px 14px;text-align:left;
   font-weight:600;font-size:13px;white-space:nowrap}
th:first-child{border-radius:6px 0 0 0}th:last-child{border-radius:0 6px 0 0}
td{padding:9px 14px;border-bottom:1px solid #eef3f0;vertical-align:middle}
tr:hover td{background:var(--green-light,#F4FBF7);opacity:.7}
tr:last-child td{border-bottom:none}
.td-actions{display:flex;gap:6px;flex-wrap:wrap}

/* ── Forms ── */
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.form-grid-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px}
.field{display:flex;flex-direction:column;gap:4px}
.field label{font-size:13px;font-weight:600;color:var(--muted)}
input[type=text],input[type=password],input[type=date],select,textarea{
  width:100%;padding:9px 12px;border:1px solid #ccd6ce;border-radius:8px;
  font-size:14px;font-family:inherit;background:#fff;color:var(--text);
  transition:.15s;outline:none}
input:focus,select:focus,textarea:focus{border-color:var(--accent);
  box-shadow:0 0 0 3px rgba(82,183,136,.15)}
input.error,select.error,textarea.error{border-color:var(--red)}
.field-hint{font-size:12px;color:var(--muted);margin-top:2px}
.form-footer{display:flex;gap:10px;margin-top:20px;flex-wrap:wrap}

/* ── Alerts ── */
.alert{padding:12px 18px;border-radius:8px;margin-bottom:16px;
       display:flex;align-items:center;gap:10px;font-size:14px}
.alert-success{background:#D4EDDA;color:#155724;border:1px solid #C3E6CB}
.alert-error{background:#F8D7DA;color:#721C24;border:1px solid #F5C6CB}
.alert-warning{background:#FFF3CD;color:#856404;border:1px solid #FFEEBA}
.alert-info{background:#D1ECF1;color:#0C5460;border:1px solid #BEE5EB}
.alert-icon{font-size:18px;flex-shrink:0}

/* ── Badges ── */
.badge{display:inline-block;padding:3px 10px;border-radius:10px;font-size:12px;font-weight:600}
.badge-admin{background:#FADBD8;color:#922B21}
.badge-user{background:#D5E8F8;color:#1A5276}
.badge-active{background:#D4EFDF;color:#1D6A39}
.badge-inactive{background:#EAECEE;color:#566573}
.badge-male{background:#D6EAF8;color:#1A5276}
.badge-female{background:#FDEDEC;color:#922B21}

/* ── Error pages ── */
.error-page{display:flex;flex-direction:column;align-items:center;
            justify-content:center;min-height:60vh;text-align:center;padding:40px}
.error-code{font-size:96px;font-weight:700;color:var(--green-light);line-height:1}
.error-title{font-size:28px;font-weight:700;color:var(--green-dark);margin:12px 0 8px}
.error-msg{color:var(--muted);font-size:16px;margin-bottom:24px}

/* ── Login ── */
.login-wrap{display:flex;align-items:center;justify-content:center;min-height:90vh}
.login-card{background:#fff;border-radius:16px;padding:40px 36px;width:380px;
            box-shadow:0 8px 40px #0002;border:1px solid var(--border)}
.login-logo{text-align:center;font-size:48px;margin-bottom:8px}
.login-title{text-align:center;font-size:22px;font-weight:700;color:var(--green-dark);margin-bottom:4px}
.login-sub{text-align:center;font-size:14px;color:var(--muted);margin-bottom:24px}

/* ── Audit ── */
.audit-action{font-size:12px;padding:2px 8px;border-radius:4px;font-weight:600}
.audit-CREATE{background:#D4EDDA;color:#155724}
.audit-UPDATE{background:#FFF3CD;color:#856404}
.audit-DELETE{background:#F8D7DA;color:#721C24}
.audit-LOGIN{background:#D1ECF1;color:#0C5460}
.audit-LOGOUT,.audit-DEACTIVATE,.audit-ACTIVATE{background:#EAECEE;color:#566573}
.audit-EXPORT{background:#E8DAEF;color:#6C3483}
.audit-CHANGE_PASSWORD{background:#FEF9E7;color:#7D6608}

/* ── Divider ── */
.divider{border:none;border-top:1px solid var(--border);margin:20px 0}

/* ── Confirm modal ── */
.modal-backdrop{display:none;position:fixed;inset:0;background:#0005;z-index:200;
                align-items:center;justify-content:center}
.modal-backdrop.show{display:flex}
.modal{background:#fff;border-radius:14px;padding:28px 32px;max-width:420px;width:90%;
       box-shadow:0 8px 40px #0004}
.modal h3{margin-bottom:10px;font-size:18px;color:var(--green-dark)}
.modal p{color:var(--muted);margin-bottom:20px;font-size:14px;line-height:1.6}
.modal-actions{display:flex;gap:10px;justify-content:flex-end}

/* ── Theme switcher ── */
.theme-switcher{position:fixed;bottom:20px;right:20px;z-index:150}
.theme-btn{width:40px;height:40px;border-radius:50%;border:3px solid #fff;
           cursor:pointer;box-shadow:0 2px 10px #0003;transition:.2s}
.theme-btn:hover{transform:scale(1.15)}
.theme-panel{display:none;position:absolute;bottom:50px;right:0;
             background:#fff;border-radius:12px;padding:14px;
             box-shadow:0 4px 24px #0002;border:1px solid var(--border);
             min-width:180px}
.theme-panel.open{display:block}
.theme-option{display:flex;align-items:center;gap:10px;padding:8px 10px;
              border-radius:8px;cursor:pointer;font-size:13px;font-weight:600;
              transition:.15s;border:none;background:none;width:100%;text-align:left}
.theme-option:hover{background:var(--green-light)}
.theme-dot{width:18px;height:18px;border-radius:50%;border:2px solid #fff;
           box-shadow:0 1px 4px #0003;flex-shrink:0}

@media(max-width:640px){
  .form-grid,.form-grid-3{grid-template-columns:1fr}
  .navbar a .label{display:none}
  .page-header{flex-direction:column;align-items:flex-start}
}
</style>
<script>
function confirmDelete(msg, url) {
  document.getElementById('confirm-msg').textContent = msg;
  document.getElementById('confirm-btn').href = url;
  document.getElementById('confirm-modal').classList.add('show');
}
function closeModal(){document.getElementById('confirm-modal').classList.remove('show')}

// Theme switcher
(function(){
  var themes = [
    {id:'',      label:'ธรรมชาติ', color:'#1A472A'},
    {id:'ocean', label:'ท้องทะเล', color:'#0D4F6C'},
    {id:'sunset',label:'พระอาทิตย์ตก', color:'#5D3A1A'},
    {id:'classic',label:'คลาสสิก', color:'#333'},
  ];
  function applyTheme(id){
    document.body.className = id ? 'theme-'+id : '';
    localStorage.setItem('ft_theme', id);
  }
  document.addEventListener('DOMContentLoaded', function(){
    var saved = localStorage.getItem('ft_theme') || '';
    applyTheme(saved);
    var panel = document.getElementById('theme-panel');
    var btn   = document.getElementById('theme-main-btn');
    if (!panel || !btn) return;
    btn.onclick = function(e){ e.stopPropagation(); panel.classList.toggle('open'); };
    document.addEventListener('click', function(){ panel.classList.remove('open'); });
    themes.forEach(function(t){
      var opt = document.createElement('button');
      opt.className = 'theme-option';
      opt.innerHTML = '<span class="theme-dot" style="background:'+t.color+'"></span>'+t.label;
      opt.onclick = function(e){ e.stopPropagation(); applyTheme(t.id); panel.classList.remove('open'); };
      panel.appendChild(opt);
    });
  });
})();
</script>
"""

CONFIRM_MODAL = """
<div class="modal-backdrop" id="confirm-modal" onclick="if(event.target===this)closeModal()">
  <div class="modal">
    <h3>ยืนยันการลบ</h3>
    <p id="confirm-msg">คุณต้องการลบรายการนี้ใช่หรือไม่? การกระทำนี้ไม่สามารถย้อนกลับได้</p>
    <div class="modal-actions">
      <button class="btn btn-gray" onclick="closeModal()">ยกเลิก</button>
      <a id="confirm-btn" href="#" class="btn btn-danger">ลบ</a>
    </div>
  </div>
</div>
<div class="theme-switcher">
  <div class="theme-panel" id="theme-panel"></div>
  <button class="theme-btn" id="theme-main-btn"
          style="background:var(--green-dark)" title="เปลี่ยนธีม">🎨</button>
</div>
"""


def navbar(user, lang='th'):
    if not user:
        return f'<nav class="navbar"><a class="brand" href="/">🌳 Family Tree</a></nav>'
    role_badge = (f'<span class="role admin">ADMIN</span>'
                  if user['role'] == 'admin' else '<span class="role">USER</span>')
    admin_links = ""
    if user['role'] == 'admin':
        admin_links = f"""
          <a href="/users"><span>👥</span> <span class="label">{t('nav_users',lang)}</span></a>
          <a href="/audit"><span>📋</span> <span class="label">{t('nav_audit',lang)}</span></a>
        """
    # Language switcher pills
    pill_parts = []
    for code, info in LANGUAGES.items():
        bg = "rgba(255,255,255,.3)" if code == lang else "rgba(255,255,255,.1)"
        lbl = info['label']
        flag = info['flag']
        # next="" tells set-lang to use Referer header (stay on current page)
        pill_parts.append(
            f'<a href="/set-lang?lang={code}" '
            f'style="text-decoration:none;padding:3px 8px;border-radius:12px;font-size:12px;'
            f'font-weight:600;background:{bg};color:#fff;white-space:nowrap" title="{lbl}">'
            f'{flag}</a>'
        )
    lang_pills = ''.join(pill_parts)
    return f"""
    <nav class="navbar">
      <a class="brand" href="/tree">🌳</a>
      <a href="/tree"><span>🌲</span> <span class="label">{t('nav_tree',lang)}</span></a>
      <a href="/members"><span>👤</span> <span class="label">{t('nav_members',lang)}</span></a>
      <a href="/relations"><span>🔗</span> <span class="label">{t('nav_relations',lang)}</span></a>
      <a href="/export"><span>📊</span> <span class="label">{t('nav_export',lang)}</span></a>
      {admin_links}
      <div class="spacer"></div>
      <div style="display:flex;align-items:center;gap:4px;margin-right:8px">{lang_pills}</div>
      <div class="user-badge">
        <span>👤 {user['full_name']}</span>{role_badge}
        <a href="/logout" class="btn btn-gray btn-sm">{t('btn_logout',lang)}</a>
      </div>
    </nav>"""


def layout(title, body, user=None, alert=None, alert_type="success", lang='th'):
    alert_html = ""
    if alert:
        icons = {"success": "✅", "error": "❌", "warning": "⚠️", "info": "ℹ️"}
        alert_html = f'<div class="alert alert-{alert_type}"><span class="alert-icon">{icons.get(alert_type,"ℹ️")}</span>{alert}</div>'
    html_lang = {'th': 'th', 'en': 'en', 'zh': 'zh-Hans'}.get(lang, 'th')
    return f"""<!DOCTYPE html><html lang="{html_lang}"><head>{CSS}</head><body>
{navbar(user, lang)}
<div class="container">
{alert_html}
{body}
</div>
{CONFIRM_MODAL}
</body></html>"""


def error_page(code, title, message, user=None, lang='th'):
    emojis = {400: "😕", 403: "🚫", 404: "🔍", 500: "💥"}
    home_label = {'th': '🏠 กลับหน้าหลัก', 'en': '🏠 Back to Home', 'zh': '🏠 返回首页'}.get(lang, '🏠 Home')
    body = f"""<div class="error-page">
      <div class="error-code">{emojis.get(code,'⚠️')}</div>
      <div class="error-code" style="font-size:64px;color:var(--green-mid)">{code}</div>
      <div class="error-title">{title}</div>
      <div class="error-msg">{message}</div>
      <a href="/tree" class="btn btn-primary">{home_label}</a>
    </div>"""
    return layout(f"Error {code}", body, user, lang=lang)


ERROR_PAGES = {
    400: {
        'th': ("คำขอไม่ถูกต้อง", "ข้อมูลที่ส่งมาไม่ครบถ้วนหรือไม่ถูกต้อง"),
        'en': ("Bad Request", "The data submitted was incomplete or invalid."),
        'zh': ("请求错误", "提交的数据不完整或无效。"),
    },
    403: {
        'th': ("ไม่มีสิทธิ์เข้าถึง", "คุณไม่มีสิทธิ์เข้าถึงหน้านี้ กรุณาติดต่อผู้ดูแลระบบ"),
        'en': ("Access Denied", "You don't have permission to access this page."),
        'zh': ("访问被拒绝", "您没有权限访问此页面。"),
    },
    404: {
        'th': ("ไม่พบหน้าที่ต้องการ", "หน้าที่คุณกำลังมองหาไม่มีอยู่หรืออาจถูกย้ายไปแล้ว"),
        'en': ("Page Not Found", "The page you're looking for doesn't exist or has been moved."),
        'zh': ("页面未找到", "您正在寻找的页面不存在或已被移动。"),
    },
    500: {
        'th': ("เกิดข้อผิดพลาดภายใน", "เซิร์ฟเวอร์พบข้อผิดพลาด กรุณาลองใหม่อีกครั้ง"),
        'en': ("Internal Server Error", "The server encountered an error. Please try again."),
        'zh': ("服务器内部错误", "服务器遇到错误，请重试。"),
    },
}


def render_tree_node(node, is_admin_user=False):
    gen_cls = f"gen{min(node['depth'], 7)}"
    icon = "♂" if node.get('gender') == 'ชาย' else ("♀" if node.get('gender') == 'หญิง' else "·")
    name = f"{node['first_name']} {node['last_name']}"
    nick = f" <small>({node['nickname']})</small>" if node.get('nickname') else ""
    spouses = ", ".join(
        f"{s['first_name']} {s['last_name']}" + (f" ({s['nickname']})" if s.get('nickname') else "")
        for s in node.get('spouses', [])
    )
    spouse_html = f'<span class="spouse">💑 {spouses}</span>' if spouses else ""
    birth = (node.get('birth_date') or '')[:4]
    death = (node.get('death_date') or '')[:4]
    year = f'<span class="meta">[{birth}{" – "+death if death else ""}]</span>' if birth else ""
    occ = f'<span class="meta">• {node["occupation"]}</span>' if node.get('occupation') else ""
    indent = node['depth'] * 32

    edit_btn = ""
    if is_admin_user:
        edit_btn = f'<div class="actions"><a href="/members/edit?id={node["id"]}" class="btn btn-warning btn-sm btn-icon">✏️</a></div>'

    html = f'<div style="margin-left:{indent}px">'
    html += f'<div class="tree-node {gen_cls}">'
    html += f'<span>{icon}</span>'
    html += f'<a href="/members/view?id={node["id"]}" class="name-link">{name}</a>{nick}'
    html += spouse_html + year + occ + edit_btn
    html += '</div></div>'
    for child in node.get('children', []):
        html += render_tree_node(child, is_admin_user)
    return html


# ─── Request Handler ──────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # suppress default Apache-style logs

    def log_error(self, fmt, *args):
        pass

    # ── Response helpers ──────────────────────────────────────────────────────

    def send_html(self, html, code=200, extra_headers=None):
        data = html.encode('utf-8')
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, url, headers=None):
        self.send_response(302)
        self.send_header("Location", url)
        if headers:
            for k, v in headers.items():
                self.send_header(k, v)
        self.end_headers()

    def send_error_page(self, code, detail=None, user=None, lang=None):
        if lang is None:
            lang = get_lang_from_request(self)
        pages = ERROR_PAGES.get(code, {})
        title, msg = pages.get(lang, pages.get('th', ("Error", "An error occurred.")))
        if detail:
            msg = detail
        html = error_page(code, title, msg, user, lang=lang)
        self.send_html(html, code)

    def parse_qs(self, raw):
        return {k: v[0] for k, v in urllib.parse.parse_qs(raw or "").items()}

    def read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        return self.rfile.read(length).decode('utf-8', errors='replace')

    def get_ip(self):
        return self.client_address[0]

    # ── Routing ───────────────────────────────────────────────────────────────

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip('/') or '/'
        qs = self.parse_qs(parsed.query)
        user = auth.current_user(self)
        lang = get_lang_from_request(self)

        try:
            routes = {
                '/':           lambda: self.redirect('/tree'),
                '/set-lang':   lambda: self.page_set_lang(qs),
                '/photos':     lambda: self.page_photo(parsed.path),
                '/tree':       lambda: self.page_tree(qs, user, lang),
                '/members':    lambda: self.page_members(qs, user, lang),
                '/members/view': lambda: self.page_member_view(qs, user, lang),
                '/members/add':  lambda: self.page_member_form(qs, user, mode='add', lang=lang),
                '/members/edit': lambda: self.page_member_form(qs, user, mode='edit', lang=lang),
                '/members/delete': lambda: self.page_member_delete(qs, user),
                '/relations':    lambda: self.page_relations(qs, user, lang),
                '/relations/delete': lambda: self.page_relation_delete(qs, user),
                '/export':       lambda: self.page_export(qs, user, lang),
                '/users':        lambda: self.page_users(qs, user, lang),
                '/users/add':    lambda: self.page_user_form(qs, user, mode='add', lang=lang),
                '/users/edit':   lambda: self.page_user_form(qs, user, mode='edit', lang=lang),
                '/users/toggle': lambda: self.page_user_toggle(qs, user),
                '/audit':        lambda: self.page_audit(qs, user, lang),
                '/login':        lambda: self.page_login(qs, user, lang),
                '/logout':       lambda: self.page_logout(user),
            }
            handler = routes.get(path)
            if handler:
                handler()
            elif path.startswith('/photos/'):
                self.page_photo(path)
            else:
                self.send_error_page(404, user=user)
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(f"[ERROR] {path}: {e}\n{tb}")
            self.send_error_page(500,
                detail=f"รายละเอียด: {type(e).__name__}: {e}",
                user=user)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip('/') or '/'
        user = auth.current_user(self)
        # Detect multipart (file upload) vs regular form
        ct = self.headers.get('Content-Type', '')
        if 'multipart/form-data' in ct:
            data, files = self._parse_multipart()
        else:
            data = self.parse_qs(self.read_body())
            files = {}

        lang = get_lang_from_request(self)
        try:
            routes = {
                '/login':       lambda: self.post_login(data),
                '/members/add':  lambda: self.post_member_form(data, user, mode='add', lang=lang, files=files),
                '/members/edit': lambda: self.post_member_form(data, user, mode='edit', lang=lang, files=files),
                '/relations/add': lambda: self.post_relation_add(data, user),
                '/users/add':    lambda: self.post_user_form(data, user, mode='add', lang=lang),
                '/users/edit':   lambda: self.post_user_form(data, user, mode='edit', lang=lang),
                '/users/change-password': lambda: self.post_change_password(data, user),
            }
            handler = routes.get(path)
            if handler:
                handler()
            else:
                self.send_error_page(404, user=user)
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(f"[ERROR POST] {path}: {e}\n{tb}")
            self.send_error_page(500,
                detail=f"รายละเอียด: {type(e).__name__}: {e}",
                user=user)

    # ── Photo serving ─────────────────────────────────────────────────────────

    def page_photo(self, path: str):
        """Serve a photo file from the photos directory."""
        filename = path.split('/')[-1]
        photo_path = validate_path(filename)
        if not photo_path:
            self.send_response(404)
            self.end_headers()
            return
        ext = photo_path.suffix.lower().lstrip('.')
        mime = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
                'png': 'image/png', 'bmp': 'image/bmp'}.get(ext, 'image/jpeg')
        data = photo_path.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'max-age=86400')
        self.end_headers()
        self.wfile.write(data)

    # ── Multipart parser ──────────────────────────────────────────────────────

    def _parse_multipart(self) -> tuple[dict, dict]:
        """Parse multipart/form-data. Returns (fields, files)."""
        import cgi as _cgi
        environ = {
            'REQUEST_METHOD': 'POST',
            'CONTENT_TYPE': self.headers.get('Content-Type', ''),
            'CONTENT_LENGTH': self.headers.get('Content-Length', '0'),
        }
        try:
            form = _cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ=environ,
                keep_blank_values=True,
            )
        except Exception:
            return {}, {}

        fields = {}
        files  = {}
        for key in form.keys():
            item = form[key]
            if hasattr(item, 'filename') and item.filename:
                files[key] = {
                    'filename': item.filename,
                    'data':     item.file.read(),
                    'mime':     item.type or '',
                }
            else:
                fields[key] = item.value if hasattr(item, 'value') else str(item)
        return fields, files

    # ── Language switcher ─────────────────────────────────────────────────────

    def page_set_lang(self, qs):
        lang = qs.get('lang', DEFAULT_LANG)
        if lang not in LANGUAGES:
            lang = DEFAULT_LANG
        # Stay on current page using Referer header
        referer = self.headers.get('Referer', '')
        if referer:
            parsed = urllib.parse.urlparse(referer)
            next_url = parsed.path or '/tree'
            if parsed.query:
                next_url += '?' + parsed.query
        else:
            next_url = qs.get('next') or '/tree'
        self.send_response(302)
        self.send_header('Location', next_url)
        self.send_header('Set-Cookie', set_lang_cookie(lang))
        self.end_headers()

    # ── Login / Logout ────────────────────────────────────────────────────────

    def page_login(self, qs, user, lang='th'):
        if user:
            return self.redirect('/tree')
        next_url = qs.get('next', '/tree')
        err = qs.get('err', '')
        alert = ""
        if err == '1':
            alert = f'<div class="alert alert-error"><span class="alert-icon">❌</span>{t("login_err",lang)}</div>'
        elif err == '2':
            alert = f'<div class="alert alert-warning"><span class="alert-icon">⚠️</span>{t("login_inactive",lang)}</div>'

        # Language pills for login page
        lang_pills = ' '.join(
            f'<a href="/set-lang?lang={code}&next=/login" '
            f'style="text-decoration:none;padding:4px 10px;border-radius:12px;font-size:13px;font-weight:600;'
            f'background:{"#2D6A4F" if code==lang else "#eee"};color:{"#fff" if code==lang else "#555"}">'
            f'{info["flag"]} {info["label"]}</a>'
            for code, info in LANGUAGES.items()
        )
        html_lang = {'th':'th','en':'en','zh':'zh-Hans'}.get(lang,'th')
        html = f"""<!DOCTYPE html><html lang="{html_lang}"><head>{CSS}</head>
        <body style="background:var(--nav-bg)">
        <div class="login-wrap">
          <div class="login-card">
            <div class="login-logo">🌳</div>
            <div class="login-title">{t('login_title',lang)}</div>
            <div class="login-sub">{t('login_sub',lang)}</div>
            <div style="display:flex;gap:6px;justify-content:center;margin-bottom:18px;flex-wrap:wrap">
              {lang_pills}
            </div>
            {alert}
            <form method="POST" action="/login">
              <input type="hidden" name="next" value="{next_url}">
              <div class="field" style="margin-bottom:14px">
                <label>{t('login_username',lang)}</label>
                <input type="text" name="username" autofocus placeholder="username" required>
              </div>
              <div class="field" style="margin-bottom:20px">
                <label>{t('login_password',lang)}</label>
                <input type="password" name="password" placeholder="••••••••" required>
              </div>
              <button type="submit" class="btn btn-primary"
                      style="width:100%;justify-content:center;padding:11px">
                🔑 {t('login_btn',lang)}
              </button>
            </form>
          </div>
        </div></body></html>"""
        self.send_html(html)

    def post_login(self, data):
        username = data.get('username', '').strip()
        password = data.get('password', '')
        next_url = data.get('next', '/tree')

        row = authenticate_user(username, password)
        if row is None:
            # Check if user exists but inactive
            with get_conn() as conn:
                exists = conn.execute(
                    "SELECT is_active FROM users WHERE username=?", (username,)
                ).fetchone()
            err = '2' if exists and not exists['is_active'] else '1'
            return self.redirect(f"/login?err={err}&next={urllib.parse.quote(next_url)}")

        token = auth.create_session(row)
        write_audit(row['id'], row['username'], 'LOGIN', ip_address=self.get_ip())
        cookie = f"ft_session={token}; Path=/; HttpOnly; Max-Age={auth.SESSION_TTL}"
        self.send_response(302)
        self.send_header("Location", next_url)
        self.send_header("Set-Cookie", cookie)
        self.end_headers()

    def page_logout(self, user):
        token = auth.get_token_from_request(self)
        if user:
            write_audit(user['user_id'], user['username'], 'LOGOUT', ip_address=self.get_ip())
        auth.destroy_session(token)
        self.send_response(302)
        self.send_header("Location", "/login")
        self.send_header("Set-Cookie", f"ft_session=; Path=/; HttpOnly; Max-Age=0")
        self.end_headers()

    # ── Tree ─────────────────────────────────────────────────────────────────

    def page_tree(self, qs, user, lang='th'):
        if not (user := auth.require_login(self)): return
        is_adm = user['role'] == 'admin'
        tree_html = render_tree_page(is_adm, lang)
        add_btn = f'<a href="/members/add" class="btn btn-primary">➕ {t("tree_add",lang)}</a>' if is_adm else ""
        body = f"""
        <div class="page-header">
          <div class="page-title"><span>🌳</span>{t('tree_title',lang)}</div>
          {add_btn}
        </div>
        <div class="card" style="padding:20px;overflow:hidden">{tree_html}</div>"""
        self.send_html(layout(t('nav_tree',lang), body, user, lang=lang))

    # ── Members list ──────────────────────────────────────────────────────────

    def page_members(self, qs, user, lang='th'):
        if not (user := auth.require_login(self)): return
        is_adm = user['role'] == 'admin'
        members = list_members()

        rows = ""
        for m in members:
            md = dict(m)
            md['_names'] = get_member_names(m['id'])
            dn = get_display_name(md, lang)
            display_fn = dn['first_name']
            display_ln = dn['last_name']
            display_nick = dn['nickname']

            gender_val = m['gender'] or ''
            gender_badge = f'<span class="badge badge-{"male" if gender_val=="ชาย" else "female"}">{gender_val}</span>' if gender_val else ""
            lifespan = format_year_only(m['birth_date'] or '', lang)
            death_y = format_year_only(m['death_date'] or '', lang)
            if lifespan and death_y:
                lifespan += f' – {death_y}'
            elif death_y:
                lifespan = f'– {death_y}'

            # updater info
            if m['updated_by']:
                upd_user = get_user(m['updated_by'])
                upd_name = upd_user['full_name'] if upd_user else '?'
            else:
                upd_name = '-'
            upd_time = (m['updated_at'] or '')[:16]

            action_btns = ""
            if is_adm:
                action_btns = f"""
                  <a href="/members/edit?id={m['id']}" class="btn btn-warning btn-sm">✏️ แก้ไข</a>
                  <a href="#" class="btn btn-danger btn-sm"
                     onclick="confirmDelete('ลบ {m['first_name']} {m['last_name']}?','/members/delete?id={m['id']}');return false">
                     🗑️
                  </a>"""

            # Show Thai name as subtitle if current lang is different
            alt_name = ''
            if lang != 'th' and (display_fn != m['first_name'] or display_ln != m['last_name']):
                alt_name = f'<br><small style="color:var(--muted);font-size:11px">{m["first_name"]} {m["last_name"]}</small>'

            rows += f"""<tr>
              <td style="color:var(--muted);font-size:13px">#{m['id']}</td>
              <td>
                <a href="/members/view?id={m['id']}" style="font-weight:600;color:var(--green-dark)">
                  {display_fn} {display_ln}
                </a>
                {'<br><small style="color:var(--muted)">'+display_nick+'</small>' if display_nick else ''}
                {alt_name}
              </td>
              <td>{gender_badge}</td>
              <td style="font-size:13px">{lifespan or '-'}</td>
              <td style="font-size:13px">{m['birth_place'] or '-'}</td>
              <td style="font-size:13px">{m['occupation'] or '-'}</td>
              <td style="font-size:12px;color:var(--muted)">{upd_name}<br>{upd_time}</td>
              <td><div class="td-actions">{action_btns}
                <a href="/members/view?id={m['id']}" class="btn btn-info btn-sm">👁 {t('btn_view',lang)}</a>
              </div></td>
            </tr>"""

        add_btn = f'<a href="/members/add" class="btn btn-primary">➕ {t("tree_add",lang)}</a>' if is_adm else ""
        count_label = {'th': f'{len(members)} คน', 'en': f'{len(members)} people', 'zh': f'{len(members)} 人'}.get(lang, str(len(members)))
        body = f"""
        <div class="page-header">
          <div class="page-title"><span>👤</span>{t('members_title',lang)}
            <span style="font-size:15px;font-weight:400;color:var(--muted)">({count_label})</span>
          </div>
          {add_btn}
        </div>
        <div class="card">
          <div class="table-wrap">
            <table>
              <tr><th>ID</th><th>{t('col_name',lang)}</th><th>{t('col_gender',lang)}</th>
                  <th>{t('col_lifespan',lang)}</th><th>{t('col_birthplace',lang)}</th>
                  <th>{t('col_occupation',lang)}</th><th>{t('col_updated',lang)}</th><th></th></tr>
              {rows}
            </table>
          </div>
        </div>"""
        self.send_html(layout(t('nav_members',lang), body, user, lang=lang))

    # ── Member view ───────────────────────────────────────────────────────────

    def page_member_view(self, qs, user, lang='th'):
        if not (user := auth.require_login(self)): return
        mid = int(qs.get('id', 0))
        m = get_member(mid)
        if not m:
            return self.send_error_page(404, t('err_not_found', lang), user=user, lang=lang)

        parents   = get_parents(mid)
        spouses   = get_spouses(mid)
        children  = get_children(mid)
        is_adm = user['role'] == 'admin'
        all_names = get_member_names(mid)
        md = dict(m)
        md['_names'] = all_names
        dn = get_display_name(md, lang)

        def person_link(p):
            pd = dict(p)
            pd['_names'] = get_member_names(p['id'])
            pdn = get_display_name(pd, lang)
            return (f'<a href="/members/view?id={p["id"]}" style="color:var(--green)">'
                    f'{pdn["first_name"]} {pdn["last_name"]}</a>')

        created_by_user = get_user(m['created_by']) if m['created_by'] else None
        updated_by_user = get_user(m['updated_by']) if m['updated_by'] else None

        rows_info = [
            (t('col_gender',lang),      m['gender'] or '-'),
            (t('field_birthdate',lang),  format_date(m['birth_date'] or '', lang) or '-'),
            (t('field_deathdate',lang),  format_date(m['death_date'] or '', lang) or '-'),
            (t('field_birthplace',lang), m['birth_place'] or '-'),
            (t('field_address',lang),    m['address']     or '-'),
            (t('field_occupation',lang), m['occupation']  or '-'),
            (t('field_phone',lang),      m['phone']       or '-'),
            (t('field_line_id',lang),    m['line_id']     or '-'),
            (t('field_email',lang),      m['email']       or '-'),
            (t('field_notes',lang),      m['notes']       or '-'),
        ]

        # Multilingual names display
        lang_names_rows = ''
        for lcode, linfo in LANGUAGES.items():
            if lcode == 'th':
                fn, ln, nn = m['first_name'], m['last_name'], m['nickname'] or ''
            else:
                v = all_names.get(lcode, {})
                fn = v.get('first_name') or ''
                ln = v.get('last_name') or ''
                nn = v.get('nickname') or ''
            if fn or ln:
                nick_html = f'<small style="color:var(--muted)"> ({nn})</small>' if nn else ''
                lang_names_rows += (
                    f'<tr><td style="font-size:12px;color:var(--muted);width:100px">'
                    f'{linfo["flag"]} {linfo["label"]}</td>'
                    f'<td style="font-size:13px">{fn} {ln}{nick_html}</td></tr>'
                )
        info_html = "".join(f"""
          <tr><td style="font-weight:600;color:var(--muted);white-space:nowrap;width:160px;font-size:13px">{k}</td>
          <td style="font-size:14px">{v}</td></tr>""" for k, v in rows_info)

        audit_rows = ""
        with get_conn() as conn:
            logs = conn.execute(
                "SELECT * FROM audit_log WHERE table_name='members' AND record_id=? ORDER BY timestamp DESC LIMIT 20",
                (mid,)
            ).fetchall()
        for lg in logs:
            action_cls = f"audit-{lg['action']}"
            audit_rows += f"""<tr>
              <td style="font-size:12px">{lg['timestamp']}</td>
              <td><span class="audit-action {action_cls}">{lg['action']}</span></td>
              <td style="font-size:13px">{lg['username'] or '-'}</td>
            </tr>"""
        audit_section = f"""
          <div class="card-title">📋 ประวัติการแก้ไข</div>
          {'<table><tr><th>เวลา</th><th>การกระทำ</th><th>โดย</th></tr>'+audit_rows+'</table>' if audit_rows else '<p style="color:var(--muted);font-size:14px">ยังไม่มีประวัติ</p>'}
        """ if is_adm else ""

        edit_btn = f'<a href="/members/edit?id={mid}" class="btn btn-warning">✏️ {t("btn_edit",lang)}</a>' if is_adm else ""
        del_name = f"{dn['first_name']} {dn['last_name']}"
        del_btn = (f'<a href="#" class="btn btn-danger"'
                   f' onclick="confirmDelete(\'{del_name}?\','
                   f'\'/members/delete?id={mid}\');return false">'
                   f'🗑️ {t("btn_delete",lang)}</a>') if is_adm else ""

        # Photo for view page
        photo_html = ''
        if m['photo_path']:
            photo_html = (f'<div style="margin-bottom:16px;text-align:center">'
                          f'<img src="/photos/{m["photo_path"]}" alt="photo"'
                          f' style="width:120px;height:160px;object-fit:cover;'
                          f'border-radius:12px;border:3px solid var(--border);'
                          f'box-shadow:0 4px 16px #0002;display:inline-block">'
                          f'</div>')

        body = f"""
        <div class="page-header">
          <div class="page-title"><span>👤</span>{dn['first_name']} {dn['last_name']}
            {' <small style="font-size:15px;color:var(--muted)">(' + dn["nickname"] + ')</small>' if dn.get('nickname') else ''}
          </div>
          <div style="display:flex;gap:8px">{edit_btn}{del_btn}
            <a href="/members" class="btn btn-gray">{t('btn_back',lang)}</a></div>
        </div>
        <div style="display:grid;grid-template-columns:2fr 1fr;gap:20px">
          <div>
            <div class="card">
              <div class="card-title">{t('page_view_member',lang)}</div>
              {photo_html}
              <table>{info_html}</table>
            </div>
            <div class="card">
              <div class="card-title">{t('field_names_section',lang)}</div>
              <table>{lang_names_rows or '<tr><td colspan="2" style="color:var(--muted);font-size:13px">-</td></tr>'}</table>
            </div>
            <div class="card">
              <div class="card-title">{t('rel_parents',lang)} / {t('rel_spouse',lang)} / {t('rel_children',lang)}</div>
              <table>
                <tr><td style="font-weight:600;color:var(--muted);font-size:13px;width:140px">{t('rel_parents',lang)}</td>
                    <td>{', '.join(person_link(p) for p in parents) or '-'}</td></tr>
                <tr><td style="font-weight:600;color:var(--muted);font-size:13px">{t('rel_spouse',lang)}</td>
                    <td>{', '.join(person_link(s) for s in spouses) or '-'}</td></tr>
                <tr><td style="font-weight:600;color:var(--muted);font-size:13px">{t('rel_children',lang)}</td>
                    <td>{', '.join(person_link(c) for c in children) or '-'}</td></tr>
              </table>
              {('<a href="/relations" class="btn btn-primary btn-sm" style="margin-top:14px">➕</a>' if is_adm else '')}
            </div>
          </div>
          <div>
            <div class="card">
              <div class="card-title">{t('sys_info',lang)}</div>
              <table>
                <tr><td style="font-size:12px;color:var(--muted)">ID</td><td style="font-size:13px">#{m['id']}</td></tr>
                <tr><td style="font-size:12px;color:var(--muted)">{t('created_by',lang)}</td>
                    <td style="font-size:13px">{(m['created_at'] or '')[:16]}<br>
                    <small>{created_by_user['full_name'] if created_by_user else '-'}</small></td></tr>
                <tr><td style="font-size:12px;color:var(--muted)">{t('updated_by',lang)}</td>
                    <td style="font-size:13px">{(m['updated_at'] or '')[:16]}<br>
                    <small>{updated_by_user['full_name'] if updated_by_user else '-'}</small></td></tr>
              </table>
            </div>
            {('<div class="card">'+audit_section+'</div>') if is_adm else ''}
          </div>
        </div>"""
        self.send_html(layout(f"{dn['first_name']} {dn['last_name']}", body, user, lang=lang))

    # ── Member Add / Edit form ────────────────────────────────────────────────

    def _member_form_html(self, m=None, errors=None, prefill=None, lang='th'):
        """Render add/edit member form HTML."""
        errors = errors or {}
        d = prefill or (dict(m) if m else {})
        v = lambda f: d.get(f) or ''
        sel = lambda f, opts: "".join(
            f'<option value="{o}" {"selected" if v(f)==o else ""}>{o}</option>'
            for o in opts
        )
        err = lambda f: f'<div style="color:var(--red);font-size:12px;margin-top:3px">{errors[f]}</div>' if f in errors else ''

        # date fields — use stored values from DB or prefill
        birth_stored = d.get('birth_date') or ''
        death_stored = d.get('death_date') or ''

        # If prefill from POST, reconstruct from _cal/_year fields
        if prefill:
            from date_utils import parse_date_from_form
            b = parse_date_from_form(prefill, 'birth_date')
            if b is not None:
                birth_stored = b
            dd = parse_date_from_form(prefill, 'death_date')
            if dd is not None:
                death_stored = dd

        # Multilingual name fields (for languages other than Thai primary)
        other_langs = {lc: li for lc, li in LANGUAGES.items() if lc != 'th'}
        lang_name_fields = ''
        for lcode, linfo in other_langs.items():
            # Get existing values from member_names or prefill
            if prefill:
                ln_fn = prefill.get(f'name_{lcode}_first', '')
                ln_ln = prefill.get(f'name_{lcode}_last', '')
                ln_nn = prefill.get(f'name_{lcode}_nick', '')
            elif m:
                existing = get_member_names(m['id']).get(lcode, {})
                ln_fn = existing.get('first_name') or ''
                ln_ln = existing.get('last_name') or ''
                ln_nn = existing.get('nickname') or ''
            else:
                ln_fn = ln_ln = ln_nn = ''

            # placeholder hints per language
            hints = {
                'en': ('e.g. John', 'e.g. Smith', 'e.g. Johnny'),
                'zh': ('例：伟', '例：王', '例：小王'),
            }
            ph = hints.get(lcode, ('', '', ''))

            lang_name_fields += f"""
            <div style="background:#F8FAF9;border:1px solid var(--border);border-radius:10px;
                        padding:16px;margin-top:12px">
              <div style="font-size:13px;font-weight:700;color:var(--green-dark);margin-bottom:12px">
                {linfo['flag']} {linfo['label']}
              </div>
              <div class="form-grid">
                <div class="field">
                  <label>{t('field_firstname',lcode)}</label>
                  <input type="text" name="name_{lcode}_first" value="{ln_fn}" placeholder="{ph[0]}">
                </div>
                <div class="field">
                  <label>{t('field_lastname',lcode)}</label>
                  <input type="text" name="name_{lcode}_last" value="{ln_ln}" placeholder="{ph[1]}">
                </div>
                <div class="field">
                  <label>{t('field_nickname',lcode)}</label>
                  <input type="text" name="name_{lcode}_nick" value="{ln_nn}" placeholder="{ph[2]}">
                </div>
              </div>
            </div>"""

        # ── Photo section ──────────────────────────────────────────────────────
        photo_labels = {
            'th': ('รูปภาพ', 'รูปถ่ายครึ่งตัวบน ลักษณะเดียวกับบัตรประชาชน/พาสปอร์ต',
                   'รองรับ JPG, PNG, BMP ขนาดไม่เกิน 10 MB', 'เลือกรูปภาพ', 'ลบรูปภาพ'),
            'en': ('Photo', 'Half-body portrait, passport/ID-card style',
                   'JPG, PNG or BMP – max 10 MB', 'Choose Photo', 'Remove Photo'),
            'zh': ('照片', '半身证件照（护照/身份证风格）',
                   '支持 JPG、PNG、BMP，最大 10 MB', '选择照片', '删除照片'),
        }
        pl = photo_labels.get(lang, photo_labels['en'])
        current_photo = d.get('photo_path') or ''
        photo_preview = ''
        delete_checkbox = ''
        if current_photo:
            photo_preview = (f'<div style="margin-bottom:10px">'
                             f'<img src="/photos/{current_photo}" alt="photo"'
                             f' style="width:90px;height:120px;object-fit:cover;border-radius:8px;'
                             f'border:2px solid var(--border);display:block;margin-bottom:6px">'
                             f'<label style="font-size:12px;color:var(--red);cursor:pointer;display:flex;align-items:center;gap:4px">'
                             f'<input type="checkbox" name="delete_photo" value="1"> {pl[4]}</label>'
                             f'</div>')

        photo_section = f"""
        <hr class="divider" style="margin-top:20px">
        <div class="card-title" style="margin:16px 0 8px">📷 {pl[0]}</div>
        <div style="display:flex;gap:20px;align-items:flex-start;flex-wrap:wrap">
          {photo_preview}
          <div style="flex:1;min-width:220px">
            <div class="field">
              <label>{pl[0]}</label>
              <input type="file" name="photo" accept=".jpg,.jpeg,.png,.bmp,image/*"
                     style="padding:6px;font-size:13px"
                     onchange="previewPhoto(this)">
              <div class="field-hint">💡 {pl[1]}<br>{pl[2]}</div>
            </div>
            <div id="photo-preview-new" style="margin-top:10px"></div>
          </div>
          <div style="flex-shrink:0;background:#FFF9EC;border:1px dashed #F39C12;
                      border-radius:10px;padding:12px 16px;max-width:220px;font-size:12px;
                      color:#7D4E00;line-height:1.7">
            <b>{'แนะนำ' if lang=='th' else ('Recommended' if lang=='en' else '推荐')}:</b><br>
            {'📐 รูปสัดส่วน 3:4 (กว้าง:สูง)' if lang=='th' else ('📐 3:4 portrait ratio' if lang=='en' else '📐 3:4 竖向比例')}<br>
            {'👤 หน้าตรง เห็นใบหน้าชัดเจน' if lang=='th' else ('👤 Face forward, clearly visible' if lang=='en' else '👤 正面，面部清晰')}<br>
            {'✂️ ระบบจะตัดรูปอัตโนมัติ' if lang=='th' else ('✂️ Auto-cropped to portrait' if lang=='en' else '✂️ 自动裁剪为证件照')}
          </div>
        </div>
        <script>
        function previewPhoto(input) {{
          var div = document.getElementById('photo-preview-new');
          if (input.files && input.files[0]) {{
            var r = new FileReader();
            r.onload = function(e) {{
              div.innerHTML = '<img src="'+e.target.result+'"'
                + ' style="width:90px;height:120px;object-fit:cover;border-radius:8px;'
                + 'border:2px solid var(--accent)">';
            }};
            r.readAsDataURL(input.files[0]);
          }}
        }}
        </script>"""

        return f"""
        <div class="card-title" style="margin-bottom:12px">
          {LANGUAGES['th']['flag']} {LANGUAGES['th']['label']} <small style="font-weight:400;color:var(--muted)">(ชื่อหลัก)</small>
        </div>
        <div class="form-grid">
          <div class="field">
            <label>{t('field_firstname','th')} <span style="color:var(--red)">*</span></label>
            <input type="text" name="first_name" value="{v('first_name')}"
                   class="{'error' if 'first_name' in errors else ''}" placeholder="กรอกชื่อ">
            {err('first_name')}
          </div>
          <div class="field">
            <label>{t('field_lastname','th')} <span style="color:var(--red)">*</span></label>
            <input type="text" name="last_name" value="{v('last_name')}"
                   class="{'error' if 'last_name' in errors else ''}" placeholder="กรอกนามสกุล">
            {err('last_name')}
          </div>
          <div class="field">
            <label>{t('field_nickname','th')}</label>
            <input type="text" name="nickname" value="{v('nickname')}" placeholder="เช่น เบส, ตู่">
          </div>
          <div class="field">
            <label>{t('field_gender',lang)}</label>
            <select name="gender">
              <option value="">{t('gender_unset',lang)}</option>
              {sel('gender', ['ชาย','หญิง','อื่นๆ'])}
            </select>
          </div>
        </div>
        <div class="form-grid" style="margin-top:14px">
          {date_field_html('birth_date', birth_stored, label=t('field_birthdate',lang))}
          {date_field_html('death_date', death_stored, label=t('field_deathdate',lang))}
        </div>
        <div class="form-grid" style="margin-top:14px">
          <div class="field">
            <label>{t('field_birthplace',lang)}</label>
            <input type="text" name="birth_place" value="{v('birth_place')}" placeholder="เช่น เชียงใหม่ / Chiang Mai / 清迈">
          </div>
          <div class="field">
            <label>{t('field_occupation',lang)}</label>
            <input type="text" name="occupation" value="{v('occupation')}" placeholder="เช่น ครู / Teacher / 教师">
          </div>
        </div>
        <div class="field" style="margin-top:14px">
          <label>{t('field_address',lang)}</label>
          <textarea name="address" rows="2" placeholder="เช่น 123 ถ.สุขุมวิท กรุงเทพฯ / 123 Sukhumvit Rd, Bangkok">{v('address')}</textarea>
        </div>
        <hr class="divider" style="margin-top:18px">
        <div class="card-title" style="margin:12px 0 10px">📞 {t('field_contact',lang)}</div>
        <div class="form-grid">
          <div class="field">
            <label>{t('field_phone',lang)}</label>
            <input type="text" name="phone" value="{v('phone')}" placeholder="เช่น 081-234-5678">
          </div>
          <div class="field">
            <label>{t('field_line_id',lang)}</label>
            <input type="text" name="line_id" value="{v('line_id')}" placeholder="เช่น @familytree">
          </div>
        </div>
        <div class="field" style="margin-top:14px">
          <label>{t('field_email',lang)}</label>
          <input type="email" name="email" value="{v('email')}" placeholder="เช่น example@email.com">
        </div>
        <div class="field" style="margin-top:14px">
          <label>{t('field_notes',lang)}</label>
          <textarea name="notes" rows="3">{v('notes')}</textarea>
        </div>
        <hr class="divider" style="margin-top:20px">
        <div class="card-title" style="margin:16px 0 4px">
          {t('field_names_section',lang)}
          <span style="font-size:12px;font-weight:400;color:var(--muted);margin-left:8px">
            {t('field_names_hint',lang)}
          </span>
        </div>
        {lang_name_fields}
        {photo_section}"""

    def page_member_form(self, qs, user, mode='add', lang='th'):
        if not (user := auth.require_admin(self)): return
        m = None
        if mode == 'edit':
            mid = int(qs.get('id', 0))
            m = get_member(mid)
            if not m:
                return self.send_error_page(404, t('err_not_found',lang), user=user, lang=lang)

        title = t('page_add_member',lang) if mode == 'add' else f"{t('page_edit_member',lang)}: {m['first_name']} {m['last_name']}"
        action = "/members/add" if mode == 'add' else "/members/edit"
        id_field = f'<input type="hidden" name="id" value="{m["id"]}">' if m else ""

        form = f"""
        <form method="POST" action="{action}" enctype="multipart/form-data" novalidate>
          {id_field}
          {self._member_form_html(m, lang=lang)}
          <div class="form-footer">
            <button type="submit" class="btn btn-primary">💾 {t('btn_save',lang)}</button>
            <a href="/members" class="btn btn-gray">{t('btn_cancel',lang)}</a>
          </div>
        </form>"""

        body = f"""
        <div class="page-header">
          <div class="page-title"><span>{'➕' if mode=='add' else '✏️'}</span>{title}</div>
        </div>
        <div class="card">{form}</div>"""
        self.send_html(layout(title, body, user, lang=lang))

    def post_member_form(self, data, user, mode='add', lang='th', files=None):
        if not (user := auth.require_admin(self)): return
        files = files or {}
        errors = {}
        fn = data.get('first_name', '').strip()
        ln = data.get('last_name', '').strip()
        if not fn:
            errors['first_name'] = t('err_required_name', lang)
        if not ln:
            errors['last_name'] = t('err_required_lname', lang)

        # Quick photo size pre-check
        photo_file = files.get('photo')
        if photo_file and photo_file.get('data') and len(photo_file['data']) > 10 * 1024 * 1024:
            msg = {'th':'ไฟล์รูปใหญ่เกิน 10 MB', 'en':'Photo exceeds 10 MB', 'zh':'照片超过10MB'}
            errors['photo'] = msg.get(lang, 'Photo too large')

        if errors:
            m = None
            if mode == 'edit':
                mid = int(data.get('id', 0))
                m = get_member(mid)
            title = t('page_add_member',lang) if mode == 'add' else t('page_edit_member',lang)
            id_field = f'<input type="hidden" name="id" value="{data.get("id","")}">  ' if mode == 'edit' else ""
            action = "/members/add" if mode == 'add' else "/members/edit"
            form = f"""
            <form method="POST" action="{action}" enctype="multipart/form-data" novalidate>
              {id_field}
              {self._member_form_html(m, errors, prefill=data, lang=lang)}
              <div class="form-footer">
                <button type="submit" class="btn btn-primary">💾 {t('btn_save',lang)}</button>
                <a href="/members" class="btn btn-gray">{t('btn_cancel',lang)}</a>
              </div>
            </form>"""
            body = f'<div class="page-header"><div class="page-title">{title}</div></div><div class="card">{form}</div>'
            alert_txt = {'th':'กรุณาตรวจสอบข้อมูลที่กรอก',
                         'en':'Please check the form fields.',
                         'zh':'请检查表单字段。'}.get(lang,'Please check.')
            return self.send_html(layout(title, body, user,
                alert=alert_txt, alert_type="error", lang=lang))

        fields = {k: (data[k].strip() or None)
                  for k in ['first_name','last_name','nickname','gender',
                            'birth_place','address','phone','line_id','email','occupation','notes']
                  if k in data}
        fields['first_name'] = fn
        fields['last_name'] = ln
        # Parse structured date fields
        bd = parse_date_from_form(data, 'birth_date')
        if bd is not None:
            fields['birth_date'] = bd
        dd = parse_date_from_form(data, 'death_date')
        if dd is not None:
            fields['death_date'] = dd

        if mode == 'add':
            fields['created_by'] = user['user_id']
            fields['updated_by'] = user['user_id']
            mid = add_member(**{k:v for k,v in fields.items() if v is not None})
            self._save_lang_names(mid, data)
            self._save_photo(mid, data, files)
            write_audit(user['user_id'], user['username'], 'CREATE',
                        'members', mid, new_data=fields, ip_address=self.get_ip())
            self.redirect(f"/members/view?id={mid}&msg=added")
        else:
            mid = int(data.get('id', 0))
            old = dict(get_member(mid))
            fields['updated_by'] = user['user_id']
            update_member(mid, **{k:v for k,v in fields.items()})
            self._save_lang_names(mid, data)
            self._save_photo(mid, data, files)
            write_audit(user['user_id'], user['username'], 'UPDATE',
                        'members', mid, old_data=old,
                        new_data={k: fields.get(k) for k in fields},
                        ip_address=self.get_ip())
            self.redirect(f"/members/view?id={mid}&msg=updated")

    def _save_photo(self, mid: int, data: dict, files: dict):
        """Handle photo upload and deletion for a member."""
        # Delete existing photo if checkbox is ticked
        if data.get('delete_photo') == '1':
            m = get_member(mid)
            if m and m['photo_path']:
                delete_photo(m['photo_path'])
                update_member(mid, photo_path=None)
            return

        # Save new photo if provided
        photo_file = files.get('photo')
        if not photo_file or not photo_file.get('data') or len(photo_file['data']) == 0:
            return
        try:
            filename = save_photo(
                mid,
                photo_file['data'],
                original_name=photo_file.get('filename', ''),
                mime=photo_file.get('mime', ''),
            )
            m = get_member(mid)
            if m and m['photo_path']:
                delete_photo(m['photo_path'])   # remove old file
            update_member(mid, photo_path=filename)
        except PhotoError:
            pass   # size/type already checked above; ignore other errors

    def _save_lang_names(self, mid: int, data: dict):
        """Save multilingual name fields from POST data for all non-Thai languages."""
        for lcode in LANGUAGES:
            if lcode == 'th':
                continue
            fn = data.get(f'name_{lcode}_first', '').strip() or None
            ln = data.get(f'name_{lcode}_last', '').strip() or None
            nn = data.get(f'name_{lcode}_nick', '').strip() or None
            if fn or ln or nn:
                set_member_name(mid, lcode, first_name=fn, last_name=ln, nickname=nn)
            else:
                delete_member_name(mid, lcode)

    def page_member_delete(self, qs, user):
        if not (user := auth.require_admin(self)): return
        mid = int(qs.get('id', 0))
        m = get_member(mid)
        if not m:
            return self.send_error_page(404, "ไม่พบข้อมูลสมาชิก", user=user)
        old = dict(m)
        delete_member(mid)
        write_audit(user['user_id'], user['username'], 'DELETE',
                    'members', mid, old_data=old, ip_address=self.get_ip())
        self.redirect("/members")

    # ── Relations ─────────────────────────────────────────────────────────────

    def page_relations(self, qs, user, lang='th'):
        if not (user := auth.require_login(self)): return
        is_adm = user['role'] == 'admin'

        with get_conn() as conn:
            rels = conn.execute("""
                SELECT r.id, r.rel_type, r.married_date, r.divorced_date,
                       m1.id AS id1, m1.first_name||' '||m1.last_name AS name1,
                       m2.id AS id2, m2.first_name||' '||m2.last_name AS name2
                FROM relationships r
                JOIN members m1 ON m1.id=r.person1_id
                JOIN members m2 ON m2.id=r.person2_id
                ORDER BY r.rel_type, r.id
            """).fetchall()

        alert = t('rel_added_ok', lang) if qs.get('msg') == 'added' else None

        rows = ""
        for r in rels:
            label = (f'👫 {t("rel_spouse",lang)}' if r['rel_type'] == 'spouse'
                     else f'👨‍👧 {t("rel_parent_child",lang)}')
            extra = f"<br><small style='color:var(--muted)'>{r['married_date']}</small>" if r['married_date'] else ""
            del_c = t('rel_delete_confirm', lang)
            del_btn = (f'<a href="#" class="btn btn-danger btn-sm btn-icon"'
                       f' onclick="confirmDelete(\'{del_c}\',\'/relations/delete?id={r["id"]}\');return false">🗑️</a>'
                       if is_adm else "")
            rows += f"""<tr>
              <td style="color:var(--muted);font-size:13px">#{r['id']}</td>
              <td>{label}</td>
              <td><a href="/members/view?id={r['id1']}" style="color:var(--green)">{r['name1']}</a></td>
              <td><a href="/members/view?id={r['id2']}" style="color:var(--green)">{r['name2']}</a>{extra}</td>
              <td><div class="td-actions">{del_btn}</div></td>
            </tr>"""

        add_form = ""
        if is_adm:
            members = list_members()
            opts = "".join(f'<option value="{m["id"]}">{m["first_name"]} {m["last_name"]}</option>'
                           for m in members)
            add_form = f"""
            <div class="card" style="margin-top:20px">
              <div class="card-title">➕ {t('rel_add_new',lang)}</div>
              <form method="POST" action="/relations/add">
                <div class="form-grid">
                  <div class="field">
                    <label>{t('rel_person1',lang)} <span style="color:var(--red)">*</span></label>
                    <select name="p1" required>{opts}</select>
                    <div class="field-hint">{t('rel_person1_hint',lang)}</div>
                  </div>
                  <div class="field">
                    <label>{t('rel_person2',lang)} <span style="color:var(--red)">*</span></label>
                    <select name="p2" required>{opts}</select>
                    <div class="field-hint">{t('rel_person2_hint',lang)}</div>
                  </div>
                  <div class="field">
                    <label>{t('rel_type_select',lang)} <span style="color:var(--red)">*</span></label>
                    <select name="rel_type" required>
                      <option value="parent-child">{t('rel_parent_child_opt',lang)}</option>
                      <option value="spouse">{t('rel_spouse_opt',lang)}</option>
                    </select>
                  </div>
                  <div class="field">
                    <label>{t('rel_married_date',lang)}</label>
                    <input type="text" name="married_date" placeholder="2530-02-14">
                  </div>
                </div>
                <div class="form-footer">
                  <button type="submit" class="btn btn-primary">💾 {t('btn_save',lang)}</button>
                </div>
              </form>
            </div>"""

        body = f"""
        <div class="page-header">
          <div class="page-title"><span>🔗</span>{t('page_relations',lang)}</div>
        </div>
        <div class="card">
          <div class="table-wrap">
            <table>
              <tr><th>ID</th><th>{t('rel_type_col',lang)}</th>
                  <th>{t('rel_person1',lang)}</th><th>{t('rel_person2',lang)}</th><th></th></tr>
              {rows}
            </table>
          </div>
        </div>
        {add_form}"""
        self.send_html(layout(t("nav_relations",lang), body, user, alert=alert, lang=lang))

    def post_relation_add(self, data, user):
        if not (user := auth.require_admin(self)): return
        p1, p2 = int(data.get('p1', 0)), int(data.get('p2', 0))
        if p1 == p2:
            return self.redirect("/relations?err=same")
        rel_type = data.get('rel_type', 'parent-child')
        kwargs = {}
        if data.get('married_date'):
            kwargs['married_date'] = data['married_date']
        rid = add_relationship(p1, p2, rel_type, **kwargs)
        write_audit(user['user_id'], user['username'], 'CREATE',
                    'relationships', rid,
                    new_data={'p1': p1, 'p2': p2, 'type': rel_type},
                    ip_address=self.get_ip())
        self.redirect("/relations?msg=added")

    def page_relation_delete(self, qs, user):
        if not (user := auth.require_admin(self)): return
        rid = int(qs.get('id', 0))
        with get_conn() as conn:
            old = conn.execute("SELECT * FROM relationships WHERE id=?", (rid,)).fetchone()
        delete_relationship(rid)
        if old:
            write_audit(user['user_id'], user['username'], 'DELETE',
                        'relationships', rid, old_data=dict(old), ip_address=self.get_ip())
        self.redirect("/relations")

    # ── Export ────────────────────────────────────────────────────────────────

    def page_export(self, qs, user, lang="th"):
        if not (user := auth.require_login(self)): return
        alert, alert_type = None, "success"
        if qs.get('do') == '1':
            try:
                path = export_excel()
                import subprocess, sys as _sys
                if _sys.platform == 'win32':
                    subprocess.Popen(['start', '', str(path)], shell=True)
                write_audit(user['user_id'], user['username'], 'EXPORT',
                            ip_address=self.get_ip())
                alert = f"{t('export_ok',lang)} {path}"
                alert_type = "success"
            except Exception as e:
                alert = f"{t('export_err',lang)} {e}"
                alert_type = "error"

        body = f"""
        <div class="page-header">
          <div class="page-title"><span>📊</span>{t('page_export',lang)}</div>
        </div>
        <div class="card">
          <p style="margin-bottom:16px;color:var(--muted)">{t('export_intro',lang)}</p>
          <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:24px">
            <div style="background:var(--green-light);padding:16px;border-radius:10px;text-align:center">
              <div style="font-size:28px;margin-bottom:6px">🌳</div>
              <div style="font-weight:700;color:var(--green-dark)">{t('export_sheet1',lang)}</div>
              <div style="font-size:13px;color:var(--muted);margin-top:4px">{t('export_sheet1d',lang)}</div>
            </div>
            <div style="background:#EAF4FB;padding:16px;border-radius:10px;text-align:center">
              <div style="font-size:28px;margin-bottom:6px">📋</div>
              <div style="font-weight:700;color:#1A5276">{t('export_sheet2',lang)}</div>
              <div style="font-size:13px;color:var(--muted);margin-top:4px">{t('export_sheet2d',lang)}</div>
            </div>
            <div style="background:#FEF9E7;padding:16px;border-radius:10px;text-align:center">
              <div style="font-size:28px;margin-bottom:6px">📖</div>
              <div style="font-weight:700;color:#7D6608">{t('export_sheet3',lang)}</div>
              <div style="font-size:13px;color:var(--muted);margin-top:4px">{t('export_sheet3d',lang)}</div>
            </div>
          </div>
          <a href="/export?do=1" class="btn btn-primary" style="font-size:16px;padding:12px 32px">
            📊 {t('btn_export',lang)}
          </a>
        </div>"""
        self.send_html(layout(t("nav_export",lang), body, user, alert=alert, alert_type=alert_type, lang=lang))

    # ── Users (Admin only) ────────────────────────────────────────────────────

    def page_users(self, qs, user, lang="th"):
        if not (user := auth.require_admin(self)): return
        users = list_users()
        msg = qs.get('msg', '')
        alert_map = {'added': t('user_added_ok',lang), 'updated': t('user_updated_ok',lang)}
        alert = alert_map.get(msg)

        rows = ""
        for u in users:
            role_b = ('<span class="badge badge-admin">ADMIN</span>' if u['role'] == 'admin'
                      else '<span class="badge badge-user">USER</span>')
            active_b = (f'<span class="badge badge-active">{t("user_active",lang)}</span>'
                        if u['is_active']
                        else f'<span class="badge badge-inactive">{t("user_inactive",lang)}</span>')
            toggle_label = f'🔒 {t("user_suspend",lang)}' if u['is_active'] else f'🔓 {t("user_enable",lang)}'
            toggle_style = "btn-warning" if u['is_active'] else "btn-primary"
            self_row = u['id'] == user['user_id']
            you_badge = (f'<span style="font-size:11px;background:var(--green-light);color:var(--green);'
                         f'padding:1px 6px;border-radius:4px;margin-left:6px">{t("user_you",lang)}</span>'
                         if self_row else '')
            toggle_btn = (f'<a href="/users/toggle?id={u["id"]}" class="btn {toggle_style} btn-sm">{toggle_label}</a>'
                          if not self_row else '')

            rows += f"""<tr {'style="background:#F4FBF7"' if self_row else ''}>
              <td style="color:var(--muted);font-size:13px">#{u['id']}</td>
              <td><b>{u['username']}</b>{you_badge}</td>
              <td>{u['full_name']}</td>
              <td>{role_b}</td>
              <td>{active_b}</td>
              <td style="font-size:13px;color:var(--muted)">{u['last_login'] or t('user_never_login',lang)}</td>
              <td><div class="td-actions">
                <a href="/users/edit?id={u['id']}" class="btn btn-warning btn-sm">✏️ {t('btn_edit',lang)}</a>
                {toggle_btn}
              </div></td>
            </tr>"""

        body = f"""
        <div class="page-header">
          <div class="page-title"><span>👥</span>{t('page_users',lang)}</div>
          <a href="/users/add" class="btn btn-primary">➕ {t('user_add_btn',lang)}</a>
        </div>
        <div class="card">
          <div class="table-wrap">
            <table>
              <tr><th>ID</th><th>Username</th><th>{t('user_col_name',lang)}</th>
                  <th>Role</th><th>{t('user_col_status',lang)}</th>
                  <th>{t('user_col_login',lang)}</th><th></th></tr>
              {rows}
            </table>
          </div>
        </div>"""
        self.send_html(layout(t("nav_users",lang), body, user, alert=alert, lang=lang))

    def _user_form_html(self, u=None, errors=None, prefill=None, mode='add', lang='th'):
        errors = errors or {}
        d = prefill or (dict(u) if u else {})
        v = lambda f: d.get(f) or ''
        err = lambda f: f'<div style="color:var(--red);font-size:12px;margin-top:3px">{errors[f]}</div>' if f in errors else ''
        sel_role = "".join(f'<option value="{r}" {"selected" if v("role")==r else ""}>{r}</option>'
                           for r in ['user','admin'])

        pw_label = t('user_pw_label_add', lang) if mode == 'add' else t('user_pw_label_edit', lang)
        pw_hint  = t('user_pw_hint_add', lang)  if mode == 'add' else t('user_pw_hint_edit', lang)
        pw_req   = f'<span style="color:var(--red)">*</span>' if mode == 'add' else ''
        un_ph    = t('user_username_placeholder', lang)
        fn_ph    = t('user_name_placeholder', lang)

        return f"""
        <div class="form-grid">
          <div class="field">
            <label>Username <span style="color:var(--red)">*</span></label>
            <input type="text" name="username" value="{v('username')}"
                   class="{'error' if 'username' in errors else ''}"
                   {'readonly style="background:#f5f5f5"' if mode=='edit' else f'placeholder="{un_ph}"'}>
            {err('username')}
          </div>
          <div class="field">
            <label>{t('user_col_name',lang)} <span style="color:var(--red)">*</span></label>
            <input type="text" name="full_name" value="{v('full_name')}"
                   class="{'error' if 'full_name' in errors else ''}" placeholder="{fn_ph}">
            {err('full_name')}
          </div>
          <div class="field">
            <label>{pw_label} {pw_req}</label>
            <input type="password" name="password" value=""
                   class="{'error' if 'password' in errors else ''}"
                   placeholder="{pw_hint}">
            {err('password')}
          </div>
          <div class="field">
            <label>Role</label>
            <select name="role">{sel_role}</select>
            <div class="field-hint">{t('user_role_hint',lang)}</div>
          </div>
        </div>"""

    def page_user_form(self, qs, user, mode='add', lang='th'):
        if not (user := auth.require_admin(self)): return
        u = None
        if mode == 'edit':
            uid = int(qs.get('id', 0))
            u = get_user(uid)
            if not u:
                return self.send_error_page(404, t('err_not_found',lang), user=user, lang=lang)

        title = t('user_add_btn',lang) if mode == 'add' else f"{t('btn_edit',lang)}: {u['username']}"
        action = "/users/add" if mode == 'add' else "/users/edit"
        id_field = f'<input type="hidden" name="id" value="{u["id"]}">' if u else ""

        form = f"""
        <form method="POST" action="{action}" novalidate>
          {id_field}
          {self._user_form_html(u, mode=mode, lang=lang)}
          <div class="form-footer">
            <button type="submit" class="btn btn-primary">💾 {t('btn_save',lang)}</button>
            <a href="/users" class="btn btn-gray">{t('btn_cancel',lang)}</a>
          </div>
        </form>"""

        body = f"""
        <div class="page-header">
          <div class="page-title"><span>{'➕' if mode=='add' else '✏️'}</span>{title}</div>
        </div>
        <div class="card" style="max-width:640px">{form}</div>"""
        self.send_html(layout(title, body, user, lang=lang))

    def post_user_form(self, data, user, mode='add', lang='th'):
        if not (user := auth.require_admin(self)): return
        errors = {}
        username = data.get('username', '').strip()
        full_name = data.get('full_name', '').strip()
        password = data.get('password', '').strip()
        role = data.get('role', 'user')

        if not full_name:
            errors['full_name'] = t('user_err_fullname', lang)
        if mode == 'add':
            if not username:
                errors['username'] = t('user_err_username', lang)
            elif not username.isalnum():
                errors['username'] = t('user_err_username_alnum', lang)
            else:
                with get_conn() as conn:
                    dup = conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
                if dup:
                    errors['username'] = t('user_err_username_dup', lang)
            if not password:
                errors['password'] = t('user_err_password', lang)
            elif len(password) < 6:
                errors['password'] = t('user_err_password_short', lang)
        else:
            if password and len(password) < 6:
                errors['password'] = t('user_err_password_short', lang)

        if errors:
            uid = int(data.get('id', 0))
            u = get_user(uid) if mode == 'edit' else None
            title = t('user_add_btn',lang) if mode == 'add' else t('btn_edit',lang)
            action = "/users/add" if mode == 'add' else "/users/edit"
            id_field = f'<input type="hidden" name="id" value="{data.get("id","")}">  ' if mode == 'edit' else ""
            form = f"""
            <form method="POST" action="{action}" novalidate>
              {id_field}{self._user_form_html(u, errors, prefill=data, mode=mode, lang=lang)}
              <div class="form-footer">
                <button type="submit" class="btn btn-primary">💾 {t('btn_save',lang)}</button>
                <a href="/users" class="btn btn-gray">{t('btn_cancel',lang)}</a>
              </div>
            </form>"""
            body = f'<div class="page-header"><div class="page-title">{title}</div></div><div class="card" style="max-width:640px">{form}</div>'
            return self.send_html(layout(title, body, user,
                alert=t('user_form_check',lang), alert_type="error", lang=lang))

        if mode == 'add':
            uid = create_user(username, password, full_name, role=role,
                              created_by=user['user_id'])
            write_audit(user['user_id'], user['username'], 'CREATE',
                        'users', uid, new_data={'username': username, 'role': role},
                        ip_address=self.get_ip())
            self.redirect("/users?msg=added")
        else:
            uid = int(data.get('id', 0))
            kwargs = {'full_name': full_name, 'role': role}
            if password:
                kwargs['password'] = password
            update_user(uid, **kwargs)
            write_audit(user['user_id'], user['username'], 'UPDATE',
                        'users', uid, new_data={'full_name': full_name, 'role': role},
                        ip_address=self.get_ip())
            self.redirect("/users?msg=updated")

    def page_user_toggle(self, qs, user):
        if not (user := auth.require_admin(self)): return
        uid = int(qs.get('id', 0))
        if uid == user['user_id']:
            return self.redirect("/users")
        u = get_user(uid)
        if u:
            new_state = 0 if u['is_active'] else 1
            update_user(uid, is_active=new_state)
            action = 'DEACTIVATE' if new_state == 0 else 'ACTIVATE'
            write_audit(user['user_id'], user['username'], action,
                        'users', uid, ip_address=self.get_ip())
        self.redirect("/users")

    def post_change_password(self, data, user):
        if not user:
            return self.redirect("/login")
        uid = user['user_id']
        cur_pw = data.get('current_password', '')
        new_pw = data.get('new_password', '').strip()
        u = get_user(uid)
        from database import _verify_password, _hash_password
        if not _verify_password(cur_pw, u['password_hash']):
            return self.redirect("/users/edit?id="+str(uid)+"&err=wrongpw")
        if len(new_pw) < 6:
            return self.redirect("/users/edit?id="+str(uid)+"&err=shortpw")
        update_user(uid, password=new_pw)
        write_audit(uid, user['username'], 'CHANGE_PASSWORD',
                    'users', uid, ip_address=self.get_ip())
        self.redirect("/users?msg=updated")

    # ── Audit Log ─────────────────────────────────────────────────────────────

    def page_audit(self, qs, user, lang="th"):
        if not (user := auth.require_admin(self)): return
        limit = int(qs.get('limit', 100))
        logs = list_audit(limit)

        rows = ""
        for lg in logs:
            action_cls = f"audit-{lg['action']}"
            old = ""
            if lg['old_data']:
                try:
                    d = json.loads(lg['old_data'])
                    old_label = t('audit_old_data', lang)
                    old = (f'<details><summary style="cursor:pointer;font-size:12px;color:var(--muted)">'
                           f'{old_label}</summary>'
                           f'<pre style="font-size:11px;background:#f5f5f5;padding:8px;border-radius:4px;max-width:300px;overflow:auto">'
                           f'{json.dumps(d, ensure_ascii=False, indent=2)}</pre></details>')
                except Exception:
                    old = lg['old_data'][:80]
            rows += f"""<tr>
              <td style="font-size:12px;color:var(--muted);white-space:nowrap">{lg['timestamp']}</td>
              <td><span class="audit-action {action_cls}">{lg['action']}</span></td>
              <td style="font-size:13px">{lg['username'] or '-'}</td>
              <td style="font-size:13px">{lg['table_name'] or '-'}</td>
              <td style="font-size:13px">{('#'+str(lg['record_id'])) if lg['record_id'] else '-'}</td>
              <td style="font-size:12px">{old}</td>
              <td style="font-size:12px;color:var(--muted)">{lg['ip_address'] or ''}</td>
            </tr>"""

        limit_links = " ".join(
            f'<a href="/audit?limit={n}" class="btn btn-gray btn-sm">{t("audit_last",lang)} {n}</a>'
            for n in [50, 100, 200, 500]
        )
        no_hist = t('audit_no_history', lang)
        body = f"""
        <div class="page-header">
          <div class="page-title"><span>📋</span>{t('audit_title',lang)}</div>
          <div style="display:flex;gap:8px;align-items:center">
            <span style="font-size:13px;color:var(--muted)">{t('audit_show',lang)}</span>
            {limit_links}
          </div>
        </div>
        <div class="card">
          <div class="table-wrap">
            <table>
              <tr><th>{t('audit_col_time',lang)}</th><th>{t('audit_col_action',lang)}</th>
                  <th>{t('audit_col_user',lang)}</th><th>{t('audit_col_table',lang)}</th>
                  <th>{t('audit_col_record',lang)}</th><th>{t('audit_col_data',lang)}</th>
                  <th>{t('audit_col_ip',lang)}</th></tr>
              {rows if rows else f'<tr><td colspan="7" style="text-align:center;color:var(--muted);padding:24px">{no_hist}</td></tr>'}
            </table>
          </div>
        </div>"""
        self.send_html(layout(t("nav_audit",lang), body, user, lang=lang))


# ─── Entry point ─────────────────────────────────────────────────────────────

def run():
    init_db()
    ensure_default_admin()
    print(f"[OK] Family Tree Web UI -> http://localhost:{PORT}")
    print("     Default login: admin / admin1234")
    print("     กด Ctrl+C เพื่อปิด")
    if not _os.environ.get("NO_BROWSER"):
        webbrowser.open(f"http://localhost:{PORT}/tree")
    HTTPServer(('', PORT), Handler).serve_forever()


if __name__ == "__main__":
    run()

