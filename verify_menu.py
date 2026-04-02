import sqlite3

def verify_menu():
    try:
        conn = sqlite3.connect('restaurant.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM MENU_ITEM ORDER BY ITEM_CATEGORY, ITEM_NAME')
        items = cursor.fetchall()
        
        if not items:
            print("No menu items found!")
            return
            
        current_category = None
        for item in items:
            if item[2] != current_category:
                current_category = item[2]
                print(f"\n{current_category}:")
            print(f"- {item[1]}: ${item[3]}")
            
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    verify_menu()