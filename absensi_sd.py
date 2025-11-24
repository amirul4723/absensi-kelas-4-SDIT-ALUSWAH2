import streamlit as st
import pandas as pd
import os
from datetime import datetime
from PIL import Image

# --- 1. PENGATURAN DATA ---
FILE_ABSENSI = 'data_absensi.csv'
FILE_PIN = 'data_pin.csv'
FOLDER_BUKTI = 'bukti_sakit'

if not os.path.exists(FOLDER_BUKTI):
    os.makedirs(FOLDER_BUKTI)

# Data Default
DEFAULT_PIN = {
    "4A": "1111", "4B": "1212",
    "4C": "2222", "4D": "2323",
    "Admin": "9999"
}

# --- FUNGSI LOAD & SAVE ---
def load_data_absensi():
    if not os.path.exists(FILE_ABSENSI):
        df = pd.DataFrame(columns=['Tanggal', 'Nama Siswa', 'Kelas', 'Status', 'Keterangan', 'Bukti File'])
        df.to_csv(FILE_ABSENSI, index=False)
    return pd.read_csv(FILE_ABSENSI)

def simpan_data_absensi(data_baru):
    df = load_data_absensi()
    df = pd.concat([df, pd.DataFrame([data_baru])], ignore_index=True)
    df.to_csv(FILE_ABSENSI, index=False)

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

# --- HEADER: LOGO & JUDUL DI TENGAH ---
col_kiri, col_tengah, col_kanan = st.columns([1, 1, 1])

with col_tengah:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True) 
    else:
        st.write("") 

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
        st.warning("📸 Mohon upload foto surat dokter atau kondisi siswa.")
        file_bukti = st.file_uploader("Upload Bukti (Gambar)", type=['png', 'jpg', 'jpeg'])
    
    keterangan = st.text_area("Keterangan Tambahan (Opsional)")

    if st.button("Kirim Absensi"):
        if nama:
            if file_bukti is not None:
                nama_file_bukti = f"{tanggal_sekarang}_{nama}_{kelas}.png".replace(" ", "_")
                path_simpan = os.path.join(FOLDER_BUKTI, nama_file_bukti)
                with open(path_simpan, "wb") as f:
                    f.write(file_bukti.getbuffer())
            
            data_baru = {
                'Tanggal': tanggal_sekarang,
                'Nama Siswa': nama,
                'Kelas': kelas,
                'Status': status,
                'Keterangan': keterangan,
                'Bukti File': nama_file_bukti
            }
            simpan_data_absensi(data_baru)
            st.success(f"Terima kasih! Data absensi {nama} berhasil dikirim.")
        else:
            st.error("Mohon isi Nama Siswa.")

# --- MENU GURU / ADMIN ---
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
                st.subheader("Rahasia: Daftar PIN Guru")
                st.dataframe(load_data_pin(), use_container_width=True)
        else:
            tab1, tab2 = st.tabs(["📊 Data Absen", "🔐 Ganti PIN Saya"])

        with tab1:
            df = load_data_absensi()
            filter_tanggal = st.date_input("Pilih Tanggal", datetime.now())
            df['Tanggal'] = pd.to_datetime(df['Tanggal']).dt.date
            df_hari_ini = df[df['Tanggal'] == filter_tanggal]
            
            if pilihan_guru == "Admin":
                st.info("Mode Admin: Menampilkan Semua Kelas")
                df_tampil = df_hari_ini
            else:
                df_tampil = df_hari_ini[df_hari_ini['Kelas'] == pilihan_guru]

            st.write(f"Data Tanggal: **{filter_tanggal}**")
            
            st.dataframe(df_tampil.drop(columns=['Bukti File'], errors='ignore'), use_container_width=True)
            
            if not df_tampil.empty:
                # --- PERBAIKAN DI SINI (Penanganan Error NaN) ---
                siswa_sakit = df_tampil[df_tampil['Status'] == "Sakit"]
                
                if not siswa_sakit.empty:
                    st.markdown("### 📸 Galeri Bukti Sakit")
                    cols = st.columns(3)
                    
                    for index, row in siswa_sakit.iterrows():
                        # Ambil nama file dan paksa jadi string (str) supaya tidak error NaN
                        nama_file = str(row.get('Bukti File', ''))
                        
                        # Cek apakah nama file valid (bukan 'nan' atau kosong)
                        if nama_file and nama_file.lower() != 'nan':
                            path_file = os.path.join(FOLDER_BUKTI, nama_file)
                            
                            # Cek apakah gambarnya benar-benar ada di server
                            if os.path.exists(path_file):
                                st.image(path_file, caption=f"{row['Nama Siswa']} ({row['Kelas']})", width=200)
                            else:
                                st.write(f"⚠️ Foto {row['Nama Siswa']} tidak ditemukan di server.")
                # ------------------------------------------------
                
                st.markdown("---")
                csv_data = df_tampil.to_csv(index=False).encode('utf-8')
                nama_file = f"Absensi_SDIT_{filter_tanggal}.csv"
                st.download_button(
                    label="📥 Download Laporan (Excel/CSV)",
                    data=csv_data,
                    file_name=nama_file,
                    mime='text/csv',
                )
            else:
                st.warning("Data kosong.")

        with tab2:
            st.subheader(f"Ubah PIN - {pilihan_guru}")
            col1, col2 = st.columns(2)
            with col1:
                pin_baru_1 = st.text_input("PIN Baru", type="password", key="p1")
            with col2:
                pin_baru_2 = st.text_input("Ulangi PIN Baru", type="password", key="p2")
            
            if st.button("Simpan PIN Baru"):
                if pin_baru_1 and pin_baru_1 == pin_baru_2:
                    update_pin(pilihan_guru, pin_baru_1)
                    st.success("✅ PIN Berhasil diubah!")
                else:
                    st.error("PIN tidak cocok.")
            
    elif password_input:
        st.error("PIN Salah!")
