import streamlit as st
import pandas as pd
import plotly.express as px
from database import DatabaseOperations
from datetime import datetime, timedelta

class RestaurantApp:
    def __init__(self):
        self.db = DatabaseOperations()
        st.set_page_config(
            page_title="Restaurant Management System",
            page_icon="🍽️",
            layout="wide"
        )

    def main(self):
        st.sidebar.title("🍽️ Restaurant Manager")
        page = st.sidebar.radio(
            "Navigation",
            ["Dashboard", "Customers", "Tables", "Menu", "Orders", "Payments", 
             "Reports", "Analytics"]
        )

        if page == "Dashboard":
            self.show_dashboard()
        elif page == "Customers":
            self.manage_customers()
        elif page == "Tables":
            self.manage_tables()
        elif page == "Menu":
            self.manage_menu()
        elif page == "Orders":
            self.manage_orders()
        elif page == "Payments":
            self.manage_payments()
        elif page == "Reports":
            self.generate_reports()
        elif page == "Analytics":
            self.show_analytics()

    def show_dashboard(self):
        st.title("Restaurant Dashboard")
        st.markdown("---")
        
        # Create three columns for metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            tables = self.db.get_all_tables()
            available_tables = sum(1 for t in tables if t[3] == 'AVAILABLE')
            st.metric(
                label="Available Tables",
                value=available_tables,
                delta=f"{available_tables}/{len(tables)}"
            )
        
        with col2:
            orders = self.db.get_all_orders()
            active_orders = sum(1 for o in orders if o[6] == 'PENDING')
            st.metric(label="Active Orders", value=active_orders)
        
        with col3:
            today_revenue = sum(o[5] for o in orders 
                              if o[3] == datetime.now().date().isoformat())
            st.metric(
                label="Today's Revenue",
                value=f"${today_revenue:,.2f}"
            )

    def manage_customers(self):
        st.title("Customer Management")
        
        tab1, tab2 = st.tabs(["Add Customer", "View Customers"])
        
        with tab1:
            with st.form("add_customer_form"):
                col1, col2 = st.columns(2)
                with col1:
                    first_name = st.text_input("First Name")
                    last_name = st.text_input("Last Name")
                    phone = st.text_input("Phone")
                
                with col2:
                    middle_name = st.text_input("Middle Name")
                    email = st.text_input("Email")
                    address = st.text_area("Address")
                
                if st.form_submit_button("Add Customer"):
                    if not first_name or not last_name or not phone:
                        st.error("First name, last name, and phone are required!")
                    else:
                        try:
                            self.db.add_customer(
                                first_name, middle_name, last_name,
                                phone, email, address
                            )
                            st.success("Customer added successfully!")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
        
        with tab2:
            customers = self.db.get_all_customers()
            if customers:
                df = pd.DataFrame(customers, columns=[
                    'ID', 'First Name', 'Middle Name', 'Last Name',
                    'Phone', 'Email', 'Address'
                ])
                st.dataframe(df)
            else:
                st.info("No customers found in the database.")

    def manage_tables(self):
        st.title("Table Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Add New Table")
            with st.form("add_table_form"):
                seating_capacity = st.number_input(
                    "Seating Capacity",
                    min_value=1,
                    value=4
                )
                status = st.selectbox(
                    "Initial Status",
                    ["AVAILABLE", "RESERVED", "OCCUPIED"]
                )
                
                if st.form_submit_button("Add Table"):
                    try:
                        self.db.add_table(seating_capacity, status)
                        st.success("Table added successfully!")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        with col2:
            st.subheader("Current Table Status")
            tables = self.db.get_all_tables()
            if tables:
                df = pd.DataFrame(tables, columns=[
                    'Table Number', 'Booking ID', 
                    'Seating Capacity', 'Status'
                ])
                
                # Color-code the status
                def color_status(val):
                    colors = {
                        'AVAILABLE': 'green',
                        'OCCUPIED': 'red',
                        'RESERVED': 'orange'
                    }
                    return f'color: {colors.get(val, "black")}'
                
                st.dataframe(df.style.applymap(
                    color_status,
                    subset=['Status']
                ))
            else:
                st.info("No tables found in the database.")

    def manage_menu(self):
        st.title("Menu Management")
        
        tab1, tab2 = st.tabs(["Add Menu Item", "View Menu"])
        
        with tab1:
            with st.form("add_menu_form"):
                col1, col2 = st.columns(2)
                with col1:
                    item_name = st.text_input("Item Name")
                    category = st.selectbox(
                        "Category",
                        ["STARTER", "MAIN COURSE", "DESSERT", "BEVERAGE"]
                    )
                
                with col2:
                    price = st.number_input(
                        "Price ($)",
                        min_value=0.0,
                        value=10.0,
                        step=0.5
                    )
                    status = st.selectbox(
                        "Availability",
                        ["AVAILABLE", "OUT OF STOCK"]
                    )
                
                if st.form_submit_button("Add Menu Item"):
                    if not item_name or price <= 0:
                        st.error("Please provide item name and valid price!")
                    else:
                        try:
                            self.db.add_menu_item(
                                item_name, category, price, status
                            )
                            st.success("Menu item added successfully!")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
        
        with tab2:
            menu_items = self.db.get_all_menu_items()
            if menu_items:
                df = pd.DataFrame(menu_items, columns=[
                    'Item ID', 'Name', 'Category',
                    'Price', 'Availability'
                ])
                st.dataframe(df)
            else:
                st.info("No menu items found in the database.")

    def manage_orders(self):
        st.title("Order Management")
        
        tab1, tab2 = st.tabs(["Create Order", "View Orders"])
        
        with tab1:
            self.create_new_order()
        
        with tab2:
            self.view_orders()

    def create_new_order(self):
        with st.form("create_order_form"):
            # Get customer list
            customers = self.db.get_all_customers()
            if not customers:
                st.error("No customers in database. Please add customers first.")
                return
            
            customer_dict = {
                f"{c[1]} {c[3]} ({c[4]})": c[0] 
                for c in customers
            }
            selected_customer = st.selectbox(
                "Select Customer",
                options=list(customer_dict.keys())
            )
            
            # Get available tables
            tables = self.db.get_all_tables()
            available_tables = [
                t for t in tables 
                if t[3] == 'AVAILABLE'
            ]
            if not available_tables:
                st.error("No tables available at the moment.")
                return
            
            table_dict = {
                f"Table {t[0]} (Seats: {t[2]})": t[0] 
                for t in available_tables
            }
            selected_table = st.selectbox(
                "Select Table",
                options=list(table_dict.keys())
            )
            
            # Get menu items
            menu_items = self.db.get_all_menu_items()
            if not menu_items:
                st.error("No menu items available. Please add menu items first.")
                return
            
            st.subheader("Select Items")
            selected_items = {}
            
            # Create columns for menu categories
            menu_df = pd.DataFrame(menu_items)
            categories = menu_df[2].unique()
            
            for category in categories:
                st.write(f"### {category}")
                category_items = [
                    item for item in menu_items 
                    if item[2] == category
                ]
                
                for item in category_items:
                    if item[4] == 'AVAILABLE':
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            st.write(f"{item[1]} (${item[3]:.2f})")
                        with col2:
                            quantity = st.number_input(
                                f"Qty",
                                min_value=0,
                                key=f"item_{item[0]}"
                            )
                        if quantity > 0:
                            selected_items[item[0]] = quantity
            
            if st.form_submit_button("Create Order"):
                if not selected_items:
                    st.error("Please select at least one item!")
                else:
                    try:
                        customer_id = customer_dict[selected_customer]
                        table_number = table_dict[selected_table]
                        items = [
                            (item_id, qty) 
                            for item_id, qty in selected_items.items()
                        ]
                        order_id = self.db.create_order(
                            customer_id,
                            table_number,
                            items
                        )
                        st.success(f"Order created successfully! Order ID: {order_id}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    def view_orders(self):
        orders = self.db.get_all_orders()
        if orders:
            df = pd.DataFrame(orders, columns=[
                'Order ID', 'Customer ID', 'Table Number',
                'Date', 'Time', 'Total Amount', 'Status',
                'Customer First Name', 'Customer Last Name'
            ])
            st.dataframe(df)
        else:
            st.info("No orders found in the database.")

    def manage_payments(self):
        st.title("Payment Management")
        
        orders = self.db.get_all_orders()
        unpaid_orders = [
            order for order in orders 
            if order[6] == 'PENDING'
        ]
        
        if unpaid_orders:
            st.subheader("Process Payment")
            with st.form("payment_form"):
                order_dict = {
                    f"Order #{o[0]} - {o[7]} {o[8]} (${o[5]:.2f})": o[0] 
                    for o in unpaid_orders
                }
                selected_order = st.selectbox(
                    "Select Order",
                    options=list(order_dict.keys())
                )
                
                payment_mode = st.selectbox(
                    "Payment Mode",
                    ["CASH", "CARD", "UPI"]
                )
                
                if st.form_submit_button("Process Payment"):
                    try:
                        order_id = order_dict[selected_order]
                        amount = next(
                            o[5] for o in unpaid_orders 
                            if o[0] == order_id
                        )
                        self.db.process_payment(
                            order_id,
                            payment_mode,
                            amount
                        )
                        st.success("Payment processed successfully!")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        else:
            st.info("No pending payments.")

    def generate_reports(self):
        st.title("Reports")
        report_type = st.selectbox(
            "Select Report Type",
            ["Sales Report", "Menu Performance"]
        )

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date")
        with col2:
            end_date = st.date_input("End Date")

        if st.button("Generate Report"):
            if report_type == "Sales Report":
                self.generate_sales_report(start_date, end_date)
            elif report_type == "Menu Performance":
                self.generate_menu_report(start_date, end_date)

    def generate_sales_report(self, start_date, end_date):
        try:
            sales_data = self.db.get_sales_report(start_date, end_date)
            if sales_data:
                df = pd.DataFrame(sales_data, columns=[
                    'Order ID', 'Date', 'Customer',
                    'Total Amount', 'Payment Mode',
                    'Amount Paid'
                ])
                
                st.subheader("Sales Summary")
                total_revenue = df['Amount Paid'].sum()
                total_orders = len(df)
                avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Revenue", f"${total_revenue:,.2f}")
                with col2:
                    st.metric("Total Orders", total_orders)
                with col3:
                    st.metric("Average Order Value", f"${avg_order_value:,.2f}")
                
                st.subheader("Detailed Sales Data")
                st.dataframe(df)
                
                # Download option
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download Report",
                    csv,
                    "sales_report.csv",
                    "text/csv"
                )
            else:
                st.info("No sales data found for the selected period.")
        except Exception as e:
            st.error(f"Error generating report: {str(e)}")

    def generate_menu_report(self, start_date, end_date):
        try:
            menu_data = self.db.get_menu_performance(start_date, end_date)
            if menu_data:
                df = pd.DataFrame(menu_data, columns=[
                    'Item Name', 'Category',
                    'Quantity Sold', 'Total Revenue'
                ])
                
                st.subheader("Menu Performance Summary")
                fig = px.bar(
                    df,
                    x='Item Name',
                    y=['Quantity Sold', 'Total Revenue'],
                    barmode='group',
                    title='Item Performance'
                )
                st.plotly_chart(fig)
                
                st.subheader("Detailed Menu Data")
                st.dataframe(df)
                
                # Download option
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download Report",
                    csv,
                    "menu_report.csv",
                    "text/csv"
                )
            else:
                st.info("No menu performance data found for the selected period.")
        except Exception as e:
            st.error(f"Error generating report: {str(e)}")

    def show_analytics(self):
        st.title("Analytics Dashboard")
        period = st.selectbox(
            "Select Time Period",
            ["Last 7 Days", "Last 30 Days", "Last 90 Days"]
        )
        
        try:
            metrics = self.db.get_revenue_metrics(period)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Total Revenue",
                    f"${metrics['total']:,.2f}",
                    f"{metrics['change']}%"
                )
            
            # Add more analytics as needed
            
        except Exception as e:
            st.error(f"Error loading analytics: {str(e)}")

if __name__ == "__main__":
    app = RestaurantApp()
    app.main()