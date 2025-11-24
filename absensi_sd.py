import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. PENGATURAN DATA ---
# Kita tidak pakai CSV lagi untuk absensi, tapi pakai koneksi GSheets
# File PIN tetap pakai CSV lokal (atau bisa dipindah ke GSheets lain kalau mau, tapi CSV cukup untuk PIN)
FILE_PIN = 'data_pin.csv'

# Data Default PIN
DEFAULT_PIN = {
    "4A": "1111", "4B": "1212",
    "4C": "2222", "4D": "2323",
    "Admin": "9999"
}

# --- FUNGSI LOAD & SAVE GOOGLE SHEETS ---
def get_data_absensi():
    # Membuat koneksi ke Google Sheets
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Membaca data dari Worksheet bernama 'Absensi'
    # ttl=0 artinya jangan simpan memori lama (selalu ambil data terbaru real-time)
    df = conn.read(worksheet="Absensi", ttl=0)
    return df

def kirim_data_absensi(data_baru):
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_lama = get_data_absensi()
    
    # Gabungkan data lama dengan data baru
    df_baru = pd.concat([df_lama, pd.DataFrame([data_baru])], ignore_index=True)
    
    # Update ke Google Sheets
    conn.update(worksheet="Absensi", data=df_baru)

# --- FUNGSI PIN (Tetap Lokal CSV agar cepat) ---
def load_data_pin():
    if not os.path.exists(FILE_PIN):
        df = pd.DataFrame(list(DEFAULT_PIN.items()), columns=['Kelas', 'PIN'])
        df['PIN'] = df['PIN'].astype(str)
        df.to_csv(FILE_PIN, index=False)
    return pd.read_csv(FILE_PIN, dtype={'PIN': str})

def update_pin(kelas, pin_baru):
    import os # Import os di sini karena dipakai
    df = load_data_pin()
    df.loc[df['Kelas'] == kelas, 'PIN'] = pin_baru
    df.to_csv(FILE_PIN, index=False)

# --- 2. TAMPILAN APLIKASI ---
st.set_page_config(page_title="Absensi KELAS 4 SDIT AL USWAH 2", layout="centered")

# CSS Pembersih
hide_st_style = """
            <style>
            [data-testid="stToolbar"] {visibility: hidden !important; right: 2rem;}
            footer {visibility: hidden !important; display: none !important;}
            [data-testid="stDecoration"] {display: none;}
            [data-testid="stStatusWidget"] {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

st.title("🏫 Absensi KELAS 4 SDIT AL USWAH 2")
st.write("Sistem Absensi Terintegrasi Wali Murid & Guru")

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
    keterangan = st.text_area("Keterangan Tambahan (Opsional)")

    if st.button("Kirim Absensi"):
        if nama:
            with st.spinner("Sedang mengirim ke Database Sekolah..."):
                data_baru = {
                    'Tanggal': tanggal_sekarang.strftime('%Y-%m-%d'), # Format tanggal string
                    'Nama Siswa': nama,
                    'Kelas': kelas,
                    'Status': status,
                    'Keterangan': keterangan
                }
                kirim_data_absensi(data_baru)
                st.success(f"✅ Data {nama} BERHASIL DISIMPAN Permanen!")
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

        # --- ISI TAB 1: DATA ABSEN ---
        with tab1:
            # Ambil data langsung dari Google Sheets
            try:
                df = get_data_absensi()
                # Pastikan kolom Tanggal dibaca sebagai datetime
                df['Tanggal'] = pd.to_datetime(df['Tanggal']).dt.date
            except:
                st.error("Gagal mengambil data. Pastikan Google Sheet sudah disetting.")
                df = pd.DataFrame()

            filter_tanggal = st.date_input("Pilih Tanggal", datetime.now())
            
            if not df.empty:
                df_hari_ini = df[df['Tanggal'] == filter_tanggal]
                
                if pilihan_guru == "Admin":
                    st.info("Mode Admin: Menampilkan Semua Kelas")
                    df_tampil = df_hari_ini
                else:
                    df_tampil = df_hari_ini[df_hari_ini['Kelas'] == pilihan_guru]

                st.write(f"Data Tanggal: **{filter_tanggal}**")
                st.dataframe(df_tampil, use_container_width=True)
                
                if not df_tampil.empty:
                    st.write("Ringkasan Status:")
                    st.write(df_tampil['Status'].value_counts())
                    
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
                    st.warning("Belum ada data masuk hari ini.")
            else:
                st.warning("Database masih kosong.")

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
                    st.error("PIN tidak cocok.")
            
    elif password_input:
        st.error("PIN Salah!")
