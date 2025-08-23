import pandas as pd
from collections import Counter
import random
import math

def load_data(file_path, mode="full", last_n=300):
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
        
        # Pilih mode data
        if mode == "last_n" and len(all_2d_numbers) > last_n:
            all_2d_numbers = all_2d_numbers[:last_n]
            print(f"✅ Menggunakan {last_n} data terbaru")
        
        print(f"🔍 5 data pertama setelah reverse: {all_2d_numbers[:5]}")
        print(f"📊 Total data yang digunakan: {len(all_2d_numbers)}")
        
        return all_2d_numbers
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return []

def calculate_dynamic_ranking(data_2d, historical_weight=0.3):
    """
    Hitung ranking dinamis dengan mempertimbangkan:
    - Data historis (dari analisis sebelumnya)
    - Data terbaru (dari dataset)
    """
    # Hitung frekuensi dari data terbaru
    recent_freq = Counter(data_2d)
    
    # Buat ranking berdasarkan frekuensi data terbaru
    recent_ranking = {num: idx for idx, (num, _) in enumerate(recent_freq.most_common())}
    
    # Gabungkan dengan ranking historis (jika ada)
    # Di sini kita bisa menambahkan bobot untuk data historis
    combined_ranking = {}
    
    for num in set(data_2d):
        # Jika angka ada di data terbaru, beri peringkat berdasarkan frekuensi
        recent_rank = recent_ranking.get(num, 100)  # Default rank 100 jika tidak ada
        
        # Beri bobot lebih besar pada data terbaru
        combined_ranking[num] = recent_rank
    
    # Urutkan berdasarkan ranking terbaik (nilai terkecil)
    ranked_numbers = sorted(combined_ranking.keys(), key=lambda x: combined_ranking[x])
    
    return ranked_numbers

def generate_unique_numbers(data_2d, total_numbers=50, use_dynamic_ranking=True):
    if not data_2d:
        return []
    
    if use_dynamic_ranking:
        # Gunakan ranking dinamis
        ranked_numbers = calculate_dynamic_ranking(data_2d)
        
        # 1. Ambil 80% hot numbers dari ranking teratas
        hot_count = math.ceil(total_numbers * 0.8)
        hot_numbers = ranked_numbers[:hot_count]
        
        # 2. Ambil 20% cold numbers dari ranking terbawah
        cold_numbers = ranked_numbers[hot_count:]
        cold_selected = random.sample(cold_numbers, min(total_numbers - hot_count, len(cold_numbers)))
    else:
        # Metode lama (berdasarkan frekuensi saja)
        freq_2d = Counter(data_2d)
        unique_numbers = list(freq_2d.keys())
        
        hot_count = math.ceil(total_numbers * 0.8)
        hot_numbers = [num for num, _ in freq_2d.most_common(hot_count)]
        
        cold_numbers = [num for num in unique_numbers if num not in hot_numbers]
        cold_selected = random.sample(cold_numbers, min(total_numbers - hot_count, len(cold_numbers)))
    
    combined = hot_numbers + cold_selected
    
    # 3. Mirror effect
    mirror_numbers = []
    for num in combined:
        mirror_num = num[1] + num[0]
        if mirror_num != num and mirror_num not in combined:
            mirror_numbers.append(mirror_num)
    combined.extend(mirror_numbers[:5])
    
    # 4. Sibling effect
    sibling_numbers = []
    for num in combined:
        n = int(num)
        siblings = [
            str(n - 1).zfill(2),
            str(n + 1).zfill(2),
            str(n - 10).zfill(2),
            str(n + 10).zfill(2)
        ]
        for s in siblings:
            if 0 <= int(s) <= 99 and s not in combined:
                sibling_numbers.append(s)
    
    combined.extend(sibling_numbers[:5])
    
    # 5. Hapus duplikat
    combined = list(dict.fromkeys(combined))
    random.shuffle(combined)
    return combined[:total_numbers]  # Pastikan tidak melebihi total_numbers

def split_for_webs(numbers, per_web=20):
    """Split numbers for betting platforms"""
    return [numbers[i:i + per_web] for i in range(0, len(numbers), per_web)]

def main():
    # Config
    FILE_PATH = "Dataset_macau.xlsx"
    TOTAL_NUMBERS = 50
    NUMBERS_PER_WEB = 20
    
    # ⚡ PILIH MODE:
    DATA_MODE = "full"    # "full" atau "last_n"
    LAST_N_DATA = 300
    USE_DYNAMIC_RANKING = True  # Gunakan ranking dinamis
    
    # Load data
    data_2d = load_data(FILE_PATH, mode=DATA_MODE, last_n=LAST_N_DATA)
    
    if not data_2d:
        print("❌ Data tidak valid. Cek file Excel!")
        return
    
    print(f"✅ Data loaded: {len(data_2d)} angka 2D")
    
    # Hitung frekuensi terbaru untuk ditampilkan
    recent_freq = Counter(data_2d)
    print(f"\n📊 10 ANGKA PALING SERING MUNCUL TERBARU:")
    for num, count in recent_freq.most_common(10):
        print(f"{num}: {count} kali")
    
    # Generate prediksi
    predicted_numbers = generate_unique_numbers(
        data_2d, 
        TOTAL_NUMBERS, 
        use_dynamic_ranking=USE_DYNAMIC_RANKING
    )
    
    print(f"\n🎯 HASIL PREDIKSI 2D DEPAN ({len(predicted_numbers)} angka):")
    print("*".join(predicted_numbers))
    
    # Split untuk web taruhan
    web_splits = split_for_webs(predicted_numbers, NUMBERS_PER_WEB)
    
    print("\n📊 PEMBAGIAN PER WEB:")
    for i, numbers in enumerate(web_splits, 1):
        print(f"\nWEB {i} ({len(numbers)} angka):")
        print("*".join(numbers))

if __name__ == "__main__":
    main()