import faiss
import numpy as np
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import pickle

# -------------------------
# LOAD PDF
# -------------------------
reader = PdfReader("notes.pdf")
text = ""

for page in reader.pages:
    text += page.extract_text() + "\n"

# -------------------------
# BETTER CHUNKING (IMPORTANT)
# -------------------------
def split_text(text, chunk_size=800, overlap=200):
    sentences = text.split(". ")
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) < chunk_size:
            current_chunk += sentence + ". "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

chunks = split_text(text)

print(f"✅ Total chunks created: {len(chunks)}")

# -------------------------
# EMBEDDINGS
# -------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(chunks)

# -------------------------
# FAISS INDEX
# -------------------------
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(np.array(embeddings))

# -------------------------
# SAVE
# -------------------------
faiss.write_index(index, "faiss_index.index")

with open("chunks.pkl", "wb") as f:
    pickle.dump(chunks, f)

print("✅ PDF processed successfully!")