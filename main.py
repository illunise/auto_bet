from playwright.sync_api import sync_playwright
import time
import requests
import threading
import datetime

USER_DATA_DIR = "./bdg-session"
BDG_URL = "https://www.bdgbasketball.com//#/saasLottery/WinGo?gameCode=WinGo_30S&lottery=WinGo"

# 🎯 Custom Martingale levels
BET_LEVELS = [1, 2, 4, 9, 18, 37, 76, 155, 311, 625]
MAX_LOSSES = len(BET_LEVELS)

# === Telegram Setup ===
BOT_TOKEN = "8448605132:AAE5wP99MmTvm6CU55WKURrFhf8mCm83S_U"  # Replace with your token
CHAT_ID = "7244803677"      # Replace with your chat/user ID

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        requests.post(url, data=data)
        print("📩 Telegram alert sent.")
    except Exception as e:
        print(f"❌ Failed to send Telegram message: {e}")

def telegram_command_listener(page):
    def get_updates(offset=None):
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        params = {"timeout": 30}
        if offset:
            params["offset"] = offset
        response = requests.get(url, params=params)
        return response.json().get("result", [])

    last_update_id = None
    print("📡 Telegram command listener started.")

    while True:
        try:
            updates = get_updates(offset=last_update_id)
            for update in updates:
                last_update_id = update["update_id"] + 1

                message = update.get("message", {})
                text = message.get("text", "")
                chat_id = message.get("chat", {}).get("id")

                if str(chat_id) != CHAT_ID:
                    continue  # Ignore messages not from you

                if text.lower() == "/balance":
                    try:
                        page.reload()
                        page.wait_for_selector(".Wallet_C-balance-11", timeout=10000)
                        balance_text = page.locator(".Wallet_C-balance-11 div").nth(0).text_content().strip()
                        send_telegram_message(f"💰 Current balance: {balance_text}")
                    except Exception as balance_error:
                        send_telegram_message(f"❌ Failed to fetch balance:\n<code>{balance_error}</code>")

        except Exception as e:
            print("❌ Telegram command listener error:", e)
            send_telegram_message(f"❌ Telegram command listener error:\n<code>{e}</code>")
            time.sleep(10)

def get_balance(page):
    try:
        page.wait_for_selector(".Wallet_C-balance-11 div", timeout=50000)
        balance_text = page.locator(".Wallet_C-balance-11 div").nth(1).text_content().strip()
        return balance_text
    except:
        return "❌ Unable to fetch balance."

def detect_win(page):
    page.wait_for_selector(".winner_result", timeout=40000)

    # Extract number and type
    result_number = page.locator(".winner_result div").nth(1).text_content().strip()
    result_type = page.locator(".winner_result div").nth(2).text_content().strip()

    print(f"🎯 Result: {result_number} ({result_type})")

    return result_type.lower() == "small"

def place_bet(page, amount):
    print(f"\n💸 Placing ₹{amount} on SMALL")

    # Click SMALL
    page.wait_for_selector(".Betting__C-foot-s", timeout=15000)
    page.click(".Betting__C-foot-s")

    # Input amount
    input_box = page.locator("input[type='number']")
    input_box.fill("")  # Clear
    input_box.type(str(amount))

    # Click Bet button (SMALL)
    page.wait_for_selector(".bet-amount.n_small", timeout=10000)
    page.click(".bet-amount.n_small")

    print("✅ Bet submitted.")

def close_result_popup(page):
    try:
        page.wait_for_selector(".closeBtn", timeout=5000)
        page.click(".closeBtn")
        print("🧹 Closed result popup.")
    except:
        print("⚠️ closeBtn not found or already closed.")

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(USER_DATA_DIR, headless=False)
    page = browser.new_page()
    page.goto(BDG_URL)
    print("🌐 Logged in and page loaded.")
    send_telegram_message("🚀 BDG bot started and is now running.")

    # 🧵 Start Telegram command listener thread
    threading.Thread(target=telegram_command_listener, args=(page,), daemon=True).start()


    loss_count = 0
    round_num = 1

    while True:
        if loss_count >= MAX_LOSSES:
            print("🛑 Max losses reached. Stopping.")
            send_telegram_message("🛑 BDG bot stopped after reaching max loss streak.")
            break

        current_bet = BET_LEVELS[loss_count]
        print(f"\n📊 ROUND {round_num} | 💰 Bet Amount: ₹{current_bet} | ❌ Loss Streak: {loss_count}")

        try:
            place_bet(page, current_bet)

            print("⏳ Waiting for result...")
            page.wait_for_selector(".winner_result", timeout=60000)

            if detect_win(page):
                print("🎉 ✅ WIN! Resetting to base level. Waiting 50s before next round...")
                loss_count = 0
            else:
                print("💀 ❌ LOSS! Moving to next bet level.")
                loss_count += 1

            time.sleep(5)

            close_result_popup(page)
            round_num += 1

        except Exception as e:
            print("🚨 Unexpected error:", e)
            send_telegram_message(f"🚨 BDG bot crashed with error:\n<code>{e}</code>")
            break

    browser.close()
