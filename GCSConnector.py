import io
import json
import base64
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor,as_completed, ProcessPoolExecutor
from google.cloud.storage import Client
from google.oauth2 import service_account
from unstructured.partition.pdf import partition_pdf

import pika

#Supress Warnings
import warnings
warnings.filterwarnings("ignore")

#Handling missing dependencies and conflicts
import os
os.environ['PATH'] += os.pathsep + 'C:/Users/Projects/Generative_AI/poppler-24.08.0/Library/bin' #for poppler
os.environ['PATH'] += os.pathsep + 'C:/Users/Projects/Generative_AI' #for tesseract (extracted lib zip in Generative_AI directory)

import nltk
nltk.download(['punkt_tab','averaged_perceptron_tagger_eng'])

#Establish Global batch size for processing pdfs
BATCH_SIZE=5

# Load credentials
creds_json=json.load(open("./Credentials/service-account-key.json"))

# Initialize GCS client with credentials
creds = service_account.Credentials.from_service_account_info(creds_json)
storage_client = Client(credentials=creds)

# List files in a folder
def list_files_in_folder(bucket_name, folder_path):
    """
    List all PDF files in a specific folder within a GCS bucket.
    """
    bucket = storage_client.bucket(bucket_name)
    if not folder_path.endswith("/"):
        folder_path += "/"
    blobs = bucket.list_blobs(prefix=folder_path)
    pdf_files = [blob for blob in blobs if blob.name.endswith(".pdf")]
    return pdf_files

# Download files asynchronously in batches
async def download_files_async(bucket_name, blob_names):
    """
    Download multiple files from GCS asynchronously.
    """
    async with aiohttp.ClientSession() as session:
        tasks = []
        for blob_name in blob_names:
            blob = storage_client.bucket(bucket_name).blob(blob_name)
            url = blob.generate_signed_url(version="v4", expiration=3600)  # Generate signed URL
            tasks.append(download_file_async(session, url, blob_name))
            print(f"Started Downloading {blob_name}")
        file_streams = await asyncio.gather(*tasks)
        return file_streams

async def download_file_async(session, url, blob_name):
    """
    Download a single file asynchronously.
    """
    async with session.get(url) as response:
        file_stream = io.BytesIO(await response.read())
        file_stream.seek(0)
        return blob_name, file_stream

# Process a batch of files, using ProcessPoolExecutor for larger files and ThreadPoolExecutor for smaller ones
def process_batch(file_streams):
    """
    Process a batch of files using ThreadPoolExecutor for smaller files and ProcessPoolExecutor for larger files.
    """
    # Separate the files into large and small on the basis of 100MB benchmark
    large_files=[(blob_name,file_stream) for blob_name,file_stream in file_streams if file_stream.getbuffer().nbytes >= 100 * 1024 * 1024]
    small_files = [(blob_name, file_stream) for blob_name, file_stream in file_streams if file_stream.getbuffer().nbytes < 100 * 1024 * 1024]
    print()
    print(large_files)
    print(small_files)
    print()
    # Process large files with ProcessPoolExecutor
    if large_files:
        with ProcessPoolExecutor() as process_executor:
            futures = {
                process_executor.submit(process_file, file_stream, blob_name): blob_name
                for blob_name, file_stream in large_files
            }
            for future in as_completed(futures):
                blob_name = futures[future]
                try:
                    future.result()  # Ensure exceptions are raised
                except Exception as e:
                    print(f"Error processing {blob_name}: {e}")

    # Process small files with ThreadPoolExecutor
    if small_files:
        with ThreadPoolExecutor() as thread_executor:
            futures = {
                thread_executor.submit(process_file, file_stream, blob_name): blob_name
                for blob_name, file_stream in small_files
            }
            for future in as_completed(futures):
                blob_name = futures[future]
                try:
                    future.result()  # Ensure exceptions are raised
                except Exception as e:
                    print(f"Error processing {blob_name}: {e}")

# Process a single file
def process_file(file_stream, blob_name):
    """
    Process a single PDF file and stream/upload the results.
    """
    file_stream.seek(0)
    print(f"Started Chunking {blob_name}")
    Unstructured_Chunks_List = partition_pdf(
        file=file_stream,
        # filename=blob_name,
        infer_table_structure=True,            # extract tables
        strategy="hi_res",                     # mandatory to infer tables

        extract_image_block_types=["Image"],   # Add 'Table' to list to extract image of tables
        # image_output_dir_path=output_path,   # if None, images and tables will saved in base64

        extract_image_block_to_payload=True,   # if true, will extract base64 for API usage

        chunking_strategy="by_title",          # or 'basic'
        max_characters=8000,                  # defaults to 500
        combine_text_under_n_chars=1500,       # defaults to 0
        new_after_n_chars=4000,

        # extract_images_in_pdf=True,          # deprecated
    )
    print(f"Processed {blob_name}: {len(Unstructured_Chunks_List)} elements")
    
    stream_RabbitMQ_Chunks(Unstructured_Chunks_List,blob_name)

def stream_RabbitMQ_Chunks(Unstructured_Chunks_List, blob_name):
    """
    Stream processed results to RabbitMQ
    """
    try:
        # Open a new RabbitMQ connection
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost',  # Replace with your RabbitMQ server hostname if needed
            port=5672,         # Replace with your RabbitMQ port if needed
            credentials=pika.PlainCredentials('guest', 'guest')  # Replace with actual credentials
        ))

        with connection:
            channel = connection.channel()
            channel.queue_declare(queue='pdf_chunks')

            for element in Unstructured_Chunks_List:
                # Extract metadata
                page_number = getattr(element.metadata, 'page_number', None)
                pdf_name = getattr(element.metadata, 'filename', None)
                
                # Check if the content is a table, image, or text
                content_type = 'text'
                content = element.text  # Default to text if it's available

                # Check for tables in the chunk
                if hasattr(element, 'tables') and element.tables:
                    content_type = 'table'
                    content = element.tables  # Extract the table as structured data (list of rows, columns)

                elif hasattr(element, 'image') and element.image:
                    content_type = 'base64_image'
                    content = base64.b64encode(element.image).decode('utf-8')  # Base64 encode the image

                # Create message
                message = {
                    'pdf_name': pdf_name,
                    'page_number': page_number,
                    'content': content,
                    'content_type': content_type  # Specify if it's 'text', 'base64_image', or 'table'
                }

                try:
                    channel.basic_publish(
                        exchange='',
                        routing_key='pdf_chunks',
                        body=json.dumps(message)
                    )
                    print(f"Successfully Pushed {pdf_name} elements to Stream")
                except Exception as e:
                    print(f"Failed to push message to RabbitMQ for {pdf_name}. Error: {e}")

    except Exception as e:
        print(f"Failed to establish RabbitMQ connection while processing {blob_name}. Error: {e}")


# Main function to process files using async I/O and batch processing
async def process_folder_async_batch(bucket_name, folder_path, batch_size=10):
    """
    Process files in a folder using async I/O and batch processing.
    """
    pdf_files = list_files_in_folder(bucket_name, folder_path)
    batches = [pdf_files[i:i + batch_size] for i in range(0, len(pdf_files), batch_size)]
    
    for batch in batches:
        blob_names = [blob.name for blob in batch]
        file_streams = await download_files_async(bucket_name, blob_names)
        process_batch(file_streams)

# Run the workflow
if __name__ == "__main__":
    bucket_name = "indgene_hackathon_pdfs"  # Replace with your GCS bucket name
    folder_path = "NCBI_PDFS_2024/2024/"  # Replace with your folder path
    batch_size = BATCH_SIZE  # Number of files to process in each batch
    
    asyncio.run(process_folder_async_batch(bucket_name, folder_path, batch_size))