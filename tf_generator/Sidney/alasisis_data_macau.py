import pandas as pd
from collections import Counter

def load_data(file_path):
    """Load semua data dari Excel dengan benar - ambil 2D depan"""
    try:
        # Baca semua kolom tanpa header
        data = pd.read_excel(file_path, header=None, dtype=str)
        
        all_2d_numbers = []
        
        # Proses setiap kolom
        for col in data.columns:
            # Bersihkan data per kolom
            cleaned_col = (
                data[col]
                .dropna()
                .astype(str)
                .str.strip()
                .str.replace(r'[^0-9]', '', regex=True)
            )
            
            # Ambil 2 digit pertama dari setiap angka
            for num in cleaned_col:
                if num.isdigit() and len(num) >= 2:
                    # AMBIL 2 DIGIT DEPAN - INI YANG BENAR!
                    two_digit = num[:2]  # Langsung ambil 2 digit pertama
                    all_2d_numbers.append(two_digit)
                elif num.isdigit() and len(num) == 1:
                    # Jika hanya 1 digit, tambahkan leading zero
                    two_digit = f"0{num}"
                    all_2d_numbers.append(two_digit)
        
        return all_2d_numbers
        
    except Exception as e:
        print(f"ERROR: {e}")
        return []

def main():
    FILE_PATH = "Dataset_Macau.xlsx"
    
    # Load semua data
    all_data = load_data(FILE_PATH)
    
    if not all_data:
        print("Data tidak valid. Cek file Excel!")
        return
    
    print("=" * 60)
    print("ANALISIS DATA KELUARAN MACAU 2D - URUT BERDASARKAN FREKUENSI")
    print("=" * 60)
    
    print(f"Total hasil undian dalam dataset: {len(all_data)}")
    
    # Hitung frekuensi
    freq_counter = Counter(all_data)
    total_draws = len(all_data)
    
    # Buat list untuk sorting
    freq_list = []
    for number, count in freq_counter.items():
        percentage = (count / total_draws) * 100
        freq_list.append((number, count, percentage))
    
    # Urutkan berdasarkan persentase tertinggi ke terendah
    freq_list_sorted = sorted(freq_list, key=lambda x: x[2], reverse=True)
    
    print(f"\n=== FREKUENSI KEMUNCULAN ANGKA 2D (URUT TERTINGGI) ===")
    print("Rank | Angka | Frekuensi | Persentase")
    print("-" * 45)
    
    # Tampilkan semua angka yang sudah diurutkan
    for rank, (number, count, percentage) in enumerate(freq_list_sorted, 1):
        print(f"{rank:3}  |  {number}   |  {count:5} kali |  {percentage:6.2f}%")
    
    # Tampilkan 10 angka terpanas
    print(f"\n=== 10 ANGKA TERPANAS ===")
    for i, (number, count, percentage) in enumerate(freq_list_sorted[:10], 1):
        print(f"{i:2}. {number}: {count:3} kali ({percentage:.2f}%)")
    
    # Tampilkan 10 angka terdingin
    print(f"\n=== 10 ANGKA TERDINGIN ===")
    for i, (number, count, percentage) in enumerate(freq_list_sorted[-10:], 1):
        print(f"{i:2}. {number}: {count:3} kali ({percentage:.2f}%)")

if __name__ == "__main__":
    main()