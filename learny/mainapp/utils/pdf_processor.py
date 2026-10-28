import os
import faiss
import numpy as np
import pickle
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

def process_pdf(file_path, output_dir):
    reader = PdfReader(file_path)
    text = ""

    for page in reader.pages:
        text += page.extract_text() + "\n"

    # Chunking
    sentences = text.split(". ")
    chunks = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) < 800:
            current += sentence + ". "
        else:
            chunks.append(current.strip())
            current = sentence + ". "

    if current:
        chunks.append(current.strip())

    # Embeddings
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(chunks)

    # FAISS
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))

    # Save
    os.makedirs(output_dir, exist_ok=True)

    faiss_path = os.path.join(output_dir, "faiss.index")
    chunks_path = os.path.join(output_dir, "chunks.pkl")

    faiss.write_index(index, faiss_path)

    with open(chunks_path, "wb") as f:
        pickle.dump(chunks, f)

    return faiss_path, chunks_path