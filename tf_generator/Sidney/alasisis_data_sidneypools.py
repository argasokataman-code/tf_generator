import pandas as pd
from collections import Counter

def load_data(file_path):
    """Load semua data dari Excel"""
    try:
        data = pd.read_excel(file_path, header=None, dtype=str, names=["Angka"])
        data_cleaned = (
            data["Angka"]
            .dropna()
            .str.strip()
            .str.replace(r'[^0-9]', '', regex=True)
        )
        # Ambil 2 digit depan dan pastikan format 2 digit
        valid_numbers = [
            num.zfill(4)[:2]  # Pastikan 4 digit dulu, lalu ambil 2 depan
            for num in data_cleaned 
            if num.isdigit() and len(num) >= 2
        ]
        return valid_numbers
    except Exception as e:
        print(f"ERROR: {e}")
        return []

def calculate_hit_rate(unique_numbers, all_results):
    """Hitung persentase hasil undian yang match dengan angka unik"""
    if not unique_numbers or not all_results:
        return 0, 0, []
    
    hit_count = 0
    total_draws = len(all_results)
    hit_details = []
    
    for result in all_results:
        if result in unique_numbers:
            hit_count += 1
            hit_details.append(f"{result}✓")
        else:
            hit_details.append(f"{result}✗")
    
    hit_rate = (hit_count / total_draws) * 100
    return hit_rate, hit_count, hit_details

def main():
    FILE_PATH = "Dataset_Sidneypools.xlsx"
    
    # Load semua data
    all_data = load_data(FILE_PATH)
    
    if not all_data:
        print("Data tidak valid. Cek file Excel!")
        return
    
    # Generate angka unik dari dataset (kayak yang sebelumnya)
    unique_numbers = list(dict.fromkeys(all_data))
    
    print("=" * 50)
    print("ANALISIS DATA KELUARAN 2D")
    print("=" * 50)
    
    print(f"\nJumlah angka unik 2D dari dataset: {len(unique_numbers)}")
    print(f"Angka unik: {'*'.join(unique_numbers)}")
    print(f"Total hasil undian dalam dataset: {len(all_data)}")
    
    # Hitung persentase match
    hit_rate, hit_count, hit_details = calculate_hit_rate(unique_numbers, all_data)
    
    print(f"\n=== HASIL TRACKING ===")
    print(f"Jumlah hasil undian: {len(all_data)}")
    print(f"Jumlah yang match dengan angka unik: {hit_count}")
    print(f"Persentase match: {hit_rate:.2f}%")
    
    # Tampilkan summary per 20 hasil untuk readability
    print(f"\nDetail hasil (✓ = match, ✗ = tidak match):")
    for i in range(0, len(hit_details), 20):
        batch = hit_details[i:i+20]
        print(f"Draw {i+1}-{i+len(batch)}: {' '.join(batch)}")
    
    # Hitung berapa banyak angka unik yang belum pernah muncul
    all_possible = [f"{i:02d}" for i in range(100)]
    missing_numbers = [num for num in all_possible if num not in unique_numbers]
    
    print(f"\n=== STATISTIK TAMBAHAN ===")
    print(f"Angka 2D yang belum pernah muncul: {len(missing_numbers)} angka")
    if missing_numbers:
        print(f"Angka yang missing: {'*'.join(missing_numbers)}")
    
    # Analisis frekuensi (dari kodingan kedua)
    freq_counter = Counter(all_data)
    total_draws = len(all_data)
    
    print(f"\n=== FREKUENSI KEMUNCULAN MASING-MASING ANGKA ===")
    print("Angka | Frekuensi | Persentase")
    print("-" * 40)
    
    # Urutkan berdasarkan frekuensi (dari yang paling sering)
    sorted_by_freq = sorted(freq_counter.items(), key=lambda x: x[1], reverse=True)
    
    for number, count in sorted_by_freq:
        percentage = (count / total_draws) * 100
        print(f"{number}    | {count:4} kali | {percentage:6.2f}%")
    
    # Hitung statistik tambahan
    avg_frequency = total_draws / len(unique_numbers)
    max_freq = max(freq_counter.values())
    min_freq = min(freq_counter.values())
    
    print(f"\n=== STATISTIK UTAMA ===")
    print(f"Rata-rata frekuensi per angka: {avg_frequency:.2f} kali")
    print(f"Frekuensi tertinggi: {max_freq} kali")
    print(f"Frekuensi terendah: {min_freq} kali")
    
    # Tampilkan 10 angka terpanas
    print(f"\n=== 10 ANGKA TERPANAS ===")
    for i, (number, count) in enumerate(sorted_by_freq[:10], 1):
        percentage = (count / total_draws) * 100
        print(f"{i:2}. {number}: {count:3} kali ({percentage:.2f}%)")
    
    # Tampilkan 10 angka terdingin
    print(f"\n=== 10 ANGKA TERDINGIN ===")
    for i, (number, count) in enumerate(sorted_by_freq[-10:], 1):
        percentage = (count / total_draws) * 100
        print(f"{i:2}. {number}: {count:3} kali ({percentage:.2f}%)")

if __name__ == "__main__":
    main()