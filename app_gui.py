import tkinter as tk
from tkinter import messagebox
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

def start_scraping():
    # جلب الروابط المدخلة في الصندوق النصي
    urls_text = text_urls.get("1.0", tk.END).strip()
    if not urls_text:
        messagebox.showwarning("تنبيه", "الرجاء إدخال رابط واحد على الأقل!")
        return

    urls = [line.strip() for line in urls_text.splitlines() if line.strip()]
    products_data = []

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # استخراج العنوان
                title_tag = soup.find('meta', property='og:title') or soup.find('h1')
                title = title_tag.get('content') if title_tag and title_tag.name == 'meta' else (title_tag.text.strip() if title_tag else "منتج بدون عنوان")
                
                # استخراج السعر
                price = 0.00
                price_tag = soup.find('meta', property='product:price:amount') or soup.find('span', {'class': lambda x: x and 'price' in x.lower()})
                if price_tag:
                    price_text = price_tag.get('content') if price_tag.name == 'meta' else price_tag.text
                    numbers = re.findall(r'\d+\.\d+|\d+', price_text)
                    if numbers:
                        price = float(numbers[0])
                        
                # استخراج رابط الصورة
                img_tag = soup.find('meta', property='og:image')
                image_url = img_tag.get('content') if img_tag else ''
                
                # إضافة البيانات مطابقة لأعمدة جدولك تماماً
                products_data.append({
                    'ID (منتج جديد)': '',
                    'اسم المنتج': title,
                    'الموديل': '',
                    'التصنيف': 'عام',
                    'الوصف': '',
                    'المواصفات الفنية': '',
                    'متاح للبيع (نعم)': 'نعم',
                    'السعر': price,
                    'المخزون': 100,
                    'رابط الصورة': image_url
                })
        except Exception as e:
            print(f"خطأ في سحب الرابط {url}: {e}")

    if products_data:
        df = pd.DataFrame(products_data)
        df.to_excel('products_import.xlsx', index=False)
        messagebox.showinfo("نجاح", "تم بنجاح توليد ملف الإكسل (products_import.xlsx) وجاهز للرفع لمتجرك!")
    else:
        messagebox.showerror("خطأ", "لم يتم استخراج أي بيانات، تأكد من صحة الروابط.")

# تصميم الواجهة الرسومية
root = tk.Tk()
root.title("أداة سحب منتجات علي بابا إلى إكسل - كنان")
root.geometry("500x400")

label = tk.Label(root, text="القرص أو الصق روابط المنتجات هنا (كل رابط في سطر):", font=("Arial", 11))
label.pack(pady=10)

text_urls = tk.Text(root, height=12, width=55)
text_urls.pack(pady=5)

btn_start = tk.Button(root, text="انطلاق وسحب البيانات", command=start_scraping, bg="green", fg="white", font=("Arial", 12, "bold"), padx=10, pady=5)
btn_start.pack(pady=15)

root.mainloop()