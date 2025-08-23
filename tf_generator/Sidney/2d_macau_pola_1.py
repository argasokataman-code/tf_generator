import pandas as pd
from collections import Counter
import random
import math

def load_data(file_path):
        """Load data dari file Excel - TANPA HEADER"""
        try:
            # Baca semua data tanpa header, skip 2 baris pertama
            data = pd.read_excel(file_path, header=None, skiprows=2, dtype=str)
            
            print(f"🔍 Shape data: {data.shape}")
            print("🔍 Sample data:")
            print(data.head(3))
            
            all_2d_numbers = []
            
            # Iterasi melalui semua baris dan kolom
            for row_idx in range(len(data)):
                for col_idx in data.columns:
                    cell_value = str(data.iloc[row_idx, col_idx]).strip()
                    
                    # Skip cell kosong atau tidak valid
                    if cell_value in ['nan', 'None', '', 'NaN', 'NaT']:
                        continue
                    
                    # Bersihkan angka dari karakter non-digit
                    clean_num = ''.join(filter(str.isdigit, cell_value))
                    
                    if clean_num and len(clean_num) >= 2:
                        two_digit = clean_num[:2]  # Ambil 2 digit pertama
                        all_2d_numbers.append(two_digit)
                    elif clean_num and len(clean_num) == 1:
                        two_digit = f"0{clean_num}"  # Format ke 2 digit
                        all_2d_numbers.append(two_digit)
            
            print(f"✅ Total angka 2D ditemukan: {len(all_2d_numbers)}")
            
            if not all_2d_numbers:
                print("❌ Tidak ada data angka yang valid ditemukan")
                return []
            
            print(f"🔍 5 data terakhir sebelum reverse: {all_2d_numbers[-5:]}")
            
            # Reverse urutan data (yang terbaru jadi pertama)
            all_2d_numbers.reverse()
            
            print(f"🔍 5 data pertama setelah reverse: {all_2d_numbers[:5]}")
            
            return all_2d_numbers
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return []

def generate_unique_numbers(data_2d, total_numbers=50):
    """Generate unique 2D numbers with hot/cold strategy"""
    if not data_2d:
        return []
    
    # Hitung frekuensi semua angka 2D dari dataset lengkap
    freq_2d = Counter(data_2d)
    
    # Debug: Cek apakah 83 ada dalam dataset
    if '83' in freq_2d:
        print(f"✓ Angka 83 ditemukan, muncul {freq_2d['83']} kali")
    else:
        print("✗ Angka 83 TIDAK ditemukan dalam dataset")
    
    # Urutkan berdasarkan frekuensi (dari yang paling sering)
    sorted_by_freq = sorted(freq_2d.items(), key=lambda x: x[1], reverse=True)
    
    # Pisahkan hot (70% teratas) dan cold (30% terbawah)
    hot_cutoff = math.ceil(len(sorted_by_freq) * 0.7)
    hot_numbers = [num for num, count in sorted_by_freq[:hot_cutoff]]
    cold_numbers = [num for num, count in sorted_by_freq[hot_cutoff:]]
    
    # Gabungkan dengan proporsi: 70% hot, 30% cold
    combined = []
    hot_count = math.ceil(total_numbers * 0.7)
    cold_count = total_numbers - hot_count
    
    # Ambil angka hot
    combined.extend(hot_numbers[:min(hot_count, len(hot_numbers))])
    
    # Ambil angka cold
    combined.extend(cold_numbers[:min(cold_count, len(cold_numbers))])
    
    # Jika masih kurang, tambahkan angka random yang belum ada
    if len(combined) < total_numbers:
        needed = total_numbers - len(combined)
        all_possible = [f"{i:02d}" for i in range(100)]
        missing_numbers = [num for num in all_possible if num not in combined]
        
        if missing_numbers:
            combined.extend(random.sample(missing_numbers, min(needed, len(missing_numbers))))
    
    # Pastikan tidak ada duplikat
    combined = list(dict.fromkeys(combined))
    
    # Jika masih kurang, generate completely random
    if len(combined) < total_numbers:
        needed = total_numbers - len(combined)
        for _ in range(needed):
            while True:
                new_num = f"{random.randint(0, 99):02d}"
                if new_num not in combined:
                    combined.append(new_num)
                    break
    
    random.shuffle(combined)
    return combined[:total_numbers]

def split_for_webs(numbers, per_web=20):
    """Split numbers for betting platforms"""
    return [numbers[i:i + per_web] for i in range(0, len(numbers), per_web)]

def main():
    # Config
    FILE_PATH = "Dataset_macau.xlsx"
    TOTAL_NUMBERS = 50  # Target 50 angka 2D unik
    NUMBERS_PER_WEB = 20  # 20 angka per web
    
    # Load data
    data_2d = load_data(FILE_PATH)
    
    if not data_2d:
        print("Data tidak valid. Cek file Excel!")
        return
    
    # Generate prediksi
    predicted_numbers = generate_unique_numbers(data_2d, TOTAL_NUMBERS)
    
    if not predicted_numbers:
        print("Gagal generate angka.")
        return
    
    print(f"\nHasil Prediksi 2D Depan ({len(predicted_numbers)} angka unik):")
    print("*".join(predicted_numbers))
    
    # Split untuk web taruhan
    web_splits = split_for_webs(predicted_numbers, NUMBERS_PER_WEB)
    
    print("\nPembagian per WEB:")
    for i, numbers in enumerate(web_splits, 1):
        print(f"\nWEB {i} ({len(numbers)} angka):")
        print("*".join(numbers))

if __name__ == "__main__":
    main()