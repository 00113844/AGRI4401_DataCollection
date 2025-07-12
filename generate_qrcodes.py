import os
import argparse
import pandas as pd
import qrcode

def generate_qr(url, path):
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(path)

def main(csv_path, base_url, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    df = pd.read_csv(csv_path)
    
    # Generate one QR code per UID (map-point record)
    for _, row in df.iterrows():
        uid = row['UID']
        map_name = row.get('MAP', '')
        point = row.get('POINT', '')
        # URL directs to specific UID
        url = f"{base_url.rstrip('/')}/?uid={uid}"
        # Filename per UID
        filename = os.path.join(out_dir, f"qr_uid_{uid}.png")
        generate_qr(url, filename)
        print(f"Saved QR for UID {uid} (Map {map_name}, Point {point}) → {filename}")

if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="Generate one QR code per UID for your Streamlit app"
    )
    p.add_argument(
        "--csv", "-c",
        default="data/points.csv",
        help="path to your points.csv"
    )
    p.add_argument(
        "--base-url", "-u",
        required=True,
        help="deployment URL (e.g. https://your-app.streamlit.app)"
    )
    p.add_argument(
        "--out", "-o",
        default="qrcodes",
        help="output directory for PNGs"
    )
    args = p.parse_args()
    main(args.csv, args.base_url, args.out)