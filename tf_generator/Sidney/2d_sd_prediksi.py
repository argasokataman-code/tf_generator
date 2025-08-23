import pandas as pd
from collections import Counter
import random
import math
from sklearn.model_selection import TimeSeriesSplit
import numpy as np

def load_data(file_path):
    """Load data & ambil 2D depan (termasuk leading zero)"""
    try:
        # 1. Load data as STRING biar leading zero aman
        data = pd.read_excel(file_path, header=None, dtype=str, names=["Angka"])
        
        # 2. Bersihkan data:
        #    - Hapus baris kosong
        #    - Hapus karakter non-digit (misal XXXX)
        #    - Ambil 2 digit pertama
        data_2d = (
            data["Angka"]
            .dropna()
            .str.strip()
            .str.replace(r'[^0-9]', '', regex=True)  # Hapus non-digit
            .str[:2]  # Ambil 2 digit depan
        )
        
        # 3. Format ke 2D dengan leading zero (1 -> 01, 12 -> 12)
        valid_numbers = [
            num.zfill(2)  # Pastikan 2 digit
            for num in data_2d 
            if num.isdigit() and len(num) >= 1  # Minimal 1 digit (nanti di-pad ke 2)
        ]
        
        return valid_numbers  # Kembalikan semua data (termasuk duplikat)
        
    except Exception as e:
        print(f"ERROR: {e}")
        return []

def generate_unique_numbers(data_2d, total_numbers=50):
    """Generate unique 2D numbers with hot/cold strategy"""
    if not data_2d:
        return []
    
    freq_2d = Counter(data_2d)
    unique_numbers = list(freq_2d.keys())
    
    # Hitung hot (70% paling sering muncul) dan cold (30% sisanya)
    hot_numbers = [num for num, _ in freq_2d.most_common(math.ceil(len(unique_numbers) * 0.7))]
    cold_numbers = [num for num in unique_numbers if num not in hot_numbers]
    
    # Gabungkan hot + cold, sisanya random
    combined = []
    remaining_slots = total_numbers
    
    # Prioritaskan hot numbers
    combined.extend(hot_numbers[:remaining_slots])
    remaining_slots = total_numbers - len(combined)
    
    # Tambahkan cold numbers jika masih kurang
    if remaining_slots > 0:
        combined.extend(random.sample(cold_numbers, min(remaining_slots, len(cold_numbers))))
    
    # Jika masih kurang, generate random 2D unik
    if len(combined) < total_numbers:
        needed = total_numbers - len(combined)
        for _ in range(needed):
            while True:
                new_num = f"{random.randint(0, 9)}{random.randint(0, 9)}"
                if new_num not in combined and new_num not in freq_2d:
                    combined.append(new_num)
                    break
    
    # Pastikan tidak ada duplikat
    assert len(combined) == len(set(combined)), "Ada angka kembar!"
    random.shuffle(combined)
    return combined[:total_numbers]

def test_accuracy(file_path, test_size=0.2, n_splits=5):
    """Test accuracy dengan time series cross validation"""
    # Load semua data
    all_data = load_data(file_path)
    
    if not all_data:
        print("Data tidak valid. Cek file Excel!")
        return
    
    # Konversi ke pandas Series untuk memudahkan splitting
    data_series = pd.Series(all_data)
    
    # Time Series Cross Validation
    tscv = TimeSeriesSplit(n_splits=n_splits)
    
    accuracies = []
    hit_rates = []
    
    for train_index, test_index in tscv.split(data_series):
        # Split data menjadi train dan test
        train_data = data_series.iloc[train_index].tolist()
        test_data = data_series.iloc[test_index].tolist()
        
        # Generate prediksi berdasarkan data training
        predicted_numbers = generate_unique_numbers(train_data, 50)
        
        # Hitung akurasi
        correct_predictions = len(set(predicted_numbers) & set(test_data))
        total_test_numbers = len(set(test_data))
        
        # Hitung persentase akurasi
        accuracy = (correct_predictions / total_test_numbers) * 100 if total_test_numbers > 0 else 0
        accuracies.append(accuracy)
        
        # Hitung hit rate (berapa banyak angka yang benar dari 50 prediksi)
        hit_rate = (correct_predictions / 50) * 100
        hit_rates.append(hit_rate)
        
        print(f"Fold {len(accuracies)}: {correct_predictions} dari {total_test_numbers} angka test terprediksi")
        print(f"Akurasi: {accuracy:.2f}%, Hit Rate: {hit_rate:.2f}%")
    
    # Hitung statistik
    avg_accuracy = np.mean(accuracies)
    avg_hit_rate = np.mean(hit_rates)
    
    print("\n" + "="*50)
    print("HASIL AKURASI PREDIKSI")
    print("="*50)
    print(f"Rata-rata Akurasi: {avg_accuracy:.2f}%")
    print(f"Rata-rata Hit Rate: {avg_hit_rate:.2f}%")
    print(f"Range Akurasi: {min(accuracies):.2f}% - {max(accuracies):.2f}%")
    
    return accuracies, hit_rates

def analyze_frequency(file_path):
    """Analisis frekuensi angka untuk melihat pola"""
    all_data = load_data(file_path)
    
    if not all_data:
        return
    
    # Hitung frekuensi
    freq = Counter(all_data)
    
    print("\n" + "="*50)
    print("ANALISIS FREKUENSI ANGKA")
    print("="*50)
    
    # 10 angka terpanas
    print("\n10 ANGKA TERPANAS:")
    for num, count in freq.most_common(10):
        print(f"{num}: {count} kali")
    
    # 10 angka terdingin
    print("\n10 ANGKA TERDINGIN:")
    for num, count in freq.most_common()[-10:]:
        print(f"{num}: {count} kali")
    
    return freq

def main():
    FILE_PATH = "Dataset_macau.xlsx"
    
    # 1. Analisis frekuensi
    freq = analyze_frequency(FILE_PATH)
    
    # 2. Test akurasi
    print("\n" + "="*50)
    print("TESTING AKURASI DENGAN CROSS VALIDATION")
    print("="*50)
    accuracies, hit_rates = test_accuracy(FILE_PATH, n_splits=5)
    
    # 3. Generate prediksi untuk data terbaru
    print("\n" + "="*50)
    print("PREDIKSI UNTUK DATA TERBARU")
    print("="*50)
    
    all_data = load_data(FILE_PATH)
    predicted_numbers = generate_unique_numbers(all_data, 60)
    
    print(f"Hasil Prediksi 2D Depan (50 angka unik):")
    print("*".join(predicted_numbers))
    
    # Split untuk web taruhan
    web_splits = [predicted_numbers[i:i+20] for i in range(0, len(predicted_numbers), 20)]
    
    print("\nPembagian per WEB:")
    for i, numbers in enumerate(web_splits, 1):
        print(f"\nWEB {i} ({len(numbers)} angka):")
        print("*".join(numbers))

if __name__ == "__main__":
    main()