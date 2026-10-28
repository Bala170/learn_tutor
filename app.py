import faiss
import numpy as np
import pickle
import requests
from sentence_transformers import SentenceTransformer

# -------------------------
# LOAD DATA
# -------------------------
index = faiss.read_index("faiss_index.index")

with open("chunks.pkl", "rb") as f:
    chunks = pickle.load(f)

model = SentenceTransformer("all-MiniLM-L6-v2")

# -------------------------
# MEMORY
# -------------------------
chat_history = []

# -------------------------
# LLM (OLLAMA PHI)
# -------------------------
def ask_llm(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "phi",
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 150
            }
        }
    )
    return response.json()["response"]

# -------------------------
# RETRIEVE
# -------------------------
def retrieve(query, k=5):
    query_vector = model.encode([query])
    distances, indices = index.search(np.array(query_vector), k)
    return [chunks[i] for i in indices[0]]

# -------------------------
# QUERY REWRITE
# -------------------------
def rewrite_query(query):
    prompt = f"Convert this into a clear question:\n{query}"
    return ask_llm(prompt)

# -------------------------
# PROMPT BUILDER
# -------------------------
def build_prompt(query, context, history):

    # POINT-WISE FIX
    if "point" in query.lower() and len(history) > 1:
        last_answer = history[-2].get("ai", "")
        return f"""
Convert this answer into bullet points:

Answer:
{last_answer}

Rules:
- Keep it short
- Do NOT add new information
"""

    # SUMMARY FIX
    if "summary" in query.lower():
        return f"""
You are an AI tutor.

Summarize the story ONLY using the context.

Context:
{context}

Rules:
- Include beginning, middle, end
- Mention Mike, Morris, thief
- Do NOT invent anything
- Keep it short (3-4 lines)
"""

    # FILL BLANK
    if "?" in query or "____" in query:
        return f"""
Complete the sentence using the context.

Answer ONLY the missing part.

Context:
{context}

Sentence:
{query}
"""

    # DEFAULT QA
    return f"""
You are a strict AI tutor.

Context:
{context}

Question:
{query}

Rules:
- Answer ONLY from context
- Do NOT guess
- If not found say: "I don't know based on the document."
"""

# -------------------------
# MAIN LOOP
# -------------------------
def chat():
    print("🤖 Smart AI Tutor Ready! Type 'exit' to quit.\n")

    while True:
        query = input("You: ")

        if query.lower() == "exit":
            print("Goodbye 👋")
            break

        chat_history.append({"user": query})

        # FOLLOW-UP FIX
        if len(query.split()) < 4 and len(chat_history) > 1:
            improved_query = chat_history[-2]["user"]
        else:
            improved_query = rewrite_query(query)

        # RETRIEVE
        docs = retrieve(improved_query, k=5)

        print("\n🔍 Retrieved chunks (debug):")
        for d in docs:
            print("-", d[:100], "\n")

        context = "\n\n".join([d[:400] for d in docs])

        # BUILD PROMPT
        prompt = build_prompt(query, context, chat_history)

        # GET ANSWER
        answer = ask_llm(prompt).strip()

        chat_history[-1]["ai"] = answer

        print("\n🎓 AI Tutor:\n", answer)
        print("\n" + "-"*50 + "\n")


# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    chat()