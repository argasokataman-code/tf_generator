import streamlit as st
import random
import json
import os
from datetime import datetime, time
import pytz

# Data akun & bank dengan 3 jendela
jendela = {
    "jendela1": {
        "pso777": ["mandiri", "seabank", "bca"],
        "indocair": ["mandiri", "seabank", "bca"],
        "royalking4d": ["mandiri", "seabank", "bca"],
        "ceri388": ["mandiri", "seabank", "bca"]
    },
    "jendela2": {
        "ibobet": ["mandiri", "seabank", "bca"],
        "digislot": ["mandiri", "seabank", "bca"],
        "galaxy88": ["mandiri", "seabank", "bca"],
        "androslot": ["mandiri", "seabank", "bca"]
    },
    "jendela3": {
        "paman empire": ["mandiri", "seabank", "bca"],
        "indo4d": ["mandiri", "seabank", "bca"],
        "angkanet4d": ["mandiri", "seabank", "bca"],
        "vivo4d": ["mandiri", "seabank", "bca"]
    }
}

# File untuk simpan history
HISTORY_FILE = "history_advanced.json"

# Load history
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return {"history": {}, "status": {}}

# Simpan history
def save_history(data):
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Generate urutan unik dengan jendela
def generate_order(data, date_key):
    history = data["history"]
    status = data["status"]
    
    # Pilih jendela secara bergantian
    jendela_keys = list(jendela.keys())
    last_jendela = history.get("last_jendela", None)
    
    if last_jendela:
        next_idx = (jendela_keys.index(last_jendela) + 1) % len(jendela_keys)
        selected_jendela = jendela_keys[next_idx]
    else:
        selected_jendela = random.choice(jendela_keys)
    
    # Acak urutan dalam jendela terpilih
    account_list = list(jendela[selected_jendela].keys())
    random.shuffle(account_list)
    
    # Assign bank dan waktu
    result = []
    now = datetime.now(pytz.timezone("Asia/Jakarta"))
    is_hongkong = now.time() < time(11, 0)  # Sebelum jam 11 siang untuk Hongkong
    
    for acc in account_list:
        banks = jendela[selected_jendela][acc]
        bank = random.choice(banks)
        
        # Cek status terakhir
        last_status = status.get(f"{acc}_{bank}", "OK")
        
        result.append({
            "akun": acc,
            "bank": bank,
            "tipe_game": "Hongkong" if is_hongkong else "Sidney",
            "waktu_transfer": now.isoformat(),
            "status_akses": last_status,
            "jendela": selected_jendela
        })
    
    # Update data
    data["history"][date_key] = result
    data["history"]["last_jendela"] = selected_jendela
    return data

# Main UI
st.title("🔄 Advanced Transfer Generator")
st.write("Sistem 3 Jendela dengan Tracking Status Akses")

# Tab interface
tab1, tab2, tab3 = st.tabs(["Generate Transfer", "Update Status", "Laporan"])

with tab1:
    # Tanggal default = hari ini WIB
    today_wib = datetime.now(pytz.timezone("Asia/Jakarta")).date()
    date_key = st.date_input("Pilih tanggal", today_wib).isoformat()
    
    data = load_history()
    
    if st.button("Generate Transfer Hari Ini"):
        if date_key in data["history"]:
            st.warning("Data untuk tanggal ini sudah ada. Menampilkan ulang hasil.")
        else:
            data = generate_order(data, date_key)
            save_history(data)
            st.success("✅ Data berhasil di-generate!")
    
    if date_key in data["history"]:
        st.subheader(f"Hasil untuk {date_key}")
        for item in data["history"][date_key]:
            waktu = datetime.fromisoformat(item["waktu_transfer"]).strftime("%H:%M")
            st.write(f"""
            **{item['akun']}** → {item['bank']}  
            🎮 Tipe Game: {item['tipe_game']}  
            ⏰ Waktu: {waktu}  
            ✅ Status: {item['status_akses']}  
            🪟 Jendela: {item['jendela']}
            """)
            st.divider()

with tab2:
    st.subheader("Update Status Akses")
    data = load_history()
    
    # Pilih akun dan bank
    all_accounts = []
    for j in jendela.values():
        all_accounts.extend(j.items())
    
    selected_acc = st.selectbox("Pilih Akun", [acc[0] for acc in all_accounts])
    selected_bank = st.selectbox("Pilih Bank", next(acc[1] for acc in all_accounts if acc[0] == selected_acc))
    
    # Update status
    status_key = f"{selected_acc}_{selected_bank}"
    current_status = data["status"].get(status_key, "OK")
    
    new_status = st.radio("Status Akses", ["OK", "Banned", "Pending", "Lemot WD"], 
                         index=["OK", "Banned", "Pending", "Lemot WD"].index(current_status))
    
    if st.button("Simpan Status"):
        data["status"][status_key] = new_status
        save_history(data)
        st.success(f"Status {selected_acc} ({selected_bank}) diperbarui menjadi {new_status}")

with tab3:
    st.subheader("Laporan Harian")
    data = load_history()
    
    # Filter by date
    date_report = st.date_input("Pilih Tanggal Laporan", datetime.now(pytz.timezone("Asia/Jakarta")).date())
    date_str = date_report.isoformat()
    
    if date_str in data["history"]:
        st.write(f"## Laporan untuk {date_str}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### Detail Transfer")
            for item in data["history"][date_str]:
                st.write(f"""
                - Akun: {item['akun']}  
                Bank: {item['bank']}  
                Game: {item['tipe_game']}  
                Status: {item['status_akses']}
                """)
        
        with col2:
            st.write("### Statistik")
            total = len(data["history"][date_str])
            ok = sum(1 for x in data["history"][date_str] if x["status_akses"] == "OK")
            banned = sum(1 for x in data["history"][date_str] if x["status_akses"] == "Banned")
            
            st.metric("Total Transfer", total)
            st.metric("Status OK", f"{ok} ({ok/total*100:.1f}%)")
            st.metric("Status Bermasalah", f"{banned} ({banned/total*100:.1f}%)")
            
            st.write("### Jendela yang Digunakan")
            jendela_used = data["history"][date_str][0]["jendela"]
            st.write(f"Jendela: {jendela_used}")
    else:
        st.warning("Tidak ada data untuk tanggal ini")