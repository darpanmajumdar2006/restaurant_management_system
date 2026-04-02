import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime, timedelta

import streamlit as st

@contextmanager
def get_db_connection():
    conn = None
    try:
        # Create a new connection for each request with thread safety
        conn = sqlite3.connect('restaurant.db', check_same_thread=False)
        conn.row_factory = sqlite3.Row
        
        # Initialize database if it doesn't exist
        if not os.path.exists('restaurant.db'):
            from create_database import init_database
            init_database()
            
            # Add sample data for new database
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO REST_TABLE (BOOKING_ID, SEATING_CAPACITY, BOOKING_STATUS) VALUES (1, 4, 'AVAILABLE')")
                cursor.execute("INSERT INTO REST_TABLE (BOOKING_ID, SEATING_CAPACITY, BOOKING_STATUS) VALUES (2, 2, 'AVAILABLE')")
                cursor.execute("INSERT INTO MENU_ITEM (ITEM_NAME, ITEM_CATEGORY, PRICE, AVAILABILITY_STATUS) VALUES ('Burger', 'MAIN COURSE', 12.99, 'AVAILABLE')")
                cursor.execute("INSERT INTO MENU_ITEM (ITEM_NAME, ITEM_CATEGORY, PRICE, AVAILABILITY_STATUS) VALUES ('Fries', 'STARTER', 5.99, 'AVAILABLE')")
                conn.commit()
            except sqlite3.IntegrityError:
                pass
        
        yield conn
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        if conn and conn.in_transaction:
            conn.rollback()
        raise
    finally:
        if conn:
            try:
                if not conn.in_transaction:
                    conn.commit()
                conn.close()
            except Exception:
                pass

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
                INSERT INTO REST_TABLE (BOOKING_ID, SEATING_CAPACITY, BOOKING_STATUS)
                VALUES ((SELECT COALESCE(MAX(BOOKING_ID), 0) + 1 FROM REST_TABLE), ?, ?)
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
                
                # Calculate total amount first
                total_amount = 0
                item_details = []
                for item_id, quantity in items:
                    # Get item price
                    cursor.execute('SELECT PRICE FROM MENU_ITEM WHERE MENUITEM_NUMBER = ?', (item_id,))
                    price = cursor.fetchone()[0]
                    item_total = price * quantity
                    total_amount += item_total
                    item_details.append((item_id, quantity, item_total))

                # Create order with calculated total
                cursor.execute('''
                    INSERT INTO ORDERS (CUSTOMER_ID, TABLE_NUMBER, TOTAL_AMOUNT)
                    VALUES (?, ?, ?)
                ''', (customer_id, table_number, total_amount))
                order_id = cursor.lastrowid

                # Add order items
                # Insert order items using pre-calculated values
                for item_id, quantity, item_total in item_details:
                    cursor.execute('''
                        INSERT INTO ORDER_ITEM (ORDER_ID, MENUITEM_NUMBER, QUANTITY, ITEM_TOTAL)
                        VALUES (?, ?, ?, ?)
                    ''', (order_id, item_id, quantity, item_total))

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
    # In database.py, add this method to the DatabaseOperations class

    @staticmethod
    def get_all_orders():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT O.*, C.FIRST_NAME, C.LAST_NAME
                FROM ORDERS O
                LEFT JOIN CUSTOMER C ON O.CUSTOMER_ID = C.CUSTOMER_ID
                ORDER BY O.ORDER_DATE DESC, O.ORDER_TIME DESC
            ''')
            return cursor.fetchall()

    @staticmethod
    def get_order_details(order_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Get order details
            cursor.execute('''
                SELECT O.*, C.FIRST_NAME, C.LAST_NAME
                FROM ORDERS O
                JOIN CUSTOMER C ON O.CUSTOMER_ID = C.CUSTOMER_ID
                WHERE O.ORDER_ID = ?
            ''', (order_id,))
            order = cursor.fetchone()
            
            # Get order items
            cursor.execute('''
                SELECT OI.*, MI.ITEM_NAME, MI.PRICE
                FROM ORDER_ITEM OI
                JOIN MENU_ITEM MI ON OI.MENUITEM_NUMBER = MI.MENUITEM_NUMBER
                WHERE OI.ORDER_ID = ?
            ''', (order_id,))
            items = cursor.fetchall()
            
            return order, items

    @staticmethod
    def get_revenue_metrics(period):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Calculate date ranges based on period
            today = datetime.now().date()
            if period == "Last 7 Days":
                start_date = today - timedelta(days=7)
                prev_start = start_date - timedelta(days=7)
            elif period == "Last 30 Days":
                start_date = today - timedelta(days=30)
                prev_start = start_date - timedelta(days=30)
            else:  # Last 90 Days
                start_date = today - timedelta(days=90)
                prev_start = start_date - timedelta(days=90)
            
            # Get current period revenue
            cursor.execute('''
                SELECT COALESCE(SUM(TOTAL_AMOUNT), 0)
                FROM ORDERS
                WHERE ORDER_DATE BETWEEN ? AND ?
                AND ORDER_STATUS = 'COMPLETED'
            ''', (start_date.isoformat(), today.isoformat()))
            current_revenue = cursor.fetchone()[0]
            
            # Get previous period revenue for comparison
            cursor.execute('''
                SELECT COALESCE(SUM(TOTAL_AMOUNT), 0)
                FROM ORDERS
                WHERE ORDER_DATE BETWEEN ? AND ?
                AND ORDER_STATUS = 'COMPLETED'
            ''', (prev_start.isoformat(), start_date.isoformat()))
            previous_revenue = cursor.fetchone()[0]
            
            # Calculate percentage change
            if previous_revenue > 0:
                change = ((current_revenue - previous_revenue) / previous_revenue) * 100
            else:
                change = 100 if current_revenue > 0 else 0
            
            return {
                'total': current_revenue,
                'change': round(change, 2)
            }

    @staticmethod
    def get_sales_report(start_date, end_date):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    O.ORDER_ID,
                    O.ORDER_DATE,
                    C.FIRST_NAME || ' ' || C.LAST_NAME as CUSTOMER,
                    O.TOTAL_AMOUNT,
                    P.PAYMENT_MODE,
                    P.AMOUNT_PAID
                FROM ORDERS O
                JOIN CUSTOMER C ON O.CUSTOMER_ID = C.CUSTOMER_ID
                LEFT JOIN PAYMENT P ON O.ORDER_ID = P.ORDER_ID
                WHERE O.ORDER_DATE BETWEEN ? AND ?
                AND O.ORDER_STATUS = 'COMPLETED'
                ORDER BY O.ORDER_DATE DESC, O.ORDER_TIME DESC
            ''', (start_date, end_date))
            return cursor.fetchall()

    @staticmethod
    def get_menu_performance(start_date, end_date):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    MI.ITEM_NAME,
                    MI.ITEM_CATEGORY,
                    SUM(OI.QUANTITY) as QUANTITY_SOLD,
                    SUM(OI.ITEM_TOTAL) as TOTAL_REVENUE
                FROM MENU_ITEM MI
                JOIN ORDER_ITEM OI ON MI.MENUITEM_NUMBER = OI.MENUITEM_NUMBER
                JOIN ORDERS O ON OI.ORDER_ID = O.ORDER_ID
                WHERE O.ORDER_DATE BETWEEN ? AND ?
                AND O.ORDER_STATUS = 'COMPLETED'
                GROUP BY MI.MENUITEM_NUMBER, MI.ITEM_NAME, MI.ITEM_CATEGORY
                ORDER BY TOTAL_REVENUE DESC
            ''', (start_date, end_date))
            return cursor.fetchall()
