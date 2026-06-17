import sqlite3
import random
import string
import time
import os
import argparse
from datetime import datetime, timedelta
from typing import List, Tuple


def generate_random_string(length: int = 10) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_random_email() -> str:
    username = generate_random_string(random.randint(5, 12)).lower()
    domain = random.choice(['gmail.com', 'yahoo.com', 'outlook.com', 'qq.com', '163.com'])
    return f"{username}@{domain}"


def generate_random_date(start_year: int = 2000, end_year: int = 2025) -> str:
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    random_date = start_date + timedelta(days=random_days)
    return random_date.strftime("%Y-%m-%d")


def generate_random_datetime() -> str:
    date = generate_random_date()
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return f"{date} {hour:02d}:{minute:02d}:{second:02d}"


def create_users_table(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            age INTEGER,
            city TEXT,
            balance REAL DEFAULT 0,
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL,
            updated_at TEXT,
            bio TEXT,
            address TEXT,
            phone TEXT,
            department TEXT,
            position TEXT,
            salary REAL,
            level INTEGER DEFAULT 1,
            points INTEGER DEFAULT 0,
            vip INTEGER DEFAULT 0,
            last_login TEXT,
            avatar_url TEXT
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_username ON users(username)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_email ON users(email)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_city ON users(city)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON users(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON users(created_at)')
    conn.commit()


def create_orders_table(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_no TEXT NOT NULL UNIQUE,
            user_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            pay_method TEXT,
            shipping_address TEXT,
            remark TEXT,
            created_at TEXT NOT NULL,
            paid_at TEXT,
            shipped_at TEXT,
            delivered_at TEXT,
            cancelled_at TEXT,
            refund_amount REAL DEFAULT 0
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_order_no ON orders(order_no)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON orders(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON orders(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON orders(created_at)')
    conn.commit()


def create_products_table(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            price REAL NOT NULL DEFAULT 0,
            stock INTEGER NOT NULL DEFAULT 0,
            description TEXT,
            supplier TEXT,
            barcode TEXT UNIQUE,
            weight REAL,
            color TEXT,
            size TEXT,
            material TEXT,
            status TEXT DEFAULT 'on_sale',
            created_at TEXT NOT NULL,
            updated_at TEXT,
            sales_count INTEGER DEFAULT 0,
            rating REAL DEFAULT 0
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON products(category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON products(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_price ON products(price)')
    conn.commit()


def generate_users_batch(batch_size: int, start_id: int) -> List[Tuple]:
    cities = ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '西安', '南京', '重庆',
              '苏州', '天津', '长沙', '青岛', '大连', '厦门', '宁波', '无锡', '合肥', '福州']
    departments = ['技术部', '产品部', '设计部', '市场部', '运营部', '人事部', '财务部', '销售部']
    positions = ['工程师', '经理', '主管', '专员', '总监', '助理', '实习生', '顾问']
    statuses = ['active', 'inactive', 'suspended', 'pending']

    batch = []
    for i in range(batch_size):
        user_id = start_id + i
        username = f"user_{user_id:07d}"
        email = f"{username}@example.com"
        age = random.randint(18, 70)
        city = random.choice(cities)
        balance = round(random.uniform(0, 100000), 2)
        status = random.choices(statuses, weights=[0.7, 0.15, 0.1, 0.05])[0]
        created_at = generate_random_datetime()
        updated_at = generate_random_datetime()
        bio = generate_random_string(random.randint(20, 100))
        address = f"{city}市{generate_random_string(8)}路{random.randint(1, 999)}号"
        phone = f"1{random.choice(['3', '5', '7', '8', '9'])}{''.join(random.choices(string.digits, k=9))}"
        department = random.choice(departments)
        position = random.choice(positions)
        salary = round(random.uniform(3000, 50000), 2)
        level = random.randint(1, 10)
        points = random.randint(0, 100000)
        vip = random.randint(0, 1)
        last_login = generate_random_datetime()
        avatar_url = f"https://example.com/avatars/{username}.jpg"

        batch.append((
            username, email, age, city, balance, status,
            created_at, updated_at, bio, address, phone,
            department, position, salary, level, points,
            vip, last_login, avatar_url
        ))

    return batch


def generate_orders_batch(batch_size: int, start_id: int, max_user_id: int) -> List[Tuple]:
    products = ['iPhone', 'MacBook', 'iPad', 'AirPods', 'Apple Watch',
                '华为手机', '小米手机', 'OPPO手机', 'vivo手机', '三星手机',
                '机械键盘', '游戏鼠标', '显示器', '笔记本电脑', '平板电脑',
                '耳机', '音箱', '摄像头', '路由器', '充电宝']
    statuses = ['pending', 'paid', 'shipped', 'delivered', 'cancelled', 'refunded']
    pay_methods = ['alipay', 'wechat', 'card', 'cod']

    batch = []
    for i in range(batch_size):
        order_id = start_id + i
        order_no = f"ORD{datetime.now().strftime('%Y%m%d')}{order_id:010d}"
        user_id = random.randint(1, max_user_id)
        product_name = random.choice(products)
        price = round(random.uniform(10, 10000), 2)
        quantity = random.randint(1, 10)
        total_amount = round(price * quantity, 2)
        status = random.choices(statuses, weights=[0.1, 0.2, 0.2, 0.4, 0.08, 0.02])[0]
        pay_method = random.choice(pay_methods) if status != 'pending' else None
        shipping_address = generate_random_string(30)
        remark = generate_random_string(random.randint(0, 50)) if random.random() > 0.5 else ""
        created_at = generate_random_datetime()
        paid_at = created_at if status in ['paid', 'shipped', 'delivered'] else None
        shipped_at = created_at if status in ['shipped', 'delivered'] else None
        delivered_at = created_at if status == 'delivered' else None
        cancelled_at = created_at if status in ['cancelled', 'refunded'] else None
        refund_amount = round(random.uniform(0, total_amount), 2) if status == 'refunded' else 0

        batch.append((
            order_no, user_id, product_name, price, quantity, total_amount,
            status, pay_method, shipping_address, remark,
            created_at, paid_at, shipped_at, delivered_at, cancelled_at, refund_amount
        ))

    return batch


def generate_products_batch(batch_size: int, start_id: int) -> List[Tuple]:
    categories = ['电子产品', '服装', '食品', '图书', '家居', '运动', '美妆', '母婴', '玩具', '汽车']
    statuses = ['on_sale', 'off_sale', 'sold_out', 'discontinued']
    suppliers = ['供应商A', '供应商B', '供应商C', '供应商D', '供应商E',
                 '供应商F', '供应商G', '供应商H', '供应商I', '供应商J']
    colors = ['黑色', '白色', '红色', '蓝色', '绿色', '黄色', '紫色', '粉色', '银色', '金色']
    sizes = ['S', 'M', 'L', 'XL', 'XXL', '均码']
    materials = ['塑料', '金属', '木材', '布料', '皮革', '玻璃', '陶瓷', '橡胶']

    batch = []
    for i in range(batch_size):
        product_id = start_id + i
        name = f"商品_{product_id:06d}"
        category = random.choice(categories)
        price = round(random.uniform(1, 9999), 2)
        stock = random.randint(0, 10000)
        description = generate_random_string(random.randint(20, 200))
        supplier = random.choice(suppliers)
        barcode = f"BC{product_id:012d}"
        weight = round(random.uniform(0.01, 50), 2)
        color = random.choice(colors)
        size = random.choice(sizes)
        material = random.choice(materials)
        status = random.choices(statuses, weights=[0.6, 0.15, 0.15, 0.1])[0]
        created_at = generate_random_datetime()
        updated_at = generate_random_datetime()
        sales_count = random.randint(0, 50000)
        rating = round(random.uniform(0, 5), 1)

        batch.append((
            name, category, price, stock, description, supplier,
            barcode, weight, color, size, material, status,
            created_at, updated_at, sales_count, rating
        ))

    return batch


def insert_data(conn: sqlite3.Connection, table: str, data: List[Tuple]) -> None:
    cursor = conn.cursor()
    placeholders = ', '.join(['?' for _ in range(len(data[0]))])
    cursor.executemany(f"INSERT INTO {table} VALUES ({placeholders})", data)


def generate_test_data(db_path: str, user_count: int = 100000,
                       order_count: int = 500000, product_count: int = 10000,
                       batch_size: int = 1000) -> None:
    print(f"开始生成测试数据到: {db_path}")
    print(f"用户数: {user_count}, 订单数: {order_count}, 商品数: {product_count}")
    print(f"批量大小: {batch_size}")
    print("-" * 60)

    conn = sqlite3.connect(db_path)

    print("创建表结构...")
    create_users_table(conn)
    create_orders_table(conn)
    create_products_table(conn)
    print("表结构创建完成")
    print("-" * 60)

    print(f"开始生成 {user_count} 条用户数据...")
    start_time = time.time()
    users_inserted = 0

    for i in range(0, user_count, batch_size):
        current_batch_size = min(batch_size, user_count - i)
        batch = generate_users_batch(current_batch_size, i + 1)
        cursor = conn.cursor()
        cursor.executemany('''
            INSERT INTO users (username, email, age, city, balance, status,
                              created_at, updated_at, bio, address, phone,
                              department, position, salary, level, points,
                              vip, last_login, avatar_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', batch)
        users_inserted += current_batch_size

        if (i // batch_size + 1) % 10 == 0 or users_inserted >= user_count:
            conn.commit()
            elapsed = time.time() - start_time
            progress = users_inserted / user_count * 100
            speed = users_inserted / elapsed if elapsed > 0 else 0
            eta = (user_count - users_inserted) / speed if speed > 0 else 0
            print(f"用户数据进度: {users_inserted}/{user_count} ({progress:.1f}%) "
                  f"速度: {speed:.0f}条/秒 预计剩余: {eta:.0f}秒")

    print(f"用户数据生成完成，共 {users_inserted} 条，耗时 {time.time() - start_time:.2f} 秒")
    print("-" * 60)

    print(f"开始生成 {product_count} 条商品数据...")
    start_time = time.time()
    products_inserted = 0

    for i in range(0, product_count, batch_size):
        current_batch_size = min(batch_size, product_count - i)
        batch = generate_products_batch(current_batch_size, i + 1)
        cursor = conn.cursor()
        cursor.executemany('''
            INSERT INTO products (name, category, price, stock, description, supplier,
                                 barcode, weight, color, size, material, status,
                                 created_at, updated_at, sales_count, rating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', batch)
        products_inserted += current_batch_size

        if (i // batch_size + 1) % 10 == 0 or products_inserted >= product_count:
            conn.commit()
            elapsed = time.time() - start_time
            progress = products_inserted / product_count * 100
            speed = products_inserted / elapsed if elapsed > 0 else 0
            eta = (product_count - products_inserted) / speed if speed > 0 else 0
            print(f"商品数据进度: {products_inserted}/{product_count} ({progress:.1f}%) "
                  f"速度: {speed:.0f}条/秒 预计剩余: {eta:.0f}秒")

    print(f"商品数据生成完成，共 {products_inserted} 条，耗时 {time.time() - start_time:.2f} 秒")
    print("-" * 60)

    print(f"开始生成 {order_count} 条订单数据...")
    start_time = time.time()
    orders_inserted = 0
    max_user_id = user_count

    for i in range(0, order_count, batch_size):
        current_batch_size = min(batch_size, order_count - i)
        batch = generate_orders_batch(current_batch_size, i + 1, max_user_id)
        cursor = conn.cursor()
        cursor.executemany('''
            INSERT INTO orders (order_no, user_id, product_name, price, quantity, total_amount,
                               status, pay_method, shipping_address, remark,
                               created_at, paid_at, shipped_at, delivered_at, cancelled_at, refund_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', batch)
        orders_inserted += current_batch_size

        if (i // batch_size + 1) % 10 == 0 or orders_inserted >= order_count:
            conn.commit()
            elapsed = time.time() - start_time
            progress = orders_inserted / order_count * 100
            speed = orders_inserted / elapsed if elapsed > 0 else 0
            eta = (order_count - orders_inserted) / speed if speed > 0 else 0
            print(f"订单数据进度: {orders_inserted}/{order_count} ({progress:.1f}%) "
                  f"速度: {speed:.0f}条/秒 预计剩余: {eta:.0f}秒")

    print(f"订单数据生成完成，共 {orders_inserted} 条，耗时 {time.time() - start_time:.2f} 秒")
    print("-" * 60)

    print("验证数据...")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count_actual = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM orders")
    order_count_actual = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM products")
    product_count_actual = cursor.fetchone()[0]

    print(f"users 表: {user_count_actual} 条")
    print(f"orders 表: {order_count_actual} 条")
    print(f"products 表: {product_count_actual} 条")

    db_size = os.path.getsize(db_path) / (1024 * 1024)
    print(f"数据库文件大小: {db_size:.2f} MB")

    conn.close()
    print("-" * 60)
    print("测试数据生成完成！")


def main():
    parser = argparse.ArgumentParser(description='SQLite 测试数据生成工具')
    parser.add_argument('--db', type=str, default='test_data.db',
                        help='数据库文件路径 (默认: test_data.db)')
    parser.add_argument('--users', type=int, default=100000,
                        help='用户数据数量 (默认: 100000)')
    parser.add_argument('--orders', type=int, default=500000,
                        help='订单数据数量 (默认: 500000)')
    parser.add_argument('--products', type=int, default=10000,
                        help='商品数据数量 (默认: 10000)')
    parser.add_argument('--batch', type=int, default=1000,
                        help='批量插入大小 (默认: 1000)')

    args = parser.parse_args()

    generate_test_data(
        db_path=args.db,
        user_count=args.users,
        order_count=args.orders,
        product_count=args.products,
        batch_size=args.batch
    )


if __name__ == '__main__':
    main()
