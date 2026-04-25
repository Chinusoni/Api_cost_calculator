import os
from django.core.wsgi import get_wsgi_application

# Replace 'your_inner_project_folder' with your actual folder name
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_inner_project_folder.settings')

application = get_wsgi_application()

# Vercel specifically looks for an object named 'app'
app = application