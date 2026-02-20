"""
מודול שליפת נתונים מ-FinBot Edge
"""
import time, json, os, re, tempfile
from bs4 import BeautifulSoup

MONTH_NAMES_HE = [
    'ינואר','פברואר','מרץ','אפריל','מאי','יוני',
    'יולי','אוגוסט','ספטמבר','אוקטובר','נובמבר','דצמבר',
]

FINBOT_URL = os.environ.get("FINBOT_URL", "https://oha.finbot-edge.co.il")
USERNAME   = os.environ["FINBOT_USERNAME"]
PASSWORD   = os.environ["FINBOT_PASSWORD"]

# עמוד דוח רווח והפסד (URL קבוע — הלקוח נבחר מהדרופדאון)
PNL_URL = FINBOT_URL + "/report/2"


def get_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1400,900")
    opts.add_argument("--disable-notifications")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opts)


def wait_for(driver, css, timeout=20):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, css))
    )


def save_debug_screenshot(driver, step_name):
    """שומר screenshot לאבחון בעיות — מדפיס נתיב לקובץ."""
    try:
        path = os.path.join(tempfile.gettempdir(), f"finbot_{step_name}.png")
        driver.save_screenshot(path)
        print(f"[DEBUG screenshot] {path}")
    except Exception as e:
        print(f"[DEBUG screenshot failed] {e}")


def login(driver):
    from selenium.webdriver.common.by import By
    print("[FinBot] מתחבר...")
    driver.get(FINBOT_URL)
    wait_for(driver, "input[name='email']")
    driver.find_element(By.CSS_SELECTOR, "input[name='email']").send_keys(USERNAME)
    driver.find_element(By.CSS_SELECTOR, "input[name='password']").send_keys(PASSWORD)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(5)
    if "dashboard" not in driver.current_url and "report" not in driver.current_url:
        save_debug_screenshot(driver, "login_failed")
        raise RuntimeError("כניסה נכשלה — בדוק פרטי התחברות")
    print("[FinBot] כניסה הצליחה")


def _open_client_dropdown(driver):
    """פותח את דרופדאון הלקוחות ומחזיר את שדה הקלט."""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys

    client_input = wait_for(driver, "input[placeholder='לקוח / שם חברה / מ.ע ']")
    client_input.click()
    time.sleep(1)
    client_input.send_keys(Keys.CONTROL + "a")
    client_input.send_keys(Keys.DELETE)
    time.sleep(2)
    return client_input


def _select_client(driver, data_id, biz_name=""):
    """בוחר לקוח לפי data-option-index, ואם לא נמצא — לפי שם עסק."""
    from selenium.webdriver.common.by import By
    from selenium.common.exceptions import StaleElementReferenceException

    print(f"[FinBot] בוחר לקוח data_id={data_id} biz_name={biz_name!r}")
    _open_client_dropdown(driver)
    time.sleep(1)

    # ניסיון 1: שאילתה ישירה לפי data-option-index — מונעת stale reference לחלוטין
    try:
        el = driver.find_element(
            By.CSS_SELECTOR, f"li[role='option'][data-option-index='{data_id}']"
        )
        driver.execute_script("arguments[0].click();", el)
        time.sleep(2)
        print(f"[FinBot] לקוח נבחר (index direct)")
        return True
    except Exception:
        pass

    # ניסיון 2: fallback לפי שם עסק עם retry לטיפול ב-stale elements
    if biz_name:
        for attempt in range(3):
            try:
                options = driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
                target_idx = None
                for i, el in enumerate(options):
                    try:
                        el_text = el.text.split("\n")[0].strip()
                        if biz_name.strip() in el_text or el_text in biz_name.strip():
                            target_idx = i
                            break
                    except StaleElementReferenceException:
                        target_idx = None
                        break
                if target_idx is not None:
                    # שאילתה מחדש ממש לפני הקליק למניעת stale reference
                    fresh = driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
                    if target_idx < len(fresh):
                        driver.execute_script("arguments[0].click();", fresh[target_idx])
                        time.sleep(2)
                        print(f"[FinBot] לקוח נבחר (שם): {biz_name}")
                        return True
                break  # לא נמצא התאמה — אין טעם לנסות שוב
            except StaleElementReferenceException:
                print(f"[FinBot] stale element, retry {attempt + 1}/3")
                time.sleep(1)
                if attempt < 2:
                    _open_client_dropdown(driver)
                    time.sleep(1)

    save_debug_screenshot(driver, "client_not_found")
    print(f"[WARN] לקוח data_id={data_id} / biz_name={biz_name!r} לא נמצא ברשימה")
    return False


def _select_year(driver, year):
    """בוחר שנה מהקומבובוקס המתאים (מדלג על שדה הלקוח)."""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys

    print(f"[FinBot] בוחר שנה {year}")
    combos = driver.find_elements(By.CSS_SELECTOR, "input[role='combobox']")

    for combo in combos:
        placeholder = combo.get_attribute("placeholder") or ""
        # מדלג על שדה הלקוח
        if "לקוח" in placeholder or "חברה" in placeholder or "מ.ע" in placeholder:
            continue
        val = combo.get_attribute("value") or ""
        if val.isdigit() and len(val) == 4:
            if val == year:
                print(f"[FinBot] שנה {year} כבר בחורה")
                return True
            combo.click()
            time.sleep(1)
            combo.send_keys(Keys.CONTROL + "a")
            combo.send_keys(year)
            time.sleep(1.5)
            opts = driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
            for o in opts:
                if year in o.text:
                    o.click()
                    time.sleep(1.5)
                    print(f"[FinBot] שנה {year} נבחרה")
                    return True

    print(f"[WARN] לא נמצא קומבובוקס לשנה — ממשיך עם ברירת מחדל")
    return False


def _try_monthly_view(driver):
    """מפעיל תצוגת 'לפי חודש'. מנסה מספר אסטרטגיות."""
    from selenium.webdriver.common.by import By

    print("[FinBot] מחפש כפתור 'לפי חודש'...")

    # אסטרטגיה 1: radio button עם value חודש
    for css in [
        "input[type='radio'][value='monthly']",
        "input[type='radio'][value='month']",
        "input[type='radio'][value='MONTHLY']",
        "input[type='radio'][value='חודשי']",
    ]:
        try:
            els = driver.find_elements(By.CSS_SELECTOR, css)
            for el in els:
                if el.is_selected():
                    print("[FinBot] 'לפי חודש' כבר בחור (radio)")
                    return True
                driver.execute_script("arguments[0].click();", el)
                time.sleep(1.5)
                print("[FinBot] 'לפי חודש' נבחר (radio)")
                return True
        except Exception:
            continue

    # אסטרטגיה 2: label / span / כפתור עם טקסט "חודש"
    xpaths = [
        "//label[contains(text(),'לפי חודש')]",
        "//label[contains(.,'לפי חודש')]",
        "//span[contains(text(),'לפי חודש')]",
        "//button[contains(text(),'לפי חודש')]",
        "//button[contains(text(),'חודשי')]",
        "//*[contains(@class,'month') and contains(text(),'חודש')]",
        "//input[@type='radio'][following::*[1][contains(text(),'חודש')]]",
        "//input[@type='radio'][preceding::*[1][contains(text(),'חודש')]]",
    ]
    for xpath in xpaths:
        try:
            els = driver.find_elements(By.XPATH, xpath)
            for el in els:
                try:
                    driver.execute_script("arguments[0].click();", el)
                    time.sleep(1.5)
                    print(f"[FinBot] 'לפי חודש' נבחר (xpath: {xpath})")
                    return True
                except Exception:
                    continue
        except Exception:
            continue

    # אסטרטגיה 3: select עם option "חודש"
    try:
        from selenium.webdriver.support.ui import Select
        for sel_el in driver.find_elements(By.CSS_SELECTOR, "select"):
            s = Select(sel_el)
            for option in s.options:
                if 'חודש' in option.text:
                    s.select_by_visible_text(option.text)
                    time.sleep(1.5)
                    print(f"[FinBot] 'לפי חודש' נבחר (select)")
                    return True
    except Exception:
        pass

    save_debug_screenshot(driver, "monthly_view_not_found")
    print("[WARN] לא נמצא כפתור 'לפי חודש' — הדוח יישלף כפי שהוא")
    return False


def _click_load(driver):
    """לוחץ כפתור 'טעינת דו\"ח' או מקביל."""
    from selenium.webdriver.common.by import By

    keywords = ["טעינת", "הפק", "הצג", "חפש", "עדכן"]
    btns = driver.find_elements(By.CSS_SELECTOR, "button")
    for btn in btns:
        txt = btn.text.strip()
        if any(kw in txt for kw in keywords):
            print(f"[FinBot] לוחץ כפתור: '{txt}'")
            btn.click()
            time.sleep(6)
            return True

    print("[WARN] לא נמצא כפתור טעינה — ממשיך לניתוח")
    return False


# ────────────────────────────────────────────────────────────
# ניתוח HTML
# ────────────────────────────────────────────────────────────

def parse_report(html):
    """מחלץ נתונים פיננסיים מדוח רוה"ס."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n")
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    data = {}

    def find_total(keyword):
        for i, line in enumerate(lines):
            if keyword in line:
                for j in range(i, min(i + 20, len(lines))):
                    nums = re.findall(r'\u200e?-?[\d,]+', lines[j])
                    nums = [n.replace(',', '').replace('\u200e', '') for n in nums
                            if len(n.replace(',', '').replace('\u200e', '')) >= 3]
                    if len(nums) >= 2:
                        return nums[-1]
        return ""

    data["turnover"]     = find_total('סה"כ הכנסות')
    data["net_income"]   = find_total('רווח / הפסד לתקופה')
    data["gross_profit"] = find_total('רווח גולמי')

    for el in soup.find_all(class_="userDetails"):
        t = el.get_text("\n", strip=True).split("\n")
        if t:
            data["business_name"] = t[0]
            if len(t) > 1:
                data["owner_name"] = t[1]

    m = re.search(r'\b(\d{9})\b', text)
    if m:
        data["vat_number"] = m.group(1)

    return data


def parse_monthly_income(html):
    """מחלץ מערך הכנסות חודשי מה-HTML."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n")
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    keywords = ['סה"כ הכנסות', "סה''כ הכנסות", 'סהכ הכנסות', 'הכנסות סה"כ']
    for i, line in enumerate(lines):
        if any(kw in line for kw in keywords):
            collected = []
            for j in range(max(0, i - 2), min(len(lines), i + 15)):
                for n in re.findall(r'-?[\d,]+', lines[j]):
                    clean = n.replace(',', '')
                    if clean.lstrip('-').isdigit() and len(clean.lstrip('-')) >= 1:
                        collected.append(int(clean))
            if len(collected) >= 12:
                monthly = collected[:12]
                if len(collected) >= 13:
                    diff = abs(collected[12] - sum(monthly))
                    if diff < max(abs(sum(monthly)) * 0.05, 500):
                        return monthly
                return monthly
            elif 3 <= len(collected) < 12:
                return collected
    return []


def analyze_periods(monthly_income, min_months=3, max_months=6):
    """מנתח תקופות רצופות עם הכנסות חיוביות."""
    n = len(monthly_income)
    periods = []
    for length in range(min_months, min(max_months + 1, n + 1)):
        for start in range(n - length + 1):
            values = monthly_income[start:start + length]
            if all(v > 0 for v in values):
                total   = sum(values)
                end_idx = start + length - 1
                periods.append({
                    "start_month":    start + 1,
                    "end_month":      start + length,
                    "months":         length,
                    "total":          total,
                    "avg_monthly":    round(total / length),
                    "start_month_he": MONTH_NAMES_HE[start]   if start   < 12 else str(start + 1),
                    "end_month_he":   MONTH_NAMES_HE[end_idx] if end_idx < 12 else str(end_idx + 1),
                    "monthly_values": values,
                })
    periods.sort(key=lambda x: (x["months"], x["total"]), reverse=True)
    return periods


# ────────────────────────────────────────────────────────────
# ממשק ציבורי
# ────────────────────────────────────────────────────────────

def get_clients():
    """מחזיר רשימת לקוחות עם data-id."""
    driver = get_driver()
    try:
        login(driver)
        driver.get(PNL_URL)
        time.sleep(4)

        _open_client_dropdown(driver)

        from selenium.webdriver.common.by import By
        clients = []
        options = driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
        for el in options:
            lines = el.text.strip().split("\n")
            biz_name   = lines[0] if lines else ""
            owner_name = lines[1] if len(lines) > 1 else ""
            data_id    = el.get_attribute("data-option-index")
            clients.append({
                "biz_name":   biz_name,
                "owner_name": owner_name,
                "data_id":    data_id,
            })
        print(f"[FinBot] נמצאו {len(clients)} לקוחות")
        return clients
    finally:
        driver.quit()


def fetch_monthly_pnl(data_id, year="2025", biz_name=""):
    """שולף דוח רו"ה לפי חודשים וניתוח תקופות רצופות לתמ"ת."""
    driver = get_driver()
    try:
        login(driver)

        # 1. עבור לעמוד דוח רווח והפסד
        print(f"[FinBot] נכנס לדוח רווח והפסד")
        driver.get(PNL_URL)
        time.sleep(4)
        save_debug_screenshot(driver, "01_pnl_loaded")

        # 2. בחר לקוח
        _select_client(driver, data_id, biz_name)
        save_debug_screenshot(driver, "02_client_selected")

        # 3. בחר שנה
        _select_year(driver, year)
        save_debug_screenshot(driver, "03_year_selected")

        # 4. בחר תצוגה חודשית
        _try_monthly_view(driver)
        save_debug_screenshot(driver, "04_monthly_view")

        # 5. לחץ "טעינת דו"ח"
        _click_load(driver)
        save_debug_screenshot(driver, "05_report_loaded")

        # 6. נתח
        html   = driver.page_source
        result = parse_report(html)
        result["year"] = year

        monthly = parse_monthly_income(html)
        result["monthly_income"] = monthly
        if monthly:
            periods = analyze_periods(monthly)
            result["periods"] = periods
            if periods:
                result["best_period"] = periods[0]
            print(f"[FinBot] נמצאו {len(monthly)} חודשים, {len(periods)} תקופות")
        else:
            print("[WARN] לא נמצאו נתונים חודשיים")

        return result
    finally:
        driver.quit()


def fetch_client_data(data_id, year="2025", biz_name=""):
    """שולף נתונים שנתיים ללקוח (למשכנתא)."""
    driver = get_driver()
    try:
        login(driver)

        print(f"[FinBot] נכנס לדוח רווח והפסד (שנתי)")
        driver.get(PNL_URL)
        time.sleep(4)
        save_debug_screenshot(driver, "01_pnl_loaded")

        _select_client(driver, data_id, biz_name)
        save_debug_screenshot(driver, "02_client_selected")

        _select_year(driver, year)
        save_debug_screenshot(driver, "03_year_selected")

        _click_load(driver)
        save_debug_screenshot(driver, "04_report_loaded")

        html = driver.page_source
        data = parse_report(html)
        data["year"] = year
        return data
    finally:
        driver.quit()


if __name__ == "__main__":
    clients = get_clients()
    print("\nרשימת לקוחות:")
    for c in clients:
        print(f"  [{c['data_id']}] {c['biz_name']} | {c['owner_name']}")
