import os
import re
import shutil

# جذر المشروع (المكان الذي يوجد فيه manage.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'shop', 'templates', 'shop')

# خريطة: اسم الملف القديم -> المجلد الفرعي الجديد
FILE_MAP = {
    'login.html': 'accounts',
    'register.html': 'accounts',
    'customer_profile.html': 'accounts',

    'cart_detail.html': 'cart',
    'checkout.html': 'cart',
    'order_success.html': 'cart',

    'order_list.html': 'orders',
    'order_detail.html': 'orders',

    'product_list.html': 'products',
    'product_detail.html': 'products',

    'merchant_dashboard.html': 'merchant',
    'merchant_product_list.html': 'merchant',
    'add_product.html': 'merchant',
    'edit_product.html': 'merchant',
    'confirm_delete_product.html': 'merchant',
    'merchant_category_list.html': 'merchant',
    'merchant_coupons_list.html': 'merchant',
    'customer_list.html': 'merchant',
    'sales_report.html': 'merchant',
    'staff_user_list.html': 'merchant',
}

def move_files():
    moved = {}
    for filename, subfolder in FILE_MAP.items():
        src = os.path.join(TEMPLATES_DIR, filename)
        if not os.path.exists(src):
            print(f'[تخطي] غير موجود: {filename}')
            continue
        dest_dir = os.path.join(TEMPLATES_DIR, subfolder)
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, filename)
        shutil.move(src, dest)
        old_path = f'shop/{filename}'
        new_path = f'shop/{subfolder}/{filename}'
        moved[old_path] = new_path
        print(f'[نقل] {old_path} -> {new_path}')
    return moved

def update_references(moved):
    # كل ملفات .py و .html في المشروع (تجاهل venv وmigrations)
    exts = ('.py', '.html')
    skip_dirs = {'venv', '__pycache__', 'migrations', '.git', 'node_modules'}

    for root, dirs, files in os.walk(BASE_DIR):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fname in files:
            if not fname.endswith(exts):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                continue

            original = content
            for old_path, new_path in moved.items():
                # يستبدل 'shop/xxx.html' أو "shop/xxx.html" فقط (مع الحفاظ على نوع علامات الاقتباس)
                content = content.replace(f"'{old_path}'", f"'{new_path}'")
                content = content.replace(f'"{old_path}"', f'"{new_path}"')

            if content != original:
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f'[تحديث مسارات] {fpath}')

if __name__ == '__main__':
    moved = move_files()
    if moved:
        update_references(moved)
    print('\nتم الانتهاء. راجع المشروع وشغّل السيرفر للتأكد.')