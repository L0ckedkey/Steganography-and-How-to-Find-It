from bpcs import BPCS, psnr
import os
import cv2
from message import Message


cover_root = r"path\to\directory"
output_dir = r"pat\to\directory"

os.makedirs(output_dir, exist_ok=True)

folders = [f for f in os.listdir(cover_root) if os.path.isdir(os.path.join(cover_root, f))]

def process_file(input_path, output_path, filename):
    try:
        bpcs = BPCS(input_path)
        msg = Message(pathname='secret.txt')
        bitplane_msg = msg.create_message()
        img_result = bpcs.hide(bitplane_msg)

        cv2.imwrite(output_path, img_result)
        print(f"✅ Disimpan ke: {output_path}")
    except Exception as e:
        print(f"❌ Gagal memproses {filename}: {e}")

if folders:
    print("📂 Ditemukan subfolder:", folders)

    for folder in folders:
        folder_path = os.path.join(cover_root, folder)
        files = [f for f in os.listdir(folder_path) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
        print(f"\nFolder {folder} berisi:", files)

        for filename in files:
            input_path = os.path.join(folder_path, filename)
            output_path = os.path.join(output_dir, f"{folder}_{filename}")
            process_file(input_path, output_path, filename)
else:
    files = [f for f in os.listdir(cover_root) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
    print("📂 Tidak ada subfolder, file langsung:", files)

    for filename in files:
        input_path = os.path.join(cover_root, filename)
        output_path = os.path.join(output_dir, f"{filename}")
        process_file(input_path, output_path, filename)

print("\n🚀 Selesai!")
