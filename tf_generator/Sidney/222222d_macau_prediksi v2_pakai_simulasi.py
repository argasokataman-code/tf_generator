import pandas as pd
from collections import Counter
import numpy as np
import random
from datetime import datetime

def load_data(file_path):
    """Load data dengan handling yang lebih robust"""
    try:
        data = pd.read_excel(file_path, header=None, dtype=str)
        
        all_numbers = []
        for col in data.columns:
            col_data = data[col].dropna().astype(str).str.strip()
            for num_str in col_data:
                clean_num = ''.join(filter(str.isdigit, num_str))
                if len(clean_num) >= 4:
                    all_numbers.append(clean_num[:2])
        
        print(f"Data loaded: {len(all_numbers)} entries")
        return all_numbers
        
    except Exception as e:
        print(f"ERROR: {e}")
        return [f"{random.randint(0, 99):02d}" for _ in range(100)]

def deterministic_selection(data, total_numbers=60):
    """Selection yang deterministic berdasarkan data"""
    if len(data) < 50:
        return [f"{i:02d}" for i in range(total_numbers)]
    
    weights = {}
    for i, num in enumerate(data):
        weight = 1.0 + (i / len(data)) * 2.0
        if num not in weights:
            weights[num] = 0
        weights[num] += weight
    
    total_weight = sum(weights.values())
    probabilities = {num: weight/total_weight for num, weight in weights.items()}
    
    sorted_nums = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
    
    selected = []
    for num, prob in sorted_nums:
        if len(selected) >= total_numbers:
            break
        if num not in selected:
            selected.append(num)
    
    return selected[:total_numbers]

def analyze_last_50_performance(data, predictions):
    """Analisis performa prediksi terhadap 50 data terakhir"""
    if len(data) < 50:
        print("Data kurang dari 50, tidak bisa analisis")
        return
    
    last_50_data = data[-200:]
    last_50_unique = set(last_50_data)
    
    print("="*70)
    print("ANALISIS PERFORMA 50 DATA TERAKHIR")
    print("="*70)
    
    # Hitung berapa banyak prediksi yang masuk di 50 data terakhir
    hits = len(set(predictions) & last_50_unique)
    total_actual = len(last_50_unique)
    accuracy = (hits / total_actual) * 100 if total_actual > 0 else 0
    
    print(f"📊 Total unique numbers in last 50 data: {total_actual}")
    print(f"🎯 Predicted numbers that hit: {hits}")
    print(f"📈 Accuracy: {accuracy:.1f}%")
    print(f"🔍 Coverage: {hits}/50 = {(hits/60)*100:.1f}% of predictions")
    
    # Tampilkan angka yang berhasil diprediksi
    successful_predictions = sorted(set(predictions) & last_50_unique)
    print(f"\n✅ Successful predictions ({len(successful_predictions)}):")
    for i in range(0, len(successful_predictions), 10):
        print(" ".join(successful_predictions[i:i+10]))
    
    # Tampilkan angka yang miss
    missed_numbers = sorted(last_50_unique - set(predictions))
    print(f"\n❌ Missed numbers ({len(missed_numbers)}):")
    for i in range(0, len(missed_numbers), 10):
        print(" ".join(missed_numbers[i:i+10]))
    
    # Analisis frekuensi data terakhir
    print(f"\n📊 Frequency analysis of last 50 data:")
    freq_last_50 = Counter(last_50_data)
    for num, count in freq_last_50.most_common(10):
        print(f"  {num}: {count} times")

        print(f"\n🔍 DETAILED MISS ANALYSIS:")
    for num in missed_numbers:
        freq = data.count(num)
        last_seen = find_last_appearance(data, num)
        print(f"  {num}: Freq={freq}x, Last seen={last_seen} data ago")
    
    # TAMBAHIN INI ↓  
    print(f"\n🎯 RECOMMENDATION:")
    for num in missed_numbers:
        if data.count(num) <= 3:
            print(f"  {num}: Extreme cold - Monitor for comeback")
        elif find_last_appearance(data, num) <= 10:
            print(f"  {num}: Recently active - Consider include")
    
    return hits, accuracy

def find_last_appearance(data, number):
    """Cari kapan terakhir kali number muncul (dalam jumlah data terakhir)"""
    # Iterasi dari data terbaru ke terlama
    for i in range(len(data)-1, -1, -1):
        if data[i] == number:
            return len(data) - i  # Jarak dari data terakhir
    return 999  # Jika never muncul

def backtest_strategy(data, window_size=50, test_runs=10):
    """Backtest strategy terhadap data historis"""
    if len(data) < window_size * 2:
        print("Data tidak cukup untuk backtesting")
        return
    
    print("="*70)
    print("BACKTESTING STRATEGY")
    print("="*70)
    
    results = []
    
    for i in range(test_runs):
        # Pilih random point untuk testing
        test_end = random.randint(window_size * 2, len(data))
        test_start = test_end - window_size
        test_data = data[test_start:test_end]
        
        # Data training adalah data sebelum test data
        train_data = data[:test_start]
        
        # Generate prediction
        prediction = deterministic_selection(train_data, 50)
        
        # Hitung accuracy
        test_unique = set(test_data)
        hits = len(set(prediction) & test_unique)
        accuracy = (hits / len(test_unique)) * 100 if test_unique else 0
        
        results.append({
            'test_run': i + 1,
            'hits': hits,
            'total_test': len(test_unique),
            'accuracy': accuracy
        })
        
        print(f"Test {i+1:2d}: {hits:2d}/{len(test_unique):2d} hits ({accuracy:5.1f}%)")
    
    # Summary
    avg_hits = np.mean([r['hits'] for r in results])
    avg_accuracy = np.mean([r['accuracy'] for r in results])
    
    print(f"\n📊 Average: {avg_hits:.1f} hits, {avg_accuracy:.1f}% accuracy")
    
    return results

def generate_recommendation(data, predictions, last_50_hits):
    """Generate rekomendasi berdasarkan analisis"""
    print("="*70)
    print("REKOMENDASI STRATEGI")
    print("="*70)
    
    last_20 = data[-20:]
    freq_last_20 = Counter(last_20)
    
    # Hot numbers terbaru
    hot_numbers = [num for num, count in freq_last_20.most_common(15)]
    
    # Cold numbers (belum muncul di 20 data terakhir)
    cold_numbers = [num for num in set(data) if num not in last_20][:10]
    
    # Angka yang berhasil diprediksi sebelumnya
    successful_numbers = list(set(predictions) & set(data[-50:]))
    
    print("🔥 Hot numbers (last 20):")
    print(" ".join(hot_numbers[:10]))
    if len(hot_numbers) > 10:
        print(" ".join(hot_numbers[10:]))
    
    print(f"\n❄️  Cold numbers (not in last 20): {len(cold_numbers)} numbers")
    print(" ".join(cold_numbers[:10]))
    
    print(f"\n✅ Previously successful: {len(successful_numbers)} numbers")
    if successful_numbers:
        print(" ".join(successful_numbers[:10]))
    
    # Rekomendasi final
    print(f"\n🎯 REKOMENDASI FINAL:")
    print("Gunakan kombinasi:")
    print("- 50% dari prediksi deterministic")
    print("- 30% dari hot numbers terbaru")
    print("- 20% dari cold numbers berpotensi")

def main():
    FILE_PATH = "Dataset_macau.xlsx"
    
    print("🔍 Loading data...")
    data = load_data(FILE_PATH)
    
    if len(data) < 50:
        print("Data kurang dari 50, tidak bisa analisis mendalam")
        return
    
    print(f"📊 Total data: {len(data)}")
    print(f"🎯 Unique numbers: {len(set(data))}")
    
    # Generate prediksi
    print("\n" + "="*70)
    print("GENERATING PREDICTION")
    print("="*70)
    
    predictions = deterministic_selection(data, 60)
    print("50 Predicted Numbers:")
    print("*".join(predictions))  # 🔥 Ganti * jadi spasi
    
    # Analisis 50 data terakhir
    hits, accuracy = analyze_last_50_performance(data, predictions)
    
    # Backtesting
    backtest_results = backtest_strategy(data, window_size=50, test_runs=10)
    
    # Rekomendasi
    generate_recommendation(data, predictions, hits)
    
    # Simpan hasil untuk referensi
    print(f"\n💾 Simpan prediksi ini dan cek keakuratannya besok!")
    print(f"   Predicted: {len(predictions)} numbers")
    print(f"   Current accuracy: {accuracy:.1f}%")
    print(f"   Backtest average: {np.mean([r['accuracy'] for r in backtest_results]):.1f}%")

if __name__ == "__main__":
    main()