from datetime import timedelta
import json
import os
import random
import sqlite3
import urllib.parse
import urllib.request
from dotenv import load_dotenv
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import stripe

# بارکرنا ژینگەهێ راستەوخۆ ژ هەمان فۆڵدەرا backend
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# 🟢 توکن و چات ئایدییا تلگرامێ ya salar هاتە دانان
TELEGRAM_BOT_TOKEN = "8871442330:AAHj6aldZasBbwCFue8ZvBWfSi5MWlyYlxs"
TELEGRAM_CHAT_ID = "6501596572"

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
app = Flask(__name__, template_folder=base_dir, static_folder=base_dir)
app.secret_key = "salar_bet_secret_key_999"
CORS(app)

# SocketIO بۆ یارییێن کۆمەکانی و ڕاستەوخۆ (Multiplayer Live)
socketio = SocketIO(app, cors_allowed_origins="*")

# Session دێ هەتا 7 رۆژان مینیت
app.permanent_session_lifetime = timedelta(days=7)

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "YOUR_GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv(
    "GOOGLE_CLIENT_SECRET", "YOUR_GOOGLE_CLIENT_SECRET"
)


# 🟢 فانکشنا فرێکرنا زانیاری و وێنەی بۆ تلگرامێ پشکدار دگەل دووگمەیێن شۆشەیی (Inline Buttons)
def send_telegram_notification(caption, deposit_id, photo_path=None):
  try:
    inline_keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "✅ تایید (زیادکردنا پارەی)",
                    "callback_data": f"approve_{deposit_id}",
                },
                {
                    "text": "❌ ڕەتکرنەوە",
                    "callback_data": f"reject_{deposit_id}",
                },
            ]
        ]
    }
    reply_markup = json.dumps(inline_keyboard)

    if photo_path and os.path.exists(photo_path):
      url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
      boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"

      with open(photo_path, "rb") as f:
        file_data = f.read()
        filename = os.path.basename(photo_path)

      body = (
          f"--{boundary}\r\n"
          f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{TELEGRAM_CHAT_ID}\r\n'
          f"--{boundary}\r\n"
          f'Content-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'
          f"--{boundary}\r\n"
          f'Content-Disposition: form-data; name="reply_markup"\r\n\r\n{reply_markup}\r\n'
          f"--{boundary}\r\n"
          f'Content-Disposition: form-data; name="photo";'
          f' filename="{filename}"\r\n'
          f"Content-Type: image/jpeg\r\n\r\n"
      ).encode("utf-8") + file_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

      req = urllib.request.Request(
          url,
          data=body,
          headers={
              "Content-Type": f"multipart/form-data; boundary={boundary}"
          },
      )
      urllib.request.urlopen(req)
    else:
      url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
      data = urllib.parse.urlencode({
          "chat_id": TELEGRAM_CHAT_ID,
          "text": caption,
          "reply_markup": reply_markup,
      }).encode("utf-8")
      req = urllib.request.Request(url, data=data)
      urllib.request.urlopen(req)
  except Exception as e:
    print("TELEGRAM NOTIFICATION ERROR:", str(e))


# ناڤ و باڵانس ل هەمی لاپەڕان دیتن
@app.context_processor
def inject_user():
  user = session.get("username")
  balance = 0.0
  if user:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT balance FROM users WHERE username=?", (user,)
    ).fetchone()
    if row:
      balance = row[0]
    conn.close()
  return dict(username=user, balance=balance)


@app.before_request
def make_session_permanent():
  session.permanent = True


def init_db():
  upload_folder = os.path.join(base_dir, "static", "uploads")
  os.makedirs(upload_folder, exist_ok=True)

  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            password TEXT,
            balance REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS crypto_deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT NOT NULL,
            tx_hash TEXT UNIQUE,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS local_deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            gateway TEXT NOT NULL,
            amount REAL NOT NULL,
            account_num TEXT,
            account_name TEXT,
            receipt_path TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            amount REAL NOT NULL,
            method TEXT NOT NULL,
            account_num TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            home_team TEXT NOT NULL,
            away_team TEXT NOT NULL,
            match_time TEXT NOT NULL,
            home_odds REAL NOT NULL,
            draw_odds REAL NOT NULL,
            away_odds REAL NOT NULL,
            status TEXT DEFAULT 'upcoming',
            result TEXT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS sports_bets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            match_id INTEGER NOT NULL,
            choice TEXT NOT NULL,
            odds REAL NOT NULL,
            amount REAL NOT NULL,
            potential_payout REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (match_id) REFERENCES matches (id)
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS pubg_rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_name TEXT NOT NULL,
            room_id TEXT NOT NULL,
            room_pass TEXT NOT NULL,
            entry_fee REAL DEFAULT 1500.0,
            prize_pool TEXT DEFAULT '1: 50,000 IQD | 2: 25,000 IQD',
            max_players INTEGER DEFAULT 100,
            status TEXT DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS pubg_participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            player_name TEXT NOT NULL,
            pubg_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id) REFERENCES pubg_rooms (id)
        )
    """)

  conn.commit()
  conn.close()


@app.route("/")
def home():
  return render_template("index.html")


# 🟢 ڕووتێ وێبهایتی بۆ وەرگرتنا پشکداریکرنێ و کلیکێن تلگرامێ (Telegram Webhook)
@app.route(f"/telegram/webhook/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
  data = request.get_json(silent=True)
  if not data:
    return "OK", 200

  if "callback_query" in data:
    callback = data["callback_query"]
    callback_id = callback["id"]
    data_str = callback["data"]
    message = callback["message"]
    chat_id = message["chat"]["id"]
    message_id = message["message_id"]

    parts = data_str.split("_")
    action = parts[0]
    deposit_id = parts[1]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    dep_row = cursor.execute(
        "SELECT username, amount, status FROM local_deposits WHERE id = ?",
        (deposit_id,),
    ).fetchone()

    if dep_row:
      username, amount, status = dep_row
      if status == "Approved":
        response_text = "⚠️ ئەڤ داواکارییە پێشتر هاتییە پەسەندکرن!"
      elif status == "Rejected":
        response_text = "⚠️ ئەڤ داواکارییە پێشتر هاتییە ڕەتکرن!"
      else:
        if action == "approve":
          cursor.execute(
              "UPDATE local_deposits SET status = 'Approved' WHERE id = ?",
              (deposit_id,),
          )
          cursor.execute(
              "UPDATE users SET balance = balance + ? WHERE username = ?",
              (amount, username),
          )
          conn.commit()
          response_text = (
              f"✅ ب سەرکەفتیانە! بڕێ {amount} بۆ هەژمارا {username} هاتە"
              " زێدەکرن."
          )
        else:
          cursor.execute(
              "UPDATE local_deposits SET status = 'Rejected' WHERE id = ?",
              (deposit_id,),
          )
          conn.commit()
          response_text = f"❌ داواکارییا {username} ب بڕێ {amount} هاتە ڕەتکرن."

      conn.close()

      # بەرسڤدانا تلگرامێ بۆ لادانا لۆدا دوگمەیی
      answer_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery"
      answer_data = urllib.parse.urlencode({
          "callback_query_id": callback_id,
          "text": response_text,
          "show_alert": True,
      }).encode("utf-8")
      try:
        req = urllib.request.Request(answer_url, data=answer_data)
        urllib.request.urlopen(req)

        # نویڤەکرنا پەیامێ ل تلگرامێ کو هاتییە یەکلاکرن
        edit_url = (
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageCaption"
        )
        new_caption = (
            f"{message.get('caption', '')}\n\n"
            f"───────────────────\nگوهڕین: **{response_text}**"
        )
        edit_data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "message_id": message_id,
            "caption": new_caption,
            "parse_mode": "Markdown",
        }).encode("utf-8")
        urllib.request.urlopen(
            urllib.request.Request(edit_url, data=edit_data)
        )
      except Exception as e:
        print("WEBHOOK ERROR:", str(e))

  return "OK", 200


@app.route("/api/pubg/rooms", methods=["GET"])
def get_pubg_rooms():
  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT id, room_name, entry_fee, prize_pool, max_players, status FROM"
      " pubg_rooms ORDER BY id DESC"
  )
  rows = cursor.fetchall()
  conn.close()

  rooms = []
  for row in rows:
    r_id = row[0]
    conn_sub = sqlite3.connect(DB_PATH)
    p_count = conn_sub.execute(
        "SELECT COUNT(*) FROM pubg_participants WHERE room_id = ?", (r_id,)
    ).fetchone()[0]
    conn_sub.close()
    rooms.append({
        "id": r_id,
        "room_name": row[1],
        "entry_fee": row[2],
        "prize_pool": row[3],
        "max_players": row[4],
        "registered_count": p_count,
        "status": row[5],
    })
  return jsonify(rooms)


@app.route("/api/pubg/join", methods=["POST"])
def join_pubg_room():
  if "username" not in session:
    return jsonify({"status": "error", "message": "تکایە سەرەتا چوو ژوورێ!"}), 401

  data = request.get_json(silent=True) or request.form
  room_id = data.get("room_id")
  player_name = data.get("player_name")
  pubg_id = data.get("pubg_id")
  username = session["username"]

  if not room_id or not player_name or not pubg_id:
    return jsonify({
        "status": "error",
        "message": "تکایە ناڤێ پۆبچی و PUBG ID یا خوە هەردوکان بنڤیسە!",
    }), 400

  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()

  entry_fee = 1500.0
  user_row = cursor.execute(
      "SELECT balance FROM users WHERE username = ?", (username,)
  ).fetchone()

  if not user_row or user_row[0] < entry_fee:
    conn.close()
    return jsonify({
        "status": "error",
        "message": "باڵانسێ تە بەس نینە! تێچوونا ڕۆمێ 1,500 دینارە.",
    }), 400

  exist = cursor.execute(
      "SELECT id FROM pubg_participants WHERE room_id = ? AND username = ?",
      (room_id, username),
  ).fetchone()
  if exist:
    conn.close()
    return jsonify(
        {"status": "error", "message": "تە پێشتر پشکداری د ڤێ ڕۆمێ دا کریە!"}
    ), 400

  new_balance = user_row[0] - entry_fee
  cursor.execute(
      "UPDATE users SET balance = ? WHERE username = ?", (new_balance, username)
  )

  cursor.execute(
      """INSERT INTO pubg_participants (room_id, username, player_name, pubg_id) 
         VALUES (?, ?, ?, ?)""",
      (room_id, username, player_name, pubg_id),
  )
  conn.commit()

  room_info = cursor.execute(
      "SELECT room_id, room_pass FROM pubg_rooms WHERE id = ?", (room_id,)
  ).fetchone()
  conn.close()

  session["balance"] = new_balance
  return jsonify({
      "status": "success",
      "message": "تە ب سەرکەفتیانە پشکداری کر و زانیاریێن ڕۆمێ دیار بوون!",
      "new_balance": new_balance,
      "room_credentials": {
          "room_id": room_info[0] if room_info else "109119",
          "room_pass": room_info[1] if room_info else "salar",
      },
  })


@app.route("/api/pubg/create-room", methods=["POST"])
def create_pubg_room():
  data = request.get_json() or request.form
  room_name = data.get("room_name", "SalarBet Solo Championship")
  r_id = data.get("room_id")
  r_pass = data.get("room_pass")

  if not r_id or not r_pass:
    return jsonify(
        {"status": "error", "message": "Room ID و Password پێدڤی نە!"}
    ), 400

  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()
  cursor.execute(
      """INSERT INTO pubg_rooms (room_name, room_id, room_pass, entry_fee, prize_pool) 
         VALUES (?, ?, ?, 1500.0, '1: 50,000 IQD | 2: 25,000 IQD')""",
      (room_name, r_id, r_pass),
  )
  conn.commit()
  conn.close()

  return jsonify(
      {"status": "success", "message": "ڕۆما پۆبچی ب سەرکەفتن هاتە دروستکرن!"}
  )


@app.route("/get_matches.php", methods=["GET"])
@app.route("/api/matches", methods=["GET"])
def get_matches():
  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT id, home_team, away_team, match_time, home_odds, draw_odds,"
      " away_odds, status FROM matches ORDER BY id DESC"
  )
  rows = cursor.fetchall()
  conn.close()

  matches = []
  for row in rows:
    matches.append({
        "id": row[0],
        "home_team": row[1],
        "away_team": row[2],
        "match_time": row[3],
        "home_odds": row[4],
        "draw_odds": row[5],
        "away_odds": row[6],
        "status": row[7],
    })
  return jsonify(matches)


@app.route("/backend/add_match.php", methods=["POST"])
@app.route("/api/matches/add", methods=["POST"])
def add_match():
  data = request.get_json() or request.form
  home_team = data.get("home_team")
  away_team = data.get("away_team")
  match_time = data.get("match_time")
  home_odds = data.get("home_odds")
  draw_odds = data.get("draw_odds")
  away_odds = data.get("away_odds")

  if not home_team or not away_team or not match_time:
    return jsonify(
        {"status": "error", "message": "تکایە هەموو خانەکان پڕ بکەوە!"}
    ), 400

  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()
  cursor.execute(
      """INSERT INTO matches (home_team, away_team, match_time, home_odds, draw_odds, away_odds, status)
           VALUES (?, ?, ?, ?, ?, ?, 'upcoming')""",
      (home_team, away_team, match_time, home_odds, draw_odds, away_odds),
  )
  conn.commit()
  conn.close()

  return jsonify({
      "status": "success",
      "message": f"یاریا {home_team} 🆚 {away_team} ب سەرکەفتن هاتە زێدەکرن!",
  })


@app.route("/place_bet.php", methods=["POST"])
@app.route("/api/place-bet", methods=["POST"])
def place_sports_bet():
  if "username" not in session:
    return jsonify({"status": "error", "message": "تکایە سەرەتا چوو ژوورێ!"}), 401

  data = request.get_json()
  match_id = data.get("match_id")
  choice = data.get("choice")
  odds = float(data.get("odds", 1.0))
  amount = float(data.get("amount", 0))

  if amount <= 0:
    return jsonify({"status": "error", "message": "بڕی پارە هەڵەیە!"}), 400

  username = session["username"]

  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()

  cursor.execute("SELECT balance FROM users WHERE username = ?", (username,))
  row = cursor.fetchone()

  if not row or row[0] < amount:
    conn.close()
    return jsonify(
        {"status": "error", "message": "باڵانسێ تە بەس نینە بۆ ئەڤ گرەوە!"}
    ), 400

  new_balance = row[0] - amount
  potential_payout = amount * odds

  cursor.execute(
      "UPDATE users SET balance = ? WHERE username = ?", (new_balance, username)
  )
  cursor.execute(
      """INSERT INTO sports_bets (username, match_id, choice, odds, amount, potential_payout)
           VALUES (?, ?, ?, ?, ?, ?)""",
      (username, match_id, choice, odds, amount, potential_payout),
  )
  conn.commit()
  conn.close()

  session["balance"] = new_balance
  return jsonify({
      "status": "success",
      "message": "گرەوی تۆ بە سەرکەوتووی تۆمار کرا!",
      "new_balance": new_balance,
  })


@app.route("/api/user/profile", methods=["GET"])
def get_user_profile_json():
  if "username" not in session:
    return jsonify({"error": "تکایە سەرەتا چوو ژوورێ!"}), 401

  username = session["username"]
  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT id, username, email, balance, created_at FROM users WHERE"
      " username = ?",
      (username,),
  )
  row = cursor.fetchone()
  conn.close()

  if row:
    user_data = {
        "id": row[0],
        "first_name": row[1],
        "last_name": "Bet",
        "username": row[1],
        "email": row[2] or "salardoske1010@gmail.com",
        "balance": row[3],
        "uuid": "1e447124-cc9e-4e3e-a4ae-b033f23a7189",
        "created_at": row[4],
    }
    return jsonify(user_data), 200
  else:
    return jsonify({"error": "بەکارهێنەر نەهاتە دیتن!"}), 404


@app.route("/api/play", methods=["POST"])
def play_game():
  if "username" not in session:
    return jsonify({"error": "تکایە سەرەتا چوو ژوورێ!"}), 401

  data = request.get_json()
  bet_amount = data.get("amount", 10)

  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT balance FROM users WHERE username = ?", (session["username"],)
  )
  row = cursor.fetchone()

  if not row or row[0] < bet_amount:
    conn.close()
    return jsonify({"error": "پارەیێ تە نینە!"}), 400

  current_balance = row[0]
  won = random.choice([True, False])

  if won:
    new_balance = current_balance + bet_amount
    message = f"تە بردەوە! +€{bet_amount}"
  else:
    new_balance = current_balance - bet_amount
    message = f"تە دۆڕاند! -€{bet_amount}"

  cursor.execute(
      "UPDATE users SET balance = ? WHERE username = ?",
      (new_balance, session["username"]),
  )
  conn.commit()
  conn.close()

  session["balance"] = new_balance
  return jsonify({
      "success": True,
      "balance": new_balance,
      "won": won,
      "message": message,
  })


@socketio.on("join")
def handle_join(data):
  username = data.get("username")
  emit(
      "update_chat",
      {"user": "سێرڤەر", "text": f"✨ {username} هاتە ناڤ ژوورا یاریێ!"},
      broadcast=True,
  )


@socketio.on("message")
def handle_message(data):
  username = session.get("username", "یاریزان")
  text = data.get("text")
  emit("update_chat", {"user": username, "text": text}, broadcast=True)


active_rooms = {}


@socketio.on("join_mani_room")
def handle_join_mani_room(data):
  room_id = data.get("roomId", "mani_room_1")
  username = data.get("username")
  players_count = data.get("playersCount", 2)
  table_fee = 200 if players_count == 2 else 400
  bet_amount = data.get("betAmount", 1000)

  from flask_socketio import join_room

  join_room(room_id)

  if room_id not in active_rooms:
    active_rooms[room_id] = {
        "players": [],
        "max_players": players_count,
        "table_fee": table_fee,
        "bet_amount": bet_amount,
        "status": "waiting",
    }

  room = active_rooms[room_id]
  if (
      username not in room["players"]
      and len(room["players"]) < room["max_players"]
  ):
    room["players"].append(username)

  socketio.emit(
      "room_update",
      {
          "message": (
              f"✨ {username} بەشداری مێزا مانی توت بوو! (یاریزان:"
              f" {len(room['players'])}/{room['max_players']})"
          ),
          "players": room["players"],
          "table_fee": room["table_fee"],
          "bet_amount": room["bet_amount"],
          "status": room["status"],
      },
      room=room_id,
  )

  if len(room["players"]) == room["max_players"]:
    room["status"] = "playing"
    socketio.emit(
        "start_mani_game",
        {
            "message": (
                "🃏 مێز پڕ بوو! وەرەقە هاتنە دابەشکرن (14 وەرەقە بۆ هر یاریزانەکی"
                " و 15 بۆ یێ دەت)."
            ),
            "players": room["players"],
        },
        room=room_id,
    )


@app.route("/api/crypto-deposit", methods=["POST"])
def crypto_deposit():
  if "username" not in session:
    return jsonify({"error": "تکایە سەرەتا چوو ژوورێ!"}), 401
  data = request.get_json()
  amount = data.get("amount")
  currency = data.get("currency", "BTC")
  tx_hash = data.get("tx_hash")

  if not amount or not tx_hash:
    return jsonify({"error": "تکایە هەموو خانەکان پڕ بکە!"}), 400

  try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO crypto_deposits (username, amount, currency, tx_hash,"
        " status) VALUES (?, ?, ?, ?, ?)",
        (session["username"], amount, currency, tx_hash, "Pending"),
    )
    conn.commit()
    deposit_id = cursor.lastrowid
    conn.close()

    # 🟢 فرێکرنا نۆتیفیکەیشنێ کریپتۆ بۆ تلگرامێ دگەل ئایدییا دپۆزیتێ
    msg = (
        f"📥 **داخوازیا کریپتۆ (Crypto Deposit)**\n\n👤 بەکارهێنەر:"
        f" {session['username']}\n💰 بڕ: {amount} {currency}\n🔗 TxHash:"
        f" {tx_hash}"
    )
    send_telegram_notification(msg, deposit_id)

    return jsonify({"success": True, "message": "داواکارییا کریپتۆ هاتە ناردن!"})
  except sqlite3.IntegrityError:
    return jsonify(
        {"error": "ئەڤ کۆدی گواستنەوەیە (TxID) پێشتر هاتییە بەکارهینان!"}
    ), 400
  except Exception as e:
    return jsonify({"error": str(e)}), 500


@app.route("/api/create-stripe-session", methods=["POST"])
def create_stripe_session(amount=10):
  try:
    checkout_session = stripe.checkout.sessions.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": "SalarBet Balance Top-up",
                    "description": f"Deposit for user: {session['username']}",
                },
                "amount": int(float(amount) * 100),
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=request.host_url
        + f"api/payment-success?session_id={{CHECKOUT_SESSION_ID}}&amount={amount}",
        cancel_url=request.host_url,
    )
    return checkout_session.url
  except Exception as e:
    print("STRIPE ERROR:", str(e))
    return None


@app.route("/api/process-deposit", methods=["POST"])
def process_deposit():
  if "username" not in session:
    return jsonify({"error": "تکایە پێشتر چوونا ژوورێ بکە!"}), 401

  gateway = request.form.get("gateway")
  amount = request.form.get("amount")

  if not amount or not gateway:
    return jsonify({"error": "بڕێ پارەی و رێگە پێدڤی نە!"}), 400

  if gateway == "Stripe":
    stripe_url = create_stripe_session(amount)
    if stripe_url:
      return jsonify({"url": stripe_url})
    else:
      return jsonify({"error": "کێشەیەک لە دروستکرنالینکێ Stripe هەیە!"}), 500

  try:
    account_num = None
    account_name = None
    receipt_relative_path = None
    full_receipt_path = None

    receipt_file = request.files.get("receipt")
    if receipt_file and receipt_file.filename != "":
      upload_folder = os.path.join(base_dir, "static", "uploads")
      os.makedirs(upload_folder, exist_ok=True)
      filename = f"{session['username']}_{receipt_file.filename}"
      full_receipt_path = os.path.join(upload_folder, filename)
      receipt_file.save(full_receipt_path)
      receipt_relative_path = f"static/uploads/{filename}"

    if gateway == "FIB":
      account_num = request.form.get("fib_phone")
      account_name = request.form.get("fib_name")
    elif gateway == "ZainCash":
      account_num = request.form.get("account")
    elif gateway in ["Korak", "Asiacell"]:
      account_num = request.form.get("code")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO local_deposits 
           (username, gateway, amount, account_num, account_name, receipt_path, status) 
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            session["username"],
            gateway,
            amount,
            account_num,
            account_name,
            receipt_relative_path,
            "Pending",
        ),
    )
    conn.commit()
    deposit_id = cursor.lastrowid
    conn.close()

    # 🟢 فرێکرنا ڕاستەوخۆ یا زانیاری و وێنەی دگەل دووگمەیێن پەسەندکرنێ بۆ تلگرامێ
    telegram_caption = (
        f"📥 **داخوازیا پرکرنا باڵانسی (Deposit)**\n\n"
        f"👤 ناڤێ بەکارهێنەری: {session['username']}\n"
        f"💳 ڕێک: {gateway}\n"
        f"💵 بڕ: {amount}\n"
        f"📞 ژمارە/کۆد: {account_num or 'دیار نینە'}\n"
        f"👤 ناڤێ هەژمارێ: {account_name or 'دیار نینە'}"
    )
    send_telegram_notification(telegram_caption, deposit_id, full_receipt_path)

    return jsonify({
        "success": True,
        "message": (
            f"داخوازیا پڕکرنا بڕێ {amount} ب ڕێکا {gateway} هاتە وەرگرتن و د"
            " زووترین دەمدا دێ هێتە پشتراستکرن!"
        ),
    })
  except Exception as e:
    print("DEPOSIT ERROR:", str(e))
    return jsonify({"error": str(e)}), 500


@app.route("/api/withdraw", methods=["POST"])
def request_withdrawal():
  if "username" not in session:
    return jsonify({"error": "تکایە سەرەتا چوو ژوورێ!"}), 401

  data = request.get_json()
  amount = data.get("amount")
  method = data.get("method")
  account_num = data.get("accountNum")

  if not amount or not method or not account_num:
    return jsonify({"error": "تکایە هەموو خانەکان پڕ بکە!"}), 400

  try:
    amount = float(amount)
  except ValueError:
    return jsonify({"error": "بڕێ پارەی هەڵەیە!"}), 400

  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()

  row = cursor.execute(
      "SELECT balance FROM users WHERE username = ?", (session["username"],)
  ).fetchone()
  if not row or row[0] < amount:
    conn.close()
    return jsonify({"error": "باڵانسێ تە بس نینە بۆ ڤی ڤەکێشانێ!"}), 400

  current_balance = row[0]
  new_balance = current_balance - amount

  try:
    cursor.execute(
        "UPDATE users SET balance = ? WHERE username = ?",
        (new_balance, session["username"],),
    )
    cursor.execute(
        "INSERT INTO withdrawals (username, amount, method, account_num,"
        " status) VALUES (?, ?, ?, ?, ?)",
        (session["username"], amount, method, account_num, "Pending"),
    )
    conn.commit()
    withdrawal_id = cursor.lastrowid
    conn.close()

    # 🟢 فرێکرنا ئاگەهداریا ڕاکێشانا پارەی بۆ تلگرامێ
    msg = (
        f"📤 **داخوازیا ڤەکێشانا پارەی (Withdrawal)**\n\n"
        f"👤 بەکارهێنەر: {session['username']}\n"
        f"💵 بڕ: ${amount}\n"
        f"💳 ڕێک: {method}\n"
        f"📞 ژمارە: {account_num}"
    )
    send_telegram_notification(msg, withdrawal_id)

    session["balance"] = new_balance
    return jsonify({
        "success": True,
        "balance": new_balance,
        "message": (
            f"داخوازیا ڤەکێشانێ ب بڕێ ${amount} ب ڕێکا {method} هاتە ناردن و د"
            " زووترین دەمدا دێ هێتە پشتراستکرن!"
        ),
    })
  except Exception as e:
    conn.close()
    return jsonify({"error": str(e)}), 500


@app.route("/api/payment-success")
def payment_success():
  amount = request.args.get("amount", type=float, default=0)
  user = session.get("username")

  if user and amount > 0:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET balance = balance + ? WHERE username = ?",
        (amount, user),
    )
    conn.commit()
    conn.close()

  return redirect("/")


@app.route("/auth/google")
def google_login():
  redirect_uri = url_for("google_authorize", _external=True)
  google_auth_url = (
      "https://accounts.google.com/o/oauth2/v2/auth?"
      f"client_id={GOOGLE_CLIENT_ID}&redirect_uri={redirect_uri}&response_type=code&scope=openid"
      " email profile"
  )
  return redirect(google_auth_url)


@app.route("/auth/google/callback")
def google_authorize():
  code = request.args.get("code")
  if not code:
    return "گەنگەشە یا هەڵەیە یاخود هاتییە رەتکرن!", 400

  redirect_uri = url_for("google_authorize", _external=True)
  token_url = "https://oauth2.googleapis.com/token"
  payload = urllib.parse.urlencode({
      "code": code,
      "client_id": GOOGLE_CLIENT_ID,
      "client_secret": GOOGLE_CLIENT_SECRET,
      "redirect_uri": redirect_uri,
      "grant_type": "authorization_code",
  }).encode("utf-8")

  try:
    req = urllib.request.Request(token_url, data=payload, method="POST")
    with urllib.request.urlopen(req) as response:
      res_data = json.loads(response.read().decode("utf-8"))
      access_token = res_data.get("access_token")

    userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    req_info = urllib.request.Request(
        userinfo_url, headers={"Authorization": f"Bearer {access_token}"}
    )
    with urllib.request.urlopen(req_info) as response:
      user_info = json.loads(response.read().decode("utf-8"))

    email = user_info.get("email")
    name = user_info.get("name") or email.split("@")[0]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    user_row = cursor.execute(
        "SELECT username FROM users WHERE email = ? OR username = ?",
        (email, name),
    ).fetchone()

    if not user_row:
      cursor.execute(
          "INSERT INTO users (username, email, password, balance) VALUES (?,"
          " ?, ?, ?)",
          (name, email, "GOOGLE_AUTH_USER", 0.0),
      )
      conn.commit()
      username = name
    else:
      username = user_row[0]

    conn.close()
    session["username"] = username
    return redirect("/")
  except Exception as e:
    return f"خەلەت د پڕۆسێسا گۆگلی دا: {str(e)}", 500


@app.route("/api/register", methods=["POST"])
def register_user():
  username = request.form.get("username")
  email = request.form.get("email")
  password = request.form.get("password")
  if not username or not password or not email:
    return "هەموو خانە پێدڤی نە!", 400

  try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, email, password, balance) VALUES (?, ?,"
        " ?, ?)",
        (username, email, password, 0.0),
    )
    conn.commit()
    conn.close()
  except sqlite3.IntegrityError:
    return (
        "ئەڤ ناڤە یان ئیمەیلە یێ هەی، تکایە یەکێ دی هەلبژێرە! <a"
        " href='/'>زڤڕەڤە</a>"
    ), 400

  session["username"] = username
  return redirect("/")


@app.route("/api/login", methods=["POST"])
def login_user():
  username = request.form.get("username")
  password = request.form.get("password")
  conn = sqlite3.connect(DB_PATH)
  user_row = conn.execute(
      "SELECT balance FROM users WHERE username = ? AND password = ?",
      (username, password),
  ).fetchone()
  conn.close()

  if user_row:
    session["username"] = username
    return redirect("/")
  return "ناڤ یان پاسوورد هەڵەیە! <a href='/'>زڤڕەڤە</a>", 401


@app.route("/logout")
def logout():
  session.clear()
  return redirect("/")


@app.route("/css/<path:filename>")
def serve_css(filename):
  return send_from_directory(os.path.join(base_dir, "css"), filename)


@app.route("/js/<path:filename>")
def serve_js(filename):
  return send_from_directory(os.path.join(base_dir, "js"), filename)


@app.route("/img/<path:filename>")
def serve_img(filename):
  return send_from_directory(os.path.join(base_dir, "img"), filename)


@app.route("/<path:page_name>")
def render_html_page(page_name):
  return render_template(page_name)


if __name__ == "__main__":
  init_db()
  socketio.run(app, host="0.0.0.0", port=5001, debug=True)
