from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

# Setup Chrome Driver
service = Service(executable_path='/Users/vanviakingali/chromedriver/chromedriver')
options = webdriver.ChromeOptions()
options.binary_location = '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
# options.add_argument('--headless')  # Nonaktifkan dulu untuk debugging
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(service=service, options=options)

try:
    print("Mengakses situs...")
    driver.get("http://128.199.129.116/")
    
    # Tunggu sampai halaman fully loaded
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "table#manual-table"))
    )
    time.sleep(2)

    # Temukan semua tabel dengan id manual-table
    all_tables = driver.find_elements(By.CSS_SELECTOR, "table#manual-table")
    print(f"Jumlah tabel ditemukan: {len(all_tables)}")

    # Temukan posisi pembatas (h4 yang tidak diinginkan)
    cutoff_point = None
    try:
        cutoff_point = driver.find_element(By.XPATH, "//h4[contains(text(), 'Data Sydney lotto Terbaru')]")
        print("Pembatas ditemukan:", cutoff_point.text)
    except:
        print("Pembatas tidak ditemukan, akan mengambil semua tabel")

    data = []
    for table in all_tables:
        # Skip tabel yang berada setelah cutoff point
        if cutoff_point and table.location['y'] > cutoff_point.location['y']:
            print("Melewati tabel di bawah pembatas")
            continue
        
        # Proses tabel yang memenuhi kriteria
        try:
            # Ambil header
            header_row = table.find_element(By.CSS_SELECTOR, "tr.headcol1")
            headers = [td.text.strip() for td in header_row.find_elements(By.TAG_NAME, "td") if td.text.strip()]
            
            # Ambil data rows
            rows = table.find_elements(By.CSS_SELECTOR, "tr:not(.headcol1)")
            
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= len(headers):
                    row_data = {headers[i]: cols[i].text.strip() for i in range(len(headers))}
                    data.append(row_data)
            
            print(f"Berhasil mengekstrak {len(rows)} baris dari satu tabel")
            
        except Exception as e:
            print(f"Gagal memproses satu tabel: {str(e)}")
            continue

    # Export ke Excel
    if data:
        df = pd.DataFrame(data)
        # Bersihkan data duplikat atau kosong
        df = df.drop_duplicates().dropna(how='all')
        
        print(f"\nTotal data terkumpul: {len(df)} baris")
        print("\n5 Data Teratas:")
        print(df.head().to_string(index=False))
        
        df.to_excel("Dataset_Sidneypools.xlsx", index=False)
        print("\nFile Excel berhasil disimpan!")
    else:
        print("Tidak ada data yang berhasil dikumpulkan")

except Exception as e:
    print(f"Error utama: {str(e)}")
    driver.save_screenshot("error_final.png")

finally:
    driver.quit()