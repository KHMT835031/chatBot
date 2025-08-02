import sqlite3

DB_PATH = "users.db"

def print_table(table):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in c.fetchall()]
        c.execute(f"SELECT * FROM {table}")
        rows = c.fetchall()
        print(f"\n=== {table.upper()} ===")
        print(" | ".join(columns))
        print("-" * 60)
        for row in rows:
            print(" | ".join(str(x) for x in row))
    except Exception as e:
        print(f"Lỗi: {e}")
    conn.close()

def add_row(table):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in c.fetchall() if col[1] != "id"]
    values = []
    print(f"Nhập dữ liệu cho bảng {table}:")
    for col in columns:
        val = input(f"{col}: ").strip()
        values.append(val)
    placeholders = ",".join(["?"] * len(columns))
    try:
        c.execute(f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})", values)
        conn.commit()
        print("✅ Thêm dữ liệu thành công.")
    except Exception as e:
        print(f"❌ Lỗi khi thêm: {e}")
    conn.close()

def update_row(table):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in c.fetchall()]
    id_col = columns[0]
    row_id = input(f"Nhập {id_col} của dòng cần sửa: ").strip()
    updates = []
    values = []
    for col in columns[1:]:
        val = input(f"{col} (bỏ trống nếu không đổi): ").strip()
        if val:
            updates.append(f"{col}=?")
            values.append(val)
    if not updates:
        print("❌ Không có trường nào để cập nhật.")
        conn.close()
        return
    values.append(row_id)
    try:
        c.execute(f"UPDATE {table} SET {', '.join(updates)} WHERE {id_col}=?", values)
        conn.commit()
        print("✅ Đã cập nhật.")
    except Exception as e:
        print(f"❌ Lỗi khi cập nhật: {e}")
    conn.close()

def delete_row(table):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in c.fetchall()]
    id_col = columns[0]
    row_id = input(f"Nhập {id_col} của dòng cần xóa: ").strip()
    try:
        c.execute(f"DELETE FROM {table} WHERE {id_col}=?", (row_id,))
        conn.commit()
        print("✅ Đã xóa.")
    except Exception as e:
        print(f"❌ Lỗi khi xóa: {e}")
    conn.close()

def drop_table():
    table = input("Nhập tên bảng cần xóa: ").strip()
    confirm = input(f"Bạn chắc chắn muốn xóa bảng {table}? (gõ YES để xác nhận): ")
    if confirm == "YES":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute(f"DROP TABLE IF EXISTS {table}")
            conn.commit()
            print(f"✅ Đã xóa bảng {table}.")
        except Exception as e:
            print(f"❌ Lỗi khi xóa bảng: {e}")
        conn.close()
    else:
        print("❌ Hủy thao tác.")

def create_table():
    table = input("Nhập tên bảng mới: ").strip()
    cols = []
    print("Nhập tên và kiểu dữ liệu các cột (vd: username TEXT), gõ 'xong' để kết thúc.")
    while True:
        col = input(f"Cột {len(cols)+1}: ").strip()
        if col.lower() == "xong":
            break
        if col:
            cols.append(col)
    if not cols:
        print("❌ Không có cột nào.")
        return
    sql = f"CREATE TABLE IF NOT EXISTS {table} (id INTEGER PRIMARY KEY AUTOINCREMENT, {', '.join(cols)})"
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute(sql)
        conn.commit()
        print(f"✅ Đã tạo bảng {table}.")
    except Exception as e:
        print(f"❌ Lỗi khi tạo bảng: {e}")
    conn.close()

def list_tables():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in c.fetchall()]
    conn.close()
    return tables

def menu():
    while True:
        print("\n====== QUẢN LÝ SQLITE (users.db) ======")
        print("1. Xem bảng")
        print("2. Thêm dòng")
        print("3. Sửa dòng")
        print("4. Xóa dòng")
        print("5. Tạo bảng mới")
        print("6. Xóa bảng")
        print("0. Thoát")
        choice = input("Chọn chức năng: ").strip()
        if choice == "1":
            tables = list_tables()
            print("Các bảng:", ", ".join(tables))
            table = input("Nhập tên bảng muốn xem: ").strip()
            print_table(table)
        elif choice == "2":
            tables = list_tables()
            print("Các bảng:", ", ".join(tables))
            table = input("Nhập tên bảng muốn thêm dòng: ").strip()
            add_row(table)
        elif choice == "3":
            tables = list_tables()
            print("Các bảng:", ", ".join(tables))
            table = input("Nhập tên bảng muốn sửa dòng: ").strip()
            update_row(table)
        elif choice == "4":
            tables = list_tables()
            print("Các bảng:", ", ".join(tables))
            table = input("Nhập tên bảng muốn xóa dòng: ").strip()
            delete_row(table)
        elif choice == "5":
            create_table()
        elif choice == "6":
            drop_table()
        elif choice == "0":
            print("Thoát.")
            break
        else:
            print("❌ Lựa chọn không hợp lệ.")

if __name__ == "__main__":
    menu()
