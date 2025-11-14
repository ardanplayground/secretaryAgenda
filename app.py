# app.py
import streamlit as st
import pandas as pd
import datetime
import json
import os
import re
from datetime import datetime, timedelta
import calendar

# Konfigurasi halaman
st.set_page_config(
    page_title="Digital Secretary Calendar",
    page_icon="📅",
    layout="wide"
)

# Password untuk CRUD operations (plain text)
CRUD_PASSWORD = "digital"

# Fungsi untuk load/save data
def load_data():
    try:
        if os.path.exists('members.json'):
            with open('members.json', 'r') as f:
                members = json.load(f)
        else:
            members = []
        
        if os.path.exists('events.json'):
            with open('events.json', 'r') as f:
                events = json.load(f)
        else:
            events = []
        
        return members, events
    except:
        return [], []

def save_data(members, events):
    with open('members.json', 'w') as f:
        json.dump(members, f)
    with open('events.json', 'w') as f:
        json.dump(events, f)

# Fungsi untuk check CRUD access
def check_crud_access():
    if 'crud_authenticated' not in st.session_state:
        st.session_state.crud_authenticated = False
    return st.session_state.crud_authenticated

# Fungsi untuk login CRUD
def crud_login():
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔐 Akses CRUD")
    
    if not check_crud_access():
        password = st.sidebar.text_input("Password CRUD:", type="password", key="crud_password")
        if st.sidebar.button("Login CRUD"):
            if password == CRUD_PASSWORD:
                st.session_state.crud_authenticated = True
                st.rerun()
            else:
                st.sidebar.error("Password CRUD salah!")
        return False
    else:
        st.sidebar.success("✅ CRUD Access Granted")
        if st.sidebar.button("🚪 Logout CRUD"):
            st.session_state.crud_authenticated = False
            st.rerun()
        return True

# Fungsi untuk convert URL ke link HTML
def convert_urls_to_links(text):
    if not text:
        return text
    
    # Pattern untuk mendeteksi URL
    url_pattern = r'https?://[^\s]+'
    
    def replace_url(match):
        url = match.group(0)
        return f'<a href="{url}" target="_blank" style="color: blue; text-decoration: underline;">{url}</a>'
    
    # Replace URLs dengan link HTML
    text_with_links = re.sub(url_pattern, replace_url, text)
    
    return text_with_links

# Fungsi untuk parse tanggal dari format Indonesia
def parse_indonesian_date(date_str):
    try:
        # Format: dd-mm-yyyy
        day, month, year = map(int, date_str.split('-'))
        return datetime(year, month, day)
    except:
        return None

# Fungsi untuk format tanggal ke Indonesia
def format_indonesian_date(date_obj):
    return date_obj.strftime("%d-%m-%Y")

# Fungsi untuk validasi waktu
def validate_time(time_str):
    try:
        # Format: HH:MM atau HH:MM:SS
        parts = time_str.split(':')
        if len(parts) == 2:
            hours, minutes = map(int, parts)
            seconds = 0
        elif len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
        else:
            return False
        
        return 0 <= hours <= 23 and 0 <= minutes <= 59 and 0 <= seconds <= 59
    except:
        return False

# Fungsi untuk sorting events by date yang aman
def safe_sort_events(events):
    def get_event_date(event):
        try:
            return parse_indonesian_date(event['date'])
        except:
            # Return tanggal sangat lama untuk event yang tidak valid
            return datetime(1900, 1, 1)
    
    return sorted(events, key=get_event_date)

# Fungsi untuk tampilan kalender dengan highlight tanggal sekarang
def display_calendar(events, selected_member=None, year=None, month=None):
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month
    
    # Navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("← Bulan Sebelumnya"):
            if month == 1:
                month = 12
                year -= 1
            else:
                month -= 1
            st.session_state.calendar_month = month
            st.session_state.calendar_year = year
            st.rerun()
    
    with col2:
        st.title(f"{calendar.month_name[month]} {year}")
    
    with col3:
        if st.button("Bulan Selanjutnya →"):
            if month == 12:
                month = 1
                year += 1
            else:
                month += 1
            st.session_state.calendar_month = month
            st.session_state.calendar_year = year
            st.rerun()
    
    # Calendar grid
    cal = calendar.monthcalendar(year, month)
    
    # Header hari
    days = ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min']
    cols = st.columns(7)
    for i, day in enumerate(days):
        cols[i].write(f"**{day}**")
    
    # Dapatkan tanggal hari ini
    today = datetime.now().date()
    
    # Isi kalender
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day != 0:
                    current_date = datetime(year, month, day)
                    date_str = format_indonesian_date(current_date)
                    is_today = current_date.date() == today
                    
                    # Filter events untuk hari ini
                    day_events = []
                    for event in events:
                        try:
                            event_date = parse_indonesian_date(event['date'])
                            if event_date and event_date.date() == current_date.date():
                                if selected_member is None or selected_member == "Semua" or selected_member in event['members']:
                                    day_events.append(event)
                        except:
                            continue
                    
                    # Tampilkan tanggal dengan styling berbeda untuk hari ini
                    if is_today:
                        # Highlight untuk hari ini - background kuning
                        day_display = f"<div style='background-color: #FFF9C4; padding: 8px; border-radius: 8px; border: 2px solid #FFD600; text-align: center;'><strong>{day}</strong></div>"
                    else:
                        day_display = f"<div style='padding: 8px; text-align: center;'><strong>{day}</strong></div>"
                    
                    # Tambah badge dengan jumlah event jika ada
                    if day_events:
                        badge_color = "#ff4b4b" if len(day_events) > 3 else "#1f77b4"
                        badge_text = f"<span style='background-color: {badge_color}; color: white; border-radius: 50%; padding: 2px 6px; font-size: 0.8em; margin-left: 5px;'>{len(day_events)}</span>"
                        day_display = day_display.replace("</div>", f" {badge_text}</div>")
                    
                    st.markdown(day_display, unsafe_allow_html=True)
                    
                    # Click handler untuk detail event
                    if st.button(f"📅 Detail", key=f"detail_{date_str}", use_container_width=True):
                        st.session_state.selected_date = date_str
                        st.session_state.show_event_detail = True

# ... (Fungsi-fungsi lainnya tetap sama seperti sebelumnya: manage_members, time_input_with_manual, date_input_indonesia, manage_events, show_day_events, public_view, main)

# Fungsi untuk manajemen member (HANYA dengan akses CRUD)
def manage_members(members):
    if not check_crud_access():
        st.warning("🔐 Akses CRUD diperlukan untuk mengelola member")
        if st.button("Login untuk Akses CRUD"):
            st.session_state.show_crud_login = True
            st.rerun()
        return members
    
    st.header("👥 Manajemen Member")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Tambah Member Baru")
        with st.form("add_member"):
            new_member_name = st.text_input("Nama Member*")
            if st.form_submit_button("Tambah Member"):
                if new_member_name:
                    member_id = len(members) + 1
                    members.append({
                        'id': member_id,
                        'name': new_member_name
                    })
                    save_data(members, st.session_state.events)
                    st.success(f"Member {new_member_name} berhasil ditambahkan!")
                    st.rerun()
                else:
                    st.error("Nama member harus diisi!")
    
    with col2:
        st.subheader("Daftar Member")
        if members:
            for member in members:
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.write(f"**{member['name']}**")
                with col_b:
                    if st.button("Hapus", key=f"del_member_{member['id']}"):
                        members = [m for m in members if m['id'] != member['id']]
                        save_data(members, st.session_state.events)
                        st.rerun()
        else:
            st.info("Belum ada member yang terdaftar")
    
    return members

# Fungsi untuk input waktu manual
def time_input_with_manual(label, value=None):
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Input manual
        default_time = value.strftime("%H:%M") if value else "09:00"
        time_str = st.text_input(
            f"{label} (HH:MM atau HH:MM:SS)", 
            value=default_time,
            help="Format: HH:MM atau HH:MM:SS, contoh: 14:30 atau 14:30:00"
        )
    
    with col2:
        # Quick pick buttons
        st.write("Cepat:")
        quick_cols = st.columns(3)
        with quick_cols[0]:
            if st.button("09:00", key=f"quick_9_{label}"):
                time_str = "09:00"
        with quick_cols[1]:
            if st.button("13:00", key=f"quick_13_{label}"):
                time_str = "13:00"
        with quick_cols[2]:
            if st.button("16:00", key=f"quick_16_{label}"):
                time_str = "16:00"
    
    # Validasi waktu
    if time_str and validate_time(time_str):
        return time_str
    elif time_str:
        st.error("Format waktu tidak valid. Gunakan HH:MM atau HH:MM:SS")
        return None
    else:
        return None

# Fungsi untuk input tanggal Indonesia
def date_input_indonesia(label, value=None):
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Input manual format Indonesia
        default_date = format_indonesian_date(value) if value else format_indonesian_date(datetime.now())
        date_str = st.text_input(
            f"{label} (DD-MM-YYYY)", 
            value=default_date,
            help="Format: DD-MM-YYYY, contoh: 25-12-2024"
        )
    
    with col2:
        # Quick pick untuk tanggal
        st.write("Cepat:")
        quick_cols = st.columns(2)
        with quick_cols[0]:
            if st.button("Hari ini", key=f"today_{label}"):
                date_str = format_indonesian_date(datetime.now())
        with quick_cols[1]:
            if st.button("Besok", key=f"tomorrow_{label}"):
                date_str = format_indonesian_date(datetime.now() + timedelta(days=1))
    
    # Parse tanggal
    if date_str:
        parsed_date = parse_indonesian_date(date_str)
        if parsed_date:
            return parsed_date
        else:
            st.error("Format tanggal tidak valid. Gunakan DD-MM-YYYY")
            return None
    else:
        return None

# Fungsi untuk manajemen event (HANYA dengan akses CRUD)
def manage_events(events, members):
    if not check_crud_access():
        st.warning("🔐 Akses CRUD diperlukan untuk mengelola agenda")
        if st.button("Login untuk Akses CRUD"):
            st.session_state.show_crud_login = True
            st.rerun()
        return events
    
    st.header("📅 Manajemen Agenda")
    
    # Form tambah event
    with st.expander("➕ Tambah Agenda Baru", expanded=False):
        with st.form("add_event"):
            col1, col2 = st.columns(2)
            
            with col1:
                event_title = st.text_input("Judul Agenda*")
                
                # Input tanggal format Indonesia
                event_date = date_input_indonesia("Tanggal*", datetime.now())
                
                # Input waktu manual
                event_time = time_input_with_manual("Waktu*", datetime.now())
            
            with col2:
                # Multi-select untuk members
                member_names = [member['name'] for member in members]
                selected_members = st.multiselect("Pilih Members*", member_names)
                event_description = st.text_area("Deskripsi (bisa berisi link)")
            
            if st.form_submit_button("Simpan Agenda"):
                if event_title and selected_members and event_date and event_time:
                    event_id = len(events) + 1
                    new_event = {
                        'id': event_id,
                        'title': event_title,
                        'date': format_indonesian_date(event_date),
                        'time': event_time,
                        'members': selected_members,
                        'description': event_description
                    }
                    events.append(new_event)
                    save_data(st.session_state.members, events)
                    st.success("Agenda berhasil ditambahkan!")
                    st.rerun()
                else:
                    st.error("Field dengan tanda * harus diisi dengan format yang benar!")
    
    # Daftar event
    st.subheader("Daftar Agenda")
    if events:
        # Urutkan events menggunakan fungsi safe sort
        sorted_events = safe_sort_events(events)
        
        for event in sorted_events:
            with st.expander(f"📅 {event['title']} - {event['date']} {event['time']}"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Tanggal:** {event['date']}")
                    st.write(f"**Waktu:** {event['time']}")
                    st.write(f"**Members:** {', '.join(event['members'])}")
                    
                    # Tampilkan deskripsi dengan link yang bisa diklik
                    if event['description']:
                        description_with_links = convert_urls_to_links(event['description'])
                        st.write(f"**Deskripsi:**")
                        st.markdown(description_with_links, unsafe_allow_html=True)
                
                with col2:
                    if st.button("Hapus", key=f"del_event_{event['id']}"):
                        events = [e for e in events if e['id'] != event['id']]
                        save_data(st.session_state.members, events)
                        st.rerun()
    else:
        st.info("Belum ada agenda yang terdaftar")
    
    return events

# Fungsi untuk menampilkan detail event per hari (PUBLIC ACCESS)
def show_day_events(events, selected_member=None):
    if 'selected_date' in st.session_state and st.session_state.show_event_detail:
        selected_date = st.session_state.selected_date
        st.header(f"📅 Agenda untuk {selected_date}")
        
        # Filter events untuk tanggal yang dipilih
        day_events = []
        for event in events:
            try:
                if event['date'] == selected_date:
                    if selected_member is None or selected_member == "Semua" or selected_member in event['members']:
                        day_events.append(event)
            except:
                continue
        
        if day_events:
            # Urutkan berdasarkan waktu dengan error handling
            def get_event_time(event):
                try:
                    time_parts = list(map(int, event['time'].split(':')))
                    return time_parts[0] * 3600 + time_parts[1] * 60 + (time_parts[2] if len(time_parts) > 2 else 0)
                except:
                    return 0
            
            sorted_day_events = sorted(day_events, key=get_event_time)
            
            for event in sorted_day_events:
                with st.container():
                    st.markdown("---")
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.subheader(event['title'])
                        st.write(f"**Waktu:** {event['time']}")
                        st.write(f"**Members:** {', '.join(event['members'])}")
                        
                        # Tampilkan deskripsi dengan link yang bisa diklik
                        if event['description']:
                            description_with_links = convert_urls_to_links(event['description'])
                            st.write(f"**Deskripsi:**")
                            st.markdown(description_with_links, unsafe_allow_html=True)
                    
                    with col2:
                        # Hanya tampilkan tombol hapus jika ada akses CRUD
                        if check_crud_access():
                            if st.button("Hapus", key=f"del_{event['id']}"):
                                events.remove(event)
                                save_data(st.session_state.members, events)
                                st.rerun()
        else:
            st.info("Tidak ada agenda untuk hari ini")
        
        if st.button("Kembali ke Kalender"):
            st.session_state.show_event_detail = False
            st.rerun()

# Fungsi untuk view public (tanpa password)
def public_view():
    st.sidebar.info("👁️ Mode View Public")
    
    # Load data
    if 'members' not in st.session_state or 'events' not in st.session_state:
        members, events = load_data()
        st.session_state.members = members
        st.session_state.events = events
    
    # Initialize session state variables
    if 'calendar_month' not in st.session_state:
        st.session_state.calendar_month = datetime.now().month
    if 'calendar_year' not in st.session_state:
        st.session_state.calendar_year = datetime.now().year
    if 'show_event_detail' not in st.session_state:
        st.session_state.show_event_detail = False
    
    # Sidebar
    st.sidebar.title("🎯 Navigasi")
    
    # Filter member
    member_names = ["Semua"] + [member['name'] for member in st.session_state.members]
    selected_member = st.sidebar.selectbox("Filter by Member:", member_names)
    
    # Menu navigasi (hanya view untuk public)
    menu = st.sidebar.radio("Menu:", ["📅 Kalender View", "👥 Daftar Member", "📝 Daftar Agenda"])
    
    # Main content
    if menu == "📅 Kalender View":
        st.header("📅 Digital Secretary Calendar")
        
        # Tampilkan kalender
        display_calendar(
            st.session_state.events, 
            selected_member,
            st.session_state.calendar_year,
            st.session_state.calendar_month
        )
        
        # Tampilkan detail event jika ada tanggal yang dipilih
        show_day_events(st.session_state.events, selected_member)
    
    elif menu == "👥 Daftar Member":
        st.header("👥 Daftar Member")
        
        if st.session_state.members:
            for member in st.session_state.members:
                st.write(f"• **{member['name']}**")
        else:
            st.info("Belum ada member yang terdaftar")
    
    elif menu == "📝 Daftar Agenda":
        st.header("📝 Daftar Agenda")
        
        if st.session_state.events:
            # Urutkan events menggunakan fungsi safe sort
            sorted_events = safe_sort_events(st.session_state.events)
            
            for event in sorted_events:
                with st.expander(f"📅 {event['title']} - {event['date']} {event['time']}"):
                    st.write(f"**Tanggal:** {event['date']}")
                    st.write(f"**Waktu:** {event['time']}")
                    st.write(f"**Members:** {', '.join(event['members'])}")
                    
                    # Tampilkan deskripsi dengan link yang bisa diklik
                    if event['description']:
                        description_with_links = convert_urls_to_links(event['description'])
                        st.write(f"**Deskripsi:**")
                        st.markdown(description_with_links, unsafe_allow_html=True)
        else:
            st.info("Belum ada agenda yang terdaftar")

# Main application
def main():
    # Load data pertama kali
    if 'members' not in st.session_state or 'events' not in st.session_state:
        members, events = load_data()
        st.session_state.members = members
        st.session_state.events = events
    
    # Initialize session state
    if 'show_crud_login' not in st.session_state:
        st.session_state.show_crud_login = False
    
    # Check jika user ingin CRUD access
    has_crud_access = crud_login()
    
    if has_crud_access:
        # Tampilan dengan akses CRUD penuh
        st.sidebar.success("🎯 Mode CRUD Active")
        
        # Initialize session state variables untuk CRUD mode
        if 'calendar_month' not in st.session_state:
            st.session_state.calendar_month = datetime.now().month
        if 'calendar_year' not in st.session_state:
            st.session_state.calendar_year = datetime.now().year
        if 'show_event_detail' not in st.session_state:
            st.session_state.show_event_detail = False
        
        # Sidebar navigation untuk CRUD mode
        st.sidebar.title("🎯 Navigasi CRUD")
        
        # Filter member
        member_names = ["Semua"] + [member['name'] for member in st.session_state.members]
        selected_member = st.sidebar.selectbox("Filter by Member:", member_names, key="crud_filter")
        
        # Menu navigasi CRUD
        menu = st.sidebar.radio("Menu CRUD:", ["📅 Kalender", "👥 Kelola Member", "📝 Kelola Agenda"], key="crud_menu")
        
        # Main content untuk CRUD mode
        if menu == "📅 Kalender":
            st.header("📅 Digital Secretary Calendar - CRUD Mode")
            
            # Tampilkan kalender
            display_calendar(
                st.session_state.events, 
                selected_member,
                st.session_state.calendar_year,
                st.session_state.calendar_month
            )
            
            # Tampilkan detail event jika ada tanggal yang dipilih
            show_day_events(st.session_state.events, selected_member)
        
        elif menu == "👥 Kelola Member":
            updated_members = manage_members(st.session_state.members)
            st.session_state.members = updated_members
        
        elif menu == "📝 Kelola Agenda":
            updated_events = manage_events(st.session_state.events, st.session_state.members)
            st.session_state.events = updated_events
    
    else:
        # Tampilan public (tanpa akses CRUD)
        public_view()

if __name__ == "__main__":
    main()
