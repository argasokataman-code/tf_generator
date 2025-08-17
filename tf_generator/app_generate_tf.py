import streamlit as st
import random
import json
import os
import pathlib
from datetime import datetime, time, timedelta
import pytz

# ========== CONSTANTS ==========
DEFAULT_JENDELA = {
    "jendela1": {},
    "jendela2": {},
    "jendela3": {}
}
DEFAULT_ACCOUNTS = {"accounts": {}}
DEFAULT_HISTORY = {"history": {}, "status": {}}
TIMEZONE = pytz.timezone("Asia/Jakarta")

# ========== DATA MANAGEMENT ==========
def get_config_path(filename):
    """Find config file in common locations"""
    base_dir = pathlib.Path(__file__).parent
    search_paths = [
        base_dir / filename,
        base_dir / "config" / filename,
        pathlib.Path.cwd() / filename
    ]
    for path in search_paths:
        if path.exists():
            return path
    return None

def load_jendela():
    path = get_config_path("jendela_config.json")
    if path:
        with open(path, "r") as f:
            data = json.load(f)
            if all(k in data for k in DEFAULT_JENDELA):
                return data
    return DEFAULT_JENDELA.copy()

def load_accounts():
    path = get_config_path("auth_config.json")
    if path:
        with open(path, "r") as f:
            data = json.load(f)
            if "accounts" in data:
                return data
    return DEFAULT_ACCOUNTS.copy()

def load_history():
    path = get_config_path("history_advanced.json")
    if path:
        with open(path, "r") as f:
            data = json.load(f)
            if all(k in data for k in DEFAULT_HISTORY):
                return data
    return DEFAULT_HISTORY.copy()

def save_data():
    """Save data to existing files only"""
    configs = {
        "jendela_config.json": jendela,
        "auth_config.json": accounts,
        "history_advanced.json": history
    }
    
    for filename, data in configs.items():
        path = get_config_path(filename)
        if path:
            with open(path, "w") as f:
                json.dump(data, f, indent=2)

# ========== CORE FUNCTIONS ==========
def clean_old_history():
    today = datetime.now(TIMEZONE).date()
    expired = [
        k for k in history["history"] 
        if k != "last_jendela" 
        and (today - datetime.fromisoformat(k).date()).days > 10
    ]
    for date in expired:
        del history["history"][date]
    return len(expired)

def generate_transfers():
    today = datetime.now(TIMEZONE)
    date_key = today.date().isoformat()
    
    if date_key in history["history"] and not st.session_state.get('override', False):
        return False
    
    result = []
    is_hongkong = time(14, 0) <= today.time() <= time(23, 59)
    
    for j_name, accounts_in_window in jendela.items():
        if not accounts_in_window:
            continue
            
        shuffled = random.sample(list(accounts_in_window.items()), len(accounts_in_window))
        
        for acc, banks in shuffled:
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
                "jendela": j_name
            })
    
    expired_count = clean_old_history()
    history["history"][date_key] = result
    save_data()
    return expired_count

# ========== UI COMPONENTS ==========
def show_transfer_results(date_key):
    window_groups = {}
    for transfer in history["history"].get(date_key, []):
        window_groups.setdefault(transfer["jendela"], []).append(transfer)
    
    cols = st.columns(min(3, len(window_groups)))
    for idx, (window, transfers) in enumerate(window_groups.items()):
        with cols[idx % len(cols)]:
            with st.expander(f"🪟 {window.upper()} ({len(transfers)} transfer)", True):
                for t in transfers:
                    matched = [
                        acc for acc in accounts["accounts"].get(t['akun'], [])
                        if acc.get("bank") == t['bank']
                    ]
                    
                    st.markdown(f"""
                    **{t['akun']}** → `{t['bank']}`  
                    🎮 **{t['tipe_game']}**  
                    ⏱️ {datetime.fromisoformat(t['waktu_transfer']).strftime('%H:%M')}  
                    {"🟢" if t['status_akses'] == "OK" else "🔴"} {t['status_akses']}
                    """)
                    
                    if matched:
                        with st.popover("🔑 Lihat Login"):
                            for acc in matched:
                                st.write(f"👤 `{acc.get('username', 'N/A')}`")
                                st.write(f"🔒 `{acc.get('password', 'N/A')}`")
                                st.divider()
                    st.divider()

# ========== MAIN APP ==========
def main():
    # Initialize session state
    if 'bank_count' not in st.session_state:
        st.session_state.bank_count = 1
    if 'edit_bank_count' not in st.session_state:
        st.session_state.edit_bank_count = 1
    
    # Load data
    global jendela, accounts, history
    jendela = load_jendela()
    accounts = load_accounts()
    history = load_history()
    
    st.set_page_config(layout="wide", page_title="Auto Transfer Pro")
    st.title("🔄 Auto Transfer Generator Pro")
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["Generate", "Manage Sites", "Account Management"])

    with tab1:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("🔁 Buat Urutan Transfer")
        with col2:
            st.session_state.override = st.checkbox("Force Regenerate")
        
        if st.button("🚀 Generate Sekarang", type="primary", use_container_width=True):
            if not any(jendela.values()):
                st.error("No sites registered!")
            else:
                with st.spinner("Processing..."):
                    expired_count = generate_transfers()
                    if expired_count > 0:
                        st.info(f"Cleaned {expired_count} expired entries")
                    st.success("Generated successfully!")
                    st.rerun()
        
        today_key = datetime.now(TIMEZONE).date().isoformat()
        if today_key in history["history"]:
            st.divider()
            st.subheader(f"📋 Hasil {today_key}")
            show_transfer_results(today_key)

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
                        st.session_state.bank_count = 1
                        st.success(f"Situs {site_name} ditambahkan!")
                        st.rerun()
        
        with crud_tabs[2]:
            st.write("### Edit Situs")
            selected_window = st.selectbox("Pilih Jendela", list(jendela.keys()), key="edit_window")
            
            if jendela[selected_window]:
                selected_site = st.selectbox("Pilih Situs", list(jendela[selected_window].keys()), key="edit_site")
                current_banks = jendela[selected_window][selected_site]
                
                if st.button("➕ Tambah Bank Baru", key="add_bank_edit"):
                    st.session_state.edit_bank_count = len(current_banks) + 1
                    st.rerun()
                
                with st.form("edit_site_form"):
                    new_name = st.text_input("Nama Baru", value=selected_site)
                    
                    new_banks = []
                    display_count = max(len(current_banks), st.session_state.edit_bank_count)
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
        
        site_bank_options = [
            f"{site} → {bank}"
            for window in jendela.values()
            for site, banks in window.items()
            for bank in banks
        ]
        
        acc_tabs = st.tabs(["Lihat Akun", "Tambah Akun", "Edit Akun"])
        
        with acc_tabs[0]:
            st.write("### Akun Terdaftar")
            for site, acc_list in accounts.get("accounts", {}).items():
                with st.expander(f"🔒 {site}"):
                    for acc in acc_list:
                        st.write(f"🏦 **{acc.get('bank', 'N/A')}**")
                        st.write(f"👤 `{acc.get('username', 'N/A')}`")
                        st.write(f"🔒 `{acc.get('password', 'N/A')}`")
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
                        accounts["accounts"].setdefault(site, []).append({
                            "bank": bank,
                            "username": username,
                            "password": password
                        })
                        if save_data():
                            st.success(f"Akun {username} tersimpan!")
                            st.rerun()
        
        with acc_tabs[2]:
            st.write("### Edit Akun")
            if accounts.get("accounts"):
                selected_site = st.selectbox("Situs", list(accounts["accounts"].keys()), key="edit_acc_site")
                
                if selected_site in accounts["accounts"]:
                    account_options = [
                        f"{acc.get('bank', 'N/A')} | {acc.get('username', 'N/A')}" 
                        for acc in accounts["accounts"][selected_site]
                    ]
                    selected_account = st.selectbox("Pilih Akun", account_options, key="edit_acc_select")
                    
                    acc_index = account_options.index(selected_account)
                    acc_data = accounts["accounts"][selected_site][acc_index]
                    
                    with st.form("edit_account_form"):
                        new_username = st.text_input("Username", value=acc_data.get("username", ""))
                        new_password = st.text_input("Password", value=acc_data.get("password", ""), type="password")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("💾 Update"):
                                accounts["accounts"][selected_site][acc_index].update({
                                    "username": new_username,
                                    "password": new_password
                                })
                                if save_data():
                                    st.success("Akun diperbarui!")
                                    st.rerun()
                        with col2:
                            if st.form_submit_button("🗑️ Hapus", type="secondary"):
                                del accounts["accounts"][selected_site][acc_index]
                                if not accounts["accounts"][selected_site]:
                                    del accounts["accounts"][selected_site]
                                if save_data():
                                    st.success("Akun dihapus!")
                                    st.rerun()
                else:
                    st.warning("Tidak ada akun untuk situs ini")
            else:
                st.warning("Belum ada akun terdaftar")

if __name__ == "__main__":
    main()
