import streamlit as st
from supabase import create_client, Client
import pandas as pd

# 1. Безопасная очистка ключей
raw_url = st.secrets.get("SUPABASE_URL", "")
raw_key = st.secrets.get("SUPABASE_KEY", "")

# Убираем пробелы, кавычки и слэши в конце
url = raw_url.strip().strip('"').strip("'").rstrip('/')
key = raw_key.strip().strip('"').strip("'")

# 2. Инициализация клиента
try:
    if not url.startswith("https://"):
        st.error("Ошибка: URL в Secrets должен начинаться с https://")
        st.stop()
    
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error(f"Не удалось подключиться к базе: {e}")
    st.stop()

# --- Дальше идет твой основной код ---
st.set_page_config(page_title="Salon Booking System", page_icon="💅", layout="wide")

st.set_page_config(page_title="Salon Booking System", page_icon="💅", layout="wide")

# Кастомный CSS для красоты
st.markdown("""
    <style>
    .main { background-color: #fff5f8; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #ff4b4b; color: white; }
    </style>
    """, unsafe_allow_html)

# Меню
menu = ["✨ Записаться", "🔐 Панель Мастера"]
choice = st.sidebar.selectbox("Меню", menu)

# --- ОКНО КЛИЕНТА ---
if choice == "✨ Записаться":
    st.title("Добро пожаловать в наш салон! 🌸")
    st.subheader("Заполните форму для онлайн-записи")
    
    with st.form("client_form", clear_on_submit=True):
        name = st.text_input("Ваше Имя и Фамилия")
        email = st.text_input("Ваш Email (для уведомлений)")
        phone = st.text_input("Номер телефона (+48...)")
        service = st.selectbox("Выберите услуга", ["Маникюр", "Педикюр", "Брови", "Маникюр + Педикюр"])
        date = st.date_input("Выберите удобную дату")
        time = st.selectbox("Выберите время", ["09:00", "10:30", "12:00", "13:30", "15:00", "16:30", "18:00"])
        
        submit = st.form_submit_button("Записаться сейчас")
        
        if submit:
            if name and email and phone:
                booking_data = {
                    "name": name, 
                    "email": email, 
                    "phone": phone,
                    "service": service, 
                    "date": str(date), 
                    "time": time,
                    "status": "Ожидает подтверждения"
                }
                # Отправка в Supabase
                supabase.table("appointments").insert(booking_data).execute()
                st.success(f"Спасибо, {name}! Ваша заявка принята. Мы отправим подтверждение на {email}.")
                st.balloons()
            else:
                st.error("Пожалуйста, заполните все поля, чтобы мы могли с вами связаться.")

# --- ОКНО МАСТЕРА ---
elif choice == "🔐 Панель Мастера":
    st.title("Управление записями")
    password = st.text_input("Введите пароль доступа", type="password")
    
    if password == st.secrets["ADMIN_PASSWORD"]:
        # Загружаем данные из Supabase
        response = supabase.table("appointments").select("*").order("date", desc=True).execute()
        data = response.data
        
        tab1, tab2 = st.tabs(["📅 Новые записи", "👥 База клиентов"])
        
        with tab1:
            st.subheader("Список всех бронирований")
            if data:
                for item in data:
                    with st.expander(f"{item['date']} | {item['time']} - {item['name']} ({item['status']})"):
                        st.write(f"**Услуга:** {item['service']}")
                        st.write(f"**Телефон:** {item['phone']}")
                        st.write(f"**Email:** {item['email']}")
                        
                        if item['status'] == "Ожидает подтверждения":
                            if st.button(f"Подтвердить запись №{item['id']}"):
                                supabase.table("appointments").update({"status": "Подтверждено"}).eq("id", item['id']).execute()
                                st.rerun()
            else:
                st.info("Записей пока нет.")

        with tab2:
            st.subheader("Ваши клиенты и их история")
            if data:
                df = pd.DataFrame(data)
                # Группируем по email для карточки клиента
                clients = df.groupby('email').agg({
                    'name': 'first',
                    'phone': 'first',
                    'id': 'count'
                }).rename(columns={'id': 'Визитов всего'})
                
                st.table(clients)
                
                st.write("---")
                st.write("**Детальная история по каждому email:**")
                search_email = st.text_input("Введите email клиента для поиска истории")
                if search_email:
                    history = df[df['email'] == search_email][['date', 'service', 'status']]
                    st.write(history)
            else:
                st.info("База клиентов пуста.")
