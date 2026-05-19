from flask import Flask, request, redirect, render_template_string
import json
import os
from datetime import datetime

app = Flask(__name__)

DB_FILE = "wallets.json"

ADMIN_PASSWORD = "GAR_Admin_9472"

# ---------------- DATA ----------------

if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        wallets = json.load(f)
else:
    wallets = {}

def save():
    with open(DB_FILE, "w") as f:
        json.dump(wallets, f)

# ---------------- INIT DEFAULT FIELDS ----------------

def ensure_user(name, password=None):
    if name not in wallets:
        wallets[name] = {
            "password": password,
            "balance": 0,
            "tokens": 0,
            "mining_unlocked": False,
            "mined_today": 0,
            "last_day": ""
        }

# ---------------- HTML ----------------

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>GARAGECOIN</title>
<style>
body{background:#111;color:white;font-family:Arial;text-align:center;padding-top:20px}
.box{background:#1e1e1e;width:420px;margin:auto;padding:20px;border-radius:15px}
input,button{width:90%;padding:10px;margin:6px;border-radius:10px;border:none}
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
<p>🎟 Токены: {{tokens}}</p>

<hr>

<h3>🔓 Разблокировка майнинга</h3>

<form method="post" action="/use_token">
<input type="hidden" name="wallet" value="{{wallet}}">
<button>Использовать 1 токен</button>
</form>

{% if mining_unlocked %}
<p>⛏ Майнинг открыт</p>
{% else %}
<p>🔒 Майнинг заблокирован</p>
{% endif %}

<hr>

<h3>⛏ Майнинг</h3>

{% if mining_unlocked %}
<form method="post" action="/mine">
<input type="hidden" name="wallet" value="{{wallet}}">
<button>Майнить 1 GAR</button>
</form>
{% else %}
<button class="lock">🔒 Закрыто</button>
{% endif %}

<p>{{msg}}</p>

<hr>

<h3>💸 Перевод</h3>
<form method="post" action="/send">
<input type="hidden" name="wallet" value="{{wallet}}">
<input name="to" placeholder="Кому">
<input name="amount" type="number" placeholder="Сумма">
<button>Отправить</button>
</form>

{% endif %}
</div>

</body>
</html>
"""

# ---------------- ROUTES ----------------

@app.route("/")
def home():
    return render_template_string(HTML, wallet=None)


@app.route("/login", methods=["POST"])
def login():
    name = request.form["name"]
    password = request.form["password"]

    ensure_user(name, password)

    if wallets[name]["password"] != password:
        return "Неверный пароль"

    return render_template_string(
        HTML,
        wallet=name,
        balance=wallets[name]["balance"],
        tokens=wallets[name]["tokens"],
        mining_unlocked=wallets[name]["mining_unlocked"],
        msg=""
    )


# ---------------- TOKEN USE ----------------

@app.route("/use_token", methods=["POST"])
def use_token():
    wallet = request.form["wallet"]

    if wallets[wallet]["tokens"] <= 0:
        return "Нет токенов"

    wallets[wallet]["tokens"] -= 1
    wallets[wallet]["mining_unlocked"] = True

    save()

    return redirect("/")


# ---------------- MINING ----------------

@app.route("/mine", methods=["POST"])
def mine():
    wallet = request.form["wallet"]

    if not wallets[wallet]["mining_unlocked"]:
        return "🔒 Нужен токен"

    today = datetime.now().strftime("%Y-%m-%d")

    if wallets[wallet]["last_day"] != today:
        wallets[wallet]["mined_today"] = 0
        wallets[wallet]["last_day"] = today

    if wallets[wallet]["mined_today"] >= 10:
        wallets[wallet]["mining_unlocked"] = False
        save()
        return "⛔ Лимит 10 GAR достигнут"

    wallets[wallet]["balance"] += 1
    wallets[wallet]["mined_today"] += 1

    save()
    return redirect("/")


# ---------------- TRANSFER ----------------

@app.route("/send", methods=["POST"])
def send():
    wallet = request.form["wallet"]
    to = request.form["to"]
    amount = int(request.form["amount"])

    if wallet not in wallets or to not in wallets:
        return "Ошибка"

    if wallets[wallet]["balance"] < amount:
        return "Недостаточно средств"

    wallets[wallet]["balance"] -= amount
    wallets[to]["balance"] += amount

    save()
    return redirect("/")


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
