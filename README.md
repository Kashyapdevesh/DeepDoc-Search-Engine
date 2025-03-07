# **DeepDoc Search Engine**

![image](https://github.com/user-attachments/assets/df316409-02af-432f-ac87-f61efc1a10b2)

# <a name="_page1_x72.00_y88.50"></a>**Table of Contents** 

[Introduction](#_page1_x72.00_y462.75) 

[Project Abstract](#_page2_x72.00_y132.00) 

[Technical Implementation](#_page2_x72.00_y562.50) 

[Data Download & Extraction Module](#_page3_x72.00_y120.00) 

[Workflow for Data Download and Extraction Module](#_page4_x72.00_y703.50) [Key Benefits of This Approach:](#_page6_x72.00_y295.50) 

[DocStore Data Storage Module](#_page6_x72.00_y540.00) 

[Workflow for DocStore Data Storage Module](#_page7_x72.00_y706.50) 

[Key Benefits of This Approach:](#_page9_x72.00_y139.50) 

[Data Summarization and VectorStore Data Storage Module](#_page9_x72.00_y337.50) 

[Workflow for Chunk Data Summarization and Storage](#_page10_x72.00_y694.50) [Key Benefits of This Approach:](#_page11_x72.00_y510.75) 

[Data Retrieval and Query Processing Module](#_page12_x72.00_y198.00) 

[Workflow for Query Processing & Retrieval Module](#_page13_x72.00_y690.75) 

[Key Benefits of this Approach:](#_page14_x72.00_y459.75) 

[Future Scope and Enhancements](#_page15_x72.00_y217.50) 

# <a name="_page1_x72.00_y462.75"></a>**Introduction** 
In today’s business environment, PDFs are widely used for sharing contracts, reports, and critical documents. However, the growing volume and complexity of these files make it challenging to efficiently extract, search, and analyze their content. This is especially problematic in industries like law, finance, and healthcare, where professionals frequently sift through large document volumes to find relevant information. According to Gartner, professionals spend up to 30% of their workweek searching for information, much of which is wasted on poorly organized or hard-to-query document systems. 

While many systems offer Optical Character Recognition (OCR) or keyword search, they still fall short in providing the smart, context-aware querying capabilities required to process intricate documents effectively. A study by *McKinsey* highlights that businesses lose approximately $3 trillion annually due to inefficiencies in document management, much of which can be attributed to time wasted in searching and organizing these documents. This issue is exacerbated by the rapid increase in document volume and the evolving need for real-time insights across various sectors. 
# <a name="_page2_x72.00_y132.00"></a>**Project Abstract** 
In this project, we have developed a highly efficient, scalable, and production-ready RAG (Retrieval-Augmented Generation) based data ingestion and querying platform. This platform supports data ingestion from multiple cloud storage sources, including: 

1. **Google Cloud Storage (GCS)** 
1. **Azure Data Lake Storage (ADLS)** 
1. **AWS Storage** 
1. **SFTP Storage** 

The data ingestion system is optimized for high-performance asynchronous multi-threaded downloading. The ingestion process extracts valuable information from PDFs and transforms it into a structured knowledge base that can be utilized for LLM-based RAG querying. This knowledge base is then stored in Elasticsearch, including relevant metadata such as document names, page numbers, and UUIDs, enabling a flexible hybrid search system. 

Additionally, the system supports the use of multiple LLM models to serve as the final querying agent. This includes the integration of the advanced, chain-of-thought-based reasoning model, **DeepSeek R1**, which enhances the platform's ability to generate context-aware, accurate responses based on the ingested data. 

This setup offers the best of both worlds—efficient data ingestion, seamless hybrid search capabilities, and powerful LLM-based querying—making it a robust, production-ready solution for document management and intelligent search. 
# <a name="_page2_x72.00_y562.50"></a>**Technical Implementation** 
Due to the vast scope and complexity of the project, the technical implementation is divided into the following modules, which are explained in detail below: 

- **Data Download and Extraction Module** (specific to data sources) 
- **DocStore Data Storage Module** 
- **Data Summarization and VectorStore Data Storage Module** 
- **Data Retrieval and Query Processing Module** 
# <a name="_page3_x72.00_y120.00"></a>**Data Download & Extraction Module**
The platform supports **automated data ingestion** from multiple cloud and storage services, including: 

1. **Google Cloud Storage (GCS)** 
1. **Azure Data Lake Storage (ADLS)** 
1. **AWS Storage** 
1. **SFTP Storage** 

For this prototype, we focus on the **Google Cloud Storage (GCS) ingestion module**. The GCSConnectors.py file in the attached codebase provides the implementation details. 

![image](https://github.com/user-attachments/assets/e969593f-a66b-4412-9910-f547b078fcb0)

<a name="_page4_x72.00_y703.50"></a>**Workflow for Data Download and Extraction Module** 

1. **Authentication & Setup:** 
- Obtain the credentials.json file for the Google Cloud Storage bucket. 
- Define the bucket and folder path where the PDFs are stored. 
2. **Listing and Batching Files:** 
- The system lists all available PDF files in the specified directory. 
- Files are processed in **batches of 10**, optimizing resource utilization. The batch size can be adjusted based on system hardware capabilities. 
3. **Asynchronous Download & Memory Optimization:** 
- PDFs are **asynchronously downloaded** using aiohttp.ClientSession(), minimizing network latency. 
- Files are stored as **raw stream buffers** in **RAM** using io.BytesIO for 

  **efficient in-memory processing**. 

- A reference list of all stream buffers is passed to the process\_batch function. 
4. **Batch Segmentation Based on File Size:** 
- The system categorizes files into two lists based on their size: 
- **Large files** (>100MB, configurable threshold based on hardware) 
- **Small files** (<100MB) 
- This distinction allows **optimized parallel processing**. 
5. **Parallel Processing for Large & Small Files:** 
   1. **Large files** spawn **separate processes** using ProcessPoolExecutor, each with its own resource pool. This mitigates Python’s **Global Interpreter Lock (GIL)** constraints and enables true parallel execution. 
   1. **Small files** spawn **separate threads** using ThreadPoolExecutor, ensuring concurrent processing with minimal overhead. 
5. **PDF Content Extraction & Chunking:** 
- The process\_file function extracts **structured** and **unstructured** content using the **Unstructured Python library**, which is widely used in **production-grade document analysis systems**. 
- The content is segmented into chunks using **title layout analysis**, preserving **document structure, tables, text, and images** (Base64-encoded). 
7. **Structured Data Representation:** 
- The process\_file function returns a **dictionary** containing: 
- pdf\_name: Original PDF file name 
- page\_number: Page number from which the chunk is extracted 
- content: List of **Unstructured objects** (tables, text, images) 
- content\_type: The type of extracted data (text, table, or image) 
8. **Real-Time Data Streaming to RabbitMQ:** 
- Extracted data is **continuously pushed** to a **global RabbitMQ message stream** 
- Each process/thread acts as a **RabbitMQ producer**, enabling **real-time streaming and message queuing** for downstream processing. 

<a name="_page6_x72.00_y295.50"></a>**Key Benefits of This Approach:** 

1) **High-Speed Parallel Processing** – Uses **async HTTP sessions** and batch processing to download PDFs efficiently. 
1) **Optimized for Large Files** – **ProcessPoolExecutor** handles large files, while **ThreadPoolExecutor** manages smaller ones. 
1) **Memory-Efficient Streaming** – Uses **in-memory file streams (io.BytesIO)** to avoid disk I/O overhead. 
1) **Scalable & Configurable** – Batch size and file size thresholds can be adjusted based on system capabilities. 
1) **Seamless Integration** – Processed data is continuously pushed to **RabbitMQ**, ensuring smooth downstream processing. 
# <a name="_page6_x72.00_y540.00"></a>**DocStore Data Storage Module** 
In this module, we actively **listen to the RabbitMQ message stream** as a consumer, continuously processing chunk data dictionaries and ingesting them into the **DocStore database**. For this demonstration, we use **Elasticsearch** as the DocStore due to its **advanced search capabilities**, including: 

- **Full-text search** with tokenization and ranking 
- **Fuzzy search** for handling typos and partial matches** 

Elasticsearch will serve as the **primary database** for storing indexed document content, linked with **UUID-based identifiers**. These UUIDs will later be used in the **Retrieval-Augmented Generation (RAG) pipeline** to enhance AI-based querying. 

Additionally, the module will create an **async event loop**, sending the chunk data dictionary to the **Data Processing and VectorStore Data Storage Module**. This ensures that **chunk data is processed in parallel** with ingestion into Elasticsearch, eliminating delays and maintaining real-time performance. 

For implementation details, refer to the ESDocStoreConsumer.py file in the attached codebase. 

![image](https://github.com/user-attachments/assets/4d3424b3-bf57-4723-bc1d-84f35a48dd3d)

<a name="_page7_x72.00_y706.50"></a>**Workflow for DocStore Data Storage Module** 

1. **Thread Management for Batch Processing:** 
- Create threads using ThreadPoolExecutor with a **configurable batch size (BATCH\_SIZE)** for efficient parallel ingestion into Elasticsearch. 
- The BATCH\_SIZE can be adjusted based on hardware capabilities to optimize performance. 
2. **Asynchronous Processing Pipeline:** 
- Set up an **async I/O queue** for handling chunk data processing in parallel with Elasticsearch ingestion. 
- This queue enables **thread-safe, concurrent execution**, ensuring high throughput. 
3. **Index Management in Elasticsearch:** 
- Check if the **Elasticsearch index (namespace)** with the required schema exists. 
- If not, create a new index with the appropriate structure. 
4. **Active Listening to RabbitMQ Stream:** 
- Establish a **persistent connection** to the global RabbitMQ message stream. 
- Continuously listen for incoming **chunk data messages**. 
5. **Processing Incoming Data:** 
- Upon receiving a new chunk, invoke the **callback function**, which: 
- Calls process\_message() with the chunk data dictionary. 
- Adds the processing task to an executor for parallel execution. 
- Sends an **acknowledgment tag** back to RabbitMQ, confirming message receipt. 
6. **Data Storage in Elasticsearch:** 
- The process\_message() function assigns a **unique chunk ID** to each document segment. 
- The processed chunk is stored in **Elasticsearch**, indexed based on the predefined schema. 
7. **Parallel Processing for Vector Embeddings:** 
- The **processed chunk is added to the async I/O queue** for vector-based storage and retrieval. 
- The queue continuously invokes the **Data Processing and VectorStore Data Storage Module** for embedding generation and semantic search indexing. 

<a name="_page9_x72.00_y139.50"></a>**Key Benefits of This Approach:** 

1) **Real-time, parallelized processing** of document chunks. 
1) **No lag or delay** in indexing, as Elasticsearch ingestion and vector storage run in tandem. 
1) **Scalable architecture**, capable of handling large document volumes efficiently. 
1) **Seamless integration** with downstream **AI-based search and RAG pipelines**. 

This ensures **fast, structured, and scalable document management**, making PDF search and retrieval highly optimized for production use. 
## <a name="_page9_x72.00_y337.50"></a>Data Summarization and VectorStore Data Storage Module 
In this module, we repeatedly call the process\_message() function, which serves as the entry point for **data processing and vector storage**. It **extracts, summarizes, and embeds** the content from the chunk data dictionary before storing it in the **Chroma Vector Store**. 

The system **unpacks the Unstructured object**, processes **tables, text, and images**, and generates **summaries** using **open-source LLMs**: 

- **Llama 3.1-8b-instant** for table and text summarization. 
- **Llama 3.2-11b-vision-preview** for base64-encoded image summarization. 

The generated summaries are **stored with their associated UUIDs** in Chroma, linking them to their original **artifacts in Elasticsearch**. This ensures seamless retrieval in the **Retrieval-Augmented Generation (RAG) pipeline**. 

For implementation details, refer to ProcessStreamChunk.py 

![image](https://github.com/user-attachments/assets/ad854a85-da63-4fa0-a497-6ed4bc5fb779)

<a name="_page10_x72.00_y694.50"></a>**Workflow for Chunk Data Summarization and Storage** 

1. **Consume Chunk Data** 
- Retrieve the chunk data dictionary from the **async I/O queue**. 
- Extract **tables, text, and base64-encoded images** from the **Unstructured object**. 
2. **Summarization with LLMs** 
   1. **Tables & Text** → Processed in batches using **Llama 3.1-8b-instant** via **LangChain ChatGroq** (max concurrency = 5, configurable). 
   1. **Images** → Summarized using **Llama 3.2-11b-vision-preview** via **LangChain ChatGroq** (max concurrency = 5). 
   1. *(Concurrency defines how many parallel requests the model can handle—higher values increase speed but require more resources.)* 
2. **Embedding & Storage** 
- **Instantiate MultiVector Retriever** → Links **Elasticsearch & Chroma Vector Store** via UUID. 
- **Generate embeddings** using an **open-source embedding model**. 
- **Store summary embeddings** in **Chroma Vector Store**, ensuring they remain linked to original artifacts in **Elasticsearch**. 

The **Chroma Vector Store now contains chunk embeddings** linked to **original artifacts in Elasticsearch**. These embeddings will be **used in the RAG pipeline** to provide accurate context for AI-based document retrieval. 

<a name="_page11_x72.00_y510.75"></a>**Key Benefits of This Approach:** 

1) **Efficient & Automated Summarization** – Uses **Llama 3.1-8b-instant** for text/tables and **Llama 3.2-11b-vision-preview** for images, enabling **automated content understanding**. 
1) **Optimized Performance** – Batch processing via **LangChain ChatGroq** with configurable **max concurrency (default: 5)** ensures efficient parallel execution. 
1) **Seamless Multi-Store Integration** – **MultiVector Retriever** links **Elasticsearch (original artifacts)** and **Chroma (vector embeddings)** via **UUID**, ensuring fast and accurate retrieval. 
4) **Enhanced RAG Contextual Search** – Embedding-based storage allows **precise AI-powered search** and **context-aware query responses**. 
4) **Scalable & Production-Ready** – Designed for **high concurrency**, **async processing**, and **modular expandability**, making it ideal for large-scale enterprise deployments 
## <a name="_page12_x72.00_y198.00"></a>Data Retrieval and Query Processing Module 
This is the **final module**, responsible for **handling user queries** and **retrieving relevant information** from the document store. It dynamically selects the best search approach based on the **availability of indexed data**. 

- If the **data ingestion pipeline is still running**, it performs a **text-based search** on **Elasticsearch**. 
- If ingestion is **complete**, it uses an **LLM-powered vector search** for more accurate results. 

For **LLM-based search**, the system: 

1. **Embeds the user query into a vector**. 
1. **Performs cosine similarity search** on **summaries stored in Chroma**. 
1. **Retrieves the top P matching results** and fetches their original **artifacts from Elasticsearch** using **UUIDs**. 
1. **Provides the original artifacts as context** to **DeepSeek R1 LLM**, enabling it to generate **context-aware responses**. 
1. **Includes metadata** (PDF name and page number from Elasticsearch) to **cite sources** for the generated response. 

![image](https://github.com/user-attachments/assets/590e89b6-230e-4269-bdf9-6792e90cb758)


<a name="_page13_x72.00_y690.75"></a>**Workflow for Query Processing & Retrieval Module** 

1. **Receive User Query** 
- Accept the query and check if the **data ingestion pipeline is complete**. 
2. **Select Search Method** 
- If **data ingestion is incomplete**, perform **text-based search** on **Elasticsearch**. 
- If **data ingestion is complete**, proceed with **LLM-based vector search**. 
3. **Vector Search in Chroma** 
   1. **Embed user query** using an **open-source embedding model**. 
   1. Perform **cosine similarity search** on **stored summaries in Chroma**. 
   1. Retrieve **top P relevant results** based on similarity scores. 
3. **Retrieve Original Artifacts** 
- Fetch the **original artifacts from Elasticsearch** using their **associated UUIDs**. 
5. **Generate Contextual Response** 
- Provide the retrieved **artifacts as context** to **DeepSeek R1 LLM**. 
- Generate an **accurate, context-aware response** based on the retrieved documents. 
- Extract **metadata (PDF name, page number)** to **cite sources** in the output. 

<a name="_page14_x72.00_y459.75"></a>**Key Benefits of this Approach:** 

1) **Hybrid Search for Maximum Accuracy** – Uses **text-based search** for **real-time queries** and **vector search** for **contextual LLM responses**, ensuring precise information retrieval. 
1) **Scalable & Efficient Retrieval** – **Cosine similarity search in Chroma** enables **fast, high-precision** document retrieval, making the system efficient even for large datasets. 
1) **Citation & Source Transparency** – Extracted **metadata (PDF name & page number)** ensures that responses are **verifiable and trustworthy**. 
1) **Production-Ready & High Performance** – Optimized for **low-latency**, supports **high concurrency**, and seamlessly scales for **large document collections**. 
5) **Advanced Reasoning for Better Understanding** – **DeepSeek R1 LLM** leverages its **reasoning capabilities** to **interpret complex queries, summarize key insights**, and **provide well-structured answers**, improving accuracy and relevance. 
5) **Context-Aware AI Responses** – The LLM generates **accurate, document-backed answers** by using **retrieved artifacts as context**, enhancing user experience and decision-making. 
# <a name="_page15_x72.00_y217.50"></a>**Future Scope and Enhancements**
1. **Frontend UI for Seamless User Interaction**: 
   1. Develop a user-friendly web-based dashboard for uploading, searching, and querying PDFs. 
   1. Implement real-time search suggestions, document previews, and interactive query refinement features, providing a smooth and intuitive experience for users. 
1. **Multi-Cloud & Storage Integrations**: 
   1. Extend the current cloud storage support to include ADLS (Azure Data Lake Storage), AWS, and SFTP connectors. 
   1. This will provide flexibility and support for various cloud and storage services, ensuring broader compatibility. 
1. **Multi-LLM Support for Adaptive Query Processing**: 
   1. Allow dynamic selection of LLMs (DeepSeek R1, GPT-4-turbo, Mixtral, and other open-source models) based on the complexity of the user query. 
   1. Integrate vision-based LLMs (such as LLaVA and Gemini) for image-based document understanding, enhancing multi-modal query capabilities. 
1. **Optimized Retrieval-Augmented Generation (RAG) with Chat History**: 
   1. Improve the answer quality by incorporating chat history as context. This will enable more natural, multi-turn conversations and enhance the accuracy and relevance of responses. 
1. **Advanced Caching & Performance Optimizations**: 
- Implement Redis caching to store frequent queries and their results, reducing latency and improving system performance for repeated searches. 

