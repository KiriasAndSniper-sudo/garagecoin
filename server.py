from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

DB_FILE = "wallets.json"
ADMIN_PASSWORD = "garage_admin_123"

if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        wallets = json.load(f)
else:
    wallets = {}

def save():
    with open(DB_FILE, "w") as f:
        json.dump(wallets, f)

@app.route("/balance")
def balance():

    name = request.args.get("name")

    if name not in wallets:
        wallets[name] = 0
        save()

    return jsonify({
        "wallet": name,
        "balance": wallets[name]
    })

@app.route("/send")
def send():

    sender = request.args.get("from")
    receiver = request.args.get("to")
    amount = int(request.args.get("amount"))

    if sender not in wallets:
        wallets[sender] = 0

    if receiver not in wallets:
        wallets[receiver] = 0

    if wallets[sender] < amount:
        return jsonify({
            "error": "Недостаточно GAR"
        })

    wallets[sender] -= amount
    wallets[receiver] += amount

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