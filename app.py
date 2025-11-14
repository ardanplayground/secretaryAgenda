# app.py
import streamlit as st
import pandas as pd
import datetime
import json
import os
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

# Fungsi untuk tampilan kalender
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
    
    # Isi kalender
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day != 0:
                    current_date = datetime(year, month, day)
                    date_str = current_date.strftime("%Y-%m-%d")
                    
                    # Filter events untuk hari ini
                    day_events = []
                    for event in events:
                        event_date = datetime.strptime(event['date'], "%Y-%m-%d").date()
                        if event_date == current_date.date():
                            if selected_member is None or selected_member == "Semua" or selected_member in event['members']:
                                day_events.append(event)
                    
                    # Tampilkan hari dengan event indicator
                    if day_events:
                        st.markdown(f"<div style='background-color: #e6f3ff; padding: 5px; border-radius: 5px;'>"
                                  f"<strong>{day}</strong></div>", unsafe_allow_html=True)
                        
                        # Tampilkan event preview
                        for event in day_events[:2]:  # Max 2 event preview
                            members_str = ", ".join(event['members'])
                            st.caption(f"📅 {event['title'][:15]}...")
                            st.caption(f"👥 {members_str[:10]}...")
                        
                        if len(day_events) > 2:
                            st.caption(f"+{len(day_events)-2} more")
                    else:
                        st.write(f"**{day}**")
                    
                    # Click handler untuk detail event
                    if st.button(f"Detail", key=f"detail_{date_str}", use_container_width=True):
                        st.session_state.selected_date = date_str
                        st.session_state.show_event_detail = True

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
            new_member_name = st.text_input("Nama Member")
            new_member_email = st.text_input("Email Member")
            if st.form_submit_button("Tambah Member"):
                if new_member_name:
                    member_id = len(members) + 1
                    members.append({
                        'id': member_id,
                        'name': new_member_name,
                        'email': new_member_email
                    })
                    save_data(members, st.session_state.events)
                    st.success(f"Member {new_member_name} berhasil ditambahkan!")
                    st.rerun()
    
    with col2:
        st.subheader("Daftar Member")
        if members:
            for member in members:
                col_a, col_b, col_c = st.columns([3, 2, 1])
                with col_a:
                    st.write(f"**{member['name']}**")
                with col_b:
                    st.write(member['email'])
                with col_c:
                    if st.button("Hapus", key=f"del_member_{member['id']}"):
                        members = [m for m in members if m['id'] != member['id']]
                        save_data(members, st.session_state.events)
                        st.rerun()
        else:
            st.info("Belum ada member yang terdaftar")
    
    return members

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
                event_date = st.date_input("Tanggal*", datetime.now())
                event_time = st.time_input("Waktu*", datetime.now().time())
            
            with col2:
                # Multi-select untuk members
                member_names = [member['name'] for member in members]
                selected_members = st.multiselect("Pilih Members*", member_names)
                event_description = st.text_area("Deskripsi")
            
            if st.form_submit_button("Simpan Agenda"):
                if event_title and selected_members:
                    event_id = len(events) + 1
                    new_event = {
                        'id': event_id,
                        'title': event_title,
                        'date': event_date.strftime("%Y-%m-%d"),
                        'time': event_time.strftime("%H:%M"),
                        'members': selected_members,
                        'description': event_description
                    }
                    events.append(new_event)
                    save_data(st.session_state.members, events)
                    st.success("Agenda berhasil ditambahkan!")
                    st.rerun()
                else:
                    st.error("Field dengan tanda * harus diisi!")
    
    # Daftar event
    st.subheader("Daftar Agenda")
    if events:
        for event in events:
            with st.expander(f"📅 {event['title']} - {event['date']} {event['time']}"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Tanggal:** {event['date']} {event['time']}")
                    st.write(f"**Members:** {', '.join(event['members'])}")
                    st.write(f"**Deskripsi:** {event['description']}")
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
        day_events = [e for e in events if e['date'] == selected_date]
        
        if selected_member and selected_member != "Semua":
            day_events = [e for e in day_events if selected_member in e['members']]
        
        if day_events:
            for event in day_events:
                with st.container():
                    st.markdown("---")
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.subheader(event['title'])
                        st.write(f"**Waktu:** {event['time']}")
                        st.write(f"**Members:** {', '.join(event['members'])}")
                        st.write(f"**Deskripsi:** {event['description']}")
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
        st.header("📅 Digital Secretary Calendar - Public View")
        st.info("Ini adalah tampilan publik. Login untuk edit data.")
        
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
        st.info("Ini adalah tampilan publik. Login untuk edit data.")
        
        if st.session_state.members:
            for member in st.session_state.members:
                st.write(f"**{member['name']}** - {member['email']}")
        else:
            st.info("Belum ada member yang terdaftar")
    
    elif menu == "📝 Daftar Agenda":
        st.header("📝 Daftar Agenda")
        st.info("Ini adalah tampilan publik. Login untuk edit data.")
        
        if st.session_state.events:
            for event in st.session_state.events:
                with st.expander(f"📅 {event['title']} - {event['date']} {event['time']}"):
                    st.write(f"**Tanggal:** {event['date']} {event['time']}")
                    st.write(f"**Members:** {', '.join(event['members'])}")
                    st.write(f"**Deskripsi:** {event['description']}")
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
