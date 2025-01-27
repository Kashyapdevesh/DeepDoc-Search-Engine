import pika
import json
import uuid

def send_dummy_data():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    
    channel.queue_declare(queue='pdf_chunks')
    
    sample_data = [
        {"pdf_name": "COVID Research 2023", "page_number": 1, "content": "Study on COVID-19 impact"},
        {"pdf_name": "Cancer Research 2024", "page_number": 2, "content": "New treatments for lung cancer"},
        {"pdf_name": "AI in Healthcare", "page_number": 3, "content": "Role of artificial intelligence"},
        {"pdf_name": "COVID Vaccine Reports", "page_number": 4, "content": "Efficacy of vaccines in 2023"},
        {"pdf_name": "Machine Learning Basics", "page_number": 5, "content": "Introduction to ML models"}
    ]
    
    for data in sample_data:
        data["id"] = str(uuid.uuid4())
        message = json.dumps(data)
        channel.basic_publish(exchange='', routing_key='pdf_chunks', body=message)
        print(f"Sent: {message}")
    
    connection.close()

if __name__ == "__main__":
    send_dummy_data()
