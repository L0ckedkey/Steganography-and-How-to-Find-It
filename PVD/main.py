import os
import subprocess

# Path utama
cover_root = r"E:\LSB Steg\LSB-Steganography\image\cover"
secret_file = "secret.txt"
output_root = r"E:\LSB Steg\LSB-Steganography\image\stegano-2\pvd"


def process_cover(cover_path, output_folder, filename):
    """Proses satu file cover → panggil test_main.py"""
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, filename)

    cmd = ["python", "test_main.py", "E", cover_path, secret_file, output_path]
    print("▶️ Running:", " ".join(cmd))
    subprocess.run(cmd)


def main():
    for root, _, files in os.walk(cover_root):
        rel_path = os.path.relpath(root, cover_root)  # path relatif terhadap cover_root
        output_folder = os.path.join(output_root, rel_path)

        png_files = [f for f in files if f.lower().endswith(".png")]
        if not png_files:
            continue

        print(f"\n📂 Folder {rel_path} berisi: {png_files}")

        for file in png_files:
            cover_path = os.path.join(root, file)
            process_cover(cover_path, output_folder, file)

    print("\nSelesai 🚀")


if __name__ == "__main__":
    main()
