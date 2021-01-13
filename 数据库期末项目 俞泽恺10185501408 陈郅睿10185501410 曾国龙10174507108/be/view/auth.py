from flask import Blueprint
from flask import request
from flask import jsonify
from be.model import user

bp_auth = Blueprint("auth", __name__, url_prefix="/auth")


@bp_auth.route("/login", methods=["POST"])
def login():
    user_id = request.json.get("user_id", "")
    password = request.json.get("password", "")
    terminal = request.json.get("terminal", "")
    u = user.User()
    code, message, token = u.login(user_id=user_id, password=password, terminal=terminal)
    return jsonify({"message": message, "token": token}), code


@bp_auth.route("/logout", methods=["POST"])
def logout():
    user_id: str = request.json.get("user_id")
    token: str = request.headers.get("token")
    u = user.User()
    code, message = u.logout(user_id=user_id, token=token)
    return jsonify({"message": message}), code


@bp_auth.route("/register", methods=["POST"])
def register():
    user_id = request.json.get("user_id", "")
    password = request.json.get("password", "")
    u = user.User()
    code, message = u.register(user_id=user_id, password=password)
    return jsonify({"message": message}), code


@bp_auth.route("/unregister", methods=["POST"])
def unregister():
    user_id = request.json.get("user_id", "")
    password = request.json.get("password", "")
    u = user.User()
    code, message = u.unregister(user_id=user_id, password=password)
    return jsonify({"message": message}), code


@bp_auth.route("/password", methods=["POST"])
def change_password():
    user_id = request.json.get("user_id", "")
    old_password = request.json.get("oldPassword", "")
    new_password = request.json.get("newPassword", "")
    u = user.User()
    code, message = u.change_password(user_id=user_id, old_password=old_password, new_password=new_password)
    return jsonify({"message": message}), code


@bp_auth.route("/search",methods=['POST'])
def search():
    target_store_id: list = None
    target_id:list = None
    target_title:list = None
    target_tags:list = None
    target_author: list = None
    target_publisher:list = None
    target_original_title:list = None
    target_translator:list = None
    target_pub_year: list = None
    target_pages:list = None
    target_price:list = None
    target_binding:list = None
    target_isbn: list = None
    target_author_intro:list = None
    target_book_intro:list = None
    target_content:list = None
    target_stock_level: int = None
    target_store_id=request.json.get("store_id")


    target_id=request.json.get("id")

    target_title=request.json.get("title")

    target_author=request.json.get("author")

    target_publisher=request.json.get("publisher")
    target_original_title=request.json.get("original_title")
    target_translator=request.json.get("translator")
    target_pub_year=request.json.get("pub_year")
    target_pages=request.json.get("pages")
    target_price=request.json.get("price")
    target_binding=request.json.get("binding")
    target_isbn=request.json.get("isbn")
    target_author_intro=request.json.get("author_intro")
    target_book_intro=request.json.get("book_intro")
    target_content=request.json.get("content")
    target_tags=request.json.get("tags")
    target_stock_level=request.json.get("stock_level")

    u=user.User()
    code,ret=u.search_by_arguments(target_store_id,target_id,target_title
                                   ,target_tags,
                            target_author,target_publisher,target_original_title
                                   ,target_translator,
                            target_pub_year,target_pages,target_price
                                   ,target_binding,
                            target_isbn,target_author_intro
                                   ,target_book_intro,target_content,
                            target_stock_level
                            )
    return jsonify("results:",ret),code