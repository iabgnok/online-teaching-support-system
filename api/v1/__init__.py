from flask import Blueprint

api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')

from . import announcements, attendance, forum, messages, auth, schedule, classes, assignments

# Register child blueprints
from .classes import classes_bp
from .assignments import assignments_bp
from .attendance import attendance_bp # Assume you have this BP

api_v1.register_blueprint(classes_bp, url_prefix='/classes')
api_v1.register_blueprint(assignments_bp)
api_v1.register_blueprint(attendance_bp)

