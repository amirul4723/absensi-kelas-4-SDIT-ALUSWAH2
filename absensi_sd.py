import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. PENGATURAN DATA ---
FILE_ABSENSI = 'data_absensi.csv'
FILE_PIN = 'data_pin.csv'

# Data Default (Perhatikan: Kepala Sekolah sudah diganti Admin)
DEFAULT_PIN = {
    "4A": "1111", "4B": "1212",
    "4C": "2222", "4D": "2323",
    "Admin": "9999"  # <-- Nama baru
}

# --- FUNGSI LOAD & SAVE ---
def load_data_absensi():
    if not os.path.exists(FILE_ABSENSI):
        df = pd.DataFrame(columns=['Tanggal', 'Nama Siswa', 'Kelas', 'Status', 'Keterangan'])
        df.to_csv(FILE_ABSENSI, index=False)
    return pd.read_csv(FILE_ABSENSI)

def simpan_data_absensi(data_baru):
    df = load_data_absensi()
    df = pd.concat([df, pd.DataFrame([data_baru])], ignore_index=True)
    df.to_csv(FILE_ABSENSI, index=False)

def load_data_pin():
    if not os.path.exists(FILE_PIN):
        # Jika file belum ada, buat baru dengan data DEFAULT_PIN (ada Admin-nya)
        df = pd.DataFrame(list(DEFAULT_PIN.items()), columns=['Kelas', 'PIN'])
        df['PIN'] = df['PIN'].astype(str)
        df.to_csv(FILE_PIN, index=False)
    return pd.read_csv(FILE_PIN, dtype={'PIN': str})

def update_pin(kelas, pin_baru):
    df = load_data_pin()
    df.loc[df['Kelas'] == kelas, 'PIN'] = pin_baru
    df.to_csv(FILE_PIN, index=False)

# --- 2. TAMPILAN APLIKASI ---
st.set_page_config(page_title="Absensi KELAS 4 SDIT AL USWAH 2", layout="centered")

st.title("🏫 Aplikasi Absensi KELAS 4 SDIT AL USWAH 2")
st.write("Sistem Absensi Terintegrasi Wali Murid & Guru")

menu = st.sidebar.selectbox("Pilih Peran Anda:", ["Wali Murid (Absen)", "Guru / Admin (Rekap Data)"])

df_pin = load_data_pin()
daftar_kelas_tersedia = df_pin['Kelas'].unique()
# --- KODE CSS PEMBERSIH TAMPILAN (FINAL) ---
# --- KODE CSS PEMBERSIH TAMPILAN (VERSI FINAL & TERUJI) ---
hide_st_style = """
            <style>
            /* 1. Hilangkan Menu Kanan Atas (Titik Tiga & GitHub) */
            [data-testid="stToolbar"] {
                visibility: hidden !important;
                right: 2rem;
            }

            /* 2. Hilangkan Footer Bawah (Tulisan Made with Streamlit) */
            footer {
                visibility: hidden !important;
                display: none !important;
            }
            
            /* 3. Hilangkan Garis Warna-warni di atas header */
            [data-testid="stDecoration"] {
                display: none;
            }

            /* 4. Hilangkan indikator 'Running' di pojok kanan atas */
            [data-testid="stStatusWidget"] {
                visibility: hidden;
            }
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)
# --- MENU WALI MURID ---
if menu == "Wali Murid (Absen)":
    st.header("📝 Form Absensi Siswa")
    
    tanggal_sekarang = datetime.now().date()
    st.info(f"📅 Absensi ini untuk hari ini: **{tanggal_sekarang.strftime('%d-%m-%Y')}**")

    st.write("Silakan isi data putra/putri Anda:")
    nama = st.text_input("Nama Lengkap Siswa")
    
    # Wali Murid tidak boleh memilih 'Admin' sebagai kelas
    pilihan_kelas_wm = [k for k in daftar_kelas_tersedia if k != "Admin"]
    kelas = st.selectbox("Kelas", pilihan_kelas_wm)
    
    status = st.radio("Status Kehadiran", ["Hadir", "Sakit", "Ijin"])
    keterangan = st.text_area("Keterangan Tambahan (Opsional)")

    if st.button("Kirim Absensi"):
        if nama:
            data_baru = {
                'Tanggal': tanggal_sekarang,
                'Nama Siswa': nama,
                'Kelas': kelas,
                'Status': status,
                'Keterangan': keterangan
            }
            simpan_data_absensi(data_baru)
            st.success(f"Terima kasih! Data absensi {nama} berhasil dikirim.")
        else:
            st.error("Mohon isi Nama Siswa.")

# --- MENU GURU / ADMIN ---
elif menu == "Guru / Admin (Rekap Data)":
    st.header("📊 Dashboard Guru")
    
    st.sidebar.markdown("---")
    st.sidebar.write("🔒 **Login Sistem**")
    pilihan_guru = st.sidebar.selectbox("Pilih Kelas/Jabatan", daftar_kelas_tersedia)
    password_input = st.sidebar.text_input("Masukkan PIN", type="password")
    
    # Validasi Login
    data_user = df_pin[df_pin['Kelas'] == pilihan_guru].iloc[0]
    pin_benar = str(data_user['PIN'])
    
    if password_input == pin_benar:
        st.success(f"Selamat Datang, {pilihan_guru}")
        
        # --- LOGIKA SPESIAL ADMIN ---
        if pilihan_guru == "Admin":
            # Admin punya 3 Tab
            tab1, tab2, tab3 = st.tabs(["📊 Data Absen", "🔐 Ganti PIN Saya", "🔑 Cek Password Guru"])
            
            # TAB KHUSUS ADMIN: LIHAT SEMUA PIN
            with tab3:
                st.subheader("Rahasia: Daftar PIN Guru")
                st.warning("Halaman ini hanya untuk Admin. Gunakan jika ada guru lupa PIN.")
                df_semua_pin = load_data_pin()
                st.dataframe(df_semua_pin, use_container_width=True)
        else:
            # Guru Biasa punya 2 Tab
            tab1, tab2 = st.tabs(["📊 Data Absen", "🔐 Ganti PIN Saya"])

        # --- ISI TAB 1: DATA ABSEN ---
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

            st.dataframe(df_tampil, use_container_width=True)
            if not df_tampil.empty:
                st.write(df_tampil['Status'].value_counts())
            else:
                st.warning("Data kosong.")

        # --- ISI TAB 2: GANTI PIN ---
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
                    st.error("PIN tidak cocok atau kosong.")
            
    elif password_input:
        st.error("PIN Salah!")







