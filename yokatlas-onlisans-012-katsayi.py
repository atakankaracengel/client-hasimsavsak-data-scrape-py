!pip install requests beautifulsoup4 lxml tqdm

import requests
from bs4 import BeautifulSoup
import csv
import os
import time
from tqdm import tqdm

headers = {"User-Agent": "Mozilla/5.0"}

years = {
    "2025": "",       # yıl klasörü yok
    "2024": "2024/",
    "2023": "2023/",
    "2022": "2022/"
}

base_main = "https://yokatlas.yok.gov.tr/onlisans-anasayfa.php"
base_program = "https://yokatlas.yok.gov.tr/onlisans-program.php?b="

def clean(text):
    return text.replace("\n","").replace("\xa0"," ").strip()

# ----------------------------------------------------
# Program ID'leri al
# ----------------------------------------------------
resp = requests.get(base_main, headers=headers)
soup = BeautifulSoup(resp.text, "lxml")

program_ids = []
for option in soup.find_all("option"):
    val = option.get("value")
    if val and val.isdigit():
        program_ids.append(val)

program_ids = list(set(program_ids))
print("Toplam Program:", len(program_ids))


# ----------------------------------------------------
# YIL DÖNGÜSÜ
# ----------------------------------------------------
for year, prefix in years.items():

    print("\n==========================")
    print("İşlenen Yıl:", year)
    print("==========================")

    csv_file = f"yokatlas_onlisans_{year}.csv"
    processed_file = f"processed_{year}.txt"

    processed_y = set()
    if os.path.exists(processed_file):
        with open(processed_file, "r") as f:
            for line in f:
                processed_y.add(line.strip())

    header_written = os.path.exists(csv_file)

    base_dynamic = f"https://yokatlas.yok.gov.tr/{prefix}content/onlisans-dynamic/3000_1.php?y="

    for program_id in tqdm(program_ids):

        try:
            program_url = base_program + program_id
            r = requests.get(program_url, headers=headers, timeout=10)
            s = BeautifulSoup(r.text, "lxml")

            y_codes = []
            for a in s.find_all("a", href=True):
                if "onlisans.php?y=" in a["href"]:
                    y = a["href"].split("y=")[1]
                    y_codes.append(y)

            y_codes = list(set(y_codes))

            for y in y_codes:

                if y in processed_y:
                    continue

                try:
                    dynamic_url = base_dynamic + y
                    d = requests.get(dynamic_url, headers=headers, timeout=10)

                    if d.status_code != 200:
                        continue

                    dsoup = BeautifulSoup(d.text, "lxml")

                    row_data = {
                        "Yıl": year,
                        "Program_ID": program_id,
                        "Y_Code": y
                    }

                    # ✅ Program Adı
                    big_tag = dsoup.find("big")
                    if big_tag:
                        row_data["Program Adı"] = clean(big_tag.text)

                    # ✅ Tüm tablolar
                    for row in dsoup.find_all("tr"):
                        cols = row.find_all("td")
                        if len(cols) == 2:
                            key = clean(cols[0].get_text())
                            value = clean(cols[1].get_text())
                            row_data[key] = value

                    # HEADER
                    if not header_written:
                        with open(csv_file, "w", newline="", encoding="utf-8-sig") as f:
                            writer = csv.DictWriter(f, fieldnames=row_data.keys())
                            writer.writeheader()
                        header_written = True

                    # APPEND
                    with open(csv_file, "a", newline="", encoding="utf-8-sig") as f:
                        writer = csv.DictWriter(f, fieldnames=row_data.keys())
                        writer.writerow(row_data)

                    with open(processed_file, "a") as f:
                        f.write(y + "\n")

                    processed_y.add(y)

                    print(f"{year} Kaydedildi:", y)

                    time.sleep(0.3)

                except:
                    continue

        except:
            continue

print("\nTÜM YILLAR TAMAMLANDI 🚀")
