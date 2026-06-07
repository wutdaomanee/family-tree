"""
Internationalization (i18n) for Family Tree.
Supported languages: th (Thai), en (English), zh (Chinese Simplified)

Date rules:
  th → Buddhist Era (พ.ศ.)
  en → Common Era (AD / no suffix)
  zh → Common Era (年)
"""

LANGUAGES = {
    'th': {'label': 'ภาษาไทย',  'flag': '🇹🇭', 'cal': 'BE'},
    'en': {'label': 'English',   'flag': '🇬🇧', 'cal': 'CE'},
    'zh': {'label': '中文',       'flag': '🇨🇳', 'cal': 'CE'},
}

DEFAULT_LANG = 'th'
LANG_COOKIE  = 'ft_lang'


# ─── UI string catalogue ──────────────────────────────────────────────────────

_T = {
    # ── Navigation ────────────────────────────────────────────────────────────
    'nav_tree':     {'th': 'แผนผัง',          'en': 'Family Tree',    'zh': '家谱'},
    'nav_members':  {'th': 'สมาชิก',           'en': 'Members',        'zh': '成员'},
    'nav_relations':{'th': 'ความสัมพันธ์',    'en': 'Relationships',  'zh': '关系'},
    'nav_export':   {'th': 'Export',           'en': 'Export',         'zh': '导出'},
    'nav_users':    {'th': 'ผู้ใช้งาน',        'en': 'Users',          'zh': '用户'},
    'nav_audit':    {'th': 'ประวัติ',          'en': 'Audit Log',      'zh': '操作日志'},

    # ── Tree page ─────────────────────────────────────────────────────────────
    'tree_title':   {'th': 'แผนผังลำดับวงศ์ตระกูล',
                     'en': 'Family Genealogy Tree',
                     'zh': '家族族谱'},
    'tree_add':     {'th': 'เพิ่มสมาชิก',     'en': 'Add Member',     'zh': '添加成员'},
    'tree_scroll':  {'th': '← เลื่อนซ้าย-ขวาได้หากมีสมาชิกจำนวนมาก →',
                     'en': '← Scroll left or right for large families →',
                     'zh': '← 左右滚动以查看更多 →'},
    'tree_empty':   {'th': 'ยังไม่มีข้อมูล',  'en': 'No data yet',    'zh': '暂无数据'},
    'tree_legend':  {'th': 'สีเข้ม = ต้นตระกูล  →  สีอ่อน = รุ่นหลัง   ♥ = คู่สมรส',
                     'en': 'Darker = older generation  →  Lighter = newer   ♥ = Spouse',
                     'zh': '深色 = 年长辈分  →  浅色 = 晚辈   ♥ = 配偶'},

    # ── Generation labels ─────────────────────────────────────────────────────
    'gen_label':    {'th': 'รุ่น',             'en': 'Gen',            'zh': '代'},

    # ── Members page ──────────────────────────────────────────────────────────
    'members_title':{'th': 'รายชื่อสมาชิกทั้งหมด',
                     'en': 'All Members',
                     'zh': '全部成员'},
    'col_name':     {'th': 'ชื่อ-นามสกุล',    'en': 'Full Name',      'zh': '姓名'},
    'col_gender':   {'th': 'เพศ',              'en': 'Gender',         'zh': '性别'},
    'col_lifespan': {'th': 'ปีเกิด-เสียชีวิต','en': 'Lifespan',       'zh': '生卒年'},
    'col_birthplace':{'th':'ภูมิลำเนา',        'en': 'Birthplace',     'zh': '籍贯'},
    'col_occupation':{'th':'อาชีพ',             'en': 'Occupation',     'zh': '职业'},
    'col_updated':  {'th': 'แก้ไขล่าสุด',     'en': 'Last Updated',   'zh': '最后更新'},

    # ── Member form fields ────────────────────────────────────────────────────
    'field_firstname':  {'th': 'ชื่อ',             'en': 'First Name',     'zh': '名'},
    'field_lastname':   {'th': 'นามสกุล',          'en': 'Last Name',      'zh': '姓'},
    'field_nickname':   {'th': 'ชื่อเล่น',         'en': 'Nickname',       'zh': '小名/别名'},
    'field_gender':     {'th': 'เพศ',               'en': 'Gender',         'zh': '性别'},
    'field_birthdate':  {'th': 'วันเกิด',           'en': 'Date of Birth',  'zh': '出生日期'},
    'field_deathdate':  {'th': 'วันเสียชีวิต',     'en': 'Date of Death',  'zh': '逝世日期'},
    'field_birthplace': {'th': 'ภูมิลำเนา/บ้านเกิด','en':'Birthplace',     'zh': '出生地'},
    'field_occupation': {'th': 'อาชีพ',              'en': 'Occupation',     'zh': '职业'},
    'field_notes':      {'th': 'หมายเหตุ',           'en': 'Notes',          'zh': '备注'},
    'field_names_section': {
        'th': 'ชื่อในภาษาต่าง ๆ',
        'en': 'Names in Other Languages',
        'zh': '多语言姓名',
    },
    'field_names_hint': {
        'th': 'กรอกเฉพาะภาษาที่มีชื่อเรียกต่างออกไป — หากไม่กรอก ระบบจะใช้ชื่อหลัก',
        'en': 'Fill only if the name differs in that language — leave blank to use the primary name.',
        'zh': '仅在该语言姓名与主名不同时填写，否则留空。',
    },

    # ── Gender values ─────────────────────────────────────────────────────────
    'gender_male':   {'th': 'ชาย',  'en': 'Male',   'zh': '男'},
    'gender_female': {'th': 'หญิง', 'en': 'Female', 'zh': '女'},
    'gender_other':  {'th': 'อื่นๆ','en': 'Other',  'zh': '其他'},
    'gender_unset':  {'th': '-- ไม่ระบุ --', 'en': '-- Not specified --', 'zh': '-- 未指定 --'},

    # ── Dates ─────────────────────────────────────────────────────────────────
    'unknown_date': {'th': 'ไม่พบข้อมูล', 'en': 'Unknown', 'zh': '不详'},
    'date_cal_be':  {'th': 'พ.ศ.',         'en': 'BE',      'zh': 'BE'},
    'date_cal_ce':  {'th': 'ค.ศ.',         'en': 'AD',      'zh': ''},  # zh: just year+年
    'date_cal_unk': {'th': 'ไม่พบข้อมูล',  'en': 'Unknown', 'zh': '不详'},

    # ── Buttons ───────────────────────────────────────────────────────────────
    'btn_save':     {'th': 'บันทึก',       'en': 'Save',       'zh': '保存'},
    'btn_cancel':   {'th': 'ยกเลิก',       'en': 'Cancel',     'zh': '取消'},
    'btn_edit':     {'th': 'แก้ไข',        'en': 'Edit',       'zh': '编辑'},
    'btn_delete':   {'th': 'ลบ',           'en': 'Delete',     'zh': '删除'},
    'btn_add':      {'th': 'เพิ่ม',        'en': 'Add',        'zh': '添加'},
    'btn_view':     {'th': 'ดู',           'en': 'View',       'zh': '查看'},
    'btn_back':     {'th': '← กลับ',       'en': '← Back',     'zh': '← 返回'},
    'btn_export':   {'th': 'Export เป็น Excel', 'en': 'Export to Excel', 'zh': '导出到Excel'},
    'btn_logout':   {'th': 'ออกจากระบบ',   'en': 'Logout',     'zh': '退出'},

    # ── Relations ─────────────────────────────────────────────────────────────
    'rel_spouse':      {'th': 'คู่สมรส',          'en': 'Spouse',            'zh': '配偶'},
    'rel_parent_child':{'th': 'พ่อ/แม่ → ลูก',   'en': 'Parent → Child',    'zh': '父母 → 子女'},
    'rel_parents':     {'th': 'บิดา-มารดา',        'en': 'Parents',           'zh': '父母'},
    'rel_children':    {'th': 'บุตร-ธิดา',         'en': 'Children',          'zh': '子女'},

    # ── Page titles ───────────────────────────────────────────────────────────
    'page_add_member':  {'th': 'เพิ่มสมาชิกใหม่',  'en': 'Add New Member',  'zh': '添加新成员'},
    'page_edit_member': {'th': 'แก้ไขข้อมูล',       'en': 'Edit Member',     'zh': '编辑成员'},
    'page_view_member': {'th': 'ข้อมูลสมาชิก',      'en': 'Member Profile',  'zh': '成员信息'},
    'page_relations':   {'th': 'ความสัมพันธ์',      'en': 'Relationships',   'zh': '家族关系'},
    'page_users':       {'th': 'จัดการผู้ใช้งาน',  'en': 'User Management', 'zh': '用户管理'},
    'page_audit':       {'th': 'ประวัติการใช้งาน',  'en': 'Audit Log',       'zh': '操作日志'},
    'page_export':      {'th': 'Export ข้อมูล',     'en': 'Export Data',     'zh': '数据导出'},

    # ── Errors ────────────────────────────────────────────────────────────────
    'err_required_name':  {'th': 'กรุณากรอกชื่อ',       'en': 'First name is required',  'zh': '请输入名字'},
    'err_required_lname': {'th': 'กรุณากรอกนามสกุล',    'en': 'Last name is required',   'zh': '请输入姓氏'},
    'err_no_permission':  {'th': 'ไม่มีสิทธิ์เข้าถึง',  'en': 'Access denied',           'zh': '访问被拒绝'},
    'err_not_found':      {'th': 'ไม่พบข้อมูล',          'en': 'Not found',               'zh': '未找到'},

    # ── Login ─────────────────────────────────────────────────────────────────
    'login_title':    {'th': 'ระบบลำดับวงศ์ตระกูล', 'en': 'Family Tree System', 'zh': '家谱系统'},
    'login_sub':      {'th': 'กรุณาเข้าสู่ระบบเพื่อใช้งาน',
                       'en': 'Please sign in to continue',
                       'zh': '请登录以继续'},
    'login_username': {'th': 'ชื่อผู้ใช้งาน', 'en': 'Username', 'zh': '用户名'},
    'login_password': {'th': 'รหัสผ่าน',      'en': 'Password', 'zh': '密码'},
    'login_btn':      {'th': 'เข้าสู่ระบบ',   'en': 'Sign In',  'zh': '登录'},
    'login_err':      {'th': 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง',
                       'en': 'Invalid username or password',
                       'zh': '用户名或密码错误'},
    'login_inactive': {'th': 'บัญชีนี้ถูกระงับการใช้งาน',
                       'en': 'This account has been deactivated',
                       'zh': '此账户已被停用'},

    # ── Misc ──────────────────────────────────────────────────────────────────
    'delete_confirm': {'th': 'คุณต้องการลบรายการนี้ใช่หรือไม่?\nการกระทำนี้ไม่สามารถย้อนกลับได้',
                       'en': 'Are you sure you want to delete this?\nThis action cannot be undone.',
                       'zh': '确定要删除此记录吗？\n此操作无法撤销。'},
    'sys_info':       {'th': 'ข้อมูลระบบ', 'en': 'System Info', 'zh': '系统信息'},
    'edit_history':   {'th': 'ประวัติการแก้ไข', 'en': 'Edit History', 'zh': '编辑历史'},
    'created_by':     {'th': 'บันทึกโดย',   'en': 'Created by',   'zh': '创建者'},
    'updated_by':     {'th': 'แก้ไขโดย',    'en': 'Updated by',   'zh': '修改者'},
    'no_data':        {'th': 'ไม่มีข้อมูล', 'en': 'No data',      'zh': '无数据'},
    'lang_label':     {'th': 'ภาษา',         'en': 'Language',     'zh': '语言'},

    # ── Relations page ────────────────────────────────────────────────────────
    'rel_type_col':       {'th': 'ประเภท',     'en': 'Type',          'zh': '类型'},
    'rel_person1':        {'th': 'คนที่ 1',    'en': 'Person 1',      'zh': '人员1'},
    'rel_person1_hint':   {'th': 'พ่อ/แม่ หรือ ฝ่ายหนึ่งของคู่สมรส',
                           'en': 'Parent or one side of couple',
                           'zh': '父母一方或配偶一方'},
    'rel_person2':        {'th': 'คนที่ 2',    'en': 'Person 2',      'zh': '人员2'},
    'rel_person2_hint':   {'th': 'ลูก หรือ อีกฝ่ายของคู่สมรส',
                           'en': 'Child or other side of couple',
                           'zh': '子女或配偶另一方'},
    'rel_type_select':    {'th': 'ประเภทความสัมพันธ์',
                           'en': 'Relationship Type',
                           'zh': '关系类型'},
    'rel_parent_child_opt': {'th': 'พ่อ/แม่ → ลูก (คนที่ 1 เป็นพ่อหรือแม่)',
                              'en': 'Parent → Child (Person 1 is the parent)',
                              'zh': '父母 → 子女（人员1为父母）'},
    'rel_spouse_opt':     {'th': 'คู่สมรส',    'en': 'Spouse / Partner', 'zh': '配偶'},
    'rel_married_date':   {'th': 'วันแต่งงาน (สำหรับคู่สมรส)',
                           'en': 'Wedding Date (for spouse)',
                           'zh': '婚礼日期（配偶）'},
    'rel_add_new':        {'th': 'เพิ่มความสัมพันธ์ใหม่',
                           'en': 'Add New Relationship',
                           'zh': '添加新关系'},
    'rel_added_ok':       {'th': 'เพิ่มความสัมพันธ์เรียบร้อยแล้ว',
                           'en': 'Relationship added successfully.',
                           'zh': '关系添加成功。'},
    'rel_delete_confirm': {'th': 'ลบความสัมพันธ์นี้?',
                           'en': 'Delete this relationship?',
                           'zh': '删除此关系？'},
    'rel_date_col':       {'th': 'วันที่',      'en': 'Date',          'zh': '日期'},

    # ── Export page ───────────────────────────────────────────────────────────
    'export_intro':    {'th': 'สร้างไฟล์ Excel ที่มีข้อมูลครบถ้วน พร้อม 3 หน้า:',
                        'en': 'Generate an Excel file with complete data — 3 sheets:',
                        'zh': '生成包含完整数据的Excel文件，共3个工作表：'},
    'export_sheet1':   {'th': 'แผนผังตระกูล',    'en': 'Family Tree',      'zh': '家谱图'},
    'export_sheet1d':  {'th': 'Tree แบบ indent + สีแยกรุ่น',
                        'en': 'Top-down tree with generation colors',
                        'zh': '带世代颜色的树状结构'},
    'export_sheet2':   {'th': 'ข้อมูลสมาชิก',    'en': 'Member Data',      'zh': '成员数据'},
    'export_sheet2d':  {'th': 'ตารางครบถ้วน (กรองได้)',
                        'en': 'Full table with filter',
                        'zh': '完整表格（可筛选）'},
    'export_sheet3':   {'th': 'วิธีใช้งาน',       'en': 'Instructions',     'zh': '使用说明'},
    'export_sheet3d':  {'th': 'คำแนะนำการใช้งาน', 'en': 'How to use guide', 'zh': '使用指南'},
    'export_ok':       {'th': 'Export สำเร็จ → ไฟล์ถูกบันทึกที่',
                        'en': 'Export successful → File saved at',
                        'zh': '导出成功 → 文件保存于'},
    'export_err':      {'th': 'เกิดข้อผิดพลาด:',
                        'en': 'Export failed:',
                        'zh': '导出失败：'},

    # ── Users page ────────────────────────────────────────────────────────────
    'user_add_btn':    {'th': 'เพิ่มผู้ใช้ใหม่',  'en': 'Add User',         'zh': '添加用户'},
    'user_col_name':   {'th': 'ชื่อ-นามสกุล',     'en': 'Full Name',        'zh': '姓名'},
    'user_col_status': {'th': 'สถานะ',             'en': 'Status',           'zh': '状态'},
    'user_col_login':  {'th': 'Login ล่าสุด',      'en': 'Last Login',       'zh': '最近登录'},
    'user_active':     {'th': 'ใช้งาน',            'en': 'Active',           'zh': '启用'},
    'user_inactive':   {'th': 'ระงับ',             'en': 'Disabled',         'zh': '停用'},
    'user_suspend':    {'th': 'ระงับ',             'en': 'Disable',          'zh': '停用'},
    'user_enable':     {'th': 'เปิดใช้',           'en': 'Enable',           'zh': '启用'},
    'user_you':        {'th': 'คุณ',               'en': 'You',              'zh': '你'},
    'user_never_login':{'th': 'ยังไม่เคย',         'en': 'Never',            'zh': '从未'},
    'user_added_ok':   {'th': 'เพิ่มผู้ใช้งานใหม่เรียบร้อยแล้ว',
                        'en': 'New user added successfully.',
                        'zh': '新用户添加成功。'},
    'user_updated_ok': {'th': 'อัพเดตข้อมูลเรียบร้อยแล้ว',
                        'en': 'User updated successfully.',
                        'zh': '用户更新成功。'},
    'user_pw_label_add':  {'th': 'รหัสผ่าน',
                            'en': 'Password',
                            'zh': '密码'},
    'user_pw_label_edit': {'th': 'รหัสผ่านใหม่ (ปล่อยว่าง = ไม่เปลี่ยน)',
                            'en': 'New Password (leave blank to keep current)',
                            'zh': '新密码（留空则不修改）'},
    'user_pw_hint_add':   {'th': 'อย่างน้อย 6 ตัวอักษร',
                            'en': 'Minimum 6 characters',
                            'zh': '至少6个字符'},
    'user_pw_hint_edit':  {'th': 'เว้นว่างเพื่อคงเดิม',
                            'en': 'Leave blank to keep current password',
                            'zh': '留空保留当前密码'},
    'user_role_hint':     {'th': 'admin = จัดการทุกอย่าง, user = ดูข้อมูลอย่างเดียว',
                            'en': 'admin = full access, user = read-only',
                            'zh': 'admin = 完全访问，user = 只读'},
    'user_name_placeholder': {'th': 'ชื่อ นามสกุล', 'en': 'Full name', 'zh': '姓名'},
    'user_username_placeholder': {'th': 'ตั้งชื่อผู้ใช้', 'en': 'Set username', 'zh': '设置用户名'},
    'user_err_fullname':  {'th': 'กรุณากรอกชื่อ-นามสกุล',
                            'en': 'Full name is required',
                            'zh': '请输入姓名'},
    'user_err_username':  {'th': 'กรุณากรอก username',
                            'en': 'Username is required',
                            'zh': '请输入用户名'},
    'user_err_username_alnum': {'th': 'username ต้องเป็นตัวอักษรหรือตัวเลขเท่านั้น',
                                 'en': 'Username must be alphanumeric only',
                                 'zh': '用户名只能包含字母和数字'},
    'user_err_username_dup':   {'th': 'username นี้ถูกใช้งานแล้ว',
                                 'en': 'This username is already taken',
                                 'zh': '该用户名已被使用'},
    'user_err_password':       {'th': 'กรุณากรอกรหัสผ่าน',
                                 'en': 'Password is required',
                                 'zh': '请输入密码'},
    'user_err_password_short': {'th': 'รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร',
                                 'en': 'Password must be at least 6 characters',
                                 'zh': '密码至少需要6个字符'},
    'user_form_check':         {'th': 'กรุณาตรวจสอบข้อมูลที่กรอก',
                                 'en': 'Please check the form fields.',
                                 'zh': '请检查表单字段。'},

    # ── Audit page ────────────────────────────────────────────────────────────
    'audit_title':     {'th': 'ประวัติการใช้งาน (Audit Log)',
                        'en': 'Audit Log',
                        'zh': '操作日志'},
    'audit_show':      {'th': 'แสดง:',          'en': 'Show:',            'zh': '显示：'},
    'audit_col_time':  {'th': 'เวลา',            'en': 'Time',             'zh': '时间'},
    'audit_col_action':{'th': 'การกระทำ',        'en': 'Action',           'zh': '操作'},
    'audit_col_user':  {'th': 'ผู้ใช้',           'en': 'User',             'zh': '用户'},
    'audit_col_table': {'th': 'ตาราง',            'en': 'Table',            'zh': '数据表'},
    'audit_col_record':{'th': 'Record',           'en': 'Record',           'zh': '记录'},
    'audit_col_data':  {'th': 'ข้อมูล',           'en': 'Data',             'zh': '数据'},
    'audit_col_ip':    {'th': 'IP',               'en': 'IP',               'zh': 'IP'},
    'audit_old_data':  {'th': 'ข้อมูลเดิม',       'en': 'Previous Data',    'zh': '原始数据'},
    'audit_no_history':{'th': 'ยังไม่มีประวัติ',  'en': 'No history yet',   'zh': '暂无日志'},
    'audit_last':      {'th': 'ล่าสุด',           'en': 'last',             'zh': '最近'},
}


def t(key: str, lang: str = 'th') -> str:
    """Translate a UI string key to the given language."""
    entry = _T.get(key)
    if entry is None:
        return key
    return entry.get(lang) or entry.get('th') or key


# ─── Date display helpers ─────────────────────────────────────────────────────

_TH_MONTHS_SHORT = ['ม.ค.','ก.พ.','มี.ค.','เม.ย.','พ.ค.','มิ.ย.',
                     'ก.ค.','ส.ค.','ก.ย.','ต.ค.','พ.ย.','ธ.ค.']
_EN_MONTHS_SHORT = ['Jan','Feb','Mar','Apr','May','Jun',
                    'Jul','Aug','Sep','Oct','Nov','Dec']
_ZH_MONTHS_SHORT = ['1月','2月','3月','4月','5月','6月',
                     '7月','8月','9月','10月','11月','12月']


def format_year(be_year: int | str, lang: str = 'th') -> str:
    """
    Format a Buddhist Era year into the appropriate display for `lang`.
    be_year: integer or string BE year (e.g. 2500)
    """
    if not be_year:
        return ''
    y = int(be_year)
    if lang == 'th':
        return f'พ.ศ. {y}'
    else:
        ce = y - 543
        if lang == 'zh':
            return f'{ce}年'
        else:
            return str(ce)


def format_date(stored: str, lang: str = 'th') -> str:
    """
    Convert a stored date string (BE:2500-06-15 / CE:1957 / UNKNOWN / legacy)
    to a human-readable string in the given language.
    """
    import re
    if not stored:
        return ''
    stored = stored.strip()
    if stored.upper() == 'UNKNOWN':
        return t('unknown_date', lang)

    cal = 'BE'
    date_part = stored
    if stored.startswith('BE:'):
        cal, date_part = 'BE', stored[3:]
    elif stored.startswith('CE:'):
        cal, date_part = 'CE', stored[3:]

    m = re.match(r'^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$', date_part)
    if not m:
        return stored

    year_raw, month_s, day_s = int(m.group(1)), m.group(2), m.group(3)

    # Convert to BE for internal use, then re-format per lang
    be_year = year_raw if cal == 'BE' else year_raw + 543
    ce_year = be_year - 543

    # Format year
    if lang == 'th':
        year_str = f'พ.ศ. {be_year}'
        months = _TH_MONTHS_SHORT
    elif lang == 'zh':
        year_str = f'{ce_year}年'
        months = _ZH_MONTHS_SHORT
    else:
        year_str = str(ce_year)
        months = _EN_MONTHS_SHORT

    if not month_s:
        return year_str

    try:
        mo_name = months[int(month_s) - 1]
    except (ValueError, IndexError):
        return year_str

    if day_s:
        day = int(day_s)
        if lang == 'th':
            return f'{year_str} ({day} {mo_name})'
        elif lang == 'zh':
            return f'{ce_year}年{month_s}月{day_s}日'
        else:
            return f'{day} {mo_name} {ce_year}'
    else:
        if lang == 'zh':
            return f'{ce_year}年{month_s}月'
        elif lang == 'en':
            return f'{mo_name} {ce_year}'
        else:
            return f'{year_str} ({mo_name})'


def format_year_only(stored: str, lang: str = 'th') -> str:
    """Extract and format just the year from a stored date string."""
    import re
    if not stored:
        return ''
    stored = stored.strip()
    if stored.upper() == 'UNKNOWN':
        return ''

    cal = 'BE'
    date_part = stored
    if stored.startswith('BE:'):
        cal, date_part = 'BE', stored[3:]
    elif stored.startswith('CE:'):
        cal, date_part = 'CE', stored[3:]

    m = re.match(r'^(\d{4})', date_part)
    if not m:
        return ''
    year_raw = int(m.group(1))
    be_year = year_raw if cal == 'BE' else year_raw + 543
    return format_year(be_year, lang)


def format_year_short(stored: str, lang: str = 'th') -> str:
    """Return just the numeric year (no prefix/suffix) for tree sidebar."""
    import re
    if not stored:
        return ''
    stored = stored.strip()
    if stored.upper() == 'UNKNOWN':
        return ''
    cal = 'BE'
    date_part = stored
    if stored.startswith('BE:'):
        cal, date_part = 'BE', stored[3:]
    elif stored.startswith('CE:'):
        cal, date_part = 'CE', stored[3:]
    m = re.match(r'^(\d{4})', date_part)
    if not m:
        return ''
    y = int(m.group(1))
    return str(y if cal == 'BE' else y + 543) if lang == 'th' else str((y if cal == 'BE' else y + 543) - 543)


def get_lang_from_request(handler) -> str:
    """Read ft_lang cookie from request handler."""
    cookie = handler.headers.get('Cookie', '')
    for part in cookie.split(';'):
        part = part.strip()
        if part.startswith(LANG_COOKIE + '='):
            val = part[len(LANG_COOKIE) + 1:].strip()
            if val in LANGUAGES:
                return val
    return DEFAULT_LANG


def set_lang_cookie(lang: str) -> str:
    """Return Set-Cookie header value for lang."""
    return f'{LANG_COOKIE}={lang}; Path=/; Max-Age=31536000'
