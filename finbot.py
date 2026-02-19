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

# מיפוי data-id -> מספר client ב-URL
# /report/2 = לקוח data-id=1 (אוחיון רואי חשבון)
# כלומר: url_id = data_id + 1

def url_id(data_id):
    return int(data_id) + 1


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


def wait_for(driver, css, timeout=15):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, css))
    )


def login(driver):
    from selenium.webdriver.common.by import By
    driver.get(FINBOT_URL)
    wait_for(driver, "input[name='email']")
    driver.find_element(By.CSS_SELECTOR, "input[name='email']").send_keys(USERNAME)
    driver.find_element(By.CSS_SELECTOR, "input[name='password']").send_keys(PASSWORD)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(5)
    if "dashboard" not in driver.current_url:
        raise RuntimeError("כניסה נכשלה")


def get_clients():
    """מחזיר רשימת לקוחות עם data-id."""
    driver = get_driver()
    try:
        login(driver)
        driver.get(FINBOT_URL + "/report/2")
        time.sleep(4)

        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys

        client_input = wait_for(driver, "input[placeholder='לקוח / שם חברה / מ.ע ']")
        client_input.click()
        time.sleep(1)
        client_input.send_keys(Keys.CONTROL + "a")
        client_input.send_keys(Keys.DELETE)
        time.sleep(2)

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
                "url_id":     url_id(data_id) if data_id else None,
            })
        return clients
    finally:
        driver.quit()


def parse_report(html):
    """מחלץ נתונים פיננסיים מדוח רוה"ס."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n")
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    data = {}

    def find_total(keyword):
        """מוצא את הסכום השנתי (אחרון) אחרי מילת מפתח."""
        for i, line in enumerate(lines):
            if keyword in line:
                # חפש שורות עם מספרים בהמשך
                for j in range(i, min(i+20, len(lines))):
                    nums = re.findall(r'\u200e?-?[\d,]+', lines[j])
                    nums = [n.replace(',','').replace('\u200e','') for n in nums if len(n.replace(',','').replace('\u200e','')) >= 3]
                    if len(nums) >= 2:  # יש מספיק עמודות = יש נתונים חודשיים
                        return nums[-1]  # האחרון = סה"כ שנתי
        return ""

    data["turnover"]     = find_total('סה"כ הכנסות')
    data["net_income"]   = find_total('רווח / הפסד לתקופה')
    data["gross_profit"] = find_total('רווח גולמי')

    # שם עסק ומספר עוסק
    for el in soup.find_all(class_="userDetails"):
        t = el.get_text("\n", strip=True).split("\n")
        if t:
            data["business_name"] = t[0]
            if len(t) > 1:
                data["owner_name"] = t[1]

    # מספר עוסק (9 ספרות)
    m = re.search(r'\b(\d{9})\b', text)
    if m:
        data["vat_number"] = m.group(1)

    return data


def _try_monthly_view(driver):
    """מנסה להפעיל תצוגת 'לפי חודש' בדוח FinBot."""
    from selenium.webdriver.common.by import By
    xpaths = [
        "//*[contains(text(),'לפי חודש')]",
        "//*[contains(text(),'חודשי')]",
        "//input[@value='monthly']",
        "//button[contains(@class,'month')]",
    ]
    for xpath in xpaths:
        try:
            for el in driver.find_elements(By.XPATH, xpath):
                try:
                    el.click()
                    time.sleep(1.5)
                    return True
                except Exception:
                    continue
        except Exception:
            continue
    return False


def parse_monthly_income(html):
    """מחלץ מערך הכנסות חודשי (עד 12 ערכים) מה-HTML של הדוח."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n")
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    keywords = ['סה"כ הכנסות', "סה''כ הכנסות", 'סהכ הכנסות', 'הכנסות סה"כ']
    for i, line in enumerate(lines):
        if any(kw in line for kw in keywords):
            collected = []
            for j in range(max(0, i - 2), min(len(lines), i + 12)):
                for n in re.findall(r'-?[\d,]+', lines[j]):
                    clean = n.replace(',', '')
                    if clean.lstrip('-').isdigit() and len(clean.lstrip('-')) >= 1:
                        collected.append(int(clean))
            if len(collected) >= 12:
                monthly = collected[:12]
                # אם הערך ה-13 הוא סכום ה-12, הוא הסה"כ השנתי — מספיק 12
                if len(collected) >= 13:
                    diff = abs(collected[12] - sum(monthly))
                    if diff < max(abs(sum(monthly)) * 0.05, 500):
                        return monthly
                return monthly
            elif 3 <= len(collected) < 12:
                return collected   # דוח חלקי (שנה לא מלאה)
    return []


def analyze_periods(monthly_income, min_months=3, max_months=6):
    """מנתח תקופות רצופות עם הכנסות חיוביות ומחזיר רשימה ממוינת."""
    n = len(monthly_income)
    periods = []
    for length in range(min_months, min(max_months + 1, n + 1)):
        for start in range(n - length + 1):
            values = monthly_income[start:start + length]
            if all(v > 0 for v in values):
                total = sum(values)
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
    # תקופות ארוכות קודם; בין שוות-אורך — הכנסה גבוהה קודם
    periods.sort(key=lambda x: (x["months"], x["total"]), reverse=True)
    return periods


def fetch_monthly_pnl(data_id, year="2025"):
    """שולף דוח רו"ה לפי חודשים וכולל ניתוח תקופות רצופות."""
    client_url_id = url_id(data_id)
    driver = get_driver()
    try:
        login(driver)
        driver.get(f"{FINBOT_URL}/report/{client_url_id}")
        time.sleep(4)

        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys

        # בחר שנה
        year_inputs = driver.find_elements(By.CSS_SELECTOR, "input[role='combobox']")
        for yi in year_inputs:
            val_str = yi.get_attribute("value") or ""
            if val_str.isdigit() and len(val_str) == 4:
                if val_str != year:
                    yi.click(); time.sleep(1)
                    yi.send_keys(Keys.CONTROL + "a")
                    yi.send_keys(year); time.sleep(1)
                    opts = driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
                    for o in opts:
                        if year in o.text:
                            o.click(); time.sleep(1); break
                break

        # נסה להפעיל תצוגה חודשית
        _try_monthly_view(driver)

        # לחץ "טעינת דו"ח"
        btns = driver.find_elements(By.CSS_SELECTOR, "button")
        for btn in btns:
            if "טעינת" in btn.text:
                btn.click(); time.sleep(5); break

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

        return result
    finally:
        driver.quit()


def fetch_client_data(data_id, year="2025"):
    """שולף נתונים ללקוח לפי data_id."""
    client_url_id = url_id(data_id)
    driver = get_driver()
    try:
        login(driver)

        # עבור לדף הדוח של הלקוח
        driver.get(f"{FINBOT_URL}/report/{client_url_id}")
        time.sleep(4)

        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys

        # בחר שנה
        year_inputs = driver.find_elements(By.CSS_SELECTOR, "input[role='combobox']")
        for yi in year_inputs:
            val = yi.get_attribute("value") or ""
            if val.isdigit() and len(val) == 4:
                if val != year:
                    yi.click(); time.sleep(1)
                    yi.send_keys(Keys.CONTROL + "a")
                    yi.send_keys(year); time.sleep(1)
                    opts = driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
                    for o in opts:
                        if year in o.text:
                            o.click(); time.sleep(1); break
                break

        # לחץ "טעינת דו"ח"
        btns = driver.find_elements(By.CSS_SELECTOR, "button")
        for btn in btns:
            if "טעינת" in btn.text:
                btn.click(); time.sleep(5); break

        html = driver.page_source
        data = parse_report(html)
        data["year"] = year
        return data

    finally:
        driver.quit()


if __name__ == "__main__":
    clients = get_clients()
    print("רשימת לקוחות:")
    for c in clients:
        print(f"  [{c['data_id']}] {c['biz_name']} | {c['owner_name']}")
