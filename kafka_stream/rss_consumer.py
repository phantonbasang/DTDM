from kafka import KafkaConsumer
import json
from pymongo import MongoClient
import os
import django
from datetime import datetime

# 👇 Cập nhật đường dẫn project phù hợp
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "News_Atlats_AI.settings")

# 👇 Nếu file không nằm ở cùng cấp manage.py, cần thêm đường dẫn gốc
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

django.setup()

try:
    # Kết nối MongoDB Atlas
    client = MongoClient("mongodb+srv://phantonbasang:22677351@cluster0.vjd7ljz.mongodb.net/Cluster0?retryWrites=true&w=majority&appName=Cluster0")
    # Kiểm tra kết nối
    client.admin.command('ping')
    print("Successfully connected to MongoDB Atlas!")
    
    db = client['news_db']
    collection = db['vnexpress_articles']

    # Khởi tạo Kafka Consumer
    consumer = KafkaConsumer(
        'vnexpress_news',
        bootstrap_servers='localhost:9092',
        auto_offset_reset='earliest',  # Đọc từ đầu topic
        enable_auto_commit=True,
        group_id='news_group',
        value_deserializer=lambda v: json.loads(v.decode('utf-8'))
    )
    print("Successfully connected to Kafka!")
    print(f"Listening on topic: vnexpress_news")

    print("Starting to consume messages...")
    for message in consumer:
        try:
            print(f"Received message: {message.topic}, partition: {message.partition}, offset: {message.offset}")
            article = message.value
            print(f"Article data: {article.keys()}")
            
            # Thêm timestamp
            article['created_at'] = datetime.now()
            
            # Kiểm tra và lưu bài báo
            if collection.count_documents({'link': article['link']}) == 0:
                result = collection.insert_one(article)
                print(f"[Consumer] Inserted: {article['title']} (ID: {result.inserted_id})")
            else:
                print(f"[Consumer] Skipped duplicate: {article['title']}")
                
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            continue

except KeyboardInterrupt:
    print("\nStopping consumer...")
    if 'consumer' in locals():
        consumer.close()
    if 'client' in locals():
        client.close()
    print("Consumer stopped")
except Exception as e:
    print(f"Error: {str(e)}")
    if 'client' in locals():
        client.close()
