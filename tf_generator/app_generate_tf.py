import streamlit as st
# MUST be the first Streamlit command
st.set_page_config(
    layout="wide",
    page_title="Auto Transfer Pro",
    page_icon="🔄",
    menu_items={
        'Get Help': 'https://example.com',
        'Report a bug': "https://example.com",
        'About': "Auto Transfer Generator v1.0"
    }
)

# ========== IMPORTS ==========
import os
import pathlib
import random
import json
from datetime import datetime, time, timedelta
import pytz
from cryptography.fernet import Fernet

# ========== CONSTANTS ==========
DEFAULT_JENDELA = {
    "jendela1": {"Contoh Situs": ["BCA"]},
    "jendela2": {},
    "jendela3": {}
}
TIMEZONE = pytz.timezone("Asia/Jakarta")

# ========== SESSION STATE ==========
def init_session_state():
    if 'bank_count' not in st.session_state:
        st.session_state.bank_count = 1
    if 'edit_bank_count' not in st.session_state:
        st.session_state.edit_bank_count = 1
    if 'override' not in st.session_state:
        st.session_state.override = False

# ========== ENCRYPTION ==========
@st.cache_resource
def get_cipher_suite():
    key_path = "secret.key"
    if not os.path.exists(key_path):
        key = Fernet.generate_key()
        with open(key_path, "wb") as key_file:
            key_file.write(key)
    return Fernet(open(key_path, "rb").read())

# ========== DATA MANAGEMENT ==========
@st.cache_data(ttl=300)
def load_jendela():
    """Load window configuration with fallback"""
    try:
        possible_paths = [
            pathlib.Path(__file__).parent / "jendela_config.json",
            pathlib.Path("/workspaces/tf_generator/jendela_config.json"),
            pathlib.Path("jendela_config.json")
        ]
        
        for path in possible_paths:
            if path.exists():
                with open(path, "r") as f:
                    data = json.load(f)
                    if not all(k in data for k in DEFAULT_JENDELA):
                        raise ValueError("Invalid structure")
                    return data
                
        # Create default if not found
        with open("jendela_config.json", "w") as f:
            json.dump(DEFAULT_JENDELA, f)
        return DEFAULT_JENDELA
        
    except Exception as e:
        st.error(f"Config error: {str(e)}")
        return DEFAULT_JENDELA

@st.cache_data(ttl=300)
def load_history():
    """Load history with empty fallback"""
    try:
        if os.path.exists("history_advanced.json"):
            with open("history_advanced.json", "r") as f:
                return json.load(f)
    except Exception as e:
        st.error(f"History error: {str(e)}")
    return {"history": {}, "status": {}}

def load_accounts(_cipher):
    """Load encrypted accounts"""
    try:
        if os.path.exists("auth_config.json"):
            with open("auth_config.json", "r") as f:
                encrypted = json.load(f)
                decrypted = {"accounts": {}}
                for site, acc_list in encrypted.get("accounts", {}).items():
                    decrypted["accounts"][site] = []
                    for acc in acc_list:
                        try:
                            dec_acc = acc.copy()
                            if "password" in dec_acc:
                                dec_acc["password"] = _cipher.decrypt(
                                    acc["password"].encode()
                                ).decode()
                            decrypted["accounts"][site].append(dec_acc)
                        except Exception as e:
                            st.error(f"Decrypt error for {site}: {str(e)}")
                            decrypted["accounts"][site].append(acc)
                return decrypted
    except Exception as e:
        st.error(f"Account load error: {str(e)}")
    return {"accounts": {}}

def save_data(jendela, accounts, history, cipher):
    """Save all data with encryption"""
    try:
        # Clean empty data
        for window in jendela.values():
            for site in list(window.keys()):
                window[site] = [b for b in window[site] if b and b.strip()]
                if not window[site]:
                    del window[site]
        
        # Encrypt sensitive data
        encrypted_acc = {"accounts": {}}
        for site, acc_list in accounts["accounts"].items():
            encrypted_acc["accounts"][site] = []
            for acc in acc_list:
                enc_acc = acc.copy()
                if "password" in enc_acc:
                    enc_acc["password"] = cipher.encrypt(
                        acc["password"].encode()
                    ).decode()
                encrypted_acc["accounts"][site].append(enc_acc)
        
        # Save files
        with open("jendela_config.json", "w") as f:
            json.dump(jendela, f, indent=2)
        
        with open("auth_config.json", "w") as f:
            json.dump(encrypted_acc, f, indent=2)
            
        with open("history_advanced.json", "w") as f:
            json.dump(history, f, indent=2)
            
        st.cache_data.clear()
        return True
        
    except Exception as e:
        st.error(f"Save failed: {str(e)}")
        return False

# ========== CORE FUNCTIONS ==========
def clean_old_history(history):
    """Remove entries older than 10 days"""
    try:
        today = datetime.now(TIMEZONE).date()
        expired = [
            k for k in history["history"] 
            if k != "last_jendela" 
            and (today - datetime.fromisoformat(k).date()).days > 10
        ]
        for date in expired:
            del history["history"][date]
        return len(expired)
    except Exception as e:
        st.error(f"Clean history error: {str(e)}")
        return 0

def generate_transfers(jendela, history, override=False):
    """Generate new transfer sequence"""
    try:
        today = datetime.now(TIMEZONE)
        date_key = today.date().isoformat()
        
        if date_key in history["history"] and not override:
            return False, 0
        
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
        
        expired = clean_old_history(history)
        history["history"][date_key] = result
        return True, expired
        
    except Exception as e:
        st.error(f"Generate error: {str(e)}")
        return False, 0

# ========== UI COMPONENTS ==========
def show_transfer_results(date_key, history, accounts):
    """Display transfer results"""
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
                    else:
                        st.warning("No account for this bank!")
                    st.divider()

# ========== MAIN APP ==========
def main():
    # Initialize
    cipher = get_cipher_suite()
    init_session_state()
    
    # Load data
    jendela = load_jendela()
    history = load_history()
    accounts = load_accounts(cipher)
    
    # UI Header
    st.title("🔄 Auto Transfer Generator Pro")
    st.caption("Multi-Account Support | Secure Storage | Dynamic Bank Input")
    
    # Debug info (collapsible)
    with st.expander("🔧 Debug Info", False):
        st.write("Current directory:", os.getcwd())
        st.write("Files:", os.listdir())
        st.write("Jendela structure:", jendela.keys())
    
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
                    success, expired = generate_transfers(
                        jendela, 
                        history,
                        st.session_state.override
                    )
                    if success:
                        if expired > 0:
                            st.info(f"Cleaned {expired} expired entries")
                        if save_data(jendela, accounts, history, cipher):
                            st.success("Generated successfully!")
                            st.rerun()
        
        today_key = datetime.now(TIMEZONE).date().isoformat()
        if today_key in history["history"]:
            st.divider()
            st.subheader(f"📋 Hasil {today_key}")
            show_transfer_results(today_key, history, accounts)
    
    # [Rest of your tab2 and tab3 UI code remains the same...]
    # (Include your existing tab2 and tab3 implementations here)

if __name__ == "__main__":
    main()