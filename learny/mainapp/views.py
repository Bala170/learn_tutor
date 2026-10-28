
# -------------------------
# SUBJECT-LEVEL AI TUTOR CHAT
# -------------------------
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

@login_required
def tutor_view(request, subject_id):
	subject = get_object_or_404(Subject, pk=subject_id)
	return render(request, 'mainapp/tutor_chat.html', {'subject': subject})

@csrf_exempt
@login_required
def tutor_api(request, subject_id):
	if request.method != "POST":
		return HttpResponseBadRequest("POST only")

	subject = get_object_or_404(Subject, pk=subject_id)
	notes = subject.notes.all()
	faiss_indexes = []
	all_chunks = []
	chunk_note_map = []  # To map chunk index to note
	for note in notes:
		if note.faiss_index_path and note.chunks_path:
			try:
				idx = faiss.read_index(note.faiss_index_path)
				with open(note.chunks_path, "rb") as f:
					chunks = pickle.load(f)
				faiss_indexes.append(idx)
				all_chunks.extend(chunks)
				chunk_note_map.extend([note.id]*len(chunks))
			except Exception as e:
				continue
	if not faiss_indexes or not all_chunks:
		return JsonResponse({"error": "No processed notes for this subject."}, status=400)

	# Merge all indexes into one (if >1)
	if len(faiss_indexes) == 1:
		index = faiss_indexes[0]
	else:
		dim = faiss_indexes[0].d
		index = faiss.IndexFlatL2(dim)
		for idx in faiss_indexes:
			xb = idx.reconstruct_n(0, idx.ntotal)
			index.add(xb)

	model = SentenceTransformer("all-MiniLM-L6-v2")
	import json
	data = json.loads(request.body.decode())
	query = data.get("query", "")
	history = data.get("history", [])

	def ask_llm(prompt):
		response = requests.post(
			"http://localhost:11434/api/generate",
			json={
				"model": "phi",
				"prompt": prompt,
				"stream": False
			}
		)
		return response.json()["response"]

	def retrieve(query, k=5):
		query_vector = model.encode([query])
		distances, indices = index.search(np.array(query_vector), k)
		return [all_chunks[i] for i in indices[0]]

	def build_prompt(query, context):
		return (
			"You are an AI tutor.\n\n"
			f"Context:\n{context}\n\n"
			f"Question:\n{query}\n\n"
			"Rules:\n"
			"- Answer ONLY from context\n"
			"- Do NOT guess\n"
			"- If not found say: 'I don't know based on the document.'\n"
			"- Keep it short\n"
		)

	docs = retrieve(query, k=5)
	context = "\n\n".join([d[:400] for d in docs])
	prompt = build_prompt(query, context)
	answer = ask_llm(prompt).strip()
	return JsonResponse({"answer": answer, "chunks": docs})
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegisterForm, SubjectForm, NotesForm
from .models import User, Subject, Notes
import faiss
import numpy as np
import pickle
import requests
from sentence_transformers import SentenceTransformer
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.forms import AuthenticationForm
from .utils.pdf_processor import process_pdf
import os
from django.conf import settings
def home(request):
	return render(request, 'mainapp/home.html')

def register(request):
	if request.method == 'POST':
		form = UserRegisterForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			if user.role == 'teacher':
				return redirect('teacher_dashboard')
			else:
				return redirect('student_dashboard')
	else:
		form = UserRegisterForm()
	return render(request, 'mainapp/register.html', {'form': form})

def user_login(request):
	if request.method == 'POST':
		form = AuthenticationForm(request, data=request.POST)
		if form.is_valid():
			username = form.cleaned_data.get('username')
			password = form.cleaned_data.get('password')
			user = authenticate(username=username, password=password)
			if user is not None:
				login(request, user)
				if user.role == 'teacher':
					return redirect('teacher_dashboard')
				else:
					return redirect('student_dashboard')
		messages.error(request, 'Invalid username or password.')
	else:
		form = AuthenticationForm()
	return render(request, 'mainapp/login.html', {'form': form})

def user_logout(request):
	logout(request)
	return redirect('home')

@login_required
def teacher_dashboard(request):
	if not request.user.role == 'teacher':
		return redirect('student_dashboard')
	subjects = Subject.objects.filter(created_by=request.user)
	notes = Notes.objects.filter(subject__in=subjects)
	return render(request, 'mainapp/teacher_dashboard.html', {'subjects': subjects, 'notes': notes})

@login_required
def student_dashboard(request):
	if not request.user.role == 'student':
		return redirect('teacher_dashboard')
	subjects = Subject.objects.filter(department=request.user.department, year=request.user.year)
	return render(request, 'mainapp/student_dashboard.html', {'subjects': subjects})

	# -------------------------
	# AI TUTOR CHAT VIEWS
	# -------------------------
@login_required
def ai_tutor_chat(request, note_id):
	note = get_object_or_404(Notes, pk=note_id)
	return render(request, 'mainapp/chat_modal.html', {'note': note})

@login_required
def ai_tutor_api(request, note_id):
	if request.method != "POST":
		return HttpResponseBadRequest("POST only")

	note = get_object_or_404(Notes, pk=note_id)
	faiss_path = note.faiss_index_path
	chunks_path = note.chunks_path
	if not (faiss_path and chunks_path):
		return JsonResponse({"error": "No processed data for this note."}, status=400)

	# Load FAISS and chunks
	index = faiss.read_index(faiss_path)
	with open(chunks_path, "rb") as f:
		chunks = pickle.load(f)
	model = SentenceTransformer("all-MiniLM-L6-v2")

	# Chat history and query
	import json
	data = json.loads(request.body.decode())
	query = data.get("query", "")
	history = data.get("history", [])

	def ask_llm(prompt):
		response = requests.post(
			"http://localhost:11434/api/generate",
			json={
				"model": "phi",
				"prompt": prompt,
				"stream": False,
				"options": {"num_predict": 150}
			}
		)
		return response.json()["response"]

	def retrieve(query, k=5):
		query_vector = model.encode([query])
		distances, indices = index.search(np.array(query_vector), k)
		return [chunks[i] for i in indices[0]]

	def rewrite_query(query):
		prompt = f"Convert this into a clear question:\n{query}"
		return ask_llm(prompt)

	def build_prompt(query, context, history):
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
		if "?" in query or "____" in query:
			return f"""
Complete the sentence using the context.

Answer ONLY the missing part.

Context:
{context}

Sentence:
{query}
"""
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

	# Query rewrite for short follow-ups
	if len(query.split()) < 4 and len(history) > 1:
		improved_query = history[-2]["user"]
	else:
		improved_query = rewrite_query(query)

	docs = retrieve(improved_query, k=5)
	context = "\n\n".join([d[:400] for d in docs])
	prompt = build_prompt(query, context, history)
	answer = ask_llm(prompt).strip()

	return JsonResponse({"answer": answer, "chunks": docs})
@login_required
def add_subject(request):
	if not request.user.role == 'teacher':
		return redirect('student_dashboard')
	if request.method == 'POST':
		form = SubjectForm(request.POST)
		if form.is_valid():
			subject = form.save(commit=False)
			subject.created_by = request.user
			subject.save()
			return redirect('teacher_dashboard')
	else:
		form = SubjectForm()
	return render(request, 'mainapp/add_subject.html', {'form': form})

@login_required
def edit_subject(request, pk):
	subject = get_object_or_404(Subject, pk=pk, created_by=request.user)
	if request.method == 'POST':
		form = SubjectForm(request.POST, instance=subject)
		if form.is_valid():
			form.save()
			return redirect('teacher_dashboard')
	else:
		form = SubjectForm(instance=subject)
	return render(request, 'mainapp/edit_subject.html', {'form': form, 'subject': subject})

@login_required
def delete_subject(request, pk):
	subject = get_object_or_404(Subject, pk=pk, created_by=request.user)
	if request.method == 'POST':
		subject.delete()
		return redirect('teacher_dashboard')
	return render(request, 'mainapp/delete_subject.html', {'subject': subject})


@login_required
def delete_notes(request, pk):
	note = get_object_or_404(Notes, pk=pk, subject__created_by=request.user)
	if request.method == 'POST':
		note.delete()
		return redirect('teacher_dashboard')
	return render(request, 'mainapp/delete_notes.html', {'note': note})

from django.shortcuts import render, redirect
from .forms import NotesForm

@login_required
def upload_notes(request):
    if request.user.role != 'teacher':
        return redirect('student_dashboard')

    if request.method == 'POST':
        form = NotesForm(request.POST, request.FILES)
        form.fields['subject'].queryset = Subject.objects.filter(created_by=request.user)

        if form.is_valid():
            note = form.save()

            # 🔥 NEW: process PDF
            file_path = note.file.path

            subject_folder = f"subject_{note.subject.id}"
            output_dir = os.path.join(
                settings.MEDIA_ROOT,
                "processed",
                subject_folder,
                f"note_{note.id}"
            )

            faiss_path, chunks_path = process_pdf(file_path, output_dir)

            # save paths
            note.faiss_index_path = faiss_path
            note.chunks_path = chunks_path
            note.save()

            return redirect('teacher_dashboard')

    else:
        form = NotesForm()
        form.fields['subject'].queryset = Subject.objects.filter(created_by=request.user)

    # ✅ KEEP OLD TEMPLATE
    return render(request, 'mainapp/upload_notes.html', {'form': form})