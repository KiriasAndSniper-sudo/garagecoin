from flask import Flask, request, redirect, render_template_string, session
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "garagecoin_secret_key_123"

DB_FILE = "wallets.json"
ADMIN_PASSWORD = "GAR_Admin_9472"

# ---------------- DATA ----------------

if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        wallets = json.load(f)
else:
    wallets = {}

admin_attempts = {}

def save():
    with open(DB_FILE, "w") as f:
        json.dump(wallets, f)


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

.top{
position:absolute;
top:10px;
right:10px;
width:160px;
}
</style>
</head>
<body>

<div class="box">

{% if wallet %}

<div class="top">

<form method="post" action="/admin_login">
<input type="hidden" name="wallet" value="{{wallet}}">
<input name="password" placeholder="Admin">
<button>👑 Admin</button>
</form>

<a href="/logout" style="color:white">🚪 Logout</a>

</div>

{% endif %}

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
<p>💰 Баланс: {{balance}} GAR</p>
<p>🎟 Токены: {{tokens}}</p>

<hr>

<h3>🔓 Майнинг</h3>

<form method="post" action="/use_token">
<input type="hidden" name="wallet" value="{{wallet}}">
<button>Использовать 1 токен</button>
</form>

{% if mining_unlocked %}
<p>⛏ Майнинг открыт</p>
{% else %}
<p>🔒 Майнинг закрыт</p>
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

# ---------------- HOME ----------------

@app.route("/")
def home():
    if "user" not in session:
        return render_template_string(HTML, wallet=None)

    user = session["user"]
    w = wallets[user]

    return render_template_string(
        HTML,
        wallet=user,
        balance=w["balance"],
        tokens=w["tokens"],
        mining_unlocked=w["mining_unlocked"]
    )

# ---------------- LOGIN ----------------

@app.route("/login", methods=["POST"])
def login():
    name = request.form["name"]
    password = request.form["password"]

    ensure_user(name, password)

    if wallets[name]["password"] != password:
        return "Неверный пароль"

    session["user"] = name
    session["admin"] = False

    return redirect("/")

# ---------------- LOGOUT (FIXED) ----------------

@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("admin", None)
    return redirect("/")

# ---------------- ADMIN LOGIN ----------------

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
        return "⛔ Нет попыток сегодня"

    if password != ADMIN_PASSWORD:
        admin_attempts[wallet]["tries"] += 1
        return "❌ Неверный пароль"

    wallets[wallet]["mining_unlocked"] = True
    save()

    session["user"] = wallet
    session["admin"] = True

    return redirect("/admin_panel")

# ---------------- ADMIN PANEL ----------------

@app.route("/admin_panel")
def admin_panel():
    if "user" not in session:
        return "Not logged in"

    if not session.get("admin", False):
        return "No admin access"

    return render_template_string("""
    <h1 style="color:white">👑 ADMIN PANEL</h1>
    <a href="/" style="color:white">← back</a>
    <hr>

    {% for name, data in wallets.items() %}
        <div style="background:#222;padding:10px;margin:10px;color:white;border-radius:10px">
            <b>{{name}}</b><br>
            💰 Balance: {{data["balance"]}}<br>
            🎟 Tokens: {{data["tokens"]}}<br>
            ⛏ Mining: {{data["mining_unlocked"]}}

            <form method="post" action="/give_token">
                <input type="hidden" name="wallet" value="{{name}}">
                <button>🎟 Выдать токен</button>
            </form>
        </div>
    {% endfor %}
    """, wallets=wallets)

# ---------------- GIVE TOKEN ----------------

@app.route("/give_token", methods=["POST"])
def give_token():
    if not session.get("admin", False):
        return "No admin access"

    wallet = request.form["wallet"]

    if wallet not in wallets:
        return "Wallet not found"

    wallets[wallet]["tokens"] += 1
    save()

    return redirect("/admin_panel")

# ---------------- USE TOKEN ----------------

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
        return "🔒 Нужен токен или админ"

    today = datetime.now().strftime("%Y-%m-%d")

    if wallets[wallet]["last_day"] != today:
        wallets[wallet]["mined_today"] = 0
        wallets[wallet]["last_day"] = today

    if wallets[wallet]["mined_today"] >= 10:
        wallets[wallet]["mining_unlocked"] = False
        save()
        return "⛔ Лимит 10 GAR"

    wallets[wallet]["balance"] += 1
    wallets[wallet]["mined_today"] += 1

    save()
    return redirect("/")

# ---------------- SEND ----------------

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
