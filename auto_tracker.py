import time
import datetime
import tkinter as tk
from tkinter import messagebox

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException


def slow_scroll(driver, steps=10, delay=0.5):
    from selenium.webdriver.common.keys import Keys
    body = driver.find_element(By.TAG_NAME, "body")
    for _ in range(steps):
        body.send_keys(Keys.ARROW_DOWN)
        time.sleep(delay)


def wait_for_manual_captcha(driver):
    input("🔐 إذا ظهرت كابتشا، يرجى حلّها يدويًا ثم اضغطي Enter للمتابعة...")
    
def scroll_to_top(driver):
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

def save_results_to_pdf(product_info, sales_info, total_sales):
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.set_font("DejaVu", size=12)

    pdf.cell(200, 10, txt="Etsy Shop Tracking Report", ln=True, align="C")
    pdf.ln(10)

    pdf.cell(200, 10, txt=f"Total Sales Today: {total_sales}", ln=True)
    pdf.ln(5)

    pdf.cell(200, 10, txt="Most Recent 5 Products Today:", ln=True)
    for i, p in enumerate(product_info, 1):
        text = f"{i}. {p['name']} | ${p['price']}\n{p['url']}"
        pdf.multi_cell(0, 10, txt=text)

    pdf.ln(5)
    pdf.cell(200, 10, txt="First 5 Sales Today:", ln=True)
    for i, s in enumerate(sales_info, 1):
        text = f"{i}. {s['name']}\n{s['url']}"
        pdf.multi_cell(0, 10, txt=text)

    pdf.output("etsy_tracker_report.pdf")
    print("✅ Report saved to etsy_tracker_report.pdf")



def run_tracker(shop_url):
    options = uc.ChromeOptions()
    options.add_argument('--lang=en-US')
    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 20)
    try:
        driver.get(shop_url)
        time.sleep(3)
        wait_for_manual_captcha(driver)  # ← تمت إضافتها هنا

        # ... ثم بقية الكود كما هو بالضبط بدون تغيير ...

        # تمرير بطيء لإظهار زر Sort
        slow_scroll(driver, steps=10, delay=0.5)

        # اضغط زر Sort
        sort_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'wt-menu__trigger') and contains(., 'Sort')]"))
        )
        sort_button.click()

        # انتظر ظهور قائمة الفرز حسب xpath container
        wait.until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='sh-wider-items']/div[3]/div[2]/div/div/div/div"))
        )
        time.sleep(1)  # تأخير بسيط قبل الضغط

        # اضغط زر Most Recent حسب xpath المحدد
        
        most_recent_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='sh-wider-items']/div[3]/div[2]/div/div/div/div/button[3]")))

        try:
            most_recent_btn.click()
            
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", most_recent_btn)

        time.sleep(2)  # انتظر تحميل الصفحة
        
        # تمرير خفيف لإظهار المنتجات
        slow_scroll(driver, steps=5, delay=0.3)

        # --- [أحدث 5 منتجات] ---
        print("\n🆕 أحدث 5 منتجات:")
        items = driver.find_elements(By.XPATH, '//*[@id="sh-wider-items"]/div[3]/div[3]//div[contains(@class, "v2-listing-card__info")]')[:5]

        product_info = []  # ← أضف هذا فوق الحلقة     
        for idx, item in enumerate(items, 1):
            try:
                name = item.find_element(By.XPATH, ".//h3").text.strip()
                price = item.find_element(By.XPATH, ".//span[@class='currency-value']").text.strip()
                url = item.find_element(By.XPATH, "../../..").get_attribute("href")  # نرجع للعنصر <a>
                product_info.append({'name': name, 'price': price, 'url': url})
                print(f"{idx}. {name} | ${price} | {url}")
            except Exception as e:
                print(f"{idx}. ❌ تعذر استخراج منتج:", e)


        # 1. الصعود لأعلى الصفحة
        scroll_to_top(driver)

        # 2. إيجاد زر المبيعات وقراءة الرقم والضغط عليه
        try:
            sales_element = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="content"]/div[1]/div/div[1]/div[1]/div[1]/div[2]/div/div/div/div[1]/div[1]/div[2]/div[2]/div[4]/span[2]/a')))
            sales_text = sales_element.text.strip()
            total_sales = sales_text  # ← أضيفي هذا
            print(f"📦 عدد المبيعات الكلي: {sales_text}")
    
        # اضغط عليه للدخول إلى صفحة المبيعات
            sales_element.click()
            time.sleep(2)
            wait_for_manual_captcha(driver)  # ← هنا نضيف التوقف فقط إن ظهرت كابتشا

        except Exception as e:
            print("❌ تعذر العثور على رابط المبيعات:", e)
            return

        # 3. استخراج أول 5 مبيعات
        try:
            sale_titles = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//h3[contains(@class,'v2-listing-card__title')]"))) 
            print("\n🛒 أول 5 مبيعات:")
            sales_info = []  # ← أضف هذا فوق حلقة المبيعات
            for idx, title in enumerate(sale_titles[:5], 1):
                name = title.text.strip()
                url = driver.find_element(By.XPATH, f'//*[@id="content"]/div[3]/div[1]/div/div[{idx}]/a').get_attribute("href")
                sales_info.append({'name': name, 'url': url})
                print(f"{idx}. {name} | {url}")
        except Exception as e:
            print("❌ تعذر استخراج أسماء المبيعات:", e)

        # بعد طباعة أحدث المنتجات والمبيعات
        save_results_to_pdf(product_info, sales_info, total_sales)
    
    except Exception as e:
        messagebox.showerror("خطأ", str(e))
    finally:
        driver.quit()
     
def start_gui():
    window = tk.Tk()
    window.title("مراقب متجر Etsy")

    tk.Label(window, text="رابط متجر Etsy:").pack()
    url_entry = tk.Entry(window, width=60)
    url_entry.insert(0, "https://www.etsy.com/shop/SerenatasJourney")
    url_entry.pack(pady=5)

    tk.Button(window, text="ابدأ المراقبة", command=lambda: run_tracker(url_entry.get())).pack(pady=10)

    window.mainloop()


if __name__ == "__main__":
    start_gui()
