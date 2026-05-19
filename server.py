from flask import Flask, request, redirect, render_template_string
import json
import os
from datetime import datetime

app = Flask(__name__)

DB_FILE = "wallets.json"
ADMIN_PASSWORD = "GAR_Admin_9472"

# ------------------ DATA ------------------

if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        wallets = json.load(f)
else:
    wallets = {}

admin_attempts = {}       # {wallet: {"date": "...", "tries": 0}}
admin_logged = {}         # {wallet: True/False}


def save():
    with open(DB_FILE, "w") as f:
        json.dump(wallets, f)


# ------------------ HTML ------------------

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>GARAGECOIN</title>
    <style>
        body{background:#111;color:white;font-family:Arial;text-align:center;padding-top:30px}
        .box{background:#1e1e1e;width:400px;margin:auto;padding:20px;border-radius:15px}
        input,button{width:90%;padding:10px;margin:8px;border-radius:10px;border:none}
        button{background:#00aa44;color:white;cursor:pointer}
        button:hover{background:#00cc55}
        .lock{background:#555}
    </style>
</head>
<body>
<div class="box">
<h1>GARAGECOIN</h1>

{% if not wallet %}
<h3>Вход / Создание</h3>
<form method="post" action="/login">
<input name="name" placeholder="Имя">
<input name="password" type="password" placeholder="Пароль">
<button>Войти</button>
</form>
{% else %}

<h3>Кошелек: {{wallet}}</h3>
<p>Баланс: {{balance}} GAR</p>

<hr>

<!-- ADMIN LOGIN -->
{% if not is_admin %}
<h3>Админ доступ</h3>
<form method="post" action="/admin_login">
<input type="hidden" name="wallet" value="{{wallet}}">
<input name="password" placeholder="Админ пароль">
<button>Войти как администратор</button>
</form>
<p>{{admin_msg}}</p>
{% else %}
<p>👑 Админ активирован</p>
{% endif %}

<hr>

<!-- MINING -->
<h3>Майнинг</h3>

{% if not is_admin %}
<button class="lock">🔒 Заблокировано (нужен админ)</button>
{% else %}
<form method="post" action="/mine">
<input type="hidden" name="wallet" value="{{wallet}}">
<button>⛏ Майнить 1 GAR</button>
</form>
{% endif %}

<p>{{msg}}</p>

<hr>

<!-- TRANSFER -->
<h3>Перевод</h3>
<form method="post" action="/send">
<input type="hidden" name="wallet" value="{{wallet}}">
<input type="text" name="to" placeholder="Кому">
<input type="number" name="amount" placeholder="Сумма">
<button>Отправить</button>
</form>

{% endif %}
</div>
</body>
</html>
"""


# ------------------ ROUTES ------------------

@app.route("/")
def home():
    return render_template_string(HTML, wallet=None)


@app.route("/login", methods=["POST"])
def login():
    name = request.form["name"]
    password = request.form["password"]

    if name not in wallets:
        wallets[name] = {
            "password": password,
            "balance": 0,
            "mined_today": 0,
            "last_day": ""
        }
        save()

    if wallets[name]["password"] != password:
        return render_template_string(HTML, wallet=None)

    return render_template_string(
        HTML,
        wallet=name,
        balance=wallets[name]["balance"],
        is_admin=admin_logged.get(name, False),
        msg="Вход выполнен",
        admin_msg=""
    )


# ------------------ ADMIN ------------------

@app.route("/admin_login", methods=["POST"])
def admin_login():
    wallet = request.form["wallet"]
    password = request.form["password"]

    today = datetime.now().strftime("%Y-%m-%d")

    if wallet not in admin_attempts:
        admin_attempts[wallet] = {"date": today, "tries": 0}

    if admin_attempts[wallet]["date"] != today:
        admin_attempts[wallet] = {"date": today, "tries": 0}

    if admin_attempts[wallet]["tries"] >= 2:
        return "⛔ Нет попыток на сегодня"

    if password != ADMIN_PASSWORD:
        admin_attempts[wallet]["tries"] += 1
        return f"❌ Неверно. Осталось: {2 - admin_attempts[wallet]['tries']}"

    admin_logged[wallet] = True

    return redirect("/")


# ------------------ MINING ------------------

@app.route("/mine", methods=["POST"])
def mine():
    wallet = request.form["wallet"]

    if wallet not in wallets:
        return redirect("/")

    if not admin_logged.get(wallet, False):
        return "🔒 Майнинг закрыт"

    today = datetime.now().strftime("%Y-%m-%d")

    if wallets[wallet]["last_day"] != today:
        wallets[wallet]["mined_today"] = 0
        wallets[wallet]["last_day"] = today

    if wallets[wallet]["mined_today"] >= 10:
        return "⛔ Лимит 10 GAR в день"

    wallets[wallet]["balance"] += 1
    wallets[wallet]["mined_today"] += 1

    save()

    return redirect("/")


# ------------------ TRANSFER ------------------

@app.route("/send", methods=["POST"])
def send():
    wallet = request.form["wallet"]
    to = request.form["to"]
    amount = int(request.form["amount"])

    if wallet not in wallets or to not in wallets:
        return redirect("/")

    if wallets[wallet]["balance"] < amount:
        return "Недостаточно средств"

    wallets[wallet]["balance"] -= amount
    wallets[to]["balance"] += amount

    save()

    return redirect("/")


# ------------------ RUN ------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
