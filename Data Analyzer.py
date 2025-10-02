import os
import matplotlib.pyplot as plt
import pandas as pd
from collections import defaultdict
import seaborn as sns

def count_images_in_folder(folder_path):
    """
    Menghitung jumlah file gambar dalam folder berdasarkan ekstensi
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
    count = 0
    
    if os.path.exists(folder_path):
        for file in os.listdir(folder_path):
            if any(file.lower().endswith(ext) for ext in image_extensions):
                count += 1
    
    return count

def analyze_folder_structure(base_path):
    """
    Menganalisis struktur folder dan menghitung gambar di setiap subfolder
    """
    results = defaultdict(lambda: defaultdict(int))
    
    # Struktur folder berdasarkan tree yang diberikan
    folder_structure = {
        'cover': ['android_icon', 'full_color', 'gray', 'pokemon'],
        'cover-reveal': ['android_icon', 'full_color', 'gray', 'pokemon'],
        'stegano/BPCS': ['android_icon', 'full_color', 'gray', 'pokemon'],
        'stegano/LSB': ['android_icon', 'full_color', 'gray', 'pokemon'],
        'stegano/PVD': ['android_icon', 'full_color', 'gray', 'pokemon'],
        'stegano-reveal/BPCS': ['android_icon', 'full_color', 'gray', 'pokemon'],
        'stegano-reveal/LSB': ['android_icon', 'full_color', 'gray', 'pokemon'],
        'stegano-reveal/PVD': ['android_icon', 'full_color', 'gray', 'pokemon']
    }
    
    for main_folder, subfolders in folder_structure.items():
        for subfolder in subfolders:
            folder_path = os.path.join(base_path, main_folder, subfolder)
            count = count_images_in_folder(folder_path)
            results[main_folder][subfolder] = count
    
    return results

def create_charts(results):
    """
    Membuat berbagai jenis chart untuk visualisasi data
    """
    # Set style untuk plot yang lebih menarik
    plt.style.use('seaborn-v0_8')
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Analisis Jumlah Gambar dalam Struktur Folder', fontsize=16, fontweight='bold')
    
    # 1. Bar Chart - Total per kategori utama
    main_categories = list(results.keys())
    total_counts = [sum(results[cat].values()) for cat in main_categories]
    
    axes[0, 0].bar(range(len(main_categories)), total_counts, 
                   color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F'])
    axes[0, 0].set_title('Total Gambar per Kategori Utama', fontweight='bold')
    axes[0, 0].set_xticks(range(len(main_categories)))
    axes[0, 0].set_xticklabels(main_categories, rotation=45, ha='right')
    axes[0, 0].set_ylabel('Jumlah Gambar')
    
    # Tambah angka di atas bar
    for i, v in enumerate(total_counts):
        axes[0, 0].text(i, v + 0.5, str(v), ha='center', va='bottom', fontweight='bold')
    
    # 2. Heatmap - Distribusi per subfolder
    # Buat dataframe untuk heatmap
    df_data = []
    for main_cat, subcats in results.items():
        for subcat, count in subcats.items():
            df_data.append({'Main Category': main_cat, 'Sub Category': subcat, 'Count': count})
    
    df = pd.DataFrame(df_data)
    pivot_df = df.pivot(index='Sub Category', columns='Main Category', values='Count')
    pivot_df = pivot_df.fillna(0)
    
    sns.heatmap(pivot_df, annot=True, cmap='YlOrRd', ax=axes[0, 1], 
                cbar_kws={'label': 'Jumlah Gambar'}, fmt='.0f')
    axes[0, 1].set_title('Heatmap Distribusi Gambar', fontweight='bold')
    axes[0, 1].set_xlabel('Kategori Utama')
    axes[0, 1].set_ylabel('Sub Kategori')
    
    # 3. Pie Chart - Distribusi tipe gambar
    type_counts = defaultdict(int)
    for main_cat, subcats in results.items():
        for subcat, count in subcats.items():
            # Ekstrak tipe dari nama subfolder
            if 'android_icon' == subcat:
                type_counts['Android Icon'] += count
            elif 'full_color' == subcat:
                type_counts['Full Color'] += count
            elif 'gray' == subcat:
                type_counts['Grayscale'] += count
            elif 'pokemon' == subcat:
                type_counts['Pokemon'] += count
    
    if sum(type_counts.values()) > 0:
        axes[1, 0].pie(type_counts.values(), labels=type_counts.keys(), autopct='%1.1f%%',
                       colors=['#FF9999', '#66B2FF', '#99FF99', '#FFCC99'])
        axes[1, 0].set_title('Distribusi Tipe Gambar', fontweight='bold')
    
    # 4. Stacked Bar Chart - Detail per metode steganografi
    stegano_methods = ['BPCS', 'LSB', 'PVD']
    categories = ['stegano', 'stegano-reveal']
    
    bottom_values = [0, 0, 0]
    colors = ['#FF6B6B', '#4ECDC4']
    
    for i, category in enumerate(categories):
        method_counts = []
        for method in stegano_methods:
            key = f'{category}/{method}'
            if key in results:
                method_counts.append(sum(results[key].values()))
            else:
                method_counts.append(0)
        
        axes[1, 1].bar(stegano_methods, method_counts, bottom=bottom_values, 
                       label=category, color=colors[i], alpha=0.8)
        bottom_values = [bottom_values[j] + method_counts[j] for j in range(len(method_counts))]
    
    axes[1, 1].set_title('Gambar per Metode Steganografi', fontweight='bold')
    axes[1, 1].set_xlabel('Metode Steganografi')
    axes[1, 1].set_ylabel('Jumlah Gambar')
    axes[1, 1].legend()
    
    plt.tight_layout()
    plt.show()
    
    return df

def print_summary(results):
    """
    Mencetak ringkasan hasil analisis
    """
    print("=" * 60)
    print("RINGKASAN ANALISIS STRUKTUR FOLDER GAMBAR")
    print("=" * 60)
    
    total_images = 0
    for main_cat, subcats in results.items():
        cat_total = sum(subcats.values())
        total_images += cat_total
        print(f"\n📁 {main_cat.upper()}: {cat_total} gambar")
        for subcat, count in subcats.items():
            print(f"   └── {subcat}: {count} gambar")
    
    print(f"\n🎯 TOTAL KESELURUHAN: {total_images} gambar")
    print("=" * 60)

# Contoh penggunaan
def main():
    # Ganti dengan path folder yang sesuai
    base_folder_path = "."  # Current directory, atau ganti dengan path absolut
    
    print("🔍 Menganalisis struktur folder...")
    results = analyze_folder_structure(base_folder_path)
    
    # Cetak ringkasan
    print_summary(results)
    
    # Buat chart
    print("\n📊 Membuat visualisasi chart...")
    df = create_charts(results)
    
    # Simpan data ke CSV (opsional)
    df.to_csv('image_count_analysis.csv', index=False)
    print("\n💾 Data analisis disimpan ke 'image_count_analysis.csv'")
    
    return results, df

if __name__ == "__main__":
    # Jalankan analisis
    results, df = main()
    
    # Tambahan: Analisis statistik sederhana
    print("\n📈 STATISTIK TAMBAHAN:")
    print(f"   • Rata-rata gambar per subfolder: {df['Count'].mean():.1f}")
    print(f"   • Subfolder dengan gambar terbanyak: {df.loc[df['Count'].idxmax(), 'Sub Category']} ({df['Count'].max()} gambar)")
    print(f"   • Subfolder dengan gambar tersedikit: {df.loc[df['Count'].idxmin(), 'Sub Category']} ({df['Count'].min()} gambar)")