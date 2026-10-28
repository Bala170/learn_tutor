from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM

# =========================
# Load embeddings + DB
# =========================
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

db = FAISS.load_local(
    "faiss_db",
    embeddings,
    allow_dangerous_deserialization=True
)

# =========================
# Load local AI
# =========================
llm = OllamaLLM(model="phi")

# =========================
# Memory
# =========================
chat_history = []

print("🤖 Smart AI Tutor Ready! Type 'exit' to quit.\n")

# =========================
# Query Type Detection
# =========================
def detect_query_type(query):
    query = query.lower()

    if any(word in query for word in ["teach", "explain"]):
        return "teaching"
    elif any(word in query for word in ["how many", "total", "calculate", "number", "topic"]):
        return "reasoning"
    else:
        return "normal"

# =========================
# Chat Loop
# =========================
while True:
    query = input("You: ")

    if query.lower() == "exit":
        break

    # 🔍 Retrieve more context
    docs = db.similarity_search(query, k=3)
    context = "\n---\n".join([doc.page_content for doc in docs])

    # 🧠 Memory
    history_text = "\n".join(chat_history[-4:])

    query_type = detect_query_type(query)

    # =========================
    # 🎓 Teaching Mode
    # =========================
    if query_type == "teaching":
        prompt = f"""
You are an expert teacher.

Teach step-by-step using the context.
Use simple language and examples.
Do not dump everything at once.
Ask if student wants next part.

History:
{history_text}

Context:
{context}

Question:
{query}

Start teaching:
"""

    # =========================
    # 🧠 Reasoning Mode (tables/numbers)
    # =========================
    elif query_type == "reasoning":
        prompt = f"""
You are a logical problem solver.

Carefully analyze the context.
If it contains table-like data:
- Identify relationships
- Perform calculations step-by-step

Do NOT guess.

Context:
{context}

Question:
{query}

Final Answer:
"""

    # =========================
    # 📘 Normal Mode
    # =========================
    else:
        prompt = f"""
Answer ONLY using the context.
If not found, say: Not found in notes.

Context:
{context}

Question:
{query}

Answer:
"""

    # 🤖 Generate response
    response = llm.invoke(prompt)

    print("\n🎓 AI Tutor:\n")
    print(response)
    print("\n" + "-"*50)

    # 💾 Save memory
    chat_history.append(f"User: {query}")
    chat_history.append(f"AI: {response}")