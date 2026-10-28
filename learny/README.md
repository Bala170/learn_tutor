# Educational Platform

A Django-based educational platform for teachers and students to manage and share notes.

## Features
- Custom user roles: Teacher and Student
- Teacher: Add/manage subjects, upload notes (PDF/DOCX)
- Student: View subjects filtered by department/year, download notes
- User authentication (login/signup)
- Responsive Bootstrap UI with sidebar navigation
- SQLite database (no external setup)
- File uploads stored in /media/notes/

## Setup
1. Install dependencies:
   ```
pip install -r requirements.txt
   ```
2. Run migrations:
   ```
python manage.py migrate
   ```
3. Start the server:
   ```
python manage.py runserver
   ```
4. Access at http://127.0.0.1:8000/

## File Uploads
- Uploaded notes are stored in `/media/notes/`.
- Configure `MEDIA_ROOT` and `MEDIA_URL` in `settings.py` (already set).

## Environment Variables
- See `.env.example` for optional environment variables.

## Admin
- Create a superuser for admin access:
   ```
python manage.py createsuperuser
   ```

## Notes
- No external APIs or AI logic included.
- For demo only. Not production-ready.
