import sqlite3
import streamlit as st
from datetime import date
import random
import pandas as pd  # Ensure pandas is imported

# Database connection
conn = sqlite3.connect("habitbuddy.db", check_same_thread=False)
c = conn.cursor()

# Create tables if not exists
c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                password TEXT)''')

# Create habit table with streak column if it does not exist
c.execute('''CREATE TABLE IF NOT EXISTS habits (
                user_id INTEGER,
                habit TEXT,
                date DATE,
                status TEXT,
                streak INTEGER DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id))''')

# Create tasks table with priority column
c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                user_id INTEGER,
                task TEXT,
                date DATE,
                status TEXT,
                priority TEXT DEFAULT 'Medium',
                feedback TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id))''')

# Create user activity tracking table
c.execute('''CREATE TABLE IF NOT EXISTS user_activity (
                total_users INTEGER DEFAULT 0,
                active_users INTEGER DEFAULT 0)''')

# Function to get random motivational quote
def get_motivational_quote():
    quotes = [
        "Believe you can and you're halfway there.",
        "Don't watch the clock; do what it does. Keep going.",
        "The future depends on what we do in the present.",
        "You are never too old to set another goal or to dream a new dream.",
        "Act as if what you do makes a difference. It does."
    ]
    return random.choice(quotes)

# Add default task for today if not exists
def add_daily_task(user_id):
    today = date.today()
    task = "Review your top 3 priorities for today"
    
    c.execute("SELECT * FROM tasks WHERE user_id = ? AND date = ? AND task = ?", (user_id, today, task))
    existing_task = c.fetchone()

    if not existing_task:
        c.execute("INSERT INTO tasks (user_id, task, date, status, priority) VALUES (?, ?, ?, ?, ?)", 
                  (user_id, task, today, "No", "Medium"))
        conn.commit()

# Update streak function
def update_streak(user_id, habit):
    c.execute("SELECT * FROM habits WHERE user_id = ? AND habit = ? ORDER BY date DESC LIMIT 1", (user_id, habit))
    last_habit = c.fetchone()
    
    new_streak = 1 if not last_habit or last_habit[3] == "No" else last_habit[4] + 1
    c.execute("UPDATE habits SET streak = ? WHERE user_id = ? AND habit = ?", (new_streak, user_id, habit))
    conn.commit()

# Signup function
def signup(email, password):
    try:
        c.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
        conn.commit()
        
        # Update total user count in user_activity table
        c.execute("UPDATE user_activity SET total_users = total_users + 1")
        conn.commit()

        return True
    except:
        return False

# Login function
def login(email, password):
    c.execute("SELECT id FROM users WHERE email = ? AND password = ?", (email, password))
    user = c.fetchone()
    
    if user:
        # Update active user count in user_activity table
        c.execute("UPDATE user_activity SET active_users = active_users + 1")
        conn.commit()
        return user[0]
    else:
        return None

# Main app function
def main_app(user_id):
    # Set new app name and title
    st.title("💪 HabitMaster – Your Personal Habit Tracker")
    today = date.today()

    # Display motivational quote
    st.subheader("💬 Daily Motivation")
    quote = get_motivational_quote()
    st.write(f"**{quote}**")

    # Automatically add a daily task
    add_daily_task(user_id)

    # Display Total and Active User Count
    c.execute("SELECT total_users, active_users FROM user_activity")
    user_counts = c.fetchone()
    total_users, active_users = user_counts if user_counts else (0, 0)
    
    st.markdown(f"**Total Users:** {total_users}")
    st.markdown(f"**Active Users Today:** {active_users}")

    # Add Habit Entry Section
    st.subheader("✅ Add Habit Entry")
    habit = st.text_input("Enter habit")
    status = st.selectbox("Completed today?", ["Yes", "No"])
    if st.button("Add Entry"):
        if habit:
            # Update the habit streak on completion
            update_streak(user_id, habit)
            c.execute("INSERT INTO habits (user_id, habit, date, status) VALUES (?, ?, ?, ?)",
                      (user_id, habit, today, status))
            conn.commit()
            st.success("Habit entry added!")

    st.subheader("📋 Your Habit Log")
    habit_df = pd.read_sql_query("SELECT habit, date, status, streak FROM habits WHERE user_id = ?", conn, params=(user_id,))
    st.dataframe(habit_df)

    if not habit_df.empty:
        st.subheader("📊 Habit Completion Rate")
        rate = habit_df[habit_df["status"] == "Yes"].shape[0] / habit_df.shape[0] * 100
        st.write(f"✅ {rate:.2f}% completed")

        # Bar chart for habit streaks
        st.subheader("📊 Habit Streaks")
        st.bar_chart(habit_df.groupby("streak")["status"].count())

    # Add Daily Task
    st.subheader("✅ Add Daily Task")
    task = st.text_input("Enter task")
    priority = st.selectbox("Priority", ["High", "Medium", "Low"])
    task_status = st.selectbox("Completed?", ["Yes", "No"])
    
    # Feedback moved to the bottom of the form
    if st.button("Add Task"):
        if task:
            c.execute("INSERT INTO tasks (user_id, task, date, status, priority) VALUES (?, ?, ?, ?, ?)",
                      (user_id, task, today, task_status, priority))
            conn.commit()
            st.success("Task entry added!")

    # Task log
    st.subheader("📋 Your Task Log")
    task_df = pd.read_sql_query("SELECT task, date, status, priority FROM tasks WHERE user_id = ?", conn, params=(user_id,))

    st.dataframe(task_df)

    # Task prioritization and completion dashboard
    if not task_df.empty:
        st.subheader("📊 Task Completion by Priority")
        task_df["priority"] = task_df["priority"].astype("category")
        st.bar_chart(task_df.groupby("priority")["status"].value_counts().unstack().fillna(0))

    # Display feedback section
    st.subheader("💬 Provide Feedback for Today's Tasks")
    feedback = st.text_area("Share your thoughts on your tasks (Optional)")
    
    if feedback:
        st.write(f"**Your Feedback:** {feedback}")
    
    st.markdown("""
        <style>
        .css-1v0mbdj {
            background-color: #f4f4f4;
            color: #333;
        }
        .css-1gw7b2w {
            background-color: #b0e0e6;
            color: #333;
        }
        .css-145k9m0 {
            background-color: #98fb98;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            font-size: 18px;
            padding: 10px 20px;
            border-radius: 5px;
            box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2);
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        .stTextInput>div {
            background-color: #ffffff;
            border-radius: 10px;
            box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
        }
        </style>
    """, unsafe_allow_html=True)

# Authentication interface
def login_signup_page():
    st.title("🔐 HabitMaster Login")

    action = st.radio("Choose an option:", ["Login", "Sign Up"])

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if action == "Sign Up":
        if st.button("Create Account"):
            if signup(email, password):
                st.success("Account created. Please log in.")
            else:
                st.error("User already exists.")
    else:
        if st.button("Login"):
            user_id = login(email, password)
            if user_id:
                st.session_state.user_id = user_id
                st.session_state.authenticated = True
                st.success("Logged in!")
            else:
                st.error("Invalid credentials.")

# App logic
if "authenticated" in st.session_state and st.session_state.authenticated:
    main_app(st.session_state.user_id)
else:
    login_signup_page()
