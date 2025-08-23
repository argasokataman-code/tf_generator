import pandas as pd
import numpy as np
from collections import Counter, defaultdict
from datetime import datetime
import random

class RootMatrixPredictor:
    def __init__(self, max_numbers=100):
        self.root_history = []
        self.number_history = []
        self.root_matrix = np.zeros((3, 3))
        self.pos_matrix = np.zeros((10, 10))
        self.last_appearance = {}
        self.current_intervals = {}
        self.root_mapping = {
            1: (0, 0), 2: (0, 1), 3: (0, 2),
            4: (1, 0), 5: (1, 1), 6: (1, 2),
            7: (2, 0), 8: (2, 1), 9: (2, 2)
        }
        self.max_numbers = max_numbers
        
    def calculate_root(self, number):
        """Hitung root number dari angka 2D"""
        n = int(number)
        if n == 0:
            return 9
        root = n % 9
        return root if root != 0 else 9
    
    def load_data(self, file_path):
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
        
    def analyze_data(self, data_2d):
        """Analisis data dan build matrix"""
        print(f"📊 Menganalisis {len(data_2d)} data...")
        day_count = 0
        for num in data_2d:
            day_count += 1
            self.add_new_data(num, day_count)
        
        print(f"✅ Analisis selesai. Total hari: {day_count}")
    
    def add_new_data(self, new_number, day_count):
        """Tambahkan data baru dan update semua parameter"""
        root = self.calculate_root(int(new_number))
        
        self.number_history.append(new_number)
        self.root_history.append(root)
        
        i, j = self.root_mapping[root]
        self.root_matrix[i][j] += 1
        
        digit1, digit2 = int(new_number[0]), int(new_number[1])
        self.pos_matrix[digit1][digit2] += 1
        
        self.last_appearance[root] = day_count
        self.recalculate_intervals(day_count)
    
    def recalculate_intervals(self, current_day):
        """Hitung interval untuk semua root number"""
        for root in range(1, 10):
            if root in self.last_appearance:
                self.current_intervals[root] = current_day - self.last_appearance[root]
            else:
                self.current_intervals[root] = 999
    
    def get_priority_roots(self, count=5):
        """Dapatkan root dengan interval tertinggi"""
        return sorted(self.current_intervals.items(), key=lambda x: x[1], reverse=True)[:count]
    
    def get_weighted_hot_zones(self, count=25, recent_weight=3):
        """Dapatkan zone terpanas dengan bobot data terbaru"""
        # Buat matrix temporari untuk data terbaru
        recent_matrix = np.zeros((10, 10))
        
        # Berikan bobot lebih untuk data terbaru (50 data terakhir)
        recent_data = self.number_history[-50:] if len(self.number_history) > 50 else self.number_history
        for num in recent_data:
            d1, d2 = int(num[0]), int(num[1])
            recent_matrix[d1][d2] += recent_weight
        
        # Gabungkan dengan historical data
        combined_matrix = self.pos_matrix + recent_matrix
        
        zones = []
        for i in range(10):
            for j in range(10):
                zones.append(((i, j), combined_matrix[i][j]))
        
        zones.sort(key=lambda x: x[1], reverse=True)
        return [zone[0] for zone in zones[:count]]
    
    def get_all_numbers_with_root(self, target_root):
        """Dapatkan semua angka 2D dengan root tertentu"""
        return [str(i).zfill(2) for i in range(100) if self.calculate_root(i) == target_root]
    
    def get_weighted_hot_numbers(self, count=30, recent_weight=2):
        """Dapatkan angka panas dengan bobot data terbaru"""
        if not self.number_history:
            return []
            
        # Data sangat terbaru (20 angka) dapat bobot lebih
        very_recent = self.number_history[-20:] if len(self.number_history) >= 20 else self.number_history
        recent_data = self.number_history[-100:] if len(self.number_history) > 100 else self.number_history
        
        freq = Counter(recent_data)
        
        # Berikan bonus weight untuk data sangat baru
        for num in very_recent:
            if num in freq:
                freq[num] += recent_weight
        
        # Urutkan berdasarkan frekuensi (descending), lalu angka (ascending)
        sorted_numbers = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
        
        return [num for num, _ in sorted_numbers[:count]]
    
    def add_mirror_and_sibling_numbers(self, base_numbers):
        """Tambahkan mirror dan sibling numbers ke base numbers"""
        enhanced = set(base_numbers)
        
        # Mirror numbers (AB → BA)
        for num in base_numbers:
            if num[0] != num[1]:  # Hindari double numbers
                mirror = num[1] + num[0]
                enhanced.add(mirror)
        
        # Sibling numbers (±1 dari masing-masing digit)
        for num in base_numbers:
            n1, n2 = int(num[0]), int(num[1])
            
            siblings = [
                f"{(n1-1)%10}{n2}", f"{(n1+1)%10}{n2}",
                f"{n1}{(n2-1)%10}", f"{n1}{(n2+1)%10}",
                f"{(n1-1)%10}{(n2-1)%10}", f"{(n1+1)%10}{(n2+1)%10}"
            ]
            
            for s in siblings:
                if 0 <= int(s) <= 99:  # Pastikan valid
                    enhanced.add(s)
        
        return list(enhanced)
    
    def prioritize_numbers(self, numbers, max_count):
        """Prioritaskan angka berdasarkan score (deterministic)"""
        scored_numbers = []
        for num in numbers:
            score = 0
            root = self.calculate_root(int(num))
            
            # Priority roots score
            priority_roots = [r for r, _ in self.get_priority_roots(5)]
            if root in priority_roots:
                score += 2
            
            # Hot zones score
            d1, d2 = int(num[0]), int(num[1])
            hot_zones = self.get_weighted_hot_zones(25)
            if (d1, d2) in hot_zones:
                score += 1
            
            # Hot numbers score
            hot_numbers = self.get_weighted_hot_numbers(30)
            if num in hot_numbers:
                score += 1.5
            
            # Recent numbers bonus
            if num in self.number_history[:10]:
                score += 1
            
            scored_numbers.append((num, score))
        
        # Urutkan berdasarkan score (descending) dan angka (ascending)
        scored_numbers.sort(key=lambda x: (-x[1], x[0]))
        return [num for num, score in scored_numbers[:max_count]]
    
    def generate_high_volume_predictions(self):
        """Generate angka prediction dengan strategi improved"""
        all_numbers = [str(i).zfill(2) for i in range(100)]
        
        if not self.number_history:
            return all_numbers[:self.max_numbers]
        
        selected = set()
        
        # 1. Priority Roots (4 roots dengan interval tertinggi)
        priority_roots = [root for root, _ in self.get_priority_roots(4)]
        for root in priority_roots:
            selected.update(self.get_all_numbers_with_root(root))
        
        # 2. Weighted Hot Zones (25 zones terpanas)
        hot_zones = self.get_weighted_hot_zones(25, recent_weight=3)
        zone_numbers = [num for num in all_numbers if (int(num[0]), int(num[1])) in hot_zones]
        selected.update(zone_numbers)
        
        # 3. Weighted Hot Numbers (30 numbers terpanas)
        hot_numbers = self.get_weighted_hot_numbers(30, recent_weight=2)
        selected.update(hot_numbers)
        
        # 4. Very Recent Numbers (10 numbers terbaru)
        very_recent = self.number_history[:10]
        selected.update(very_recent)
        
        # 5. Add mirror and sibling numbers
        enhanced = self.add_mirror_and_sibling_numbers(selected)
        
        # Prioritaskan angka (deterministic, bukan random)
        final_numbers = self.prioritize_numbers(enhanced, self.max_numbers)
        final_numbers.sort()
        
        return final_numbers
    
    def split_for_webs(self, numbers, overlap_percent=50):
        """Bagi angka untuk 2 web dengan overlap percentage"""
        if not numbers:
            return [], [], []
            
        total = len(numbers)
        overlap_count = max(10, int(total * overlap_percent / 100))
        overlap_count = min(overlap_count, total)
        
        # Web 1: pertama sampai (total - overlap_count/2)
        # Web 2: (overlap_count/2) sampai akhir
        split_point = (total - overlap_count) // 2
        
        web1 = numbers[:split_point + overlap_count]
        web2 = numbers[split_point:]
        overlap = numbers[split_point:split_point + overlap_count]
        
        return web1, web2, overlap

    def get_recent_results(self, count=10):
        """Dapatkan hasil keluaran terakhir dengan detail"""
        if not self.number_history:
            return []
            
        recent_data = []
        actual_count = min(count, len(self.number_history))
        
        for i in range(actual_count):
            num = self.number_history[i]
            root = self.calculate_root(int(num))
            recent_data.append({
                'number': num,
                'root': root
            })
        
        return recent_data

    def test_accuracy(self, test_size=300):
        """Test accuracy terhadap data historis"""
        if len(self.number_history) < test_size + 1:
            return "Not enough data"
        
        # Simpan nilai max_numbers asli
        original_max = self.max_numbers
        
        correct_predictions = 0
        for i in range(test_size):
            # Set max_numbers untuk testing
            self.max_numbers = 50
            
            # Train dengan data sampai index i
            test_predictor = RootMatrixPredictor(max_numbers=50)
            
            # Gunakan data historis sampai index i untuk training
            training_data = self.number_history[:i+1]
            
            # Analisis data training dengan benar
            test_predictor.analyze_data(training_data)
            
            # Predict next number
            predictions = test_predictor.generate_high_volume_predictions()
            actual_next = self.number_history[i+1]
            
            if actual_next in predictions:
                correct_predictions += 1
            
            # Progress indicator untuk testing yang lama
            if (i + 1) % 10 == 0:
                print(f"  Testing {i + 1}/{test_size} completed")
        
        # Kembalikan nilai max_numbers asli
        self.max_numbers = original_max
        
        accuracy = (correct_predictions / test_size) * 100
        return f"Accuracy: {accuracy:.2f}% ({correct_predictions}/{test_size})"

    def real_time_test(self):
        """Test prediksi untuk data terbaru"""
        if len(self.number_history) < 2:
            return "Not enough data"
        
        # Simpan nilai max_numbers asli
        original_max = self.max_numbers
        self.max_numbers = 50
        
        # Predict untuk data kedua terbaru (test pada data pertama)
        test_data = self.number_history[1:]
        test_predictor = RootMatrixPredictor(max_numbers=50)
        test_predictor.analyze_data(test_data)
        
        predictions = test_predictor.generate_high_volume_predictions()
        actual = self.number_history[0]
        
        # Kembalikan nilai max_numbers asli
        self.max_numbers = original_max
        
        print(f"🔍 REAL-TIME TEST:")
        print(f"Actual: {actual}")
        print(f"In predictions: {actual in predictions}")
        print(f"Total predictions: {len(predictions)}")
        
        if actual not in predictions:
            print("Analyzing why missed...")
            root = self.calculate_root(int(actual))
            print(f"Root: {root}")
            priority_roots = [r for r, _ in self.get_priority_roots(5)]
            print(f"Root in priority: {root in priority_roots}")
            
            # Cek hot zones
            d1, d2 = int(actual[0]), int(actual[1])
            hot_zones = self.get_weighted_hot_zones(25)
            print(f"Position in hot zones: {(d1, d2) in hot_zones}")
            
            # Cek hot numbers
            hot_numbers = self.get_weighted_hot_numbers(30)
            print(f"In hot numbers: {actual in hot_numbers}")

    def save_root_analysis(self):
        """Simpan analisis root number ke file"""
        if not self.number_history:
            print("❌ Tidak ada data untuk dianalisis")
            return
            
        with open("root_analysis.txt", "w", encoding="utf-8") as f:
            f.write("=== ANALISIS ROOT NUMBER ===\n")
            f.write(f"Total Data: {len(self.number_history)} angka\n")
            f.write(f"Tanggal Analisis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("📊 FREKUENSI ROOT NUMBER:\n")
            root_freq = Counter(self.root_history)
            for root in range(1, 10):
                count = root_freq.get(root, 0)
                percentage = (count / len(self.root_history)) * 100
                f.write(f"Root {root}: {count} kali ({percentage:.1f}%)\n")
            
            f.write("\n⏰ INTERVAL KEMUNCULAN (hari):\n")
            for root in range(1, 10):
                interval = self.current_intervals.get(root, 999)
                f.write(f"Root {root}: {interval} hari\n")
            
            f.write("\n🎯 REKOMENDASI ROOT PRIORITAS:\n")
            priority_roots = self.get_priority_roots(5)
            for root, interval in priority_roots:
                f.write(f"Root {root}: {interval} hari → ★★★\n")
            
            f.write("\n📋 DETAIL ANGKANYA:\n")
            for root in range(1, 10):
                numbers = self.get_all_numbers_with_root(root)
                f.write(f"Root {root}: {', '.join(numbers)}\n")

def main():
    # ==================== TAN INI BRO ====================
    MAX_PREDICTED_NUMBERS = 79  # GANTI ANGKA INI SESUKA LO
    # =====================================================
    
    predictor = RootMatrixPredictor(max_numbers=MAX_PREDICTED_NUMBERS)
    FILE_PATH = "Dataset_Sidneypools.xlsx"
    
    print("🔍 Memuat data dari Excel...")
    data_2d = predictor.load_data(FILE_PATH)
    
    if not data_2d:
        print("❌ Gagal memuat data. Pastikan file Excel ada dan formatnya benar.")
        return
    
    print(f"✅ Data berhasil dimuat: {len(data_2d)} angka 2D")
    
    # Analisis data
    predictor.analyze_data(data_2d)
    
    # Tampilkan data terbaru
    if predictor.number_history:
        latest = predictor.number_history[0]
        print(f"\n🔍 DATA TERBARU: {latest} (Root {predictor.calculate_root(int(latest))})")
    
    # Tampilkan beberapa data terbaru
    print(f"\n🔍 10 DATA TERBARU:")
    recent = predictor.get_recent_results(10)
    for i, data in enumerate(recent, 1):
        print(f"  {i}. {data['number']} (Root {data['root']})")
    
    # Real-time test
    predictor.real_time_test()
    
    # Test accuracy
    print(f"\n🧪 TESTING ACCURACY...")
    accuracy_result = predictor.test_accuracy(300)
    print(accuracy_result)
    
    # Generate predictions
    print(f"\n🎯 GENERATING PREDICTIONS...")
    predicted_numbers = predictor.generate_high_volume_predictions()
    print(f"TOTAL PREDICTED NUMBERS: {len(predicted_numbers)} angka")
    
    # Split untuk webs
    web1, web2, overlap = predictor.split_for_webs(predicted_numbers, 48)
    
    print(f"\n🌐 WEB 1 ({len(web1)} angka):")
    print("*".join(web1))
    
    print(f"\n🌐 WEB 2 ({len(web2)} angka):")
    print("*".join(web2))
    
    print(f"\n🔥 OVERLAP ({len(overlap)} angka):")
    print("*".join(overlap))
    
    # Simpan analisis
    predictor.save_root_analysis()
    print(f"\n💾 Analisis disimpan ke root_analysis.txt")

if __name__ == "__main__":
    main()