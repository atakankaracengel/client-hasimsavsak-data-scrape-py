import asyncio
import nest_asyncio
nest_asyncio.apply()

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import csv, os

BASE_URL = "https://rehberpanda.com"
START_URL = BASE_URL + "/araclar/taban-puanlari/lgs/sehir/"
CSV_FILE = "lgs_taban_puanlari_live.csv"

# CSV başlık
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
        csv.writer(f).writerow([
            "Il","Ilce","LiseTuru","OkulAdi",
            "Dil","TabanPuan","Yuzdelik","Kontenjan","Yil"
        ])

async def run():
    print("🚀 Scraper başladı (YEAR-AWARE / STABLE)")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process",
                "--no-zygote"
            ]
        )

        page = await browser.new_page(viewport={"width":1920,"height":1080})

        # ANA SAYFA – İLLER
        print("📍 İller yükleniyor…")
        await page.goto(START_URL, wait_until="domcontentloaded")
        await page.wait_for_selector("a.city-card")

        soup = BeautifulSoup(await page.content(), "html.parser")
        cities = [
            (a.select_one("h3").text.strip(), BASE_URL + a["href"])
            for a in soup.select("a.city-card")
        ]

        print(f"✅ {len(cities)} il bulundu")

        # HER İL
        for ci, (city, city_url) in enumerate(cities, 1):
            print(f"\n🏙️ ({ci}/{len(cities)}) {city}")
            await page.goto(city_url, wait_until="domcontentloaded")
            await page.wait_for_selector(".school-card")

            # 🔑 BU SAYFADAKİ YILLARI OKU
            year_buttons = await page.locator("div.flex.flex-wrap.gap-2.mb-6 button").all_text_contents()
            years = [y.strip() for y in year_buttons]

            print(f"  📅 Bulunan yıllar: {years}")

            for yi, year in enumerate(years):
                if yi > 0:
                    await page.click(f"button:has-text('{year}')")
                    await page.wait_for_selector(".school-card")

                soup = BeautifulSoup(await page.content(), "html.parser")
                cards = soup.select(".school-card")

                print(f"    🏫 {year}: {len(cards)} okul")

                for card in cards:
                    spans = card.select("span")
                    values = card.select(".text-xl.font-bold")

                    with open(CSV_FILE, "a", newline="", encoding="utf-8-sig") as f:
                        csv.writer(f).writerow([
                            city,
                            spans[0].text.strip(),
                            spans[1].text.strip(),
                            card.select_one("h3").text.strip(),
                            spans[2].text.strip(),
                            values[0].text.strip(),
                            values[1].text.replace("%","").strip(),
                            values[2].text.strip(),
                            year
                        ])

        await browser.close()

    print("\n🎉 Tamamlandı – Karabük dahil hiçbir il takılmadı")
    print(f"📁 CSV hazır: {CSV_FILE}")

asyncio.get_event_loop().run_until_complete(run())
