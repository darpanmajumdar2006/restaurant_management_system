import sqlite3

def init_database(conn=None):
    if conn is None:
        conn = sqlite3.connect('restaurant.db')
    cursor = conn.cursor()

    try:
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

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    init_database()
    
#NUMBER GENERATED BY DEFAULT AS IDENTITY → INTEGER PRIMARY KEY AUTOINCREMENT
#VARCHAR2 → TEXT
#NUMBER → INTEGER or DECIMAL
#SYSDATE → date('now')
#SYSTIMESTAMP → CURRENT_TIMESTAMP
#Integrated CHECK constraints directly in table creation
#Added IF NOT EXISTS to prevent errors on repeated runs