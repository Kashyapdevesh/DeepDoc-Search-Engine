import base64
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from CDBVectorStore import load_vector_data

def display_base64_image(base64_code):
    image_data = base64.b64decode(base64_code)
    return image_data #binary data needs to be parsed

def get_images_base64(chunk):
    images_b64 = []
    if "CompositeElement" in str(type(chunk)):
        chunk_els = chunk.metadata.orig_elements
        for el in chunk_els:
            if "Image" in str(type(el)):
                images_b64.append(el.metadata.image_base64)
    return images_b64

def generate_table_text_summaries(tables,texts):
    prompt_text = """
    You are an assistant tasked with summarizing tables and text.
    Give a concise summary of the table or text.

    Respond only with the summary, no additionnal comment.
    Do not start your message by saying "Here is a summary" or anything like that.
    Just give the summary as it is.

    Table or text chunk: {element}

    """
    prompt = ChatPromptTemplate.from_template(prompt_text)

    # Summary chain
    model = ChatGroq(temperature=0.5, model="llama-3.1-8b-instant")
    summarize_chain = {"element": lambda x: x} | prompt | model | StrOutputParser()

    # Summarize text
    text_summaries = summarize_chain.batch(texts, {"max_concurrency": 5})

    # Summarize tables
    tables_html = [table.metadata.text_as_html for table in tables]
    table_summaries = summarize_chain.batch(tables_html, {"max_concurrency": 5})

    return table_summaries,text_summaries

def generate_image_summaries(images_b64):    
    # Define the image as base64 (replace `{image_data}` with actual base64 or URL)
    image_url = "data:image/jpeg;base64,{image_data}"

    # Define a generic prompt for image summarization
    prompt_template = """Analyze this research figure for detailed technical understanding.

    **Focus on:**
    1. Figure type (e.g., bar plot, architecture diagram, flowchart)
    2. Key elements:
    - For graphs: Axes, labels, units, trends, annotations
    - For diagrams: Components, connections, flow directions
    - For tables: Headers, row/column relationships, highlighted data
    3. Contextual relevance:
    - How it relates to transformer architecture
    - Specific technical insights (e.g., attention mechanisms, layer norms)
    4. Quantitative details:
    - Explicit values, ranges, or comparisons
    - Statistical markers (e.g., p-values, error bars)

    **Requirements:**
    - Use precise technical terminology
    - Avoid vague descriptions
    - Maintain academic tone
    - Highlight key takeaways for researchers"""

    # Create the messages structure for Groq API
    messages = [
        (
            "user",
            [
                {"type": "text", "text": prompt_template},
                {"type": "image_url", "image_url": {"url": image_url}},
            ],
        )
    ]

    # Define the ChatGroq chain with model and the Groq API key
    chain = ChatPromptTemplate.from_messages(messages) | ChatGroq(
        model_name="llama-3.2-11b-vision-preview",
        temperature=0.3,            #controls randomness,less temperatur more focused & determinstic, don't want extra details not in img
        max_tokens=1024,            # Sufficient for detailed analysis
        top_p=0.9,                  # Focused diversity
        frequency_penalty=0.2,      # Allow necessary term repetition
        presence_penalty=0.2,       # Encourage novel insights
    )

    # Process the images in batch (assuming `images` is a list of base64 image strings or URLs)
    image_summaries = chain.batch(images_b64)

    return image_summaries


def generate_element_summaries(doc):
    chunk_id=doc["id"]
    pdf_name=doc["pdf_name"]
    page_number=doc["page_number"]
    chunk=doc["content"]

    tables,texts,images_b64 = [],[],[]
    if "Table" in str(type(chunk)):
        tables.append(chunk)

    if "CompositeElement" in str(type((chunk))):
        texts.append(chunk)
        chunk_els = chunk.metadata.orig_elements
        for el in chunk_els:
            if "Image" in str(type(el)):
                images_b64.append(el.metadata.image_base64)
    
    #TO-Do: add async await to below functions so they can run parallely
    table_summaries,text_summaries=generate_table_text_summaries(tables,texts)

    image_summaries=generate_image_summaries(images_b64)

    return (table_summaries,text_summaries,image_summaries)

def process_stream_chunk(doc):
    table_summaries,text_summaries,image_summaries=generate_element_summaries(doc)

    load_vector_data(table_summaries,text_summaries,image_summaries,doc["id"])



    
    





