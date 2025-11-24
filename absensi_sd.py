import streamlit as st
import pandas as pd
import os
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. PENGATURAN DATA ---
# Kita gunakan st-gsheets untuk absensi
# Folder foto tetap lokal (temporary)
FOLDER_BUKTI = 'bukti_sakit'
FILE_PIN = 'data_pin.csv'

if not os.path.exists(FOLDER_BUKTI):
    os.makedirs(FOLDER_BUKTI)

# Data Default PIN (Lokal CSV)
DEFAULT_PIN = {
    "4A": "1111", "4B": "1212",
    "4C": "2222", "4D": "2323",
    "Admin": "9999"
}

# --- FUNGSI GOOGLE SHEETS (INIT) ---
def get_data_absensi():
    # Membuat koneksi
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Membaca data, ttl=0 agar selalu refresh real-time
    try:
        df = conn.read(worksheet="Absensi", ttl=0)
        return df
    except:
        return pd.DataFrame()

def kirim_data_absensi(data_baru):
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_lama = get_data_absensi()
    
    # Gabungkan data
    df_baru = pd.concat([df_lama, pd.DataFrame([data_baru])], ignore_index=True)
    
    # Update ke Sheet
    conn.update(worksheet="Absensi", data=df_baru)

# --- FUNGSI PIN (Lokal) ---
def load_data_pin():
    if not os.path.exists(FILE_PIN):
        df = pd.DataFrame(list(DEFAULT_PIN.items()), columns=['Kelas', 'PIN'])
        df['PIN'] = df['PIN'].astype(str)
        df.to_csv(FILE_PIN, index=False)
    return pd.read_csv(FILE_PIN, dtype={'PIN': str})

def update_pin(kelas, pin_baru):
    df = load_data_pin()
    df.loc[df['Kelas'] == kelas, 'PIN'] = pin_baru
    df.to_csv(FILE_PIN, index=False)

# --- 2. TAMPILAN APLIKASI ---
st.set_page_config(page_title="Absensi KELAS 4 SDIT AL USWAH 2", layout="centered", initial_sidebar_state="expanded")

# CSS Pembersih
hide_st_style = """
            <style>
            [data-testid="stToolbar"] {visibility: hidden !important; right: 2rem;}
            footer {visibility: hidden !important; display: none !important;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# HEADER
col_kiri, col_tengah, col_kanan = st.columns([1, 1, 1])
with col_tengah:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True) 

st.markdown("<h1 style='text-align: center;'>Absensi KELAS 4 SDIT AL USWAH 2</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Sistem Absensi Terintegrasi Wali Murid & Guru</p>", unsafe_allow_html=True)
st.markdown("---")

menu = st.sidebar.selectbox("Pilih Peran Anda:", ["Wali Murid (Absen)", "Guru / Admin (Rekap Data)"])

df_pin = load_data_pin()
daftar_kelas_tersedia = df_pin['Kelas'].unique()

# --- MENU WALI MURID ---
if menu == "Wali Murid (Absen)":
    st.header("📝 Form Absensi Siswa")
    
    tanggal_sekarang = datetime.now().date()
    st.info(f"📅 Absensi ini untuk hari ini: **{tanggal_sekarang.strftime('%d-%m-%Y')}**")

    st.write("Silakan isi data putra/putri Anda:")
    nama = st.text_input("Nama Lengkap Siswa")
    
    pilihan_kelas_wm = [k for k in daftar_kelas_tersedia if k != "Admin"]
    kelas = st.selectbox("Kelas", pilihan_kelas_wm)
    
    status = st.radio("Status Kehadiran", ["Hadir", "Sakit", "Ijin"])
    
    file_bukti = None
    nama_file_bukti = ""
    
    if status == "Sakit":
        st.warning("📸 Mohon upload foto surat dokter.")
        file_bukti = st.file_uploader("Upload Bukti", type=['png', 'jpg', 'jpeg'])
    
    keterangan = st.text_area("Keterangan Tambahan")

    if st.button("Kirim Absensi"):
        if nama:
            # Simpan Foto (Lokal Sementara)
            if file_bukti is not None:
                nama_file_bukti = f"{tanggal_sekarang}_{nama}_{kelas}.png".replace(" ", "_")
                path_simpan = os.path.join(FOLDER_BUKTI, nama_file_bukti)
                with open(path_simpan, "wb") as f:
                    f.write(file_bukti.getbuffer())
            
            # Simpan Data (Google Sheets)
            with st.spinner("Sedang menyimpan ke Database Sekolah..."):
                data_baru = {
                    'Tanggal': tanggal_sekarang.strftime('%Y-%m-%d'),
                    'Nama Siswa': nama,
                    'Kelas': kelas,
                    'Status': status,
                    'Keterangan': keterangan,
                    'Bukti File': nama_file_bukti
                }
                try:
                    kirim_data_absensi(data_baru)
                    st.success(f"✅ Data {nama} BERHASIL DISIMPAN Permanen!")
                except Exception as e:
                    st.error(f"Gagal koneksi ke Google Sheet: {e}")
        else:
            st.error("Mohon isi Nama Siswa.")

# --- MENU GURU ---
elif menu == "Guru / Admin (Rekap Data)":
    st.header("📊 Dashboard Guru & Admin")
    
    st.sidebar.markdown("---")
    st.sidebar.write("🔒 **Login Sistem**")
    pilihan_guru = st.sidebar.selectbox("Pilih Kelas/Jabatan", daftar_kelas_tersedia)
    password_input = st.sidebar.text_input("Masukkan PIN", type="password")
    
    data_user = df_pin[df_pin['Kelas'] == pilihan_guru].iloc[0]
    pin_benar = str(data_user['PIN'])
    
    if password_input == pin_benar:
        st.success(f"Selamat Datang, {pilihan_guru}")
        
        if pilihan_guru == "Admin":
            tab1, tab2, tab3 = st.tabs(["📊 Data Absen", "🔐 Ganti PIN Saya", "🔑 Cek Password Guru"])
            with tab3:
                st.subheader("Daftar PIN Guru")
                st.dataframe(load_data_pin(), use_container_width=True)
        else:
            tab1, tab2 = st.tabs(["📊 Data Absen", "🔐 Ganti PIN Saya"])

        with tab1:
            # Ambil Data dari Google Sheets
            try:
                df = get_data_absensi()
                # Bersihkan data kosong
                df = df.dropna(how='all') 
                # Format Tanggal
                df['Tanggal'] = pd.to_datetime(df['Tanggal']).dt.date
            except Exception as e:
                st.error("Belum ada data di Google Sheet atau koneksi putus.")
                df = pd.DataFrame()

            filter_tanggal = st.date_input("Pilih Tanggal", datetime.now())
            
            if not df.empty:
                df_hari_ini = df[df['Tanggal'] == filter_tanggal]
                
                if pilihan_guru == "Admin":
                    st.info("Mode Admin: Semua Kelas")
                    df_tampil = df_hari_ini
                else:
                    df_tampil = df_hari_ini[df_hari_ini['Kelas'] == pilihan_guru]

                st.write(f"Data Tanggal: **{filter_tanggal}**")
                
                # Tampil Tabel
                st.dataframe(df_tampil.drop(columns=['Bukti File'], errors='ignore'), use_container_width=True)
                
                # Galeri Foto
                siswa_sakit = df_tampil[df_tampil['Status'] == "Sakit"]
                if not siswa_sakit.empty:
                    st.markdown("### 📸 Galeri Bukti Sakit (Sementara)")
                    cols = st.columns(3)
                    for index, row in siswa_sakit.iterrows():
                        nama_file = str(row.get('Bukti File', ''))
                        if nama_file and nama_file.lower() != 'nan':
                            path_file = os.path.join(FOLDER_BUKTI, nama_file)
                            if os.path.exists(path_file):
                                st.image(path_file, caption=f"{row['Nama Siswa']}", width=200)
                            else:
                                st.caption(f"Foto {row['Nama Siswa']} expired/reset.")

                # Download Button
                if not df_tampil.empty:
                    st.markdown("---")
                    csv_data = df_tampil.to_csv(index=False).encode('utf-8')
                    nama_file = f"Absensi_{filter_tanggal}.csv"
                    st.download_button("📥 Download Excel/CSV", csv_data, nama_file, "text/csv")
            else:
                st.warning("Data kosong.")

        with tab2:
            st.subheader(f"Ubah PIN - {pilihan_guru}")
            col1, col2 = st.columns(2)
            with col1:
                p1 = st.text_input("PIN Baru", type="password", key="p1")
            with col2:
                p2 = st.text_input("Ulangi PIN Baru", type="password", key="p2")
            if st.button("Simpan PIN"):
                if p1 and p1 == p2:
                    update_pin(pilihan_guru, p1)
                    st.success("✅ Sukses!")
                else:
                    st.error("PIN beda.")

    elif password_input:
        st.error("PIN Salah!")
