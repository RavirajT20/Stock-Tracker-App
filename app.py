import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# Connect to database
conn = sqlite3.connect('stock_data.db', check_same_thread=False)

# Create table if not exists
conn.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_name TEXT NOT NULL,
        transaction_type TEXT CHECK(transaction_type IN ('buy', 'sell')),
        quantity INTEGER NOT NULL,
        price_per_share REAL NOT NULL,
        date TEXT NOT NULL
    )
''')
conn.commit()

# Function to insert data
def add_transaction(stock, t_type, qty, price, t_date):
    conn.execute('''INSERT INTO transactions (stock_name, transaction_type, quantity, price_per_share, date)
                    VALUES (?, ?, ?, ?, ?)''', (stock, t_type, qty, price, t_date))
    conn.commit()

# Function to delete data
def delete_transaction(t_id):
    conn.execute("DELETE FROM transactions WHERE id=?", (t_id,))
    conn.commit()

# Reset form values
if "reset_form" not in st.session_state:
    st.session_state.update({
        "stock": "",
        "qty": 1,
        "price": 0.0,
        "t_date": date.today(),
        "reset_form": False
    })

if st.session_state.reset_form:
    st.session_state.update({
        "stock": "",
        "qty": 1,
        "price": 0.0,
        "t_date": date.today(),
        "reset_form": False
    })

# UI Header
st.title("📈 Stock Tracker App")
st.markdown("Track your buying/selling and profit/loss of stocks easily.")

# Add Transaction Form
with st.form("add_form"):
    stock = st.text_input("Stock Name", key="stock")
    t_type = st.selectbox("Transaction Type", ["buy", "sell"])
    qty = st.number_input("Quantity", min_value=1, key="qty")
    price = st.number_input("Price per Share", min_value=0.0, key="price")
    t_date = st.date_input("Transaction Date", key="t_date")
    submitted = st.form_submit_button("Add Transaction")

    if submitted:
        add_transaction(stock, t_type, qty, price, str(t_date))
        st.session_state.reset_form = True
        st.success("✅ Transaction Added")
        st.rerun()

# Load DataFrame
df = pd.read_sql("SELECT * FROM transactions", conn)

# 🔍 Search Filter
st.subheader("🔎 Search Transactions")
search_query = st.text_input("Search by Stock Name").strip().lower()

if search_query:
    df = df[df['stock_name'].str.lower().str.contains(search_query)]

# 📋 Transaction Table in Expandable Section
st.subheader("📋 All Transactions")
with st.expander("Click to Expand/Collapse Transactions Table", expanded=True):
    if not df.empty:
        for idx, row in df.iterrows():
            col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 1.2, 1, 1.5, 1.5, 1.5, 1])
            col1.write(f"📌 {row['stock_name']}")
            col2.write(row['transaction_type'].capitalize())
            col3.write(row['quantity'])
            col4.write(f"₹{row['price_per_share']:.2f}")
            col5.write(f"₹{row['quantity'] * row['price_per_share']:.2f}")
            col6.write(row['date'])
            if col7.button("❌", key=f"delete_{row['id']}"):
                delete_transaction(row['id'])
                st.rerun()
    else:
        st.info("No transactions to display.")

# 📥 Download CSV Button
if not df.empty:
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Transactions as CSV",
        data=csv,
        file_name='stock_transactions.csv',
        mime='text/csv',
    )

# 📊 Summary
if not df.empty:
    df['total'] = df['quantity'] * df['price_per_share']
    buy_total = df[df['transaction_type'] == 'buy']['total'].sum()
    sell_total = df[df['transaction_type'] == 'sell']['total'].sum()
    profit = sell_total - buy_total

    st.subheader("📊 Summary")
    st.write(f"🟢 Total Buy: ₹{buy_total:.2f}")
    st.write(f"🔴 Total Sell: ₹{sell_total:.2f}")
    st.write(f"💰 Net Profit/Loss: ₹{profit:.2f}")
