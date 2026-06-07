"""
Command-line interface for Family Tree — no web browser needed.
Run: python cli.py
"""
import sys
from database import (
    init_db, add_member, update_member, delete_member, get_member,
    list_members, add_relationship, delete_relationship,
    get_roots, build_tree, get_children, get_spouses, get_parents,
    get_conn, seed_sample_data
)
from export_excel import export_excel

def clear(): print("\n" * 2)

def hr(): print("─" * 55)

def prompt(label, default=""):
    val = input(f"  {label}{' ['+default+']' if default else ''}: ").strip()
    return val if val else default

def print_tree(node, indent=0):
    prefix = "  " * indent + ("└─ " if indent > 0 else "")
    icon = "♂" if node.get('gender') == 'ชาย' else ("♀" if node.get('gender') == 'หญิง' else "·")
    name = f"{node['first_name']} {node['last_name']}"
    nick = f" ({node['nickname']})" if node.get('nickname') else ""
    birth = (node.get('birth_date') or '')[:4]
    death = (node.get('death_date') or '')[:4]
    year = f" [{birth}{' – '+death if death else ''}]" if birth else ""
    spouses = ", ".join(f"{s['first_name']} {s['last_name']}" for s in node.get('spouses', []))
    sp_str = f"  💑 {spouses}" if spouses else ""
    print(f"{prefix}{icon} [{node['id']}] {name}{nick}{year}{sp_str}")
    for child in node.get('children', []):
        print_tree(child, indent + 1)


def menu_main():
    while True:
        hr()
        print("🌳  ระบบบันทึกลำดับวงศ์ตระกูล")
        hr()
        print("  1. แสดงแผนผัง (Tree)")
        print("  2. รายชื่อสมาชิกทั้งหมด")
        print("  3. เพิ่มสมาชิกใหม่")
        print("  4. แก้ไขข้อมูลสมาชิก")
        print("  5. ลบสมาชิก")
        print("  6. จัดการความสัมพันธ์")
        print("  7. Export เป็น Excel")
        print("  8. สร้างข้อมูลตัวอย่าง")
        print("  0. ออกจากโปรแกรม")
        hr()
        choice = input("เลือก: ").strip()

        if choice == '1':
            menu_tree()
        elif choice == '2':
            menu_list()
        elif choice == '3':
            menu_add()
        elif choice == '4':
            menu_edit()
        elif choice == '5':
            menu_delete()
        elif choice == '6':
            menu_relations()
        elif choice == '7':
            menu_export()
        elif choice == '8':
            if input("สร้างข้อมูลตัวอย่าง? (y/n): ").lower() == 'y':
                seed_sample_data()
        elif choice == '0':
            print("👋 ลาก่อน!")
            sys.exit(0)


def menu_tree():
    print("\n🌳 แผนผังลำดับวงศ์ตระกูล\n")
    roots = get_roots()
    if not roots:
        print("  ยังไม่มีข้อมูล")
        return
    for r in roots:
        print_tree(build_tree(r['id']))
    input("\n  (กด Enter เพื่อกลับ)")


def menu_list():
    print("\n👥 รายชื่อสมาชิกทั้งหมด\n")
    members = list_members()
    if not members:
        print("  ยังไม่มีข้อมูล")
        return
    print(f"  {'ID':<4} {'ชื่อ-นามสกุล':<25} {'ชื่อเล่น':<12} {'เพศ':<6} {'เกิด':<12} {'อาชีพ'}")
    hr()
    for m in members:
        print(f"  {m['id']:<4} {m['first_name']+' '+m['last_name']:<25} "
              f"{(m['nickname'] or ''):<12} {(m['gender'] or ''):<6} "
              f"{(m['birth_date'] or ''):<12} {m['occupation'] or ''}")
    input("\n  (กด Enter เพื่อกลับ)")


def _input_member_fields(existing=None):
    e = existing or {}
    d = lambda f: e.get(f) or ''
    print("  (* = จำเป็น, Enter เพื่อข้ามหรือคงค่าเดิม)")
    fn  = prompt("ชื่อ *", d('first_name')) or (None if not existing else d('first_name'))
    ln  = prompt("นามสกุล *", d('last_name')) or (None if not existing else d('last_name'))
    nn  = prompt("ชื่อเล่น", d('nickname'))
    g   = prompt("เพศ (ชาย/หญิง/อื่นๆ)", d('gender'))
    bd  = prompt("วันเกิด YYYY-MM-DD", d('birth_date'))
    dd  = prompt("วันเสียชีวิต YYYY-MM-DD", d('death_date'))
    bp  = prompt("ภูมิลำเนา", d('birth_place'))
    occ = prompt("อาชีพ", d('occupation'))
    nt  = prompt("หมายเหตุ", d('notes'))
    return dict(first_name=fn or None, last_name=ln or None,
                nickname=nn or None, gender=g or None,
                birth_date=bd or None, death_date=dd or None,
                birth_place=bp or None, occupation=occ or None,
                notes=nt or None)


def menu_add():
    print("\n➕ เพิ่มสมาชิกใหม่\n")
    fields = _input_member_fields()
    if not fields.get('first_name') or not fields.get('last_name'):
        print("  ❌ ต้องระบุชื่อและนามสกุล")
        return
    mid = add_member(**{k: v for k, v in fields.items() if v is not None})
    print(f"\n  ✅ เพิ่ม [{mid}] {fields['first_name']} {fields['last_name']} เรียบร้อย")
    input("  (กด Enter เพื่อกลับ)")


def menu_edit():
    print("\n✏️ แก้ไขข้อมูลสมาชิก\n")
    menu_list()
    mid = input("  ใส่ ID ที่ต้องการแก้ไข: ").strip()
    if not mid.isdigit():
        return
    m = get_member(int(mid))
    if not m:
        print("  ❌ ไม่พบ ID นี้")
        return
    print(f"\n  แก้ไข: {m['first_name']} {m['last_name']}\n")
    fields = _input_member_fields(dict(m))
    update_member(int(mid), **{k: v for k, v in fields.items() if k not in ('first_name','last_name') or v})
    print(f"\n  ✅ อัพเดตเรียบร้อย")
    input("  (กด Enter เพื่อกลับ)")


def menu_delete():
    print("\n🗑️ ลบสมาชิก\n")
    menu_list()
    mid = input("  ใส่ ID ที่ต้องการลบ: ").strip()
    if not mid.isdigit():
        return
    m = get_member(int(mid))
    if not m:
        print("  ❌ ไม่พบ ID นี้")
        return
    confirm = input(f"  ยืนยันลบ '{m['first_name']} {m['last_name']}'? (y/n): ")
    if confirm.lower() == 'y':
        delete_member(int(mid))
        print("  ✅ ลบเรียบร้อย")
    input("  (กด Enter เพื่อกลับ)")


def menu_relations():
    while True:
        print("\n🔗 ความสัมพันธ์\n")
        print("  1. ดูความสัมพันธ์ทั้งหมด")
        print("  2. เพิ่มความสัมพันธ์ (พ่อแม่-ลูก)")
        print("  3. เพิ่มความสัมพันธ์ (คู่สมรส)")
        print("  4. ลบความสัมพันธ์")
        print("  0. กลับ")
        c = input("  เลือก: ").strip()
        if c == '0':
            break
        elif c == '1':
            with get_conn() as conn:
                rels = conn.execute("""
                    SELECT r.id, r.rel_type,
                           m1.first_name||' '||m1.last_name AS n1,
                           m2.first_name||' '||m2.last_name AS n2,
                           r.married_date
                    FROM relationships r
                    JOIN members m1 ON m1.id=r.person1_id
                    JOIN members m2 ON m2.id=r.person2_id
                """).fetchall()
            print(f"\n  {'ID':<4} {'ประเภท':<15} {'คนที่ 1':<20} {'คนที่ 2'}")
            hr()
            for r in rels:
                t = "คู่สมรส" if r['rel_type']=='spouse' else "พ่อ/แม่ → ลูก"
                extra = f" ({r['married_date']})" if r.get('married_date') else ""
                print(f"  {r['id']:<4} {t:<15} {r['n1']:<20} {r['n2']}{extra}")
            input("\n  (กด Enter เพื่อกลับ)")

        elif c in ('2', '3'):
            menu_list()
            p1 = input("  ID บุคคลที่ 1 (พ่อ/แม่ หรือ คู่สมรส): ").strip()
            p2 = input("  ID บุคคลที่ 2 (ลูก หรือ คู่สมรส): ").strip()
            if not (p1.isdigit() and p2.isdigit()):
                continue
            rel_type = 'parent-child' if c == '2' else 'spouse'
            kwargs = {}
            if c == '3':
                md = input("  วันแต่งงาน YYYY-MM-DD (Enter ข้าม): ").strip()
                if md:
                    kwargs['married_date'] = md
            add_relationship(int(p1), int(p2), rel_type, **kwargs)
            print("  ✅ เพิ่มความสัมพันธ์เรียบร้อย")

        elif c == '4':
            rid = input("  ใส่ ID ความสัมพันธ์ที่ต้องการลบ: ").strip()
            if rid.isdigit():
                delete_relationship(int(rid))
                print("  ✅ ลบเรียบร้อย")


def menu_export():
    print("\n📊 Export เป็น Excel\n")
    path = export_excel()
    if input("  เปิดไฟล์ตอนนี้เลย? (y/n): ").lower() == 'y':
        import subprocess, sys as _sys
        if _sys.platform == 'win32':
            subprocess.Popen(['start', '', str(path)], shell=True)
    input("  (กด Enter เพื่อกลับ)")


if __name__ == "__main__":
    init_db()
    menu_main()
