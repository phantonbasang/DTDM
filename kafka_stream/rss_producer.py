import time
import feedparser
from kafka import KafkaProducer
import json
from bs4 import BeautifulSoup
import requests

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

RSS_URLS = [
    "https://vnexpress.net/rss/tin-moi-nhat.rss",
    "https://vnexpress.net/rss/the-gioi.rss",
    "https://vnexpress.net/rss/kinh-doanh.rss",
    "https://vnexpress.net/rss/thoi-su.rss",
    "https://vnexpress.net/rss/giao-duc.rss",
    "https://vnexpress.net/rss/van-hoa.rss",
    "https://vnexpress.net/rss/khoa-hoc.rss",
    "https://vnexpress.net/rss/giai-tri.rss",
    "https://vnexpress.net/rss/the-thao.rss",
    "https://vnexpress.net/rss/phap-luat.rss",
    # Thêm các link khác nếu muốn
]
TOPIC_NAME = "vnexpress_news"

def get_article_content(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        article = soup.find('article', class_='fck_detail')
        if article:
            # Loại bỏ các thẻ script và style
            for script in article.find_all(['script', 'style']):
                script.decompose()
            # Lấy text từ các thẻ p
            content = ' '.join([p.get_text().strip() for p in article.find_all('p')])
            return content
        return None
    except Exception as e:
        print(f"Error getting article content: {str(e)}")
        return None

def extract_image_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    img_tag = soup.find('img')
    if img_tag and img_tag.get('src'):
        return img_tag['src']
    return None

def fetch_rss_and_send():
    sent_links = set()  # tránh gửi trùng nếu chạy lại nhanh

    while True:
        print("[Fetcher] Fetching RSS...")
        for rss_url in RSS_URLS:
            print(f"[Fetcher] Fetching from: {rss_url}")
            feed = feedparser.parse(rss_url)
            # Lấy category từ đường dẫn rss
            category = rss_url.split('/')[-1].replace('.rss', '')
            for entry in feed.entries:
                if entry.link in sent_links:
                    continue

                # Lấy nội dung chi tiết của bài báo
                content = get_article_content(entry.link)
                # Lấy ảnh từ summary
                image_url = extract_image_from_html(entry.summary)
                # Nếu không có ảnh trong summary, lấy từ nội dung chi tiết
                if not image_url and content:
                    image_url = extract_image_from_html(content)
                # Nếu vẫn không có, dùng ảnh mặc định
                if not image_url:
                    image_url = "https://via.placeholder.com/300x200?text=No+Image"

                # Lấy description sạch từ summary
                soup = BeautifulSoup(entry.summary, 'html.parser')
                description = soup.get_text()

                data = {
                    'title': entry.title,
                    'link': entry.link,
                    'description': description[:100] + '...' if len(description) > 100 else description,
                    'pub_date': entry.published,
                    'category': category,
                    'image_url': image_url
                }
                producer.send(TOPIC_NAME, value=data)
                print(f"[Producer] Sent: {entry.title} | Category: {category} | Image: {image_url}")
                sent_links.add(entry.link)
        print("[Fetcher] Sleeping for 5 minutes...")
        time.sleep(300)

if __name__ == "__main__":
    fetch_rss_and_send()
