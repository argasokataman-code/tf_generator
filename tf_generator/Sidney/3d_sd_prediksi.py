import pandas as pd
from collections import Counter
import random
import math

def load_data(file_path):
    """Load 3D depan (termasuk yang ada leading zeros)"""
    try:
        # 1. Load data as STRING untuk jaga leading zeros
        data = pd.read_excel(file_path, header=None, dtype=str, names=["Angka"])
        
        # 2. Bersihkan data:
        #    - Hapus baris kosong
        #    - Hapus spasi
        #    - Ambil 3 digit pertama
        data_3d = (
            data["Angka"]
            .dropna()
            .str.strip()
            .str.replace(r'[^0-9]', '', regex=True)  # Hapus semua non-digit
            .str[:3]  # Ambil 3 digit depan
        )
        
        # 3. Filter & format:
        #    - Pastikan panjang = 3 digit
        #    - Pad dengan leading zero jika kurang (1 -> 001, 12 -> 012)
        valid_numbers = [
            num.zfill(3)
            for num in data_3d 
            if num.isdigit() and len(num) >= 1  # Terima minimal 1 digit (nanti di-pad ke 3)
        ]
        
        # 4. Hapus duplikat & return
        return list(dict.fromkeys(valid_numbers))  # Jaga urutan awal
        
    except Exception as e:
        print(f"ERROR: {e}")
        return []

def generate_unique_numbers(data_3d, total_numbers=70):
    """Generate unique 3D numbers with hot/cold strategy"""
    if not data_3d:
        return []
    
    freq_3d = Counter(data_3d)
    unique_numbers = list(freq_3d.keys())
    
    # Calculate hot and cold numbers
    hot_numbers = [num for num, _ in freq_3d.most_common(math.ceil(len(unique_numbers) * 0.7))]
    cold_numbers = [num for num in unique_numbers if num not in hot_numbers]
    
    # Generate numbers with priority to hot numbers
    combined = []
    remaining_slots = total_numbers
    
    # Add hot numbers first
    combined.extend(hot_numbers[:remaining_slots])
    remaining_slots = total_numbers - len(combined)
    
    # Add cold numbers if needed
    if remaining_slots > 0:
        combined.extend(random.sample(cold_numbers, min(remaining_slots, len(cold_numbers))))
    
    # If still not enough, generate random unique numbers
    if len(combined) < total_numbers:
        needed = total_numbers - len(combined)
        for _ in range(needed):
            while True:
                new_num = f"{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}"
                if new_num not in combined and new_num not in freq_3d:
                    combined.append(new_num)
                    break
    
    # Final check for duplicates
    assert len(combined) == len(set(combined)), "Duplicate numbers found!"
    random.shuffle(combined)
    return combined[:total_numbers]

def split_for_webs(numbers, per_web=25):
    """Split numbers for multiple betting WEB"""
    return [numbers[i:i + per_web] for i in range(0, len(numbers), per_web)]

def main():
    # Configuration
    FILE_PATH = "Dataset_Sidneypools.xlsx"
    TOTAL_NUMBERS = 70  # Target total numbers to generate
    NUMBERS_PER_WEB = 25  # Numbers for each betting platform
    
    # Load and process data
    data_3d = load_data(FILE_PATH)
    
    if not data_3d:
        print("No valid data found. Check your Excel file.")
        return
    
    # Generate numbers
    predicted_numbers = generate_unique_numbers(data_3d, TOTAL_NUMBERS)
    
    if not predicted_numbers:
        print("Failed to generate numbers.")
        return
    
    print(f"\nSuccessfully generated {len(predicted_numbers)} unique 3D numbers:")
    print("*".join(predicted_numbers))
    
    # Split for multiple betting WEB
    web_splits = split_for_webs(predicted_numbers, NUMBERS_PER_WEB)
    
    print("\nSplit for betting WEB:")
    for i, numbers in enumerate(web_splits, 1):
        print(f"\nWEB {i} ({len(numbers)} numbers):")
        print("*".join(numbers))

if __name__ == "__main__":
    main()