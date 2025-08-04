from playwright.sync_api import sync_playwright
import time
import datetime

USER_DATA_DIR = "./bdg-session"
BDG_URL = "https://www.bdgbasketball.com//#/saasLottery/WinGo?gameCode=WinGo_30S&lottery=WinGo"

# 🎯 Custom Martingale levels
BET_LEVELS = [1, 2, 4, 9, 18, 37, 76, 155, 311, 625]
MAX_LOSSES = len(BET_LEVELS)

def detect_win(page):
    page.wait_for_selector(".winner_result", timeout=60000)

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

    loss_count = 0
    round_num = 1

    while True:
        if loss_count >= MAX_LOSSES:
            print("🛑 Max losses reached. Stopping.")
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
            break

    browser.close()
