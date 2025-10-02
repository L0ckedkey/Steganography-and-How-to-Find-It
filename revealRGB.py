from PIL import Image
import numpy as np
import os

input_root = r"path\to\directory"
output_root = r"path\to\directory"


def extract_lsb_rgb_visual(input_path, output_path):
    img = Image.open(input_path).convert("RGB")
    img_array = np.array(img)

    red_lsb   = (img_array[:, :, 0] & 1) * 255
    green_lsb = (img_array[:, :, 1] & 1) * 255
    blue_lsb  = (img_array[:, :, 2] & 1) * 255

    lsb_image = np.stack([red_lsb, green_lsb, blue_lsb], axis=2).astype(np.uint8)
    result = Image.fromarray(lsb_image)
    result.save(output_path)
    print(f"✅ Saved LSB visual: {output_path}")


def main():
    for root, _, files in os.walk(input_root):
        rel_path = os.path.relpath(root, input_root)  # path relatif
        output_folder = os.path.join(output_root, rel_path)

        os.makedirs(output_folder, exist_ok=True)

        images = [f for f in files if f.lower().endswith((".png", ".jpg", ".jpeg"))]
        if not images:
            continue

        print(f"\n📂 Folder {rel_path} berisi: {images}")

        for filename in images:
            input_path = os.path.join(root, filename)
            output_path = os.path.join(output_folder, filename)
            extract_lsb_rgb_visual(input_path, output_path)

    print("\n🚀 Selesai!")


if __name__ == "__main__":
    main()
