from functools import wraps
from flask import request


def admin_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        role = request.headers.get("X-Role")

        if role != "admin":
            return {
                "success": False,
                "message": "Admin access required"
            }, 403

        return function(*args, **kwargs)

    return wrapper