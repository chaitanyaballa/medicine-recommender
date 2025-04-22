import streamlit as st
import pickle
import pandas as pd
from PIL import Image
import hashlib
import sqlite3

# Database setup for authentication
conn = sqlite3.connect('users.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users
             (username TEXT PRIMARY KEY, password TEXT)''')
conn.commit()

# Custom CSS for enhanced UI
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("css/style.css")

# Load data
medicines_dict = pickle.load(open('medicine_dict.pkl','rb'))
medicines = pd.DataFrame(medicines_dict)
similarity = pickle.load(open('similarity.pkl','rb'))

# Recommendation function
def recommend(medicine):
    medicine_index = medicines[medicines['Drug_Name'] == medicine].index[0]
    distances = similarity[medicine_index]
    medicines_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]
    return [medicines.iloc[i[0]].Drug_Name for i in medicines_list]

# Authentication functions
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

def create_user(username, password):
    c.execute('INSERT INTO users(username,password) VALUES (?,?)', (username, make_hashes(password)))
    conn.commit()

def login_user(username, password):
    c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, make_hashes(password)))
    return c.fetchone()

# Page navigation
def landing_page():
    st.title("Welcome to MedRec")
    st.subheader("Your Personalized Medicine Recommendation System")
    
    # Hero image with error handling
    try:
        hero_img = Image.open('images/hero-image.jpg')
        st.image(hero_img, use_column_width=True)
    except:
        st.warning("Hero image not found - using placeholder")
        st.image(Image.new('RGB', (800, 400), color='#4a90e2'))
    
    st.write("""
    Discover alternative medications tailored to your needs.
    Our AI-powered system helps you find suitable substitutes for your prescriptions.
    """)
    
    if st.button("Get Started"):
        st.session_state.page = "login"

def login_page():
    st.title("Login / Register")
    
    menu = ["Login", "Register"]
    choice = st.selectbox("Select Option", menu)
    
    if choice == "Login":
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')
        
        if st.button("Login"):
            if login_user(username, password):
                st.success("Logged In as {}".format(username))
                st.session_state.logged_in = True
                st.session_state.page = "main"
            else:
                st.warning("Incorrect Username/Password")
    
    else:
        new_user = st.text_input("Username")
        new_password = st.text_input("Password", type='password')
        
        if st.button("Register"):
            create_user(new_user, new_password)
            st.success("Account created! Please login.")

def main_page():
    st.title('Medicine Recommender System')
    
    # Sidebar with user info
    st.sidebar.title("User Profile")
    if st.session_state.get('logged_in'):
        st.sidebar.success("Logged In")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.page = "landing"
    else:
        st.session_state.page = "login"
    
    # Main content
    selected_medicine = st.selectbox(
        'Search for medicine alternatives',
        medicines['Drug_Name'].values)
    
    if st.button('Recommend'):
        recommendations = recommend(selected_medicine)
        
        st.subheader("Recommended Alternatives:")
        for i, med in enumerate(recommendations, 1):
            col1, col2 = st.columns([1, 3])
            with col1:
                try:
                    st.image(Image.open(f'images/med_{i}.jpg'), width=100)
                except:
                    st.image(Image.new('RGB', (100, 100), color='#2b5876'))
            with col2:
                st.write(f"{i}. {med}")
                st.write(f"[Purchase on PharmEasy](https://pharmeasy.in/search/all?name={med})")

# App flow
if 'page' not in st.session_state:
    st.session_state.page = "landing"
    st.session_state.logged_in = False

if st.session_state.page == "landing":
    landing_page()
elif st.session_state.page == "login":
    login_page()
elif st.session_state.page == "main":
    main_page()
