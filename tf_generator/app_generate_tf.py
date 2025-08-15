import streamlit as st
import random
import json
import os
from datetime import datetime, time, timedelta
import pytz
from cryptography.fernet import Fernet

# ========== INITIAL SETUP ==========
# Encryption setup
def get_encryption_key():
    if not os.path.exists("secret.key"):
        key = Fernet.generate_key()
        with open("secret.key", "wb") as key_file:
            key_file.write(key)
    return open("secret.key", "rb").read()

cipher_suite = Fernet(get_encryption_key())

# ========== DATA MANAGEMENT ==========
def load_jendela():
    if os.path.exists("jendela_config.json"):
        with open("jendela_config.json", "r") as f:
            return json.load(f)
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
                
                # Validate structure
                if not isinstance(encrypted_data, dict) or "accounts" not in encrypted_data:
                    st.warning("Invalid auth_config structure - resetting")
                    return {"accounts": {}}
                
                decrypted_data = {"accounts": {}}
                for site, account_list in encrypted_data["accounts"].items():
                    if not isinstance(account_list, list):
                        st.warning(f"Skipping invalid account list for {site}")
                        continue
                        
                    decrypted_data["accounts"][site] = []
                    for account in account_list:
                        if isinstance(account, dict) and "password" in account:
                            try:
                                decrypted_account = account.copy()
                                decrypted_account["password"] = cipher_suite.decrypt(
                                    account["password"].encode()
                                ).decode()
                                decrypted_data["accounts"][site].append(decrypted_account)
                            except Exception as e:
                                st.warning(f"Failed to decrypt password for {site}: {str(e)}")
                                decrypted_data["accounts"][site].append(account)
                        else:
                            st.warning(f"Invalid account format for {site}")
                            decrypted_data["accounts"][site].append(account)
                
                return decrypted_data
        except Exception as e:
            st.error(f"Error loading auth data: {str(e)}")
    return {"accounts": {}}

def save_data():
    # Encrypt passwords before saving
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
    
    try:
        with open("auth_config.json", "w") as f:
            json.dump(accounts_data, f, indent=4)
        
        with open("jendela_config.json", "w") as f:
            json.dump(jendela, f, indent=4)
        
        with open("history_advanced.json", "w") as f:
            json.dump(history, f, indent=4)
    except Exception as e:
        st.error(f"Error saving data: {str(e)}")

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
            bank = random.choice(banks)
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
st.title("🔄 Auto Generate Transfer Anti-Banned V.1")
st.caption("Multi-Account Support | Secure Storage | Bank Matching System")

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
        st.subheader("🔁 Create Transfer Order")
    with col2:
        st.session_state.override = st.checkbox("Force Regenerate")
    
    if st.button("🚀 Generate Now", type="primary", use_container_width=True):
        if not any(jendela.values()):
            st.error("No sites registered! Add sites first in Manage Sites tab")
        else:
            with st.spinner("Processing..."):
                expired_count = generate_transfers()
                if expired_count > 0:
                    st.info(f"Auto-cleaned {expired_count} expired records")
                st.toast("✅ Generation complete!", icon="🎯")
    
    if today_key in history["history"]:
        st.divider()
        st.subheader(f"📋 Results for {today_key}")
        
        window_groups = {}
        for transfer in history["history"][today_key]:
            window = transfer["jendela"]
            window_groups.setdefault(window, []).append(transfer)
        
        cols = st.columns(3)
        for idx, (window, transfers) in enumerate(window_groups.items()):
            with cols[idx % 3]:
                with st.expander(f"🪟 {window.upper()} ({len(transfers)} transfers)", expanded=True):
                    for t in transfers:
                        # Find matching account
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
                            with st.popover("🔑 View Login Info"):
                                for acc in matched_accounts:
                                    st.write(f"👤 `{acc.get('username', 'N/A')}`")
                                    st.write(f"🔒 `{acc.get('password', 'N/A')}`")
                                    st.divider()
                        else:
                            st.warning("No login info for this bank!")
                        st.divider()

with tab2:
    st.subheader("🗃️ Site Management")
    
    crud_tabs = st.tabs(["View Sites", "Add Site", "Edit/Delete"])
    
    with crud_tabs[0]:
        st.write("### Current Sites")
        for window_name, sites in jendela.items():
            with st.expander(f"🪟 {window_name.upper()} ({len(sites)} sites)"):
                if not sites:
                    st.write("No sites in this window")
                    continue
                
                cols = st.columns(3)
                for i, (site, banks) in enumerate(sites.items()):
                    cols[i%3].markdown(f"""
                    **{site}**  
                    🏦: {', '.join(banks)}
                    """)
    
    with crud_tabs[1]:
        st.write("### Add New Site")
        with st.form("add_site_form", clear_on_submit=True):
            window = st.selectbox("Window", list(jendela.keys()))
            site_name = st.text_input("Site Name*")
            banks = st.text_input("Banks* (comma separated)", placeholder="BCA, BRI, Mandiri")
            
            if st.form_submit_button("💾 Save"):
                if not site_name or not banks:
                    st.error("Please fill all required fields")
                else:
                    jendela[window][site_name] = [b.strip() for b in banks.split(",")]
                    save_data()
                    st.success(f"Site {site_name} added to {window}!")
                    st.rerun()
    
    with crud_tabs[2]:
        st.write("### Edit Site")
        selected_window = st.selectbox("Select Window", list(jendela.keys()), key="edit_window")
        
        if jendela[selected_window]:
            selected_site = st.selectbox("Select Site", list(jendela[selected_window].keys()), key="edit_site")
            current_banks = jendela[selected_window][selected_site]
            
            with st.form("edit_site_form"):
                new_name = st.text_input("New Name", value=selected_site)
                new_banks = st.text_input("New Banks", value=", ".join(current_banks))
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Update"):
                        if new_name != selected_site:
                            del jendela[selected_window][selected_site]
                        jendela[selected_window][new_name] = [b.strip() for b in new_banks.split(",")]
                        save_data()
                        st.success("Site updated!")
                        st.rerun()
                with col2:
                    if st.form_submit_button("🗑️ Delete", type="secondary"):
                        del jendela[selected_window][selected_site]
                        save_data()
                        st.success("Site deleted!")
                        st.rerun()
        else:
            st.warning("No sites in this window")

with tab3:
    st.subheader("🔐 Account Management")
    
    # Get all available site-bank combinations
    site_bank_options = []
    for window in jendela.values():
        for site, banks in window.items():
            for bank in banks:
                site_bank_options.append(f"{site} → {bank}")
    
    acc_tabs = st.tabs(["View Accounts", "Add Account", "Edit Account"])
    
    with acc_tabs[0]:
        st.write("### Registered Accounts")
        for site in accounts.get("accounts", {}):
            with st.expander(f"🔒 {site}"):
                for acc in accounts["accounts"][site]:
                    st.write(f"🏦 **{acc.get('bank', 'N/A')}**")
                    st.write(f"👤 `{acc.get('username', 'N/A')}`")
                    st.write(f"🔒 `{'*' * len(acc.get('password', ''))}`")
                    st.divider()
    
    with acc_tabs[1]:
        st.write("### Add New Account")
        with st.form("add_account_form", clear_on_submit=True):
            site_bank = st.selectbox("Select Site & Bank*", site_bank_options)
            username = st.text_input("Username*")
            password = st.text_input("Password*", type="password")
            
            if st.form_submit_button("💾 Save Account"):
                if not all([site_bank, username, password]):
                    st.error("Please fill all fields")
                else:
                    site, bank = site_bank.split(" → ")
                    
                    # Initialize if site doesn't exist
                    if site not in accounts["accounts"]:
                        accounts["accounts"][site] = []
                    
                    # Add new account
                    accounts["accounts"][site].append({
                        "bank": bank,
                        "username": username,
                        "password": password
                    })
                    save_data()
                    st.success(f"Account for {site} ({bank}) saved!")
                    st.rerun()
    
    with acc_tabs[2]:
        st.write("### Edit Account")
        if accounts.get("accounts", {}):
            selected_site = st.selectbox("Select Site", list(accounts["accounts"].keys()), key="edit_acc_site")
            
            if selected_site in accounts["accounts"] and accounts["accounts"][selected_site]:
                # Create options for account selection
                account_options = [
                    f"{acc.get('bank', 'N/A')} | {acc.get('username', 'N/A')}" 
                    for acc in accounts["accounts"][selected_site]
                ]
                
                selected_account = st.selectbox(
                    "Select Account", 
                    account_options,
                    key="edit_acc_select"
                )
                
                # Find the actual account data
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
                            st.success("Account updated!")
                            st.rerun()
                    with col2:
                        if st.form_submit_button("🗑️ Delete", type="secondary"):
                            del accounts["accounts"][selected_site][acc_index]
                            # Remove site if no accounts left
                            if not accounts["accounts"][selected_site]:
                                del accounts["accounts"][selected_site]
                            save_data()
                            st.success("Account deleted!")
                            st.rerun()
            else:
                st.warning("No accounts for selected site")
        else:
            st.warning("No accounts registered")

if __name__ == "__main__":
    st.balloons()