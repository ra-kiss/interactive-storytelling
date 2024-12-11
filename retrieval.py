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

def retrieve(query):
    # generate query embedding
    query_embedding = model.encode(query, convert_to_tensor=True).cpu().numpy()

    # number of closest matches to retrieve
    top_k = 10

    # search
    distances, indices = index.search(query_embedding.reshape(1, -1), top_k)

    for i, idx in enumerate(indices[0]):
        print(f"Result {i + 1}:")
        print(f"Sentence: {metadata.iloc[idx]['Sentence']}")
        print(f"Story Title: {metadata.iloc[idx]['StoryTitle']}")
        print(f"Distance: {distances[0][i]}")
        print()

