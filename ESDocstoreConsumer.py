import pika
import json
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor
from elasticsearch import Elasticsearch
from ProcessStreamChunk import process_stream_chunk  # Import processing function

# Config
BATCH_SIZE = 5
INDEX_NAME = "pdf_chunks"
es = Elasticsearch("http://localhost:9200")

# Async Queue
processing_queue = asyncio.Queue()

def create_index():
    """Create index if not exists"""
    mapping = {
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "pdf_name": {"type": "keyword"},
                "page_number": {"type": "integer"},
                "content": {"type": "text", "analyzer": "standard"}
            }
        }
    }
    if not es.indices.exists(index=INDEX_NAME):
        es.indices.create(index=INDEX_NAME, body=mapping)

def insert(doc):
    """Insert document into Elasticsearch"""
    response = es.index(index=INDEX_NAME, id=doc['id'], document=doc)
    print(f"Stored document {doc['id']}: {response['result']}")

def process_message(body):
    """Process message from RabbitMQ"""
    try:
        data = json.loads(body)
        
        chunk_id = str(uuid.uuid4())  # Generate UUID
        doc = {
            'id': chunk_id,
            'pdf_name': data['pdf_name'],
            'page_number': data['page_number'],
            'content': data['content']
        }

        insert(doc)  # Store in Elasticsearch

        # Send to async queue for further processing
        asyncio.run_coroutine_threadsafe(process_async(doc), loop)

    except Exception as e:
        print(f"Error processing message: {e}")

async def process_async(doc):
    """Send document to processor asynchronously"""
    await processing_queue.put(doc)

async def background_task():
    """Background worker to process docs from the queue"""
    while True:
        doc = await processing_queue.get()
        await process_stream_chunk(doc)  # Call function from processor module
        processing_queue.task_done()

def callback(ch, method, properties, body):
    """Callback function for RabbitMQ"""
    executor.submit(process_message, body)
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    global executor, loop
    executor = ThreadPoolExecutor(max_workers=BATCH_SIZE)

    # Create asyncio event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Start background processing task
    loop.create_task(background_task())

    create_index()  # Ensure index exists

    # RabbitMQ Setup
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='pdf_chunks')

    # Consume messages
    channel.basic_consume(queue='pdf_chunks', on_message_callback=callback)
    print("Waiting for messages...")
    channel.start_consuming()

if __name__ == "__main__":
    main()
