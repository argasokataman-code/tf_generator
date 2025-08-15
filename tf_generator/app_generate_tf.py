import streamlit as st
import random
import json
import os
from datetime import datetime, time, timedelta
import pytz
from cryptography.fernet import Fernet

# ========== INITIAL SETUP ==========
def get_encryption_key():
    if not os.path.exists("secret.key"):
        key = Fernet.generate_key()
        with open("secret.key", "wb") as key_file:
            key_file.write(key)
    return open("secret.key", "rb").read()

cipher_suite = Fernet(get_encryption_key())

# Initialize session state for dynamic bank input
if 'bank_count' not in st.session_state:
    st.session_state.bank_count = 1
if 'edit_bank_count' not in st.session_state:
    st.session_state.edit_bank_count = 1

# ========== DATA MANAGEMENT ==========
def load_jendela():
    if os.path.exists("jendela_config.json"):
        with open("jendela_config.json", "r") as f:
            data = json.load(f)
            for window in data.values():
                for site in list(window.keys()):
                    window[site] = [b for b in window[site] if b and b.strip()]
                    if not window[site]:
                        del window[site]
            return data
    return {"jendela1": {}, "jendela2": {}, "jendela3": {}}

def load_history():
    if os.path.exists("history_advanced.json"):
        with open("history_advanced.json", "r") as f:
            return json.load(f)
    return {"history": {}, "status": {}}

def load_accounts():
    if os.path.exists("auth_config.json"):
        try:
            with open("auth_config.json", "r") as f:
                encrypted_data = json.load(f)
                decrypted_data = {"accounts": {}}
                for site, account_list in encrypted_data.get("accounts", {}).items():
                    decrypted_data["accounts"][site] = []
                    for account in account_list:
                        if isinstance(account, dict) and "password" in account:
                            try:
                                decrypted_account = account.copy()
                                decrypted_account["password"] = cipher_suite.decrypt(
                                    account["password"].encode()
                                ).decode()
                                decrypted_data["accounts"][site].append(decrypted_account)
                            except:
                                decrypted_data["accounts"][site].append(account)
                return decrypted_data
        except:
            st.error("Gagal load data akun!")
    return {"accounts": {}}

def save_data():
    # Clean empty banks first
    for window in jendela.values():
        for site in list(window.keys()):
            window[site] = [b for b in window[site] if b and b.strip()]
            if not window[site]:
                del window[site]
    
    # Encrypt passwords
    accounts_data = {"accounts": {}}
    for site in accounts["accounts"]:
        accounts_data["accounts"][site] = []
        for account in accounts["accounts"][site]:
            encrypted_account = account.copy()
            if "password" in encrypted_account:
                encrypted_account["password"] = cipher_suite.encrypt(
                    account["password"].encode()
                ).decode()
            accounts_data["accounts"][site].append(encrypted_account)
    
    # Save all files
    with open("jendela_config.json", "w") as f:
        json.dump(jendela, f, indent=4)
    
    with open("auth_config.json", "w") as f:
        json.dump(accounts_data, f, indent=4)
    
    with open("history_advanced.json", "w") as f:
        json.dump(history, f, indent=4)

# ========== CORE FUNCTIONS ==========
def clean_old_history():
    today = datetime.now(pytz.timezone("Asia/Jakarta")).date()
    expired = [k for k in history["history"] 
              if k != "last_jendela" 
              and (today - datetime.fromisoformat(k).date()).days > 10]
    
    for date in expired:
        del history["history"][date]
    return len(expired)

def generate_transfers():
    today = datetime.now(pytz.timezone("Asia/Jakarta"))
    date_key = today.date().isoformat()
    
    if date_key in history["history"] and not st.session_state.get('override', False):
        return False
    
    result = []
    is_hongkong = time(14, 0) <= today.time() <= time(23, 59)
    
    for jendela_name, accounts_in_window in jendela.items():
        if not accounts_in_window:
            continue
            
        shuffled_accounts = random.sample(list(accounts_in_window.items()), len(accounts_in_window))
        
        for acc, banks in shuffled_accounts:
            valid_banks = [b for b in banks if b and b.strip()]
            if not valid_banks:
                continue
                
            bank = random.choice(valid_banks)
            status_key = f"{acc}_{bank}"
            
            result.append({
                "akun": acc,
                "bank": bank,
                "tipe_game": "Hongkong" if is_hongkong else "Sidney",
                "waktu_transfer": today.isoformat(),
                "status_akses": history["status"].get(status_key, "OK"),
                "jendela": jendela_name
            })
    
    expired_count = clean_old_history()
    history["history"][date_key] = result
    save_data()
    return expired_count

# ========== STREAMLIT UI ==========
st.set_page_config(layout="wide", page_title="Auto Transfer Pro")
st.title("🔄 Auto Transfer Generator Pro")
st.caption("Multi-Account Support | Secure Storage | Dynamic Bank Input")

# Load all data
jendela = load_jendela()
history = load_history()
accounts = load_accounts()
today_key = datetime.now(pytz.timezone("Asia/Jakarta")).date().isoformat()

# ========== MAIN TABS ==========
tab1, tab2, tab3 = st.tabs(["Generate Transfer", "Manage Sites", "Account Management"])

with tab1:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("🔁 Buat Urutan Transfer")
    with col2:
        st.session_state.override = st.checkbox("Force Regenerate")
    
    if st.button("🚀 Generate Sekarang", type="primary", use_container_width=True):
        if not any(jendela.values()):
            st.error("Belum ada situs terdaftar!")
        else:
            with st.spinner("Memproses..."):
                expired_count = generate_transfers()
                if expired_count > 0:
                    st.info(f"Data expired {expired_count} hari dihapus")
                st.success("Generate berhasil!")
    
    if today_key in history["history"]:
        st.divider()
        st.subheader(f"📋 Hasil {today_key}")
        
        window_groups = {}
        for transfer in history["history"][today_key]:
            window = transfer["jendela"]
            window_groups.setdefault(window, []).append(transfer)
        
        cols = st.columns(3)
        for idx, (window, transfers) in enumerate(window_groups.items()):
            with cols[idx % 3]:
                with st.expander(f"🪟 {window.upper()} ({len(transfers)} transfer)", expanded=True):
                    for t in transfers:
                        matched_accounts = []
                        if t['akun'] in accounts["accounts"]:
                            matched_accounts = [
                                acc for acc in accounts["accounts"][t['akun']] 
                                if acc.get("bank") == t['bank']
                            ]
                        
                        st.markdown(f"""
                        **{t['akun']}** → `{t['bank']}`  
                        🎮 **{t['tipe_game']}**  
                        ⏱️ {datetime.fromisoformat(t['waktu_transfer']).strftime('%H:%M')}  
                        {"🟢" if t['status_akses'] == "OK" else "🔴"} {t['status_akses']}
                        """)
                        
                        if matched_accounts:
                            with st.popover("🔑 Lihat Login"):
                                for acc in matched_accounts:
                                    st.write(f"👤 `{acc.get('username', 'N/A')}`")
                                    st.write(f"🔒 `{acc.get('password', 'N/A')}`")
                                    st.divider()
                        else:
                            st.warning("Tidak ada akun untuk bank ini!")
                        st.divider()

with tab2:
    st.subheader("🗃️ Kelola Situs")
    
    crud_tabs = st.tabs(["Lihat Situs", "Tambah Situs", "Edit/Hapus"])
    
    with crud_tabs[0]:
        st.write("### Daftar Situs Terdaftar")
        for window_name, sites in jendela.items():
            with st.expander(f"🪟 {window_name.upper()} ({len(sites)} situs)"):
                if not sites:
                    st.write("Belum ada situs")
                    continue
                
                cols = st.columns(3)
                for i, (site, banks) in enumerate(sites.items()):
                    cols[i%3].markdown(f"""
                    **{site}**  
                    🏦: {', '.join(banks)}
                    """)
    
    with crud_tabs[1]:
        st.write("### Tambah Situs Baru")
        
        # Tombol tambah bank di luar form
        if st.button("➕ Tambah Bank", key="add_bank_main"):
            st.session_state.bank_count += 1
            st.rerun()
        
        with st.form("add_site_form", clear_on_submit=True):
            window = st.selectbox("Jendela", list(jendela.keys()))
            site_name = st.text_input("Nama Situs*")
            
            banks = []
            for i in range(st.session_state.bank_count):
                bank = st.text_input(f"Bank {i+1}", key=f"bank_{i}", placeholder="BCA")
                if bank and bank.strip():
                    banks.append(bank.strip())
            
            if st.form_submit_button("💾 Simpan"):
                if not site_name or not banks:
                    st.error("Harap isi nama situs dan minimal 1 bank!")
                else:
                    jendela[window][site_name] = banks
                    save_data()
                    st.session_state.bank_count = 1  # Reset counter
                    st.success(f"Situs {site_name} ditambahkan!")
                    st.rerun()
    
    with crud_tabs[2]:
        st.write("### Edit Situs")
        selected_window = st.selectbox("Pilih Jendela", list(jendela.keys()), key="edit_window")
        
        if jendela[selected_window]:
            selected_site = st.selectbox("Pilih Situs", list(jendela[selected_window].keys()), key="edit_site")
            current_banks = jendela[selected_window][selected_site]
            
            # Tombol tambah bank di luar form
            if st.button("➕ Tambah Bank Baru", key="add_bank_edit"):
                st.session_state.edit_bank_count = len(current_banks) + 1
                st.rerun()
            
            with st.form("edit_site_form"):
                new_name = st.text_input("Nama Baru", value=selected_site)
                
                new_banks = []
                display_count = max(len(current_banks), st.session_state.get('edit_bank_count', 1))
                for i in range(display_count):
                    bank_value = current_banks[i] if i < len(current_banks) else ""
                    new_bank = st.text_input(f"Bank {i+1}", value=bank_value, key=f"edit_bank_{i}")
                    if new_bank and new_bank.strip():
                        new_banks.append(new_bank.strip())
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Update"):
                        if not new_banks:
                            st.error("Harap isi minimal 1 bank!")
                        else:
                            if new_name != selected_site:
                                del jendela[selected_window][selected_site]
                            jendela[selected_window][new_name] = new_banks
                            save_data()
                            st.session_state.edit_bank_count = len(new_banks)
                            st.success("Data diperbarui!")
                            st.rerun()
                with col2:
                    if st.form_submit_button("🗑️ Hapus", type="secondary"):
                        del jendela[selected_window][selected_site]
                        save_data()
                        st.success("Situs dihapus!")
                        st.rerun()
        else:
            st.warning("Tidak ada situs di jendela ini")

with tab3:
    st.subheader("🔐 Kelola Akun Login")
    
    # Get all site-bank pairs
    site_bank_options = []
    for window in jendela.values():
        for site, banks in window.items():
            for bank in banks:
                site_bank_options.append(f"{site} → {bank}")
    
    acc_tabs = st.tabs(["Lihat Akun", "Tambah Akun", "Edit Akun"])
    
    with acc_tabs[0]:
        st.write("### Akun Terdaftar")
        for site in accounts.get("accounts", {}):
            with st.expander(f"🔒 {site}"):
                for acc in accounts["accounts"][site]:
                    st.write(f"🏦 **{acc.get('bank', 'N/A')}**")
                    st.write(f"👤 `{acc.get('username', 'N/A')}`")
                    st.write(f"🔒 `{'*' * len(acc.get('password', ''))}`")
                    st.divider()
    
    with acc_tabs[1]:
        st.write("### Tambah Akun Baru")
        with st.form("add_account_form", clear_on_submit=True):
            site_bank = st.selectbox("Pilih Situs & Bank*", site_bank_options)
            username = st.text_input("Username*")
            password = st.text_input("Password*", type="password")
            
            if st.form_submit_button("💾 Simpan"):
                if not all([site_bank, username, password]):
                    st.error("Harap isi semua field!")
                else:
                    site, bank = site_bank.split(" → ")
                    
                    if site not in accounts["accounts"]:
                        accounts["accounts"][site] = []
                    
                    accounts["accounts"][site].append({
                        "bank": bank,
                        "username": username,
                        "password": password
                    })
                    save_data()
                    st.success(f"Akun {username} untuk {site} ({bank}) tersimpan!")
                    st.rerun()
    
    with acc_tabs[2]:
        st.write("### Edit Akun")
        if accounts.get("accounts", {}):
            selected_site = st.selectbox("Situs", list(accounts["accounts"].keys()), key="edit_acc_site")
            
            if selected_site in accounts["accounts"] and accounts["accounts"][selected_site]:
                account_options = [
                    f"{acc.get('bank', 'N/A')} | {acc.get('username', 'N/A')}" 
                    for acc in accounts["accounts"][selected_site]
                ]
                
                selected_account = st.selectbox(
                    "Pilih Akun", 
                    account_options,
                    key="edit_acc_select"
                )
                
                acc_index = account_options.index(selected_account)
                acc_data = accounts["accounts"][selected_site][acc_index]
                
                with st.form("edit_account_form"):
                    new_username = st.text_input("Username", value=acc_data.get("username", ""))
                    new_password = st.text_input("Password", value=acc_data.get("password", ""), type="password")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Update"):
                            accounts["accounts"][selected_site][acc_index] = {
                                "bank": acc_data.get("bank", ""),
                                "username": new_username,
                                "password": new_password
                            }
                            save_data()
                            st.success("Akun diperbarui!")
                            st.rerun()
                    with col2:
                        if st.form_submit_button("🗑️ Hapus", type="secondary"):
                            del accounts["accounts"][selected_site][acc_index]
                            if not accounts["accounts"][selected_site]:
                                del accounts["accounts"][selected_site]
                            save_data()
                            st.success("Akun dihapus!")
                            st.rerun()
            else:
                st.warning("Tidak ada akun untuk situs ini")
        else:
            st.warning("Belum ada akun terdaftar")

if __name__ == "__main__":
    st.balloons()