import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client

# ---------- ПОДКЛЮЧЕНИЕ К SUPABASE ----------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------- НАСТРОЙКИ ----------
DAILY_LIMIT = 700
START_DATE = date(2026, 4, 1)
TABLE_NAME = "savings_data"  # ← имя твоей таблицы

st.set_page_config(page_title="Моя копилка", layout="wide")
st.title("💰 Моя копилка")


# ---------- ФУНКЦИИ ----------
def load_data():
    response = supabase.table(TABLE_NAME).select("*").order("date").execute()
    if not response.data:
        return pd.DataFrame(columns=['date', 'spent'])
    df = pd.DataFrame(response.data)
    df['date'] = pd.to_datetime(df['date']).dt.date
    return df


def save_data(date_input, spent_input):
    supabase.table(TABLE_NAME).upsert({
        "date": str(date_input),
        "spent": spent_input
    }).execute()


# ---------- ФОРМА ДЛЯ ДОБАВЛЕНИЯ ----------
st.subheader("➕ Добавить запись")
with st.form("savings_form"):
    col1, col2 = st.columns(2)
    with col1:
        date_input = st.date_input("Дата", value=date.today())
    with col2:
        spent_input = st.number_input("Потрачено на алкоголь (₽)", min_value=0, step=50)
    submitted = st.form_submit_button("Сохранить")

    if submitted:
        save_data(date_input, spent_input)
        st.success(f"✅ Записано: потрачено {spent_input} ₽ за {date_input}")
        st.rerun()

# ---------- ЗАГРУЗКА ДАННЫХ ИЗ SUPABASE ----------
df = load_data()

if df.empty:
    st.info("📌 Нет данных. Добавьте первую запись.")
    st.stop()

df = df.sort_values('date')
df['saved'] = DAILY_LIMIT - df['spent']
df['cumulative_saved'] = df['saved'].cumsum()
df['planned'] = [((d - START_DATE).days + 1) * DAILY_LIMIT for d in df['date']]

planned_total = df['planned'].iloc[-1]
actual_saved = df['cumulative_saved'].iloc[-1]

# ---------- КАРТОЧКИ ----------
st.subheader("📊 Итоги")
col1, col2 = st.columns(2)
with col1:
    st.metric("📉 План (могло быть потрачено)", f"-{planned_total:,.0f} ₽", delta_color="inverse")
with col2:
    st.metric("💰 Накоплено в копилке", f"{actual_saved:,.0f} ₽")

# ---------- ТАБЛИЦА ----------
st.subheader("📋 Детализация по дням")
df_display = df.copy()
df_display['date'] = df_display['date'].astype(str)
df_display['planned'] = -df_display['planned']
df_display.columns = ['Дата', 'Потрачено (₽)', 'Отложено в копилку (₽)',
                      'Накоплено всего (₽)', 'План (могло быть потрачено, ₽)']
st.dataframe(df_display, use_container_width=True)

# ---------- ГРАФИК ----------
st.subheader("📈 График: накоплено vs план")
chart_df = df_display[['Дата', 'Накоплено всего (₽)', 'План (могло быть потрачено, ₽)']].copy()
chart_df = chart_df.rename(columns={
    'Накоплено всего (₽)': 'Факт (копилка)',
    'План (могло быть потрачено, ₽)': 'План (отрицательная сумма)'
})
st.line_chart(chart_df.set_index('Дата'), use_container_width=True)