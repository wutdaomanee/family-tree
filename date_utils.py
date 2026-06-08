"""
Date utilities for Family Tree.
Storage format: "BE:2500", "BE:2500-06-15", "CE:1957", "CE:1957-01-20", "UNKNOWN"
Legacy (plain year/date): treated as BE.
"""
import re


def parse_date_input(year_str: str, cal: str) -> str:
    """
    Convert form input → storage string.
    year_str: '2500', '2500-06-15', '1957', etc.
    cal: 'BE' | 'CE' | 'UNKNOWN'
    """
    if cal == 'UNKNOWN' or not year_str.strip():
        return 'UNKNOWN'
    year_str = year_str.strip()
    cal = cal.upper()
    if cal not in ('BE', 'CE'):
        cal = 'BE'
    return f"{cal}:{year_str}"


def display_date(stored: str) -> str:
    """
    Convert storage string → human-readable Thai string.
    'BE:2500-06-15' → 'พ.ศ. 2500 (15 มิ.ย.)'
    'CE:1957'       → 'ค.ศ. 1957'
    'UNKNOWN'       → 'ไม่พบข้อมูล'
    '2500'          → 'พ.ศ. 2500'  (legacy)
    ''              → ''
    """
    if not stored:
        return ''
    stored = stored.strip()
    if stored in ('UNKNOWN','DECEASED'):
        return 'ไม่พบข้อมูล'

    cal = 'BE'
    date_part = stored
    if stored.startswith('BE:'):
        cal = 'BE'
        date_part = stored[3:]
    elif stored.startswith('CE:'):
        cal = 'CE'
        date_part = stored[3:]

    # parse year and optional month-day
    m = re.match(r'^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$', date_part)
    if not m:
        return stored  # fallback: show raw

    year, month, day = m.group(1), m.group(2), m.group(3)
    th_months = ['ม.ค.','ก.พ.','มี.ค.','เม.ย.','พ.ค.','มิ.ย.',
                 'ก.ค.','ส.ค.','ก.ย.','ต.ค.','พ.ย.','ธ.ค.']

    prefix = 'พ.ศ.' if cal == 'BE' else 'ค.ศ.'
    result = f'{prefix} {year}'
    if month:
        try:
            mo_name = th_months[int(month) - 1]
            result += f' ({int(day) if day else ""} {mo_name})'.replace('(  ', '(').strip('( ').strip(')')
            if day:
                result = f'{prefix} {year} ({int(day)} {mo_name})'
            else:
                result = f'{prefix} {year} ({mo_name})'
        except (ValueError, IndexError):
            pass
    return result


def display_year(stored: str, short: bool = False) -> str:
    """
    Return just the year (BE) for display.
    short=True → plain number string, suitable for math.
    'BE:2500-06-15' → '2500'
    'CE:1957'       → '2500'  (CE+543)
    'UNKNOWN'       → ''
    '2500'          → '2500'  (legacy)
    """
    if not stored:
        return ''
    stored = stored.strip()
    if stored in ('UNKNOWN','DECEASED'):
        return ''

    cal = 'BE'
    date_part = stored
    if stored.startswith('BE:'):
        cal = 'BE'
        date_part = stored[3:]
    elif stored.startswith('CE:'):
        cal = 'CE'
        date_part = stored[3:]

    m = re.match(r'^(\d{4})', date_part)
    if not m:
        return ''
    year = int(m.group(1))
    if cal == 'CE':
        year += 543  # convert to BE
    return str(year)


def form_values(stored: str) -> dict:
    """
    Parse stored date string into form field values.
    Returns {'cal': 'BE'|'CE'|'UNKNOWN', 'year': '2500', 'month': '06', 'day': '15'}
    """
    if not stored or stored.strip() == 'UNKNOWN':
        return {'cal': 'UNKNOWN', 'year': '', 'month': '', 'day': ''}
    if stored.strip() == 'DECEASED':
        return {'cal': 'DECEASED', 'year': '', 'month': '', 'day': ''}

    stored = stored.strip()
    cal = 'BE'
    date_part = stored
    if stored.startswith('BE:'):
        cal = 'BE'
        date_part = stored[3:]
    elif stored.startswith('CE:'):
        cal = 'CE'
        date_part = stored[3:]

    m = re.match(r'^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$', date_part)
    if not m:
        return {'cal': cal, 'year': date_part, 'month': '', 'day': ''}
    return {
        'cal': cal,
        'year': m.group(1) or '',
        'month': m.group(2) or '',
        'day': m.group(3) or '',
    }


def date_field_html(field_name: str, stored: str = '',
                    label: str = 'วันเกิด', required: bool = False,
                    allow_deceased: bool = False) -> str:
    """
    Render a date input group: calendar type selector + year + month + day inputs.
    If allow_deceased=True, adds "เสียชีวิต (ไม่ระบุวัน)" option for death_date field.
    """
    fv = form_values(stored)
    req = '<span style="color:var(--red)">*</span>' if required else ''
    th_months = [
        ('01','มกราคม'),('02','กุมภาพันธ์'),('03','มีนาคม'),('04','เมษายน'),
        ('05','พฤษภาคม'),('06','มิถุนายน'),('07','กรกฎาคม'),('08','สิงหาคม'),
        ('09','กันยายน'),('10','ตุลาคม'),('11','พฤศจิกายน'),('12','ธันวาคม'),
    ]

    cal_choices = [('BE','พ.ศ.'),('CE','ค.ศ.'),('UNKNOWN','ไม่พบข้อมูล')]
    if allow_deceased:
        cal_choices.append(('DECEASED','เสียชีวิต (ไม่ระบุวัน)'))

    cal_opts = ''.join(
        f'<option value="{v}" {"selected" if fv["cal"]==v else ""}>{lbl}</option>'
        for v, lbl in cal_choices
    )
    month_opts = '<option value="">-- เดือน --</option>' + ''.join(
        f'<option value="{v}" {"selected" if fv["month"]==v else ""}>{lbl}</option>'
        for v, lbl in th_months
    )
    day_opts = '<option value="">-- วัน --</option>' + ''.join(
        f'<option value="{str(d).zfill(2)}" {"selected" if fv["day"]==str(d).zfill(2) else ""}>{d}</option>'
        for d in range(1, 32)
    )

    hide_sub = fv['cal'] in ('UNKNOWN', 'DECEASED')
    return f"""<div class="field date-field" id="df-{field_name}">
      <label>{label} {req}</label>
      <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
        <select name="{field_name}_cal" class="date-cal-sel" data-target="{field_name}"
                style="width:190px;flex-shrink:0" onchange="toggleDateFields('{field_name}')">
          {cal_opts}
        </select>
        <div class="date-sub-fields" id="dsf-{field_name}"
             style="display:{{'none' if hide_sub else 'flex'}};gap:6px;flex-wrap:wrap">
          <input type="text" name="{field_name}_year" value="{fv['year']}"
                 placeholder="ปี เช่น 2500" style="width:110px">
          <select name="{field_name}_month" style="width:130px">{month_opts}</select>
          <select name="{field_name}_day" style="width:90px">{day_opts}</select>
        </div>
        <span class="date-unknown-label" id="dul-{field_name}"
              style="display:{{'inline' if hide_sub else 'none'}};
                     color:var(--muted);font-size:13px;font-style:italic">
          {{{'ไม่พบข้อมูล' if fv['cal']=='UNKNOWN' else ('เสียชีวิต (ไม่ระบุวัน)' if fv['cal']=='DECEASED' else '')}}}
        </span>
      </div>
      <div class="field-hint" style="font-size:11px">เดือนและวันไม่จำเป็น หากทราบเฉพาะปี</div>
    </div>
    <script>
    function toggleDateFields(name) {{
      var cal = document.querySelector('select[name="'+name+'_cal"]').value;
      var hide = (cal === 'UNKNOWN' || cal === 'DECEASED');
      document.getElementById('dsf-'+name).style.display = hide ? 'none' : 'flex';
      var lbl = document.getElementById('dul-'+name);
      if (hide) {{
        lbl.textContent = (cal === 'DECEASED') ? 'เสียชีวิต (ไม่ระบุวัน)' : 'ไม่พบข้อมูล';
        lbl.style.display = 'inline';
      }} else {{
        lbl.style.display = 'none';
      }}
    }}
    </script>"""


def parse_date_from_form(data: dict, field_name: str) -> str | None:
    """
    Extract and build a storage date string from POST form data.
    Returns None if empty/not present.
    """
    cal = data.get(f'{field_name}_cal', 'BE')
    year = data.get(f'{field_name}_year', '').strip()
    month = data.get(f'{field_name}_month', '').strip()
    day = data.get(f'{field_name}_day', '').strip()

    if cal in ('UNKNOWN', 'DECEASED'):
        return cal
    if not year:
        return None  # not provided

    date_str = year
    if month:
        date_str += f'-{month}'
        if day:
            date_str += f'-{day}'

    return f'{cal}:{date_str}'
