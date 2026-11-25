from pathlib import Path

import pandas as pd
import streamlit as st
import joblib

st.set_page_config(page_title="SmartStay", layout="wide")
st.title("SmartStay | تحليل أسعار الإقامة")


@st.cache_data
def load_data():
    path = Path(__file__).resolve().parent / "data" / "clean.csv"
    return pd.read_csv(path)
@st.cache_resource
def load_model():
    model_path = Path(__file__).resolve().parent / "Smartstay_model.pkl"
    return joblib.load(model_path)

try:
    model = load_model()
    st.success("تم تحميل نموذج التنبؤ بنجاح")
except Exception as e:
    st.error(f"تعذر تحميل نموذج التنبؤ: {e}")
    st.stop()


try:
    data = load_data()
except (FileNotFoundError, pd.errors.EmptyDataError):
    st.error("تأكدي أن ملف data/clean.csv موجود ويحتوي على البيانات.")
    st.stop()

required = {"neighbourhood_group", "room_type", "neighbourhood", "price"}
missing = required - set(data.columns)
if missing:
    st.error("أعمدة غير موجودة في الملف: " + ", ".join(sorted(missing)))
    st.stop()

st.sidebar.header("الفلاتر")
areas = sorted(data["neighbourhood_group"].dropna().unique())
room_types = sorted(data["room_type"].dropna().unique())

selected_areas = st.sidebar.multiselect("المنطقة", areas, default=areas)
selected_types = st.sidebar.multiselect("نوع السكن", room_types, default=room_types)

filtered = data[
    data["neighbourhood_group"].isin(selected_areas)
    & data["room_type"].isin(selected_types)
]

if filtered.empty:
    st.info("اختاري منطقة ونوع سكن لعرض النتائج.")
    st.stop()

prices = filtered["price"]
count, median, low, high = st.columns(4)
count.metric("عدد الإعلانات", f"{len(filtered):,}")
median.metric("وسيط سعر الليلة", f"${prices.median():,.0f}")
low.metric("الربع الأول للسعر", f"${prices.quantile(0.25):,.0f}")
high.metric("الربع الثالث للسعر", f"${prices.quantile(0.75):,.0f}")

st.subheader("وسيط سعر الليلة حسب المنطقة")
by_area = filtered.groupby("neighbourhood_group")["price"].median()
st.bar_chart(by_area, x_label="المنطقة", y_label="السعر بالدولار")

st.subheader("وسيط سعر الليلة حسب نوع السكن")
by_room = filtered.groupby("room_type")["price"].median()
st.bar_chart(by_room, x_label="نوع السكن", y_label="السعر بالدولار")

st.subheader("أعلى 10 أحياء حسب وسيط سعر الليلة")
by_neighbourhood = filtered.groupby("neighbourhood")["price"].agg(
    median="median", listings="count"
)
eligible = by_neighbourhood[by_neighbourhood["listings"] >= 30]

if eligible.empty:
    st.info("ما فيه حي فيه 30 إعلانًا على الأقل ضمن الاختيارات الحالية.")
else:
    st.caption("يشمل الرسم الأحياء التي تضم 30 إعلانًا فأكثر.")
    st.bar_chart(
        eligible["median"].nlargest(10),
        x_label="الحي",
        y_label="السعر بالدولار",
    )
