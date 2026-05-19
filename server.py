from flask import Flask, request, jsonify, render_template_string, redirect
import json
import os
import secrets
from datetime import datetime

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
        body {background:#111;color:white;font-family:Arial;text-align:center;padding-top:30px;}
        .box {background:#1e1e1e;width:380px;margin:auto;padding:20px;border-radius:15px;}
        input,button{width:90%;padding:10px;margin:8px;border-radius:10px;border:none}
        button{background:#00aa44;color:white;cursor:pointer}
        button:hover{background:#00cc55}
        .lock{background:#555}
        .info{margin-top:10px}
    </style>
</head>
<body>
<div class="box">
<h1>GARAGECOIN</h1>

{% if not logged_in %}
<h3>Вход / создание</h3>
<form action="/login" method="post">
<input name="name" placeholder="Имя">
<input name="password" type="password" placeholder="Пароль">
<button>Войти</button>
</form>
{% if message %}<div class="info">{{message}}</div>{% endif %}

{% else %}

<h3>Кошелек: {{wallet}}</h3>
<p>Баланс: {{balance}} GAR</p>

<h3>Ваши токены</h3>
<ul>
{% for t in tokens %}
<li>{{t}}</li>
{% endfor %}
</ul>

<h3>Майнинг</h3>
{% if not has_token %}
<button class="lock">🔒 Нужен токен</button>
{% else %}
<form action="/mine" method="post">
<input type="hidden" name="wallet" value="{{wallet}}">
<input type="text" name="token" placeholder="Введите токен">
<button>⛏ Майнить 1 GAR</button>
</form>
{% endif %}

<h3>Перевод</h3>
<form action="/send" method="post">
<input type="hidden" name="sender" value="{{wallet}}">
<input type="hidden" name="password" value="{{password}}">
<input name="receiver" placeholder="Кому">
<input name="amount" type="number" placeholder="Сумма">
<button>Отправить</button>
</form>

{% if message %}<div class="info">{{message}}</div>{% endif %}

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

    if name not in wallets:
        wallets[name] = {
            "password": password,
            "balance": 0,
            "tokens": [],
            "mine_used": 0,
            "last_mine": ""
        }
        save()

    if wallets[name]["password"] != password:
        return render_template_string(HTML, logged_in=False, message="Неверный пароль")

    return render_template_string(HTML,
        logged_in=True,
        wallet=name,
        password=password,
        balance=wallets[name]["balance"],
        tokens=wallets[name]["tokens"],
        has_token=len(wallets[name]["tokens"])>0,
        message="Вход выполнен"
    )

@app.route("/mine", methods=["POST"])
def mine():
    wallet = request.form.get("wallet")
    token = request.form.get("token")

    if wallet not in wallets:
        return redirect("/")

    if token not in wallets[wallet]["tokens"]:
        return render_template_string(HTML,
            logged_in=True,
            wallet=wallet,
            password=wallets[wallet]["password"],
            balance=wallets[wallet]["balance"],
            tokens=wallets[wallet]["tokens"],
            has_token=True,
            message="Неверный токен"
        )

    today = datetime.now().strftime("%Y-%m-%d")

    if wallets[wallet]["last_mine"] != today:
        wallets[wallet]["mine_used"] = 0

    if wallets[wallet]["mine_used"] >= 10:
        return render_template_string(HTML,
            logged_in=True,
            wallet=wallet,
            password=wallets[wallet]["password"],
            balance=wallets[wallet]["balance"],
            tokens=wallets[wallet]["tokens"],
            has_token=True,
            message="Лимит 10 GAR в день достигнут"
        )

    wallets[wallet]["balance"] += 1
    wallets[wallet]["mine_used"] += 1
    wallets[wallet]["last_mine"] = today

    save()

    return render_template_string(HTML,
        logged_in=True,
        wallet=wallet,
        password=wallets[wallet]["password"],
        balance=wallets[wallet]["balance"],
        tokens=wallets[wallet]["tokens"],
        has_token=True,
        message="+1 GAR"
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
        return redirect("/")

    wallets[sender]["balance"] -= amount
    wallets[receiver]["balance"] += amount
    save()

    return redirect("/")

# ADMIN: выдача токена
@app.route("/admin/give_token")
def give_token():
    admin = request.args.get("admin_password")
    user = request.args.get("user")

    if admin != ADMIN_PASSWORD:
        return "no access"

    token = secrets.token_hex(4)

    if user not in wallets:
        return "no user"

    wallets[user]["tokens"].append(token)
    save()

    return jsonify({"user": user, "token": token})

@app.route("/admin/wallets")
def admin_wallets():
    if request.args.get("admin_password") != ADMIN_PASSWORD:
        return "no access"

    return jsonify(wallets)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
