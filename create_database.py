import sqlite3

def init_database(conn=None):
    should_close = False
    if conn is None:
        conn = sqlite3.connect('restaurant.db')
        should_close = True
    cursor = conn.cursor()

    try:
        # Add sample data if tables are empty
        cursor.execute('SELECT COUNT(*) FROM REST_TABLE')
        if cursor.fetchone()[0] == 0:
            # Add sample tables
            cursor.execute("INSERT INTO REST_TABLE (BOOKING_ID, SEATING_CAPACITY, BOOKING_STATUS) VALUES (1, 2, 'AVAILABLE')")
            cursor.execute("INSERT INTO REST_TABLE (BOOKING_ID, SEATING_CAPACITY, BOOKING_STATUS) VALUES (2, 4, 'AVAILABLE')")
            cursor.execute("INSERT INTO REST_TABLE (BOOKING_ID, SEATING_CAPACITY, BOOKING_STATUS) VALUES (3, 6, 'AVAILABLE')")
            cursor.execute("INSERT INTO REST_TABLE (BOOKING_ID, SEATING_CAPACITY, BOOKING_STATUS) VALUES (4, 8, 'AVAILABLE')")

        cursor.execute('SELECT COUNT(*) FROM MENU_ITEM')
        if cursor.fetchone()[0] == 0:
            # Add sample menu items
            sample_menu = [
                # Starters
                ('Fresh Garden Salad', 'STARTER', 8.99, 'AVAILABLE'),
                ('Garlic Bread', 'STARTER', 5.99, 'AVAILABLE'),
                ('Chicken Wings', 'STARTER', 12.99, 'AVAILABLE'),
                ('Tomato Soup', 'STARTER', 6.99, 'AVAILABLE'),
                
                # Main Course
                ('Classic Burger', 'MAIN COURSE', 14.99, 'AVAILABLE'),
                ('Margherita Pizza', 'MAIN COURSE', 16.99, 'AVAILABLE'),
                ('Grilled Salmon', 'MAIN COURSE', 24.99, 'AVAILABLE'),
                ('Pasta Alfredo', 'MAIN COURSE', 18.99, 'AVAILABLE'),
                ('Chicken Curry', 'MAIN COURSE', 19.99, 'AVAILABLE'),
                
                # Desserts
                ('Chocolate Cake', 'DESSERT', 7.99, 'AVAILABLE'),
                ('Ice Cream Sundae', 'DESSERT', 6.99, 'AVAILABLE'),
                ('Apple Pie', 'DESSERT', 8.99, 'AVAILABLE'),
                ('Cheesecake', 'DESSERT', 9.99, 'AVAILABLE'),
                
                # Beverages
                ('Cola', 'BEVERAGE', 2.99, 'AVAILABLE'),
                ('Coffee', 'BEVERAGE', 3.99, 'AVAILABLE'),
                ('Fresh Orange Juice', 'BEVERAGE', 4.99, 'AVAILABLE'),
                ('Iced Tea', 'BEVERAGE', 3.49, 'AVAILABLE'),
            ]
            
            for item in sample_menu:
                cursor.execute("""
                    INSERT INTO MENU_ITEM (ITEM_NAME, ITEM_CATEGORY, PRICE, AVAILABILITY_STATUS)
                    VALUES (?, ?, ?, ?)
                """, item)
                
        # Customer table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS CUSTOMER (
            CUSTOMER_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            FIRST_NAME TEXT NOT NULL,
            MIDDLE_NAME TEXT,
            LAST_NAME TEXT NOT NULL,
            PHONE TEXT UNIQUE,
            EMAIL TEXT UNIQUE,
            ADDRESS TEXT
        )
        ''')

        # Restaurant tables
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS REST_TABLE (
            TABLE_NUMBER INTEGER PRIMARY KEY AUTOINCREMENT,
            BOOKING_ID INTEGER NOT NULL UNIQUE,
            SEATING_CAPACITY INTEGER CHECK(SEATING_CAPACITY>0),
            BOOKING_STATUS TEXT DEFAULT 'AVAILABLE' 
                CHECK (BOOKING_STATUS IN ('AVAILABLE','OCCUPIED','RESERVED'))
        )
        ''')

        # Menu items
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS MENU_ITEM (
            MENUITEM_NUMBER INTEGER PRIMARY KEY AUTOINCREMENT,
            ITEM_NAME TEXT NOT NULL,
            ITEM_CATEGORY TEXT CHECK (ITEM_CATEGORY IN ('STARTER','MAIN COURSE','DESSERT','BEVERAGE')),
            PRICE DECIMAL(10,2) CHECK (PRICE > 0),
            AVAILABILITY_STATUS TEXT DEFAULT 'AVAILABLE'
                CHECK (AVAILABILITY_STATUS IN ('AVAILABLE','OUT OF STOCK'))
        )
        ''')

        # Orders
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ORDERS (
            ORDER_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            CUSTOMER_ID INTEGER NOT NULL,
            TABLE_NUMBER INTEGER NOT NULL,
            ORDER_DATE DATE DEFAULT (date('now')),
            ORDER_TIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            TOTAL_AMOUNT DECIMAL(10,2) CHECK (TOTAL_AMOUNT > 0),
            ORDER_STATUS TEXT DEFAULT 'PENDING'
                CHECK (ORDER_STATUS IN ('PENDING','COMPLETED','CANCELLED')),
            FOREIGN KEY (CUSTOMER_ID) REFERENCES CUSTOMER(CUSTOMER_ID),
            FOREIGN KEY (TABLE_NUMBER) REFERENCES REST_TABLE(TABLE_NUMBER)
        )
        ''')

        # Payment
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS PAYMENT (
            TRANSACTION_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ORDER_ID INTEGER NOT NULL,
            PAYMENT_DATE DATE DEFAULT (date('now')),
            PAYMENT_MODE TEXT CHECK (PAYMENT_MODE IN ('CASH','CARD','UPI')),
            AMOUNT_PAID DECIMAL(10,2) CHECK (AMOUNT_PAID >= 0),
            FOREIGN KEY (ORDER_ID) REFERENCES ORDERS(ORDER_ID)
        )
        ''')

        # Reservation
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS RESERVATION (
            RESERVATION_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            CUSTOMER_ID INTEGER NOT NULL,
            TABLE_NUMBER INTEGER NOT NULL,
            RESERVATION_DATE DATE NOT NULL,
            RESERVATION_TIME TIMESTAMP NOT NULL,
            NUMBER_OF_PEOPLE INTEGER CHECK (NUMBER_OF_PEOPLE > 0),
            FOREIGN KEY (CUSTOMER_ID) REFERENCES CUSTOMER(CUSTOMER_ID),
            FOREIGN KEY (TABLE_NUMBER) REFERENCES REST_TABLE(TABLE_NUMBER)
        )
        ''')

        # Order items
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ORDER_ITEM (
            ORDER_ID INTEGER,
            MENUITEM_NUMBER INTEGER,
            QUANTITY INTEGER NOT NULL CHECK (QUANTITY > 0),
            ITEM_TOTAL DECIMAL(10,2) CHECK (ITEM_TOTAL >= 0),
            PRIMARY KEY(ORDER_ID, MENUITEM_NUMBER),
            FOREIGN KEY (ORDER_ID) REFERENCES ORDERS(ORDER_ID),
            FOREIGN KEY (MENUITEM_NUMBER) REFERENCES MENU_ITEM(MENUITEM_NUMBER)
        )
        ''')

        # Staff
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS STAFF (
            STAFF_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            FIRST_NAME TEXT NOT NULL,
            MIDDLE_NAME TEXT,
            LAST_NAME TEXT NOT NULL,
            PHONE TEXT UNIQUE,
            EMAIL TEXT UNIQUE,
            ADDRESS TEXT,
            STAFF_ROLE TEXT NOT NULL CHECK (STAFF_ROLE IN ('WAITER','CHEF','MANAGER','CLEANER')),
            SHIFT_START TIMESTAMP,
            SHIFT_END TIMESTAMP
        )
        ''')

        # Staff assignment
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS STAFF_ASSIGNMENT (
            STAFF_ID INTEGER,
            ORDER_ID INTEGER,
            ROLE_IN_ORDER TEXT,
            ASSIGNMENT_TIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (STAFF_ID, ORDER_ID),
            FOREIGN KEY (STAFF_ID) REFERENCES STAFF(STAFF_ID),
            FOREIGN KEY (ORDER_ID) REFERENCES ORDERS(ORDER_ID)
        )
        ''')

        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS IDX_ORDERS_CUSTOMER ON ORDERS(CUSTOMER_ID)')
        cursor.execute('CREATE INDEX IF NOT EXISTS IDX_ORDERS_TABLE ON ORDERS(TABLE_NUMBER)')
        cursor.execute('CREATE INDEX IF NOT EXISTS IDX_ORDERITEM_MENU ON ORDER_ITEM(MENUITEM_NUMBER)')
        cursor.execute('CREATE INDEX IF NOT EXISTS IDX_PAYMENT_ORDER ON PAYMENT(ORDER_ID)')
        cursor.execute('CREATE INDEX IF NOT EXISTS IDX_RESERVATION_CUSTOMER ON RESERVATION(CUSTOMER_ID)')
        cursor.execute('CREATE INDEX IF NOT EXISTS IDX_RESERVATION_TABLE ON RESERVATION(TABLE_NUMBER)')

        conn.commit()
        print("Database initialized successfully!")
        return True

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if should_close and conn:
            conn.close()

if __name__ == "__main__":
    try:
        conn = sqlite3.connect('restaurant.db')
        success = init_database(conn)
        print(f"Database initialization {'succeeded' if success else 'failed'}")
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        if conn:
            conn.close()