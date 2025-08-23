from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import re

# Setup Chrome Driver
service = Service(executable_path='/Users/vanviakingali/chromedriver/chromedriver')
options = webdriver.ChromeOptions()
options.binary_location = '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(service=service, options=options)

def is_real_time(text, cell_element):
    """Deteksi apakah angka benar-benar merepresentasikan jam"""
    text = str(text).strip()
    
    # Cek parent element untuk konteks
    try:
        parent_html = cell_element.find_element(By.XPATH, "./..").get_attribute("outerHTML")
        # Jika ada indikator waktu/jam di HTML sekitar
        if "jam" in parent_html.lower() or "time" in parent_html.lower():
            return True
    except:
        pass
    
    # Filter khusus untuk format jam yang ketat
    if len(text) == 4:
        hours = int(text[:2])
        minutes = int(text[2:])
        # Hanya angka dengan format jam yang valid (00:00-23:59)
        if 0 <= hours <= 23 and 0 <= minutes <= 59:
            # Jam-jam spesifik yang ingin difilter
            if text in {'0001', '1300', '1600', '1900', '2200', '2300'}:
                return True
    return False

def is_nomor_urut(text):
    """Deteksi kolom nomor urut (1-3 digit)"""
    text = str(text).strip()
    return text.isdigit() and 1 <= len(text) <= 3

def clean_number(text, cell_element=None):
    """Bersihkan angka dengan konteks yang lebih cerdas"""
    if pd.isna(text) or not str(text).strip():
        return None
    
    text = str(text).strip()
    cleaned = re.sub(r"[^\d]", "", text)
    
    # Skip hanya jika benar-benar jam (dengan konteks)
    if cell_element and is_real_time(text, cell_element):
        return None
    
    # Terima semua 4 digit lainnya
    return cleaned if len(cleaned) == 4 else None

def process_table(table):
    all_rows = []
    try:
        rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
        for i, row in enumerate(rows):  # Tambahkan enumerasi
            # Skip 2 baris pertama
            if i < 2:
                continue
                
            cells = row.find_elements(By.TAG_NAME, "td")
            row_data = []
            
            start_idx = 1 if cells and is_nomor_urut(cells[0].text) else 0
            
            for cell in cells[start_idx:]:
                cleaned = clean_number(cell.text)
                if cleaned is not None:
                    row_data.append(cleaned)
            
            if len(row_data) >= 3:
                all_rows.append(row_data)

        # Hapus kolom kosong di kanan
        max_len = max(len(r) for r in all_rows)
        cleaned_rows = []
        for row in all_rows:
            # Cari index terakhir yang berisi data
            last_idx = len(row) - 1
            while last_idx >= 0 and row[last_idx] == "":
                last_idx -= 1
            cleaned_rows.append(row[:last_idx+1])
        
        return pd.DataFrame(cleaned_rows)

    except Exception as e:
        print(f"Error processing table: {str(e)}")
        return pd.DataFrame()

try:
    print("Mengakses situs paito...")
    driver.get("http://178.128.80.8/")
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    print("Memproses tabel...")
    all_tables = driver.find_elements(By.TAG_NAME, "table")
    dfs = []

    for table in all_tables:
        try:
            h3_above = table.find_element(By.XPATH, "./preceding::h3[1]")
            if "Data Macau 5D 2025" in h3_above.text:
                continue
        except:
            pass

        df_table = process_table(table)
        if not df_table.empty:
            dfs.append(df_table)

    if dfs:
        df_final = pd.concat(dfs, ignore_index=True)
        
        # Hapus kolom yang seluruhnya kosong
        df_final = df_final.dropna(axis=1, how='all')
        
        # REVERSE THE ORDER OF ROWS - MOST RECENT FIRST
        df_final = df_final.iloc[::-1].reset_index(drop=True)
        
        # Format output
        excel_path = "Data_Macau_FINAL_FIX.xlsx"
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False)
            
            # Force text format
            workbook = writer.book
            worksheet = writer.sheets['Sheet1']
            for col in range(df_final.shape[1]):
                for row in range(2, df_final.shape[0] + 2):
                    cell = worksheet.cell(row=row, column=col+1)
                    cell.number_format = '@'
        
        print(f"\n✅ File tersimpan: {excel_path}")
        print("Contoh data setelah cleaning (paling baru di atas):")
        print(df_final.head(10).to_string(index=False))
        
    else:
        print("❌ Tidak ada data valid yang ditemukan")

except Exception as e:
    print(f"ERROR: {str(e)}")
    driver.save_screenshot("error_final.png")

finally:
    driver.quit()