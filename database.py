import sqlite3
from contextlib import contextmanager
from datetime import datetime

@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = sqlite3.connect('restaurant.db')
        conn.row_factory = sqlite3.Row
        yield conn
    finally:
        if conn:
            conn.close()

class DatabaseOperations:
    # Customer Operations
    @staticmethod
    def add_customer(first_name, middle_name, last_name, phone, email, address):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO CUSTOMER (FIRST_NAME, MIDDLE_NAME, LAST_NAME, PHONE, EMAIL, ADDRESS)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (first_name, middle_name, last_name, phone, email, address))
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def get_all_customers():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM CUSTOMER')
            return cursor.fetchall()

    # Table Operations
    @staticmethod
    def add_table(seating_capacity, status='AVAILABLE'):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO REST_TABLE (SEATING_CAPACITY, BOOKING_STATUS)
                VALUES (?, ?)
            ''', (seating_capacity, status))
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def get_all_tables():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM REST_TABLE')
            return cursor.fetchall()

    @staticmethod
    def update_table_status(table_number, status):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE REST_TABLE 
                SET BOOKING_STATUS = ? 
                WHERE TABLE_NUMBER = ?
            ''', (status, table_number))
            conn.commit()

    # Menu Operations
    @staticmethod
    def add_menu_item(name, category, price, status='AVAILABLE'):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO MENU_ITEM (ITEM_NAME, ITEM_CATEGORY, PRICE, AVAILABILITY_STATUS)
                VALUES (?, ?, ?, ?)
            ''', (name, category, price, status))
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def get_all_menu_items():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM MENU_ITEM')
            return cursor.fetchall()

    # Order Operations
    @staticmethod
    def create_order(customer_id, table_number, items):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('BEGIN TRANSACTION')
                
                # Create order
                cursor.execute('''
                    INSERT INTO ORDERS (CUSTOMER_ID, TABLE_NUMBER, TOTAL_AMOUNT)
                    VALUES (?, ?, 0)
                ''', (customer_id, table_number))
                order_id = cursor.lastrowid

                total_amount = 0
                # Add order items
                for item_id, quantity in items:
                    # Get item price
                    cursor.execute('SELECT PRICE FROM MENU_ITEM WHERE MENUITEM_NUMBER = ?', (item_id,))
                    price = cursor.fetchone()[0]
                    item_total = price * quantity
                    total_amount += item_total

                    cursor.execute('''
                        INSERT INTO ORDER_ITEM (ORDER_ID, MENUITEM_NUMBER, QUANTITY, ITEM_TOTAL)
                        VALUES (?, ?, ?, ?)
                    ''', (order_id, item_id, quantity, item_total))

                # Update order total
                cursor.execute('''
                    UPDATE ORDERS 
                    SET TOTAL_AMOUNT = ? 
                    WHERE ORDER_ID = ?
                ''', (total_amount, order_id))

                # Update table status
                cursor.execute('''
                    UPDATE REST_TABLE 
                    SET BOOKING_STATUS = 'OCCUPIED' 
                    WHERE TABLE_NUMBER = ?
                ''', (table_number,))

                cursor.execute('COMMIT')
                return order_id
            except Exception as e:
                cursor.execute('ROLLBACK')
                raise e

    @staticmethod
    def get_order_details(order_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT O.*, C.FIRST_NAME, C.LAST_NAME, RT.TABLE_NUMBER
                FROM ORDERS O
                JOIN CUSTOMER C ON O.CUSTOMER_ID = C.CUSTOMER_ID
                JOIN REST_TABLE RT ON O.TABLE_NUMBER = RT.TABLE_NUMBER
                WHERE O.ORDER_ID = ?
            ''', (order_id,))
            return cursor.fetchone()

    # Payment Operations
    @staticmethod
    def process_payment(order_id, payment_mode, amount):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('BEGIN TRANSACTION')
                
                cursor.execute('''
                    INSERT INTO PAYMENT (ORDER_ID, PAYMENT_MODE, AMOUNT_PAID)
                    VALUES (?, ?, ?)
                ''', (order_id, payment_mode, amount))

                cursor.execute('''
                    UPDATE ORDERS 
                    SET ORDER_STATUS = 'COMPLETED' 
                    WHERE ORDER_ID = ?
                ''', (order_id,))

                # Free up the table
                cursor.execute('''
                    UPDATE REST_TABLE 
                    SET BOOKING_STATUS = 'AVAILABLE' 
                    WHERE TABLE_NUMBER = (
                        SELECT TABLE_NUMBER 
                        FROM ORDERS 
                        WHERE ORDER_ID = ?
                    )
                ''', (order_id,))

                cursor.execute('COMMIT')
            except Exception as e:
                cursor.execute('ROLLBACK')
                raise e