import os
import random
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import tweepy
import urllib.parse

# --- FUNGSI UNTUK SCRAPING ---
def scrape_trends_from_trends24():
    """Mengambil 4 tren teratas dari trends24.in untuk United States."""
    url = "https://trends24.in/united-states/"
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        trend_list = soup.select('ol.trend-card__list li a')
        
        trends = [trend.text.strip().replace('#', '') for trend in trend_list[:4]]
        
        if not trends:
            print("Peringatan: Tidak ada tren yang ditemukan. Mungkin struktur website berubah.")
            return None
            
        print(f"Tren yang ditemukan: {trends}")
        return trends
    except requests.exceptions.RequestException as e:
        print(f"Error saat mengakses trends24.in: {e}")
        return None

# --- FUNGSI UNTUK GENERASI KONTEN (DIPERBAIKI) ---
def generate_post_with_gemini(trend):
    """Membuat konten post dengan Gemini API berdasarkan satu tren."""
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY tidak ditemukan di environment variables!")
        
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
    # --- PERUBAHAN DI SINI ---
    # Prompt diubah agar AI fokus membuat teks saja, tanpa perlu memikirkan link.
    prompt = (
        f"You are a social media expert creating a post for X.com. "
        f"Write a short and engaging post in English about this topic: '{trend}'. "
        f"The post should have a strong Call to Action to encourage clicks on a link that will be added later. "
        f"Do NOT add any links or hashtags in your response. Just provide the main text."
    )
    
    try:
        response = model.generate_content(prompt)
        print("Konten berhasil dibuat oleh Gemini.")
        return response.text.strip()
    except Exception as e:
        print(f"Error saat menghubungi Gemini API: {e}")
        return None

# --- FUNGSI UNTUK MENDAPATKAN LINK ---
def get_random_link(filename="links.txt"):
    """Membaca file dan memilih satu link secara acak."""
    try:
        with open(filename, 'r') as f:
            links = [line.strip() for line in f if line.strip()]
        return random.choice(links) if links else None
    except FileNotFoundError:
        print(f"Error: File '{filename}' tidak ditemukan.")
        return None

# --- FUNGSI UNTUK POSTING KE X.COM ---
def post_to_x(text_to_post, image_url=None):
    """Memposting teks dan gambar (opsional) ke X.com."""
    try:
        media_ids = []
        if image_url:
            auth = tweepy.OAuth1UserHandler(
                os.getenv('X_API_KEY'), os.getenv('X_API_SECRET'),
                os.getenv('X_ACCESS_TOKEN'), os.getenv('X_ACCESS_TOKEN_SECRET')
            )
            api = tweepy.API(auth)
            
            filename = 'temp_image.jpg'
            response = requests.get(image_url, stream=True)
            if response.status_code == 200:
                with open(filename, 'wb') as image_file:
                    for chunk in response.iter_content(1024):
                        image_file.write(chunk)
                
                media = api.media_upload(filename=filename)
                media_ids.append(media.media_id_string)
                print("Gambar berhasil di-upload.")
            else:
                print(f"Gagal mengunduh gambar. Status code: {response.status_code}")

        client = tweepy.Client(
            bearer_token=os.getenv('X_BEARER_TOKEN'),
            consumer_key=os.getenv('X_API_KEY'),
            consumer_secret=os.getenv('X_API_SECRET'),
            access_token=os.getenv('X_ACCESS_TOKEN'),
            access_token_secret=os.getenv('X_ACCESS_TOKEN_SECRET')
        )
        
        if media_ids:
            response = client.create_tweet(text=text_to_post, media_ids=media_ids)
        else:
            response = client.create_tweet(text=text_to_post)
            
        print(f"Berhasil memposting tweet ID: {response.data['id']}")
        
    except Exception as e:
        print(f"Error saat memposting ke X.com: {e}")

# --- FUNGSI UTAMA (DIPERBAIKI) ---
if __name__ == "__main__":
    print("Memulai proses auto-posting...")
    
    top_trends = scrape_trends_from_trends24()
    
    if top_trends:
        selected_trend = random.choice(top_trends)
        print(f"Tren yang dipilih untuk konten: {selected_trend}")
        
        random_link = get_random_link()
        
        if random_link:
            # Panggil Gemini untuk membuat teks saja, tanpa menyertakan link
            gemini_text = generate_post_with_gemini(selected_trend)
            
            if gemini_text:
                print(f"Teks dari Gemini: {gemini_text}")

                hashtags_string = f"#{selected_trend.replace(' ', '')}"
                print(f"Hashtag yang dibuat: {hashtags_string}")
                
                image_url = f"https://tse1.mm.bing.net/th?q={urllib.parse.quote(selected_trend)}"
                print(f"URL Gambar: {image_url}")

                # --- PERUBAHAN DI SINI ---
                # Gabungkan teks dari AI, link acak, dan hashtag secara manual.
                # Ini memastikan semua elemen PASTI ada di post akhir.
                final_post = f"{gemini_text}\n\n{random_link}\n\n{hashtags_string}"
                
                print("--- POSTINGAN FINAL ---")
                print(final_post)
                print("-----------------------")
                
                post_to_x(final_post, image_url)
    
    print("Proses selesai.")