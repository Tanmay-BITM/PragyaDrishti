# Deprecated router module: routes moved to reports.py, admin.py, chatbot.py.
# Face recognition has been permanently decommissioned and removed.
from app.api.v1.reports import reports_router
from app.api.v1.admin import admin_router
from app.api.v1.chatbot import chatbot_router, ChatbotRequest
