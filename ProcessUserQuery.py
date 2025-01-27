from elasticsearch import Elasticsearch

# Config
INDEX_NAME = "pdf_chunks"
es = Elasticsearch("http://localhost:9200")


def text_match_results(text, top_n=5):
    """Search for the top N similar documents based on text similarity"""
    try:
        # Query Elasticsearch for documents with content similar to the input text
        response = es.search(
            index=INDEX_NAME,
            body={
                "query": {
                    "match": {
                        "content": text
                    }
                },
                "size": top_n,  # Fetch the top N results
                "_source": ["id", "pdf_name", "page_number", "content"]  # Include only necessary fields
            }
        )

        # Process and display the results
        results = []
        for hit in response['hits']['hits']:
            doc = {
                "id": hit["_id"],
                "pdf_name": hit["_source"]["pdf_name"],
                "page_number": hit["_source"]["page_number"],
                "content": hit["_source"]["content"],
                "score": hit["_score"]  # The relevance score
            }
            results.append(doc)

        return results

    except Exception as e:
        print(f"Error: {e}")
        return []

def semantic_similar_results():
    pass

if __name__ == "__main__":
    # Example usage: searching for a sample text
    query_text = "machine learning algorithms"
    top_results = text_match_results(query_text, top_n=5)

    # Display the results
    if top_results:
        print("Top similar documents:")
        for result in top_results:
            print(f"ID: {result['id']}, PDF Name: {result['pdf_name']}, Page: {result['page_number']}, Score: {result['score']}")
            print(f"Content: {result['content'][:200]}...")  # Display first 200 chars of content for brevity
            print("-" * 40)
    else:
        print("No similar documents found.")
