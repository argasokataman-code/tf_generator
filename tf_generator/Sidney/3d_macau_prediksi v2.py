import pandas as pd
import numpy as np
from collections import Counter, defaultdict
from datetime import datetime

class RootMatrixPredictor:
    def __init__(self):
        self.root_history = []
        self.number_history = []  # Menyimpan 2D depan
        self.number_3d_history = []  # Menyimpan 3D depan (jika ada)
        self.root_matrix = np.zeros((3, 3))
        self.pos_matrix = np.zeros((10, 10))
        self.first_digit_freq = np.zeros(10)  # Frekuensi digit pertama untuk 3D
        self.last_appearance = {}
        self.current_intervals = {}
        self.root_mapping = {
            1: (0, 0), 2: (0, 1), 3: (0, 2),
            4: (1, 0), 5: (1, 1), 6: (1, 2),
            7: (2, 0), 8: (2, 1), 9: (2, 2)
        }
        
    def calculate_root(self, number):
        """Hitung root number dari angka 2D"""
        n = int(number)
        if n == 0:
            return 9
        root = n % 9
        return root if root != 0 else 9
    
    def load_data(self, file_path, use_3d=False):
        """Load data dari file Excel - TANPA HEADER"""
        try:
            # Baca semua data tanpa header, skip 2 baris pertama
            data = pd.read_excel(file_path, header=None, skiprows=2, dtype=str)
            
            print(f"🔍 Shape data: {data.shape}")
            print("🔍 Sample data:")
            print(data.head(3))
            
            all_numbers = []
            
            # Iterasi melalui semua baris dan kolom
            for row_idx in range(len(data)):
                for col_idx in data.columns:
                    cell_value = str(data.iloc[row_idx, col_idx]).strip()
                    
                    # Skip cell kosong atau tidak valid
                    if cell_value in ['nan', 'None', '', 'NaN', 'NaT']:
                        continue
                    
                    # Bersihkan angka dari karakter non-digit
                    clean_num = ''.join(filter(str.isdigit, cell_value))
                    
                    if use_3d and len(clean_num) >= 3:
                        three_digit = clean_num[:3]  # Ambil 3 digit pertama (3D depan)
                        all_numbers.append(three_digit)
                    elif not use_3d and len(clean_num) >= 2:
                        two_digit = clean_num[:2]  # Ambil 2 digit pertama (2D depan)
                        all_numbers.append(two_digit)
                    elif len(clean_num) == 1:
                        # Format ke 2 digit dengan leading zero
                        formatted_num = f"0{clean_num}" if not use_3d else f"00{clean_num}"
                        all_numbers.append(formatted_num)
            
            print(f"✅ Total angka {'3D' if use_3d else '2D'} ditemukan: {len(all_numbers)}")
            
            if not all_numbers:
                print("❌ Tidak ada data angka yang valid ditemukan")
                return []
            
            print(f"🔍 5 data terakhir sebelum reverse: {all_numbers[-5:]}")
            
            # Reverse urutan data (yang terbaru jadi pertama)
            all_numbers.reverse()
            
            print(f"🔍 5 data pertama setelah reverse: {all_numbers[:5]}")
            
            return all_numbers
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def convert_2d_to_3d_optimized(self, hot_digits_count=3, max_predictions=100):
        """Convert 2D predictions to 3D dengan filter lebih ketat"""
        if not self.number_history:
            return []
        
        # 1. Dapatkan prediksi 2D yang sudah difilter
        predicted_2d = self.generate_high_volume_predictions()
        
        # 2. Filter lagi prediksi 2D berdasarkan frekuensi terbaru
        recent_2d = self.number_history[-100:] if len(self.number_history) > 100 else self.number_history
        freq_2d = Counter(recent_2d)
        
        # Prioritaskan 2D yang sering muncul
        filtered_2d = []
        for num in predicted_2d:
            if num in freq_2d and freq_2d[num] >= 1:  # Minimal muncul 1x dalam 100 data terakhir
                filtered_2d.append(num)
        
        # Jika masih terlalu banyak, ambil yang paling sering
        if len(filtered_2d) > 30:
            filtered_2d = sorted(filtered_2d, key=lambda x: freq_2d.get(x, 0), reverse=True)[:30]
        
        print(f"🔥 2D terfilter: {len(filtered_2d)} angka")
        
        # 3. Analisis digit pertama yang paling hot
        first_digit_counter = Counter()
        
        if self.number_3d_history:
            # Ambil data 3D terbaru saja (100 data terakhir)
            recent_3d = self.number_3d_history[-100:] if len(self.number_3d_history) > 100 else self.number_3d_history
            for num in recent_3d:
                if len(num) >= 3:
                    first_digit = int(num[0])
                    first_digit_counter[first_digit] += 1
        else:
            # Fallback ke digit umum
            for i in range(10):
                first_digit_counter[i] = 1
        
        # Ambil hanya 3 digit terpanas
        hot_digits = [digit for digit, count in first_digit_counter.most_common(hot_digits_count)]
        print(f"🔥 Digit terpanas untuk 3D: {hot_digits}")
        
        # 4. Gabungkan dengan pattern matching
        predicted_3d = []
        for digit in hot_digits:
            for num_2d in filtered_2d:
                predicted_3d.append(f"{digit}{num_2d}")
        
        # 5. Filter tambahan berdasarkan pattern
        final_predictions = []
        for num in predicted_3d:
            # Filter angka kembar berlebihan (kecuali 2 digit terakhir)
            if num[0] == num[1] == num[2]:
                continue  # Skip triple angka sama
            final_predictions.append(num)
        
        # Batasi maksimal output
        final_predictions = final_predictions[:max_predictions]
        
        print(f"✅ 3D predictions dioptimasi: {len(final_predictions)} angka")
        return final_predictions
        
    def analyze_data(self, data_2d, data_3d=None):
        """Analisis data dan build matrix"""
        print(f"📊 Menganalisis {len(data_2d)} data 2D...")
        day_count = 0
        for num in data_2d:
            day_count += 1
            self.add_new_data(num, day_count)
        
        # Simpan data 3D jika tersedia
        if data_3d:
            self.number_3d_history = data_3d
            print(f"📊 Juga menyimpan {len(data_3d)} data 3D untuk referensi")
        
        print(f"✅ Analisis selesai. Total hari: {day_count}")
    
    def add_new_data(self, new_number, day_count):
        """Tambahkan data baru dan update semua parameter"""
        root = self.calculate_root(int(new_number))
        
        self.number_history.append(new_number)
        self.root_history.append(root)
        
        i, j = self.root_mapping[root]
        self.root_matrix[i][j] += 1
        
        # Untuk 2D, digit1 adalah puluhan, digit2 adalah satuan
        if len(new_number) == 2:
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
    
    def get_hot_zones(self, count=20):
        """Dapatkan zone terpanas berdasarkan position matrix"""
        zones = []
        for i in range(10):
            for j in range(10):
                zones.append(((i, j), self.pos_matrix[i][j]))
        
        zones.sort(key=lambda x: x[1], reverse=True)
        return [zone[0] for zone in zones[:count]]
    
    def get_all_numbers_with_root(self, target_root):
        """Dapatkan semua angka 2D dengan root tertentu"""
        return [str(i).zfill(2) for i in range(100) if self.calculate_root(i) == target_root]
    
    def get_recent_hot_numbers(self, count=30):
        """Dapatkan angka yang sering muncul baru-baru ini"""
        if not self.number_history:
            return []
            
        recent_data = self.number_history[-300:] if len(self.number_history) > 300 else self.number_history
        freq = Counter(recent_data)
        
        # Urutkan berdasarkan frekuensi (descending), lalu angka (ascending)
        sorted_numbers = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
        
        return [num for num, _ in sorted_numbers[:count]]
    
    def generate_high_volume_predictions(self):
        """Generate angka prediction 2D dengan strategi"""
        all_numbers = [str(i).zfill(2) for i in range(100)]
        
        if not self.number_history:
            return all_numbers
        
        # 1. Priority Roots
        priority_roots = [root for root, _ in self.get_priority_roots(4)]
        root_based = [num for num in all_numbers if self.calculate_root(int(num)) in priority_roots]
        
        # 2. Hot Zones
        hot_zones = self.get_hot_zones(25)
        zone_based = [num for num in all_numbers if (int(num[0]), int(num[1])) in hot_zones]
        
        # 3. Recent Hot Numbers
        hot_numbers = self.get_recent_hot_numbers(25)
        
        # 4. Combine semua
        combined = list(set(root_based + zone_based + hot_numbers))
        combined.sort()
        
        return combined
    
    def split_for_webs(self, numbers, overlap_percent=50):
        """Bagi angka untuk 2 web dengan overlap percentage"""
        if not numbers:
            return [], [], []
            
        total = len(numbers)
        overlap_count = max(10, int(total * overlap_percent / 100))
        overlap_count = min(overlap_count, total)
        
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

    def test_accuracy(self, test_size=1000):
        """Test accuracy terhadap data historis"""
        if len(self.number_history) < test_size + 1:
            return "Not enough data"
        
        correct_predictions = 0
        for i in range(test_size):
            test_predictor = RootMatrixPredictor()
            training_data = self.number_history[:i+1]
            test_predictor.analyze_data(training_data)
            
            predictions = test_predictor.generate_high_volume_predictions()
            actual_next = self.number_history[i+1]
            
            if actual_next in predictions:
                correct_predictions += 1
            
            if (i + 1) % 10 == 0:
                print(f"  Testing {i + 1}/{test_size} completed")
        
        accuracy = (correct_predictions / test_size) * 100
        return f"Accuracy: {accuracy:.2f}% ({correct_predictions}/{test_size})"

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
    predictor = RootMatrixPredictor()
    FILE_PATH = "Data_Macau_FINAL_FIX.xlsx"
    
    print("🔍 Memuat data 2D dari Excel...")
    data_2d = predictor.load_data(FILE_PATH, use_3d=False)
    
    if not data_2d:
        print("❌ Gagal memuat data 2D. Pastikan file Excel ada dan formatnya benar.")
        return
    
    print(f"✅ Data 2D berhasil dimuat: {len(data_2d)} angka")
    
    # Optional: Load 3D data for first digit analysis
    print("\n🔍 Memuat data 3D dari Excel (untuk analisis digit pertama)...")
    data_3d = predictor.load_data(FILE_PATH, use_3d=True)
    
    # Analisis data 2D (dan simpan data 3D jika ada)
    predictor.analyze_data(data_2d, data_3d)
    
    # Tampilkan data terbaru
    if predictor.number_history:
        latest = predictor.number_history[0]
        print(f"\n🔍 DATA TERBARU: {latest} (Root {predictor.calculate_root(int(latest))})")
    
    # Tampilkan beberapa data terbaru
    print(f"\n🔍 10 DATA TERBARU:")
    recent = predictor.get_recent_results(10)
    for i, data in enumerate(recent, 1):
        print(f"  {i}. {data['number']} (Root {data['root']})")
    
    # Test accuracy
    print(f"\n🧪 TESTING ACCURACY 2D...")
    accuracy_result = predictor.test_accuracy(1000)
    print(accuracy_result)
    
    # Generate 2D predictions
    print(f"\n🎯 GENERATING 2D PREDICTIONS...")
    predicted_2d = predictor.generate_high_volume_predictions()
    print(f"TOTAL PREDICTED 2D NUMBERS: {len(predicted_2d)} angka")
    
    # Convert to 3D predictions
    print(f"\n🔄 CONVERTING TO 3D PREDICTIONS...")
    predicted_3d = predictor.convert_2d_to_3d_optimized(hot_digits_count=3, max_predictions=100)

    print(f"TOTAL PREDICTED 3D NUMBERS: {len(predicted_3d)} angka")
    
    # Split untuk webs
    web1, web2, overlap = predictor.split_for_webs(predicted_3d, 50)
    
    print(f"\n🌐 WEB 1 3D ({len(web1)} angka):")
    print("*".join(web1))
    
    print(f"\n🌐 WEB 2 3D ({len(web2)} angka):")
    print("*".join(web2))
    
    print(f"\n🔥 OVERLAP 3D ({len(overlap)} angka):")
    print("*".join(overlap))
    
    # Simpan analisis
    predictor.save_root_analysis()
    print(f"\n💾 Analisis disimpan ke root_analysis.txt")

if __name__ == "__main__":
    main()