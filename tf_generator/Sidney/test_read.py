import pandas as pd

try:
    df = pd.read_excel("Dataset_Macau.xlsx")
    print("File berhasil dibaca!")
    print(df.head()) # Menampilkan 5 baris pertama
except FileNotFoundError:
    print("ERROR: File tidak ditemukan di direktori yang benar.")
except Exception as e:
    print(f"ERROR LAIN: Terjadi kesalahan saat membaca file. Pesan: {e}")