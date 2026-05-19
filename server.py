from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

DB_FILE = "wallets.json"

ADMIN_PASSWORD = "GAR_Admin_9472"

# загрузка базы
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        wallets = json.load(f)
else:
    wallets = {}

def save():
    with open(DB_FILE, "w") as f:
        json.dump(wallets, f)

# главная страница
@app.route("/")
def home():
    return "GARAGECOIN SERVER ONLINE"

# регистрация / вход
@app.route("/login")
def login():

    name = request.args.get("name")
    password = request.args.get("password")

    if not name or not password:
        return jsonify({
            "error": "Введите имя и пароль"
        })

    # новый кошелек
    if name not in wallets:

        if len(password) < 8 or len(password) > 12:
            return jsonify({
                "error": "Пароль должен быть от 8 до 12 символов"
            })

        wallets[name] = {
            "password": password,
            "balance": 0
        }

        save()

        return jsonify({
            "status": "Кошелек создан",
            "wallet": name
        })

    # проверка пароля
    if wallets[name]["password"] != password:
        return jsonify({
            "error": "Неверный пароль"
        })

    return jsonify({
        "status": "Вход выполнен",
        "wallet": name,
        "balance": wallets[name]["balance"]
    })

# баланс
@app.route("/balance")
def balance():

    name = request.args.get("name")
    password = request.args.get("password")

    if name not in wallets:
        return jsonify({
            "error": "Кошелек не найден"
        })

    if wallets[name]["password"] != password:
        return jsonify({
            "error": "Неверный пароль"
        })

    return jsonify({
        "wallet": name,
        "balance": wallets[name]["balance"]
    })

# перевод
@app.route("/send")
def send():

    sender = request.args.get("from")
    password = request.args.get("password")
    receiver = request.args.get("to")
    amount = int(request.args.get("amount"))

    if sender not in wallets:
        return jsonify({
            "error": "Кошелек отправителя не найден"
        })

    if wallets[sender]["password"] != password:
        return jsonify({
            "error": "Неверный пароль"
        })

    if receiver not in wallets:
        return jsonify({
            "error": "Кошелек получателя не найден"
        })

    if wallets[sender]["balance"] < amount:
        return jsonify({
            "error": "Недостаточно GAR"
        })

    wallets[sender]["balance"] -= amount
    wallets[receiver]["balance"] += amount

    save()

    return jsonify({
        "status": "Перевод выполнен"
    })

# просмотр всех кошельков
@app.route("/admin/wallets")
def admin_wallets():

    admin_password = request.args.get("admin_password")

    if admin_password != ADMIN_PASSWORD:
        return jsonify({
            "error": "Неверный админ пароль"
        })

    return jsonify(wallets)

# изменить баланс
@app.route("/admin/setbalance")
def admin_setbalance():

    admin_password = request.args.get("admin_password")
    name = request.args.get("name")
    amount = int(request.args.get("amount"))

    if admin_password != ADMIN_PASSWORD:
        return jsonify({
            "error": "Неверный админ пароль"
        })

    if name not in wallets:
        return jsonify({
            "error": "Кошелек не найден"
        })

    wallets[name]["balance"] = amount
    save()

    return jsonify({
        "status": "Баланс изменен",
        "wallet": name,
        "new_balance": amount
    })

# смена пароля
@app.route("/admin/setpassword")
def admin_setpassword():

    admin_password = request.args.get("admin_password")
    name = request.args.get("name")
    new_password = request.args.get("new_password")

    if admin_password != ADMIN_PASSWORD:
        return jsonify({
            "error": "Неверный админ пароль"
        })

    if name not in wallets:
        return jsonify({
            "error": "Кошелек не найден"
        })

    wallets[name]["password"] = new_password
    save()

    return jsonify({
        "status": "Пароль изменен"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
