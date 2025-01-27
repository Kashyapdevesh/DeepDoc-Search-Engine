import uuid
from langchain.vectorstores import Chroma

# USE ELASTIC SEARCH DB REFERNCE HERE
from langchain.storage import InMemoryStore 
from langchain.schema.document import Document

# USE HUGGINGFACE/GROQ EMBEDDING MODELS INSTEAD
from langchain.embeddings import OpenAIEmbeddings 

from langchain.retrievers.multi_vector import MultiVectorRetriever

def instantiate_multi_vector_retriver(id_key):
    # The vectorstore to use to index the child chunks; TO-DO: Don't use openai or provide options
    vectorstore = Chroma(collection_name="multi_modal_rag", embedding_function=OpenAIEmbeddings())

    # The storage layer for the parent documents; To-Do: Use ES DB Referce here
    store = InMemoryStore()

    # The retriever (empty to start)
    retriever = MultiVectorRetriever(
        vectorstore=vectorstore,
        docstore=store,
        id_key=id_key,
    )

    return retriever


#To-Do: Resolve Key mismatch issue here
def load_vector_data(table_summaries,text_summaries,image_summaries,id_key):

    retriever=instantiate_multi_vector_retriver(id_key)
    
    # Add texts
    doc_ids = [str(uuid.uuid4()) for _ in text_summaries]
    summary_texts = [
        Document(page_content=summary, metadata={id_key: doc_ids[i]}) for i, summary in enumerate(text_summaries)
    ]
    retriever.vectorstore.add_documents(summary_texts)
    retriever.docstore.mset(list(zip(doc_ids, text_summaries)))

    # Add tables
    table_ids = [str(uuid.uuid4()) for _ in table_summaries]
    summary_tables = [
        Document(page_content=summary, metadata={id_key: table_ids[i]}) for i, summary in enumerate(table_summaries)
    ]
    retriever.vectorstore.add_documents(summary_tables)
    retriever.docstore.mset(list(zip(table_ids, table_summaries)))

    # Add image summaries
    img_ids = [str(uuid.uuid4()) for _ in image_summaries]
    summary_img = [
        Document(page_content=summary, metadata={id_key: img_ids[i]}) for i, summary in enumerate(image_summaries)
    ]
    retriever.vectorstore.add_documents(summary_img)
    retriever.docstore.mset(list(zip(img_ids, image_summaries)))

    print(f"Finished loading all values to vectorstore for key {id_key}")
    




