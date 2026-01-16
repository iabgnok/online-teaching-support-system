from flask import Blueprint

api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')

from . import announcements, attendance, forum, messages, auth, schedule, classes, assignments, student

# Child blueprints are registered in the main app to avoid nesting errors
from .classes import classes_bp
from .assignments import assignments_bp
from .attendance import attendance_bp

