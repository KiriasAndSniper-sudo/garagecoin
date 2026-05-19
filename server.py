from flask import Flask, request, jsonify, render_template_string, redirect
import json
import os

app = Flask(__name__)

DB_FILE = "wallets.json"
ADMIN_PASSWORD = "GAR_Admin_9472"

if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        wallets = json.load(f)
else:
    wallets = {}


def save():
    with open(DB_FILE, "w") as f:
        json.dump(wallets, f)


HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>GARAGECOIN</title>
    <style>
        body {
            background: #111;
            color: white;
            font-family: Arial;
            text-align: center;
            padding-top: 40px;
        }

        .box {
            background: #1e1e1e;
            width: 350px;
            margin: auto;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 0 20px black;
        }

        input {
            width: 90%;
            padding: 10px;
            margin: 10px;
            border-radius: 10px;
            border: none;
        }

        button {
            background: #00aa44;
            color: white;
            border: none;
            padding: 12px;
            width: 95%;
            border-radius: 10px;
            cursor: pointer;
            margin-top: 10px;
        }

        button:hover {
            background: #00cc55;
        }

        .info {
            margin-top: 20px;
            font-size: 18px;
        }
    </style>
</head>
<body>

<div class="box">
    <h1>GARAGECOIN</h1>

    {% if not logged_in %}

    <h3>Войти или создать кошелек</h3>

    <form action="/login" method="post">
        <input type="text" name="name" placeholder="Имя кошелька" required>
        <input type="password" name="password" placeholder="Пароль" required>
        <button type="submit">Войти</button>
    </form>

    {% if message %}
    <div class="info">{{ message }}</div>
    {% endif %}

    {% else %}

    <h2>Кошелек: {{ wallet }}</h2>

    <div class="info">
        Баланс: {{ balance }} GAR
    </div>

    <h3>Перевод GAR</h3>

    <form action="/send" method="post">
        <input type="hidden" name="sender" value="{{ wallet }}">
        <input type="hidden" name="password" value="{{ password }}">

        <input type="text" name="receiver" placeholder="Кому перевести" required>
        <input type="number" name="amount" placeholder="Количество GAR" required>

        <button type="submit">Перевести</button>
    </form>

    {% if message %}
    <div class="info">{{ message }}</div>
    {% endif %}

    {% endif %}
</div>

</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML, logged_in=False, message="")


@app.route("/login", methods=["POST"])
def login():

    name = request.form.get("name")
    password = request.form.get("password")

    if len(password) < 8 or len(password) > 12:
        return render_template_string(
            HTML,
            logged_in=False,
            message="Пароль должен быть от 8 до 12 символов"
        )

    if name not in wallets:

        wallets[name] = {
            "password": password,
            "balance": 0
        }

        save()

        return render_template_string(
            HTML,
            logged_in=True,
            wallet=name,
            password=password,
            balance=0,
            message="Кошелек создан"
        )

    if wallets[name]["password"] != password:
        return render_template_string(
            HTML,
            logged_in=False,
            message="Неверный пароль"
        )

    return render_template_string(
        HTML,
        logged_in=True,
        wallet=name,
        password=password,
        balance=wallets[name]["balance"],
        message="Вход выполнен"
    )


@app.route("/send", methods=["POST"])
def send():

    sender = request.form.get("sender")
    password = request.form.get("password")
    receiver = request.form.get("receiver")
    amount = int(request.form.get("amount"))

    if sender not in wallets:
        return redirect("/")

    if wallets[sender]["password"] != password:
        return redirect("/")

    if receiver not in wallets:
        return render_template_string(
            HTML,
            logged_in=True,
            wallet=sender,
            password=password,
            balance=wallets[sender]["balance"],
            message="Кошелек получателя не найден"
        )

    if wallets[sender]["balance"] < amount:
        return render_template_string(
            HTML,
            logged_in=True,
            wallet=sender,
            password=password,
            balance=wallets[sender]["balance"],
            message="Недостаточно GAR"
        )

    wallets[sender]["balance"] -= amount
    wallets[receiver]["balance"] += amount

    save()

    return render_template_string(
        HTML,
        logged_in=True,
        wallet=sender,
        password=password,
        balance=wallets[sender]["balance"],
        message="Перевод выполнен"
    )


@app.route("/admin/wallets")
def admin_wallets():

    admin_password = request.args.get("admin_password")

    if admin_password != ADMIN_PASSWORD:
        return jsonify({
            "error": "Неверный админ пароль"
        })

    return jsonify(wallets)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
