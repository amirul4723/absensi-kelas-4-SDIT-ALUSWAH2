import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. PENGATURAN DATA ---
FILE_ABSENSI = 'data_absensi.csv'
FILE_PIN = 'data_pin.csv'

# Data Default Kelas 4 SDIT
DEFAULT_PIN = {
    "4A": "1111", "4B": "1212",
    "4C": "2222", "4D": "2323",
    "Admin": "9999"
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
        df = pd.DataFrame(list(DEFAULT_PIN.items()), columns=['Kelas', 'PIN'])
        df['PIN'] = df['PIN'].astype(str)
        df.to_csv(FILE_PIN, index=False)
    return pd.read_csv(FILE_PIN, dtype={'PIN': str})

def update_pin(kelas, pin_baru):
    df = load_data_pin()
    df.loc[df['Kelas'] == kelas, 'PIN'] = pin_baru
    df.to_csv(FILE_PIN, index=False)

# --- 2. TAMPILAN APLIKASI ---
# initial_sidebar_state="expanded" memaksa menu samping terbuka saat pertama kali buka
st.set_page_config(page_title="Absensi KELAS 4 SDIT AL USWA
