import os
import argparse
import pandas as pd
import qrcode
from urllib.parse import quote

def generate_qr_code(url, path):
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(path)

def main(csv_path, base_url, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    df = pd.read_csv(csv_path)

    for _, row in df.iterrows():
        uid     = row["UID"]
        map_nm  = row["MAP"]
        point   = row["POINT"]
        # percent‐encode UID exactly like in your app
        url = f"{base_url.rstrip('/')}?uid={quote(uid)}"
        filename = os.path.join(out_dir, f"qr_uid_{uid}.png")
        generate_qr_code(url, filename)
        print(f"→ {map_nm}-Point {point}: {filename}")

if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="Generate one QR code per UID for your Streamlit app"
    )
    p.add_argument("-c", "--csv",      default="data/points.csv")
    p.add_argument("-u", "--base-url", required=True)
    p.add_argument("-o", "--out",      default="qrcodes")
    args = p.parse_args()
    main(args.csv, args.base_url, args.out)