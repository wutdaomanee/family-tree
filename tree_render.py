"""
Family Tree — 4 display modes
  1. top-down   : traditional top-down tree with connectors
  2. left-right : horizontal left→right org-chart style
  3. timeline   : generation bands with year axis on left
  4. cards      : grid cards grouped by generation
"""
from database import get_roots, build_tree, get_display_name, get_member_names
from i18n import t, format_year_short, LANGUAGES
from photo_utils import photo_url


# ─── Colour palette ────────────────────────────────────────────────────────────
GEN_COLORS = [
    ("#1A472A", "#fff"),  ("#2D6A4F", "#fff"),  ("#40916C", "#EBF7F0"),
    ("#52B788", "#F2FBF6"), ("#74C69D", "#F7FDF9"), ("#95D5B2", "#FAFFFE"),
    ("#B7E4C7", "#fff"),  ("#D8F3DC", "#fff"),
]
CONN_COLOR = "#2D6A4F"


# ─── Shared CSS ───────────────────────────────────────────────────────────────
SHARED_CSS = """
<style>
/* ── Photo thumbnail in person cards ── */
.ft-photo{
  width:54px; height:72px;
  object-fit:cover; object-position:center top;
  border-radius:8px;
  display:block; margin:0 auto 6px;
  border:2px solid rgba(255,255,255,.6);
  box-shadow:0 2px 6px rgba(0,0,0,.2);
}
.ft-photo-wrap{ text-align:center; margin-bottom:2px }
/* Slightly wider card when photo present */
.ft-person:has(.ft-photo){ min-width:120px }
/* ── Mode selector ── */
.tree-modes{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:18px}
.tree-mode-btn{
  display:inline-flex;align-items:center;gap:6px;
  padding:7px 16px;border-radius:20px;border:2px solid var(--border,#D5E8DC);
  background:#fff;color:var(--muted,#6c757d);cursor:pointer;
  font-size:13px;font-weight:600;font-family:inherit;transition:.15s;
}
.tree-mode-btn:hover{border-color:var(--accent,#52B788);color:var(--green,#2D6A4F)}
.tree-mode-btn.active{
  background:var(--green,#2D6A4F);color:#fff;
  border-color:var(--green,#2D6A4F);
}
.tree-panel{display:none}.tree-panel.active{display:block}

/* ── Person card (shared) ── */
.ft-person{
  background:#fff;border:2px solid var(--node-border,#40916C);
  border-radius:10px;padding:8px 14px;text-align:center;
  min-width:110px;max-width:170px;cursor:pointer;transition:.15s;
  position:relative;box-shadow:0 2px 8px #0001;
}
.ft-person:hover{border-color:var(--accent,#52B788);box-shadow:0 4px 16px #0002;transform:translateY(-2px)}
.ft-person.gen-0{border-color:#1A472A;background:#1A472A;color:#fff}
.ft-person.gen-1{border-color:#2D6A4F;background:#2D6A4F;color:#fff}
.ft-person.gen-2{border-color:#40916C;background:#EBF7F0}
.ft-person.gen-3{border-color:#52B788;background:#F2FBF6}
.ft-person.gen-4{border-color:#74C69D;background:#F7FDF9}
.ft-person.gen-5{border-color:#95D5B2;background:#FAFFFE}
.ft-person.gen-6{border-color:#B7E4C7;background:#fff}
.ft-person.gen-7{border-color:#D8F3DC;background:#fff}
.ft-name{font-size:13px;font-weight:700;line-height:1.3;word-break:break-word}
.ft-alt-name{font-size:10px;opacity:.7;margin-top:1px;font-style:italic}
.ft-nick{font-size:11px;opacity:.7;margin-top:2px}
.ft-year{font-size:10px;opacity:.65;margin-top:3px}
.ft-gender{position:absolute;top:-8px;left:50%;transform:translateX(-50%);
           font-size:11px;background:#fff;border:1px solid var(--border,#D5E8DC);
           border-radius:8px;padding:0 5px;line-height:18px;color:#555}
.ft-person.gen-0 .ft-gender,.ft-person.gen-1 .ft-gender{background:#2D6A4F;border-color:#40916C;color:#fff}
.ft-edit-btn{display:none;position:absolute;bottom:-10px;right:-10px;width:24px;height:24px;
             border-radius:50%;background:var(--yellow,#F39C12);color:#fff;font-size:11px;
             line-height:24px;text-align:center;text-decoration:none;box-shadow:0 2px 6px #0003;z-index:1}
.ft-card:hover .ft-edit-btn{display:block}
.ft-spouse-conn{font-size:14px;color:var(--red,#E74C3C);flex-shrink:0;margin-top:12px}

/* ── Legend ── */
.ft-legend{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px;padding:10px 14px;
           background:#f8faf9;border-radius:10px;border:1px solid var(--border,#D5E8DC)}
.ft-legend-item{display:flex;align-items:center;gap:5px;font-size:12px;color:var(--muted,#6c757d)}
.ft-legend-dot{width:13px;height:13px;border-radius:4px;border:2px solid;flex-shrink:0}
.ft-scroll-hint{font-size:12px;color:var(--muted,#999);text-align:center;margin-top:10px}
</style>
"""

# ── Mode 1: Top-Down ──────────────────────────────────────────────────────────

TD_CSS = """
<style>
.td-outer{display:flex;gap:0;overflow-x:auto;overflow-y:visible;min-width:0}
.td-sidebar{flex-shrink:0;width:120px;border-right:2px solid var(--border,#D5E8DC);
            margin-right:20px;padding-right:12px}
.td-gen-label{display:flex;flex-direction:column;align-items:flex-end;padding:8px 0;
              min-height:120px;justify-content:flex-start;
              border-bottom:1px dashed var(--border,#D5E8DC)}
.td-gen-label:last-child{border-bottom:none}
.td-gen-num{font-size:13px;font-weight:700;color:var(--green-dark,#1A472A);
            background:var(--green-light,#D8F3DC);padding:3px 10px;
            border-radius:10px;margin-bottom:6px;white-space:nowrap}
.td-gen-year{font-size:11px;color:var(--muted,#6c757d);text-align:right;line-height:1.6}
.td-content{flex:1;min-width:0;padding-bottom:20px}
.td-group{display:flex;flex-direction:column;align-items:center}
.td-card{display:flex;flex-direction:column;align-items:center;gap:4px;position:relative}
.td-couple{display:flex;align-items:flex-start;gap:6px;flex-wrap:wrap;justify-content:center}
.td-conn-down{width:2px;height:24px;background:var(--green-mid,#40916C);margin:0 auto}
.td-children-wrap{display:flex;flex-direction:column;align-items:center}
.td-h-bar{height:2px;background:var(--green-mid,#40916C);align-self:stretch}
.td-children-row{display:flex;flex-direction:row;gap:20px;justify-content:center;align-items:flex-start}
.td-child-branch{display:flex;flex-direction:column;align-items:center}
.td-conn-up{width:2px;height:24px;background:var(--green-mid,#40916C)}
</style>
"""

def _person_card(person, depth, lang, is_admin, view_base="/members/view"):
    gc = f"gen-{min(depth,7)}"
    dn = get_display_name(person, lang)
    name = f"{dn['first_name']} {dn['last_name']}"
    nick = f'<div class="ft-nick">({dn["nickname"]})</div>' if dn.get('nickname') else ''

    alt = ''
    if lang != 'th' and (dn['first_name'] != person['first_name'] or dn['last_name'] != person['last_name']):
        alt = f'<div class="ft-alt-name">{person["first_name"]} {person["last_name"]}</div>'

    by = format_year_short(person.get('birth_date') or '', lang)
    dy = format_year_short(person.get('death_date') or '', lang)
    bd = person.get('birth_date') or ''
    yr = ''
    if by:
        yr = f'{by}' + (f'–{dy}' if dy else '')
        if lang == 'th': yr = f'พ.ศ. {yr}'
        elif lang == 'zh': yr = f'{yr}年'
    elif bd.upper() == 'UNKNOWN':
        yr = t('unknown_date', lang)
    year_html = f'<div class="ft-year">{yr}</div>' if yr else ''

    # Photo thumbnail — show if available, else fall back to gender icon
    photo_path = person.get('photo_path') or ''
    photo_html  = ''
    gender_html = ''
    if photo_path:
        url = photo_url(photo_path)
        photo_html = (f'<div class="ft-photo-wrap">'
                      f'<img class="ft-photo" src="{url}" alt="{name}" loading="lazy">'
                      f'</div>')
    else:
        icon = '♂' if person.get('gender') in ('ชาย','Male','男') else (
               '♀' if person.get('gender') in ('หญิง','Female','女') else '')
        gender_html = f'<div class="ft-gender">{icon}</div>' if icon else ''

    edit = ''
    if is_admin:
        edit = f'<a href="/members/edit?id={person["id"]}" class="ft-edit-btn">✏</a>'

    href = f'{view_base}?id={person["id"]}'
    return (f'<div class="ft-person {gc}" onclick="location.href=\'{href}\'" title="{name}">'
            f'{gender_html}{photo_html}'
            f'<div class="ft-name">{name}</div>{alt}{nick}{year_html}{edit}</div>')


def _td_node(node, depth, lang, is_admin):
    children = node.get('children', [])
    spouses   = node.get('spouses', [])

    parts = [_person_card(node, depth, lang, is_admin)]
    for sp in spouses:
        parts.append('<span class="ft-spouse-conn">♥</span>')
        parts.append(_person_card(sp, depth, lang, is_admin))

    card = (f'<div class="td-card">'
            f'<div class="td-couple">{"".join(parts)}</div></div>')

    if not children:
        return f'<div class="td-group">{card}</div>'

    branches = ''.join(
        f'<div class="td-child-branch"><div class="td-conn-up"></div>{_td_node(c,depth+1,lang,is_admin)}</div>'
        for c in children
    )
    single = 'style="justify-content:center"' if len(children) == 1 else ''
    children_html = (f'<div class="td-children-wrap">'
                     f'<div class="td-conn-down"></div>'
                     f'<div class="td-h-bar"></div>'
                     f'<div class="td-children-row" {single}>{branches}</div></div>')
    return f'<div class="td-group">{card}{children_html}</div>'


def _collect_gen_info(trees, lang):
    gen_years = {}
    def walk(n, d=0):
        for p in [n] + n.get('spouses', []):
            y = format_year_short(p.get('birth_date') or '', lang)
            if y and y.isdigit():
                gen_years.setdefault(d, []).append(int(y))
        for c in n.get('children', []): walk(c, d+1)
    for t_ in trees: walk(t_)
    return gen_years


def _max_depth(node):
    if not node.get('children'): return 0
    return 1 + max(_max_depth(c) for c in node['children'])


def render_topdown(trees, lang, is_admin, gen_label_word, total_gens, gen_years):
    sidebar_items = []
    for g in range(total_gens):
        years = gen_years.get(g, [])
        if years:
            mn, mx = min(years), max(years)
            if lang == 'th':    yr_t = f'พ.ศ. {mn}' if mn==mx else f'พ.ศ. {mn}<br>–{mx}'
            elif lang == 'zh':  yr_t = f'{mn}年' if mn==mx else f'{mn}年<br>–{mx}年'
            else:               yr_t = str(mn) if mn==mx else f'{mn}<br>–{mx}'
        else: yr_t = ''
        sidebar_items.append(f"""<div class="td-gen-label">
          <div class="td-gen-num">{gen_label_word} {g+1}</div>
          <div class="td-gen-year">{yr_t}</div></div>""")

    sidebar = f'<div class="td-sidebar">{"".join(sidebar_items)}</div>'
    trees_html = ''.join(_td_node(t_, 0, lang, is_admin) for t_ in trees)
    content = (f'<div class="td-content">'
               f'<div style="display:flex;flex-direction:column;gap:40px;align-items:center">'
               f'{trees_html}</div></div>')
    return TD_CSS + f'<div class="td-outer">{sidebar}{content}</div>'


# ── Mode 2: Left-Right ────────────────────────────────────────────────────────

LR_CSS = """
<style>
.lr-outer{overflow:auto;padding-bottom:10px}
.lr-tree-wrap{display:inline-flex;flex-direction:column;gap:40px;min-width:max-content;padding:8px}
.lr-group{display:flex;flex-direction:row;align-items:center;gap:0}
.lr-card{display:flex;flex-direction:column;align-items:center;flex-shrink:0;position:relative}
.lr-couple{display:flex;flex-direction:column;align-items:flex-start;gap:4px}
.lr-conn-right{width:28px;height:2px;background:var(--green-mid,#40916C);flex-shrink:0}
.lr-children-wrap{display:flex;flex-direction:column;gap:16px;
                  border-left:2px solid var(--green-mid,#40916C);margin-left:0;padding-left:0}
.lr-child-branch{display:flex;flex-direction:row;align-items:center;position:relative}
.lr-conn-h{width:28px;height:2px;background:var(--green-mid,#40916C);flex-shrink:0}
/* person card narrower for LR */
.lr-outer .ft-person{min-width:130px;max-width:180px}
.lr-gen-badge{position:absolute;left:-52px;top:50%;transform:translateY(-50%);
              font-size:11px;font-weight:700;color:#fff;background:var(--green,#2D6A4F);
              padding:2px 7px;border-radius:8px;white-space:nowrap;pointer-events:none}
</style>
"""

def _lr_node(node, depth, lang, is_admin, show_gen_badge=False):
    children = node.get('children', [])
    spouses   = node.get('spouses', [])

    cards = [_person_card(node, depth, lang, is_admin)]
    for sp in spouses:
        sp_card = _person_card(sp, depth, lang, is_admin)
        cards.append(f'<div style="display:flex;align-items:center;gap:4px;margin-top:4px">'
                     f'<span class="ft-spouse-conn" style="margin:0 4px">♥</span>{sp_card}</div>')

    couple_html = f'<div class="lr-couple">{"".join(cards)}</div>'
    card_html = f'<div class="lr-card">{couple_html}</div>'

    if not children:
        return f'<div class="lr-group">{card_html}</div>'

    branches = ''.join(
        f'<div class="lr-child-branch">'
        f'<div class="lr-conn-h"></div>'
        f'{_lr_node(c, depth+1, lang, is_admin)}</div>'
        for c in children
    )
    children_html = (f'<div class="lr-conn-right"></div>'
                     f'<div class="lr-children-wrap">{branches}</div>')
    return f'<div class="lr-group">{card_html}{children_html}</div>'


def render_leftright(trees, lang, is_admin, gen_label_word, total_gens, gen_years):
    trees_html = ''.join(_lr_node(t_, 0, lang, is_admin, show_gen_badge=True) for t_ in trees)
    hint = t('tree_scroll', lang)
    return (LR_CSS
            + f'<div class="lr-outer"><div class="lr-tree-wrap">{trees_html}</div></div>'
            + f'<div class="ft-scroll-hint">{hint}</div>')


# ── Mode 3: Timeline (Generation Bands) ──────────────────────────────────────

TL_CSS = """
<style>
.tl-wrap{overflow-x:auto}
.tl-gen-band{display:flex;align-items:flex-start;gap:16px;padding:16px 0;
             border-bottom:1px solid var(--border,#D5E8DC)}
.tl-gen-band:last-child{border-bottom:none}
.tl-gen-label{flex-shrink:0;width:100px;text-align:right;padding-right:16px;
              border-right:3px solid;padding-top:8px}
.tl-gen-num{font-size:14px;font-weight:700;color:var(--green-dark,#1A472A)}
.tl-gen-year{font-size:11px;color:var(--muted,#6c757d);margin-top:3px;line-height:1.5}
.tl-members{display:flex;flex-wrap:wrap;gap:10px;align-items:flex-start;flex:1}
.tl-member-card{
  background:#fff;border:2px solid;border-radius:10px;padding:10px 14px;
  min-width:120px;max-width:180px;cursor:pointer;transition:.15s;
  box-shadow:0 2px 6px #0001;text-align:center;
}
.tl-member-card:hover{transform:translateY(-3px);box-shadow:0 6px 18px #0002}
.tl-member-name{font-size:13px;font-weight:700;line-height:1.3}
.tl-member-nick{font-size:11px;opacity:.7;margin-top:2px}
.tl-member-year{font-size:11px;opacity:.65;margin-top:3px}
.tl-member-occ{font-size:11px;opacity:.6;margin-top:2px;
               white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:140px}
.tl-couple-group{display:flex;align-items:flex-start;gap:4px;flex-direction:column}
.tl-couple-pair{display:flex;align-items:center;gap:6px}
.tl-heart{color:var(--red,#E74C3C);font-size:13px}
.tl-member-alt{font-size:10px;opacity:.6;margin-top:1px;font-style:italic}
</style>
"""

def _collect_gen_nodes(trees):
    """Return {depth: [node, ...]} flattening the trees."""
    result = {}
    def walk(node, depth=0):
        result.setdefault(depth, []).append(node)
        for c in node.get('children', []):
            walk(c, depth+1)
    for t_ in trees:
        walk(t_)
    return result


def render_timeline(trees, lang, is_admin, gen_label_word, total_gens, gen_years):
    gen_nodes = _collect_gen_nodes(trees)

    # Remove duplicate nodes (same id can appear via multiple parent paths)
    seen = set()
    for d in gen_nodes:
        unique = []
        for n in gen_nodes[d]:
            if n['id'] not in seen:
                seen.add(n['id'])
                unique.append(n)
        gen_nodes[d] = unique

    bands = []
    for d in range(total_gens):
        nodes = gen_nodes.get(d, [])
        if not nodes:
            continue

        bg, fg = GEN_COLORS[min(d, len(GEN_COLORS)-1)]
        years = gen_years.get(d, [])
        if years:
            mn, mx = min(years), max(years)
            if lang == 'th':   yr_t = f'พ.ศ. {mn}' + (f'–{mx}' if mn!=mx else '')
            elif lang == 'zh': yr_t = f'{mn}年' + (f'–{mx}年' if mn!=mx else '')
            else:              yr_t = str(mn) + (f'–{mx}' if mn!=mx else '')
        else: yr_t = ''

        label_html = (f'<div class="tl-gen-label" style="border-color:{bg}">'
                      f'<div class="tl-gen-num" style="color:{bg}">'
                      f'{gen_label_word} {d+1}</div>'
                      f'<div class="tl-gen-year">{yr_t}</div></div>')

        member_cards = []
        for node in nodes:
            dn = get_display_name(node, lang)
            name = f"{dn['first_name']} {dn['last_name']}"
            nick = dn.get('nickname','')
            alt = ''
            if lang != 'th' and (dn['first_name'] != node['first_name'] or dn['last_name'] != node['last_name']):
                alt = f'<div class="tl-member-alt">{node["first_name"]} {node["last_name"]}</div>'

            by = format_year_short(node.get('birth_date') or '', lang)
            dy = format_year_short(node.get('death_date') or '', lang)
            yr = ''
            if by:
                yr = f'{by}' + (f'–{dy}' if dy else '')
                if lang == 'th': yr = f'พ.ศ. {yr}'
                elif lang == 'zh': yr = f'{yr}年'
            elif (node.get('birth_date') or '').upper() == 'UNKNOWN':
                yr = t('unknown_date', lang)

            icon = '♂' if node.get('gender') in ('ชาย','Male','男') else (
                   '♀' if node.get('gender') in ('หญิง','Female','女') else '')
            occ = node.get('occupation', '') or ''

            spouses = node.get('spouses', [])
            href = f'/members/view?id={node["id"]}'
            edit_btn = (f'<a href="/members/edit?id={node["id"]}" '
                        f'style="font-size:10px;color:var(--yellow,#F39C12);display:block;margin-top:4px">'
                        f'✏ {t("btn_edit",lang)}</a>') if is_admin else ''

            # Main card
            main = (f'<div class="tl-member-card" style="border-color:{bg};background:{bg};color:{fg}"'
                    f' onclick="location.href=\'{href}\'">'
                    f'<div class="tl-member-name">{icon} {name}</div>'
                    f'{alt}'
                    f'{"<div class=tl-member-nick>("+nick+")</div>" if nick else ""}'
                    f'{"<div class=tl-member-year>"+yr+"</div>" if yr else ""}'
                    f'{"<div class=tl-member-occ>"+occ+"</div>" if occ else ""}'
                    f'{edit_btn}</div>')

            if spouses:
                spouse_cards = []
                for sp in spouses:
                    sp_dn = get_display_name(sp, lang)
                    sp_name = f"{sp_dn['first_name']} {sp_dn['last_name']}"
                    sp_by = format_year_short(sp.get('birth_date') or '', lang)
                    sp_dy = format_year_short(sp.get('death_date') or '', lang)
                    sp_yr = ''
                    if sp_by:
                        sp_yr = sp_by + (f'–{sp_dy}' if sp_dy else '')
                        if lang == 'th': sp_yr = f'พ.ศ. {sp_yr}'
                        elif lang == 'zh': sp_yr = f'{sp_yr}年'
                    sp_href = f'/members/view?id={sp["id"]}'
                    sp_card = (f'<div class="tl-member-card" style="border-color:{bg};background:{bg};color:{fg};min-width:100px"'
                               f' onclick="location.href=\'{sp_href}\'">'
                               f'<div class="tl-member-name">{sp_name}</div>'
                               f'{"<div class=tl-member-year>"+sp_yr+"</div>" if sp_yr else ""}'
                               f'</div>')
                    spouse_cards.append(sp_card)
                couple_content = ''.join(
                    f'<div class="tl-couple-pair">{main}<span class="tl-heart">♥</span>{sc}</div>'
                    if i == 0 else f'<div class="tl-couple-pair" style="margin-left:20px"><span class="tl-heart">♥</span>{sc}</div>'
                    for i, sc in enumerate(spouse_cards)
                )
                member_cards.append(f'<div class="tl-couple-group">'
                                     f'<div class="tl-couple-pair">{main}</div>'
                                     + ''.join(
                                         f'<div class="tl-couple-pair" style="margin-top:4px">'
                                         f'<span class="tl-heart" style="margin-left:16px">♥</span>{sc}</div>'
                                         for sc in spouse_cards
                                     ) + '</div>')
            else:
                member_cards.append(main)

        members_html = f'<div class="tl-members">{"".join(member_cards)}</div>'
        bands.append(f'<div class="tl-gen-band">{label_html}{members_html}</div>')

    return TL_CSS + f'<div class="tl-wrap">{"".join(bands)}</div>'


# ── Mode 4: Cards Grid ────────────────────────────────────────────────────────

CG_CSS = """
<style>
.cg-wrap{display:flex;flex-direction:column;gap:24px}
.cg-gen-section{}
.cg-gen-header{
  display:flex;align-items:center;gap:12px;margin-bottom:14px;
  padding:10px 16px;border-radius:10px;
}
.cg-gen-title{font-size:16px;font-weight:700}
.cg-gen-count{font-size:13px;opacity:.75}
.cg-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}
.cg-card{
  background:#fff;border:1.5px solid var(--border,#D5E8DC);border-radius:12px;
  padding:14px;cursor:pointer;transition:.15s;box-shadow:0 1px 6px #0001;
  border-left:5px solid;
}
.cg-card:hover{box-shadow:0 4px 18px #0002;transform:translateY(-2px)}
.cg-card-top{display:flex;align-items:flex-start;gap:10px}
.cg-avatar{width:42px;height:42px;border-radius:50%;display:flex;align-items:center;
           justify-content:center;font-size:18px;flex-shrink:0;font-weight:700}
.cg-info{flex:1;min-width:0}
.cg-name{font-size:14px;font-weight:700;line-height:1.3;color:var(--text,#1a1a2e)}
.cg-name-alt{font-size:11px;color:var(--muted,#999);font-style:italic;margin-top:1px}
.cg-nick{font-size:12px;color:var(--muted,#6c757d);margin-top:2px}
.cg-meta{font-size:12px;color:var(--muted,#6c757d);margin-top:8px;
         display:flex;flex-direction:column;gap:3px}
.cg-meta-row{display:flex;align-items:center;gap:6px}
.cg-meta-icon{width:16px;text-align:center;font-size:13px;flex-shrink:0}
.cg-divider{border:none;border-top:1px solid var(--border,#D5E8DC);margin:10px 0}
.cg-rels{font-size:12px;color:var(--muted,#6c757d)}
.cg-rels a{color:var(--green,#2D6A4F);text-decoration:none}
.cg-rels a:hover{text-decoration:underline}
.cg-badge{display:inline-block;font-size:11px;font-weight:600;padding:2px 8px;
          border-radius:8px;margin-top:6px}
</style>
"""

def _collect_all_by_gen(trees):
    result = {}
    seen = set()
    def walk(n, d=0):
        if n['id'] not in seen:
            seen.add(n['id'])
            result.setdefault(d, []).append(n)
        for c in n.get('children', []):
            walk(c, d+1)
    for t_ in trees: walk(t_)
    return result


def render_cards(trees, lang, is_admin, gen_label_word, total_gens, gen_years):
    from database import get_parents, get_children, get_spouses

    gen_nodes = _collect_all_by_gen(trees)

    sections = []
    for d in range(total_gens):
        nodes = gen_nodes.get(d, [])
        if not nodes: continue

        bg, fg = GEN_COLORS[min(d, len(GEN_COLORS)-1)]
        count = len(nodes)
        count_label = (f'{count} คน' if lang=='th' else
                       f'{count} people' if lang=='en' else f'{count} 人')

        header = (f'<div class="cg-gen-header" style="background:{bg};color:{fg}">'
                  f'<div class="cg-gen-title">{gen_label_word} {d+1}</div>'
                  f'<div class="cg-gen-count">{count_label}</div></div>')

        cards = []
        for node in nodes:
            dn = get_display_name(node, lang)
            name = f"{dn['first_name']} {dn['last_name']}"
            nick = dn.get('nickname','')
            alt = ''
            if lang != 'th' and (dn['first_name'] != node['first_name'] or dn['last_name'] != node['last_name']):
                alt = f'<div class="cg-name-alt">{node["first_name"]} {node["last_name"]}</div>'

            icon = '♂' if node.get('gender') in ('ชาย','Male','男') else (
                   '♀' if node.get('gender') in ('หญิง','Female','女') else '·')

            by = format_year_short(node.get('birth_date') or '', lang)
            dy = format_year_short(node.get('death_date') or '', lang)
            yr = ''
            if by:
                yr = by + (f'–{dy}' if dy else '')
                if lang == 'th': yr = f'พ.ศ. {yr}'
                elif lang == 'zh': yr = f'{yr}年'
            elif (node.get('birth_date') or '').upper() == 'UNKNOWN':
                yr = t('unknown_date', lang)

            occ = node.get('occupation','') or ''
            bp  = node.get('birth_place','') or ''

            # Relations
            parents_raw  = get_parents(node['id'])
            spouses_raw  = get_spouses(node['id'])
            children_raw = get_children(node['id'])

            def rel_link(p):
                pd = dict(p); pd['_names'] = get_member_names(p['id'])
                rn = get_display_name(pd, lang)
                return f'<a href="/members/view?id={p["id"]}">{rn["first_name"]} {rn["last_name"]}</a>'

            parents_html  = ', '.join(rel_link(p) for p in parents_raw)  or '-'
            spouses_html  = ', '.join(rel_link(s) for s in spouses_raw)  or '-'
            children_html = ', '.join(rel_link(c) for c in children_raw) or '-'

            par_label = t('rel_parents', lang)
            sp_label  = t('rel_spouse', lang)
            ch_label  = t('rel_children', lang)

            meta_rows = ''
            if yr:     meta_rows += f'<div class="cg-meta-row"><span class="cg-meta-icon">📅</span>{yr}</div>'
            if bp:     meta_rows += f'<div class="cg-meta-row"><span class="cg-meta-icon">📍</span>{bp}</div>'
            if occ:    meta_rows += f'<div class="cg-meta-row"><span class="cg-meta-icon">💼</span>{occ}</div>'

            edit_badge = (f'<a href="/members/edit?id={node["id"]}" '
                          f'class="cg-badge" style="background:var(--yellow,#F39C12);color:#fff;'
                          f'text-decoration:none">✏ {t("btn_edit",lang)}</a>') if is_admin else ''

            href = f'/members/view?id={node["id"]}'
            card = (f'<div class="cg-card" style="border-left-color:{bg}" onclick="location.href=\'{href}\'">'
                    f'<div class="cg-card-top">'
                    f'<div class="cg-avatar" style="background:{bg};color:{fg}">{icon}</div>'
                    f'<div class="cg-info">'
                    f'<div class="cg-name">{name}</div>'
                    f'{alt}'
                    f'{"<div class=cg-nick>("+nick+")</div>" if nick else ""}'
                    f'</div></div>'
                    f'{"<div class=cg-meta>"+meta_rows+"</div>" if meta_rows else ""}'
                    f'<hr class="cg-divider">'
                    f'<div class="cg-rels">'
                    f'<div class="cg-meta-row"><span class="cg-meta-icon">👨‍👩‍</span>'
                    f'<span style="color:var(--muted,#999);margin-right:4px">{par_label}:</span>{parents_html}</div>'
                    f'<div class="cg-meta-row"><span class="cg-meta-icon">💑</span>'
                    f'<span style="color:var(--muted,#999);margin-right:4px">{sp_label}:</span>{spouses_html}</div>'
                    f'<div class="cg-meta-row"><span class="cg-meta-icon">👶</span>'
                    f'<span style="color:var(--muted,#999);margin-right:4px">{ch_label}:</span>{children_html}</div>'
                    f'</div>'
                    f'{edit_badge}'
                    f'</div>')
            cards.append(card)

        grid = f'<div class="cg-grid">{"".join(cards)}</div>'
        sections.append(f'<div class="cg-gen-section">{header}{grid}</div>')

    return CG_CSS + f'<div class="cg-wrap">{"".join(sections)}</div>'


# ─── Legend helper ─────────────────────────────────────────────────────────────

def _legend_html(total_gens, gen_label_word):
    items = ''.join(
        f'<div class="ft-legend-item">'
        f'<div class="ft-legend-dot" style="border-color:{bg};background:{bg2}"></div>'
        f'{gen_label_word} {i+1}</div>'
        for i, (bg, bg2) in enumerate(GEN_COLORS[:total_gens])
    )
    return f'<div class="ft-legend">{items}</div>'


# ─── Main page renderer ───────────────────────────────────────────────────────

MODE_ICONS = {
    'topdown':    '🌳',
    'leftright':  '➡️',
    'timeline':   '📅',
    'cards':      '🗂️',
}
MODE_LABELS = {
    'topdown':   {'th':'ต้นไม้ (บน→ล่าง)',   'en':'Top-Down Tree',  'zh':'从上到下'},
    'leftright': {'th':'แนวนอน (ซ้าย→ขวา)', 'en':'Left to Right',  'zh':'从左到右'},
    'timeline':  {'th':'แถบรุ่น (Timeline)',  'en':'Generation Bands','zh':'世代时间轴'},
    'cards':     {'th':'การ์ดรุ่น (Cards)',   'en':'Generation Cards','zh':'世代卡片'},
}
MODES = ['topdown', 'leftright', 'timeline', 'cards']


def render_tree_page(is_admin: bool = False, lang: str = 'th') -> str:
    roots = get_roots()
    if not roots:
        return (f'<div class="alert alert-info"><span class="alert-icon">ℹ️</span>'
                f'{t("tree_empty",lang)} — <a href="/members/add">{t("tree_add",lang)}</a></div>')

    trees = [build_tree(r['id']) for r in roots]
    gen_years   = _collect_gen_info(trees, lang)
    total_gens  = max((_max_depth(t_) for t_ in trees), default=0) + 1
    glabel      = t('gen_label', lang)

    # ── Mode selector buttons ──────────────────────────────────────────────────
    btns = []
    for mode in MODES:
        icon  = MODE_ICONS[mode]
        label = MODE_LABELS[mode].get(lang, MODE_LABELS[mode]['en'])
        btns.append(f'<button class="tree-mode-btn" data-mode="{mode}" onclick="switchMode(\'{mode}\')">'
                    f'{icon} {label}</button>')
    selector = f'<div class="tree-modes">{"".join(btns)}</div>'

    # ── Legend ─────────────────────────────────────────────────────────────────
    legend = _legend_html(total_gens, glabel)
    legend_text = t('tree_legend', lang)
    legend = (f'<div class="ft-legend">'
              + ''.join(
                  f'<div class="ft-legend-item">'
                  f'<div class="ft-legend-dot" style="border-color:{bg};background:{bg2}"></div>'
                  f'{glabel} {i+1}</div>'
                  for i, (bg, bg2) in enumerate(GEN_COLORS[:total_gens])
              )
              + f'<div style="flex:1;text-align:right;font-size:11px;opacity:.7">{legend_text}</div>'
              + '</div>')

    # ── Render each panel ──────────────────────────────────────────────────────
    panels = {
        'topdown':   render_topdown(trees, lang, is_admin, glabel, total_gens, gen_years),
        'leftright': render_leftright(trees, lang, is_admin, glabel, total_gens, gen_years),
        'timeline':  render_timeline(trees, lang, is_admin, glabel, total_gens, gen_years),
        'cards':     render_cards(trees, lang, is_admin, glabel, total_gens, gen_years),
    }

    panels_html = ''.join(
        f'<div class="tree-panel" id="panel-{mode}">{html}</div>'
        for mode, html in panels.items()
    )

    js = """
<script>
function switchMode(mode) {
  document.querySelectorAll('.tree-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tree-mode-btn').forEach(b => b.classList.remove('active'));
  var panel = document.getElementById('panel-' + mode);
  if (panel) panel.classList.add('active');
  document.querySelectorAll('[data-mode="' + mode + '"]').forEach(b => b.classList.add('active'));
  try { localStorage.setItem('ft_tree_mode', mode); } catch(e) {}
}
document.addEventListener('DOMContentLoaded', function() {
  var saved = 'topdown';
  try { saved = localStorage.getItem('ft_tree_mode') || 'topdown'; } catch(e) {}
  switchMode(saved);
});
</script>
"""

    return (SHARED_CSS
            + selector
            + legend
            + panels_html
            + js)
