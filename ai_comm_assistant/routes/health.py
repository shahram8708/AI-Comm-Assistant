"""Health and metrics endpoints."""

from flask import Blueprint, jsonify
import psutil

from ..extensions import db
from ..models import User, Email, Thread


health_bp = Blueprint('health', __name__)


@health_bp.route('/healthz')
def healthz():
    return jsonify(status='ok')


@health_bp.route('/metrics')
def metrics():
    mem = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=None)
    return jsonify({
        'users': User.query.count(),
        'threads': Thread.query.count(),
        'emails': Email.query.count(),
        'memory_used_mb': mem.used // (1024 * 1024),
        'memory_total_mb': mem.total // (1024 * 1024),
        'cpu_percent': cpu,
    })