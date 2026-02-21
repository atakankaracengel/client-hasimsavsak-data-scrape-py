import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from datetime import datetime

def create_folders():
    folder_name = "bolum-universite"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_path = os.path.join(folder_name, f"university_data_{timestamp}.xlsx")
    csv_path = os.path.join(folder_name, f"university_data_{timestamp}.csv")
    return excel_path, csv_path

def get_all_programs():
    url = "https://yokatlas.yok.gov.tr/lisans-anasayfa.php"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        programs = {}
        select = soup.find('select', {'id': 'bolum2'})
        if select:
            options = select.find_all('option')
            for option in options:
                program_code = option.get('value')
                program_name = option.text.strip()
                if program_code and program_code.isdigit():
                    programs[program_code] = program_name

        return programs

    except Exception as e:
        print(f"\rHata: Programlar listesi alınırken hata oluştu: {e}", end='', flush=True)
        return {}

def get_program_links(program_code):
    url = f"https://yokatlas.yok.gov.tr/lisans-bolum.php?b={program_code}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        university_codes = []
        panel_headings = soup.find_all('div', class_='panel-heading')

        for panel in panel_headings:
            link = panel.find('a')
            if link and 'href' in link.attrs:
                href = link['href']
                if 'y=' in href:
                    university_code = href.split('y=')[1]
                    university_codes.append(university_code)

        return university_codes

    except Exception as e:
        print(f"\rHata: Program linkleri alınırken hata oluştu: {e}", end='', flush=True)
        return []

def get_university_details(university_code):
    url = f"https://yokatlas.yok.gov.tr/content/lisans-dynamic/1000_1.php?y={university_code}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        details = {}

        program_title = soup.find('th', class_='thb text-center')
        if program_title and program_title.find('big'):
            details['Program Adı'] = program_title.find('big').text.strip()

        tables = soup.find_all('table', class_='table table-bordered')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) == 2:
                    key = cols[0].text.strip().replace('\n', ' ').replace('*', '')
                    value = cols[1].text.strip().replace('\n', ' ')
                    details[key] = value

        return details

    except Exception as e:
        print(f"\rHata: Üniversite detayları alınırken hata oluştu: {e}", end='', flush=True)
        return None

def save_data(data, excel_path, csv_path, is_first=False):
    try:
        df = pd.DataFrame([data])

        if os.path.exists(excel_path) and not is_first:
            with pd.ExcelWriter(excel_path, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                df.to_excel(writer, index=False, header=False, startrow=writer.sheets['Sheet1'].max_row)
        else:
            df.to_excel(excel_path, index=False)

        if os.path.exists(csv_path) and not is_first:
            df.to_csv(csv_path, mode='a', header=False, index=False)
        else:
            df.to_csv(csv_path, index=False)

    except Exception as e:
        print(f"\rHata: Veri kaydedilirken hata oluştu: {e}", end='', flush=True)

def main():
    excel_path, csv_path = create_folders()
    print(f"Excel dosyası: {excel_path}")
    print(f"CSV dosyası: {csv_path}")

    programs = get_all_programs()
    total_programs = len(programs)
    print(f"\nToplam {total_programs} program bulundu.")

    is_first = True
    for prog_idx, (program_code, program_name) in enumerate(programs.items(), 1):
        print(f"\rProgram {prog_idx}/{total_programs}: {program_name}", end='', flush=True)

        university_codes = get_program_links(program_code)
        print(f"\rProgram {prog_idx}/{total_programs}: {program_name} - {len(university_codes)} üniversite bulundu", end='', flush=True)

        for univ_idx, univ_code in enumerate(university_codes, 1):
            print(f"\rProgram {prog_idx}/{total_programs}: {program_name} - Üniversite {univ_idx}/{len(university_codes)} işleniyor...", end='', flush=True)

            details = get_university_details(univ_code)

            if details:
                save_data(details, excel_path, csv_path, is_first)
                is_first = False

            time.sleep(1)

        print()  # Yeni satıra geç
        time.sleep(2)

    print("\nTüm işlemler tamamlandı!")

if __name__ == "__main__":
    main()












######################################################



import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

def create_folders():
    folder_name = "bolum-universite"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_path = os.path.join(folder_name, f"university_data_{timestamp}.xlsx")
    csv_path = os.path.join(folder_name, f"university_data_{timestamp}.csv")
    return excel_path, csv_path

def get_all_programs():
    url = "https://yokatlas.yok.gov.tr/lisans-anasayfa.php"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        programs = {}
        select = soup.find('select', {'id': 'bolum2'})
        if select:
            options = select.find_all('option')
            for option in options:
                program_code = option.get('value')
                program_name = option.text.strip()
                if program_code and program_code.isdigit():
                    programs[program_code] = program_name

        return programs

    except Exception as e:
        print(f"Hata: Programlar listesi alınırken hata oluştu: {e}")
        return {}

def get_program_links(program_code):
    url = f"https://yokatlas.yok.gov.tr/lisans-bolum.php?b={program_code}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        university_codes = []
        panel_headings = soup.find_all('div', class_='panel-heading')

        for panel in panel_headings:
            link = panel.find('a')
            if link and 'href' in link.attrs:
                href = link['href']
                if 'y=' in href:
                    university_code = href.split('y=')[1]
                    university_codes.append(university_code)

        return university_codes

    except Exception as e:
        print(f"Hata: Program linkleri alınırken hata oluştu: {e}")
        return []

def get_university_details(args):
    university_code, program_name = args
    url = f"https://yokatlas.yok.gov.tr/content/lisans-dynamic/1000_1.php?y={university_code}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        details = {}
        details['Program'] = program_name

        program_title = soup.find('th', class_='thb text-center')
        if program_title and program_title.find('big'):
            full_title = program_title.find('big').text.strip()
            university_name = full_title.split('(')[0].strip()
            details['Üniversite'] = university_name
        else:
            details['Üniversite'] = ""

        tables = soup.find_all('table', class_='table table-bordered')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all(['th', 'td'])
                if len(cols) == 2:
                    key = cols[0].text.strip().replace('\n', ' ').replace('*', '').replace('  ', ' ')
                    value = cols[1].text.strip().replace('\n', ' ')
                    details[key] = value

        return details

    except Exception as e:
        print(f"Hata (Üniversite {university_code}): {e}")
        return None

def process_program(program_code, program_name, all_data):
    university_codes = get_program_links(program_code)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(get_university_details, (code, program_name)) for code in university_codes]

        for future in as_completed(futures):
            result = future.result()
            if result:
                all_data.append(result)

def save_batch_data(data_list, excel_path, csv_path):
    if data_list:
        df = pd.DataFrame(data_list)
        df.to_excel(excel_path, index=False)
        df.to_csv(csv_path, index=False)

def main():
    excel_path, csv_path = create_folders()
    print(f"Excel dosyası: {excel_path}")
    print(f"CSV dosyası: {csv_path}")

    programs = get_all_programs()
    total_programs = len(programs)
    print(f"Toplam {total_programs} program bulundu.")

    all_data = []
    batch_size = 5  # Her 5 programda bir kaydet

    with tqdm(total=total_programs, desc="Programlar işleniyor") as pbar:
        for batch_idx in range(0, total_programs, batch_size):
            batch_items = list(programs.items())[batch_idx:batch_idx + batch_size]

            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(process_program, prog_code, prog_name, all_data)
                    for prog_code, prog_name in batch_items
                ]

                for _ in as_completed(futures):
                    pbar.update(1)

            # Her batch sonunda kaydet
            save_batch_data(all_data, excel_path, csv_path)

    print("\nTüm işlemler tamamlandı!")
    print(f"Toplam {len(all_data)} kayıt toplandı.")

if __name__ == "__main__":
    main()

#######################################


import requests
from bs4 import BeautifulSoup
import csv
import time
import pandas as pd
from datetime import datetime
import re
import os
import random

def get_puan_turu(url, max_retries=3, initial_wait=2):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            title_tag = soup.find('title')

            if title_tag:
                title_text = title_tag.text.strip()
                matches = re.findall(r'\((SAY|SÖZ|EA|DİL)\)', title_text)
                if matches:
                    return matches[0]

            wait_time = initial_wait * (attempt + 1)
            print(f"Veri alınamadı. {wait_time} saniye bekleniyor... (Deneme {attempt + 1}/{max_retries})")
            time.sleep(wait_time)

        except requests.exceptions.RequestException as e:
            wait_time = initial_wait * (attempt + 1)
            print(f"Bağlantı hatası: {e}")
            print(f"{wait_time} saniye bekleniyor... (Deneme {attempt + 1}/{max_retries})")
            time.sleep(wait_time)
        except Exception as e:
            print(f"Beklenmeyen hata: {e}")
            wait_time = initial_wait * (attempt + 1)
            print(f"{wait_time} saniye bekleniyor... (Deneme {attempt + 1}/{max_retries})")
            time.sleep(wait_time)

    print(f"Maksimum deneme sayısına ulaşıldı ({max_retries})")
    return None

def get_table_data(url, puan_turu, max_retries=3, initial_wait=2):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', {'id': 'mydata'})

            if not table:
                wait_time = initial_wait * (attempt + 1)
                print(f"Tablo bulunamadı. {wait_time} saniye bekleniyor... (Deneme {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue

            rows = table.find_all('tr')
            all_data = []

            for row in rows[2:]:  # İlk iki satırı atlıyoruz
                cols = row.find_all('td')
                if len(cols) >= 12:
                    data = []

                    # Temel bilgiler (tüm puan türleri için ortak)
                    data.append(cols[1].text.strip())  # Üniversite
                    data.append(cols[2].text.strip())  # Yıl
                    data.append(cols[3].text.strip())  # Tür
                    data.append(cols[4].text.strip())  # Katsayı
                    data.append(cols[5].text.strip())  # OBP
                    data.append(cols[6].text.strip())  # Yerleşen Son Kişi Yerleştiği Puan
                    data.append(cols[7].text.strip())  # Yerleşen
                    data.append(cols[8].text.strip())  # TYT Türkçe
                    data.append(cols[9].text.strip())  # TYT Sosyal
                    data.append(cols[10].text.strip()) # TYT Mat
                    data.append(cols[11].text.strip()) # TYT Fen

                    # Puan türüne göre ek sütunlar
                    if puan_turu == 'SAY':
                        data.append(cols[12].text.strip())  # AYT Mat
                        data.append(cols[13].text.strip())  # AYT Fizik
                        data.append(cols[14].text.strip())  # AYT Kimya
                        data.append(cols[15].text.strip())  # AYT Biyoloji
                    elif puan_turu == 'EA':
                        data.append(cols[12].text.strip())  # AYT Mat
                        data.append(cols[13].text.strip())  # AYT Türk Dili
                        data.append(cols[14].text.strip())  # AYT Tarih1
                        data.append(cols[15].text.strip())  # AYT Coğrafya1
                    elif puan_turu == 'SÖZ':
                        data.append(cols[12].text.strip())  # AYT TDE
                        data.append(cols[13].text.strip())  # AYT Tar1
                        data.append(cols[14].text.strip())  # AYT Coğ1
                        data.append(cols[15].text.strip())  # AYT Tar2
                        data.append(cols[16].text.strip())  # AYT Coğ2
                        data.append(cols[17].text.strip())  # AYT Fel
                        data.append(cols[18].text.strip())  # AYT Din
                    elif puan_turu == 'DİL':
                        data.append(cols[12].text.strip())  # YDT Dil

                    all_data.append(data)

            if all_data:
                return all_data

            wait_time = initial_wait * (attempt + 1)
            print(f"Veri bulunamadı. {wait_time} saniye bekleniyor... (Deneme {attempt + 1}/{max_retries})")
            time.sleep(wait_time)

        except requests.exceptions.RequestException as e:
            wait_time = initial_wait * (attempt + 1)
            print(f"Bağlantı hatası: {e}")
            print(f"{wait_time} saniye bekleniyor... (Deneme {attempt + 1}/{max_retries})")
            time.sleep(wait_time)
        except Exception as e:
            print(f"Beklenmeyen hata: {e}")
            wait_time = initial_wait * (attempt + 1)
            print(f"{wait_time} saniye bekleniyor... (Deneme {attempt + 1}/{max_retries})")
            time.sleep(wait_time)

    print(f"Maksimum deneme sayısına ulaşıldı ({max_retries})")
    return []

def get_headers(puan_turu):
    base_headers = [
        'Program Adı',
        'Üniversite', 'Yılı', 'Türü', 'Katsayı',
        'Yerleşen Son Kişinin OBP', 'Yerleşen Son Kişi Yerleştiği Puan', 'Yerleşen',
        'TYT Türkçe(40)', 'TYT Sosyal(20)',
        'TYT Mat(40)', 'TYT Fen(20)'
    ]
    if puan_turu == 'SAY':
        return base_headers + [
            'AYT Mat(40)',
            'AYT Fizik(14)',
            'AYT Kimya(13)',
            'AYT Biyoloji(13)'
        ]
    elif puan_turu == 'EA':
        return base_headers + [
            'AYT Mat(40)',
            'AYT Türk Dili(24)',
            'AYT Tarih1(10)',
            'AYT Coğrafya1(6)'
        ]
    elif puan_turu == 'SÖZ':
        return base_headers + [
            'AYT TDE(24)',
            'AYT Tar1(10)',
            'AYT Coğ1(6)',
            'AYT Tar2(11)',
            'AYT Coğ2(11)',
            'AYT Fel(12)',
            'AYT Din(6)'
        ]
    elif puan_turu == 'DİL':
        return base_headers + ['YDT Dil(80)']

    return base_headers

def save_to_files(data, program_name, puan_turu):
    headers = get_headers(puan_turu)

    # Lisans klasörünü oluştur
    os.makedirs('lisans', exist_ok=True)

    # Dosya isimleri
    csv_filename = f"lisans/{puan_turu.lower()}.csv"
    excel_filename = f"lisans/{puan_turu.lower()}.xlsx"

    # Program verilerini formatla
    formatted_data = []
    for row in data:
        # Program adını her satırın başına ekle
        row = [program_name] + row
        # Eksik sütunları --- ile doldur
        while len(row) < len(headers):
            row.append('---')
        formatted_data.append(row)

    # CSV'ye kaydet
    try:
        if os.path.exists(csv_filename):
            # Mevcut CSV'yi oku
            existing_data = []
            with open(csv_filename, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Başlığı atla
                existing_data = list(reader)

            # Tüm veriyi yeni baştan yaz
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)  # Başlıkları yaz
                writer.writerows(existing_data)  # Mevcut verileri yaz
                writer.writerows(formatted_data)  # Yeni verileri yaz
        else:
            # Yeni CSV oluştur
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(formatted_data)
        print(f"CSV dosyası güncellendi: {csv_filename}")
    except Exception as e:
        print(f"CSV kaydedilirken hata: {e}")

    # Excel'e kaydet
    try:
        if os.path.exists(excel_filename):
            df_existing = pd.read_excel(excel_filename)
            df_new = pd.DataFrame(formatted_data, columns=headers)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_combined = pd.DataFrame(formatted_data, columns=headers)

        df_combined.to_excel(excel_filename, index=False, engine='openpyxl')
        print(f"Excel dosyası güncellendi: {excel_filename}")
    except Exception as e:
        print(f"Excel kaydedilirken hata: {e}")

def process_programs():
    # Lisans programlarını oku
    try:
        programs_df = pd.read_csv('lisans_programlari.csv')
    except FileNotFoundError:
        print("Hata: lisans_programlari.csv dosyası bulunamadı!")
        print("Lütfen önce programları çekin.")
        return
    except Exception as e:
        print(f"Dosya okuma hatası: {e}")
        return

    # Tüm programlar için işlem yap
    test_programs = programs_df

    # Lisans klasörünü oluştur
    os.makedirs('lisans', exist_ok=True)

    # Dosyaları baştan oluştur
    for puan_turu in ['SAY', 'SÖZ', 'EA', 'DİL']:
        with open(f"lisans/{puan_turu.lower()}.csv", 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(get_headers(puan_turu))

    total_programs = len(test_programs)
    start_time = datetime.now()

    # Puan türlerine göre sayaçlar
    counters = {'SAY': 0, 'SÖZ': 0, 'EA': 0, 'DİL': 0}

    # İşlem durumu için sayaçlar
    success_count = 0
    error_count = 0

    for index, row in test_programs.iterrows():
        program_name = row['Program Adı']
        url = row['URL']

        print(f"\nİşleniyor: {program_name} - {index+1}/{total_programs}")

        try:
            # Puan türünü belirle
            puan_turu = get_puan_turu(url)
            if puan_turu:
                print(f"Puan Türü: {puan_turu}")

                # Tablodan verileri al
                program_data = get_table_data(url, puan_turu)

                if program_data:
                    # Verileri kaydet
                    save_to_files(program_data, program_name, puan_turu)
                    counters[puan_turu] += len(program_data)
                    print(f"Veri kaydedildi: {len(program_data)} satır")
                    success_count += 1
                else:
                    print("Veri bulunamadı!")
                    error_count += 1
            else:
                print("Puan türü belirlenemedi!")
                error_count += 1

        except Exception as e:
            print(f"Hata: {program_name} işlenirken hata oluştu: {e}")
            error_count += 1

        # Rastgele bekleme süresi (1-3 saniye arası)
        wait_time = 1 + random.random() * 2
        time.sleep(wait_time)

    end_time = datetime.now()
    total_time = end_time - start_time

    print("\n" + "="*50)
    print("İŞLEM RAPORU")
    print("="*50)
    print(f"Toplam Program Sayısı: {total_programs}")
    print(f"Başarılı İşlem: {success_count}")
    print(f"Başarısız İşlem: {error_count}")
    print("\nPuan türlerine göre toplam kayıt sayıları:")
    for puan_turu, count in counters.items():
        print(f"{puan_turu}: {count} satır")
    print(f"\nToplam geçen süre: {total_time}")
    print("="*50)

if __name__ == "__main__":
    try:
        print("YÖK Atlas Veri Çekme Programı")
        print("="*30)
        print("Program başlatılıyor...")
        process_programs()
    except KeyboardInterrupt:
        print("\nProgram kullanıcı tarafından durduruldu!")
    except Exception as e:
        print(f"\nBeklenmeyen bir hata oluştu: {e}")
    finally:
        print("\nProgram sonlandırıldı.")


##################################



import requests
from bs4 import BeautifulSoup
import csv
import time
import urllib3

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://yokatlas.yok.gov.tr/netler.php"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

try:
    # SSL doğrulamasını kapatarak isteği yap
    response = requests.get(url, headers=headers, verify=False, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    # Lisans programları select
    lisans_select = soup.find('select', {'id': 'bolum'})
    if not lisans_select:
        raise Exception("Lisans programları bulunamadı!")
    lisans_options = lisans_select.find_all('option')

    # Önlisans programları select
    onlisans_select = soup.find('select', {'id': 'program'})
    if not onlisans_select:
        raise Exception("Önlisans programları bulunamadı!")
    onlisans_options = onlisans_select.find_all('option')

    # Lisans CSV yaz
    with open('lisans_programlari.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Program Adı', 'URL'])

        for option in lisans_options:
            if option.get('value'):
                program_adi = option.text.strip()
                program_kodu = option.get('value')
                detail_url = f"https://yokatlas.yok.gov.tr/netler-tablo.php?b={program_kodu}"
                writer.writerow([program_adi, detail_url])
                print(f"Lisans: {program_adi} kaydedildi.")

    # Önlisans CSV yaz
    with open('onlisans_programlari.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Program Adı', 'URL'])

        for option in onlisans_options:
            if option.get('value'):
                program_adi = option.text.strip()
                program_kodu = option.get('value')
                detail_url = f"https://yokatlas.yok.gov.tr/netler-onlisans-tablo.php?b={program_kodu}"
                writer.writerow([program_adi, detail_url])
                print(f"Önlisans: {program_adi} kaydedildi.")

    print("\nİşlem başarıyla tamamlandı!")
    print(f"Toplam {len(lisans_options)-1} lisans ve {len(onlisans_options)-1} önlisans programı kaydedildi.")

except requests.RequestException as e:
    print(f"Bağlantı hatası: {e}")
except Exception as e:
    print(f"Bir hata oluştu: {e}")


#################################



import requests
from bs4 import BeautifulSoup
import csv
import time
import pandas as pd
from datetime import datetime
import re
import os
import random
import urllib3

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_puan_turu(url, max_retries=3, initial_wait=2):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, verify=False, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            title_tag = soup.find('title')

            if title_tag:
                title_text = title_tag.text.strip()
                matches = re.findall(r'\((SAY|SÖZ|EA|DİL)\)', title_text)
                if matches:
                    return matches[0]

            wait_time = initial_wait * (attempt + 1)
            print(f"Veri alınamadı. {wait_time} saniye bekleniyor... (Deneme {attempt + 1}/{max_retries})")
            time.sleep(wait_time)

        except requests.exceptions.RequestException as e:
            wait_time = initial_wait * (attempt + 1)
            print(f"Bağlantı hatası: {e}")
            print(f"{wait_time} saniye bekleniyor... (Deneme {attempt + 1}/{max_retries})")
            time.sleep(wait_time)
        except Exception as e:
            print(f"Beklenmeyen hata: {e}")
            wait_time = initial_wait * (attempt + 1)
            print(f"{wait_time} saniye bekleniyor... (Deneme {attempt + 1}/{max_retries})")
            time.sleep(wait_time)

    print(f"Maksimum deneme sayısına ulaşıldı ({max_retries})")
    return None

def get_table_data(url, puan_turu, max_retries=3, initial_wait=2):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, verify=False, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', {'id': 'mydata'})

            if not table:
                wait_time = initial_wait * (attempt + 1)
                print(f"Tablo bulunamadı. {wait_time} saniye bekleniyor... (Deneme {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue

            rows = table.find_all('tr')
            all_data = []

            for row in rows[2:]:
                cols = row.find_all('td')
                if len(cols) >= 10:
                    data = []

                    data.append(cols[1].text.strip())
                    data.append(cols[2].text.strip())
                    data.append(cols[3].text.strip())
                    data.append(cols[4].text.strip())
                    data.append(cols[5].text.strip())
                    data.append(cols[7].text.strip())
                    data.append(cols[8].text.strip())
                    data.append(cols[9].text.strip())
                    data.append(cols[10].text.strip())
                    data.append(cols[11].text.strip())

                    if puan_turu == 'SAY':
                        data.append(cols[12].text.strip())
                        data.append(cols[13].text.strip())
                        data.append(cols[14].text.strip())
                        data.append(cols[15].text.strip())
                    elif puan_turu == 'EA':
                        data.append(cols[12].text.strip())
                        data.append(cols[13].text.strip())
                        data.append(cols[14].text.strip())
                        data.append(cols[15].text.strip())
                    elif puan_turu == 'SÖZ':
                        data.append(cols[12].text.strip())
                        data.append(cols[13].text.strip())
                        data.append(cols[14].text.strip())
                        data.append(cols[15].text.strip())
                        data.append(cols[16].text.strip())
                        data.append(cols[17].text.strip())
                        data.append(cols[18].text.strip())
                    elif puan_turu == 'DİL':
                        data.append(cols[12].text.strip())

                    all_data.append(data)

            if all_data:
                return all_data

            wait_time = initial_wait * (attempt + 1)
            print(f"Veri bulunamadı. {wait_time} saniye bekleniyor... (Deneme {attempt + 1}/{max_retries})")
            time.sleep(wait_time)

        except Exception as e:
            wait_time = initial_wait * (attempt + 1)
            print(f"Hata: {e} - {wait_time} saniye bekleniyor")
            time.sleep(wait_time)

    return []

def get_headers(puan_turu):
    base_headers = [
        'Program Adı',
        'Üniversite', 'Yılı', 'Türü', 'Katsayı',
        'Yerleşen Son Kişinin OBP', 'Yerleşen',
        'TYT Türkçe(40)', 'TYT Sosyal(20)',
        'TYT Mat(40)', 'TYT Fen(20)'
    ]

    if puan_turu == 'SAY':
        return base_headers + ['AYT Mat(40)', 'AYT Fizik(14)', 'AYT Kimya(13)', 'AYT Biyoloji(13)']
    elif puan_turu == 'EA':
        return base_headers + ['AYT Mat(40)', 'AYT Türk Dili(24)', 'AYT Tarih1(10)', 'AYT Coğrafya1(6)']
    elif puan_turu == 'SÖZ':
        return base_headers + [
            'AYT TDE(24)', 'AYT Tar1(10)', 'AYT Coğ1(6)',
            'AYT Tar2(11)', 'AYT Coğ2(11)', 'AYT Fel(12)', 'AYT Din(6)'
        ]
    elif puan_turu == 'DİL':
        return base_headers + ['YDT Dil(80)']

    return base_headers

def save_to_files(data, program_name, puan_turu):
    headers = get_headers(puan_turu)

    os.makedirs('lisans', exist_ok=True)

    csv_filename = f"lisans/{puan_turu.lower()}.csv"
    excel_filename = f"lisans/{puan_turu.lower()}.xlsx"

    formatted_data = []
    for row in data:
        row = [program_name] + row
        while len(row) < len(headers):
            row.append('---')
        formatted_data.append(row)

    try:
        if os.path.exists(csv_filename):
            existing_data = []
            with open(csv_filename, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)
                existing_data = list(reader)

            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(existing_data)
                writer.writerows(formatted_data)
        else:
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(formatted_data)

        print(f"CSV güncellendi: {csv_filename}")
    except Exception as e:
        print(f"CSV hata: {e}")

    try:
        if os.path.exists(excel_filename):
            df_existing = pd.read_excel(excel_filename)
            df_new = pd.DataFrame(formatted_data, columns=headers)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_combined = pd.DataFrame(formatted_data, columns=headers)

        df_combined.to_excel(excel_filename, index=False, engine='openpyxl')
        print(f"Excel güncellendi: {excel_filename}")
    except Exception as e:
        print(f"Excel hata: {e}")

def process_programs():
    try:
        programs_df = pd.read_csv('lisans_programlari.csv')
    except:
        print("Hata: lisans_programlari.csv yok!")
        return

    test_programs = programs_df

    os.makedirs('lisans', exist_ok=True)

    for puan_turu in ['SAY', 'SÖZ', 'EA', 'DİL']:
        with open(f"lisans/{puan_turu.lower()}.csv", 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(get_headers(puan_turu))

    total_programs = len(test_programs)
    counters = {'SAY': 0, 'SÖZ': 0, 'EA': 0, 'DİL': 0}

    for index, row in test_programs.iterrows():
        program_name = row['Program Adı']
        url = row['URL']

        print(f"\nİşleniyor: {program_name} - {index+1}/{total_programs}")

        try:
            puan_turu = get_puan_turu(url)
            if not puan_turu:
                print("Puan türü bulunamadı!")
                continue

            print(f"Puan Türü: {puan_turu}")

            program_data = get_table_data(url, puan_turu)
            if not program_data:
                print("Tablo verisi boş!")
                continue

            save_to_files(program_data, program_name, puan_turu)
            counters[puan_turu] += len(program_data)

        except Exception as e:
            print(f"Hata: {e}")

        time.sleep(1 + random.random() * 2)

    print("\nBitti!")
    print(counters)

if __name__ == "__main__":
    process_programs()


#######################


import requests
from bs4 import BeautifulSoup
import csv
import time
import os
import pandas as pd
import urllib3
import random

# SSL uyarılarını kapat (YÖK Atlas sertifika hataları için)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Çıktı başlıkları
ONLISANS_HEADERS = [
    "Program Adı",
    "Üniversite",
    "Yılı",
    "Türü",
    "Katsayı",
    "OBP",
    "Yerleşen",
    "TYT Türkçe(40)",
    "TYT Sosyal(20)",
    "TYT Mat(40)",
    "TYT Fen(20)"
]

def get_col_index(headers, key):
    """
    headers: thead içindeki th yazıları listesi
    key: aranan metnin bir kısmı ("TYT Türkçe", "Yerleşen Son Kişinin" vs.)
    """
    for i, h in enumerate(headers):
        if key in h:
            return i
    return None

def get_onlisans_table(url, max_retries=3):
    headers_req = {
        "User-Agent": "Mozilla/5.0"
    }

    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=headers_req, verify=False, timeout=10)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")
            table = soup.find("table", {"id": "mydata"})

            if not table:
                print("Tablo bulunamadı, yeniden denenecek...")
                time.sleep(2)
                continue

            # --- THEAD'den kolon indexlerini çıkar ---
            thead = table.find("thead")
            if not thead:
                print("Thead bulunamadı, atlanıyor.")
                return []

            header_rows = thead.find_all("tr")
            if not header_rows:
                print("Header satırı bulunamadı.")
                return []

            first_header = header_rows[0]
            th_list = first_header.find_all("th")
            header_texts = [th.get_text(strip=True) for th in th_list]

            idx_uni      = get_col_index(header_texts, "Üniversite")
            idx_yil      = get_col_index(header_texts, "Yılı")
            idx_tur      = get_col_index(header_texts, "Türü")
            idx_katsayi  = get_col_index(header_texts, "Katsayı")
            idx_obp      = get_col_index(header_texts, "Yerleşen Son Kişinin")
            idx_yerlesen = get_col_index(header_texts, "Yerleşen")
            idx_tyt_tr   = get_col_index(header_texts, "TYT Türkçe")
            idx_tyt_sos  = get_col_index(header_texts, "TYT Sosyal")
            idx_tyt_mat  = get_col_index(header_texts, "TYT Mat")
            idx_tyt_fen  = get_col_index(header_texts, "TYT Fen")

            needed = [idx_uni, idx_yil, idx_tur, idx_katsayi, idx_obp,
                      idx_yerlesen, idx_tyt_tr, idx_tyt_sos, idx_tyt_mat, idx_tyt_fen]

            if any(i is None for i in needed):
                print("Bazı kolon indexleri bulunamadı, header yapısı değişmiş olabilir.")
                print("Header textleri:", header_texts)
                return []

            # --- Tbody'den verileri oku ---
            tbody = table.find("tbody")
            if tbody:
                rows = tbody.find_all("tr")
            else:
                # Bazı tablolarda tbody olmayabiliyor
                rows = table.find_all("tr")[2:]

            all_data = []

            for row in rows:
                cols = row.find_all("td")
                if not cols:
                    continue

                # Her ihtimale karşı uzunluk kontrolü
                max_idx = max(needed)
                if len(cols) <= max_idx:
                    continue

                uni       = cols[idx_uni].get_text(strip=True)
                yil       = cols[idx_yil].get_text(strip=True)
                tur       = cols[idx_tur].get_text(strip=True)
                katsayi   = cols[idx_katsayi].get_text(strip=True)
                obp       = cols[idx_obp].get_text(strip=True)
                yerlesen  = cols[idx_yerlesen].get_text(strip=True)
                tyt_tr    = cols[idx_tyt_tr].get_text(strip=True)
                tyt_sos   = cols[idx_tyt_sos].get_text(strip=True)
                tyt_mat   = cols[idx_tyt_mat].get_text(strip=True)
                tyt_fen   = cols[idx_tyt_fen].get_text(strip=True)

                data_row = [
                    uni,
                    yil,
                    tur,
                    katsayi,
                    obp,
                    yerlesen,
                    tyt_tr,
                    tyt_sos,
                    tyt_mat,
                    tyt_fen
                ]

                all_data.append(data_row)

            return all_data

        except Exception as e:
            print(f"Hata: {e} (deneme {attempt+1}/{max_retries})")
            time.sleep(2)

    return []

def save_onlisans(program_name, table_data):
    os.makedirs("onlisans", exist_ok=True)

    csv_filename   = "onlisans/onlisans.csv"
    excel_filename = "onlisans/onlisans.xlsx"

    formatted = []
    for row in table_data:
        # Program Adı en başa
        formatted.append([program_name] + row)

    # CSV
    if not os.path.exists(csv_filename):
        with open(csv_filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(ONLISANS_HEADERS)

    with open(csv_filename, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerows(formatted)

    # Excel
    if os.path.exists(excel_filename):
        df_old = pd.read_excel(excel_filename)
        df_new = pd.DataFrame(formatted, columns=ONLISANS_HEADERS)
        df_all = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_all = pd.DataFrame(formatted, columns=ONLISANS_HEADERS)

    df_all.to_excel(excel_filename, index=False, engine="openpyxl")

def process_onlisans():
    # onlisans_programlari.csv: Program Adı, URL
    try:
        df = pd.read_csv("onlisans_programlari.csv")
    except FileNotFoundError:
        print("onlisans_programlari.csv bulunamadı!")
        return

    total = len(df)
    print(f"Toplam Önlisans Programı: {total}")

    for i, row in df.iterrows():
        program_name = row["Program Adı"]
        url          = row["URL"]

        print(f"\n{i+1}/{total} → {program_name}")
        table_data = get_onlisans_table(url)

        if table_data:
            save_onlisans(program_name, table_data)
            print(f"✓ {len(table_data)} satır kaydedildi.")
        else:
            print("✗ Veri bulunamadı veya header uyumsuz.")

        # YÖK Atlas'a yüklenmemek için küçük delay
        time.sleep(1 + random.random() * 2)

    print("\nİşlem tamamlandı.")

if __name__ == "__main__":
    process_onlisans()
