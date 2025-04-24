from functools import wraps
from flask import request, jsonify
import jwt

from ..models import User
from app.config import SECRET

def isAuthorized(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            token = request.headers.get("Authorization", None).split(" ")[1]
            if token is None:
                print(1)
                return jsonify({ "message": "Пользователь не авторизован!" }), 403
            
            decoded = jwt.decode(token, key=SECRET, algorithms=["HS256"])
            if decoded is None:
                print(2)
                return jsonify({ "message": "Пользователь не авторизован!" }), 403
                
            user_id = decoded["_id"]
            candidate = User.objects(id=user_id).first()
            if candidate is None:
                print(3)
                return jsonify({ "message": "Пользователь не авторизован!" }), 403
            
            return func(candidate, *args, **kwargs)
        except Exception as ex:
            print(ex)
            return jsonify({ "message": "Пользователь не авторизован!"}), 403
    
    return wrapper