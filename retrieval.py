import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# Load faiss index
index = faiss.read_index('faiss_index')

# Load metadata
metadata = pd.read_csv('metadata.csv')

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Example query
# query = "It's so good to be alive"

def retrieve(query, top_k):
    # generate query embedding
    query_embedding = model.encode(query, convert_to_tensor=True).cpu().numpy()

    # number of closest matches to retrieve
    # top_k = 10

    # search
    distances, indices = index.search(query_embedding.reshape(1, -1), top_k)

    results = []
    for i, idx in enumerate(indices[0]):
        results.append({
            "sentence": metadata.iloc[idx]['Sentence'],
            "story_title": metadata.iloc[idx]['StoryTitle'],
            "distance": distances[0][i],
        })
    return results

