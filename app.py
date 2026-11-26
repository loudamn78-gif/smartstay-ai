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
    model_path = Path(__file__).resolve().parent / "smartstay_model.pkl"
    return joblib.load(model_path)


@st.cache_data
def load_comparison_data():
    path = Path(__file__).resolve().parent / "data" / "clean.csv"
    return pd.read_csv(path)


def find_similar_listings(df, room_type, neighbourhood_group, neighbourhood):
    similar = df[
        (df["room_type"] == room_type)
        & (df["neighbourhood_group"] == neighbourhood_group)
    ].copy()

    if neighbourhood:
        same_neighbourhood = similar[
            similar["neighbourhood"] == neighbourhood
        ]

        if len(same_neighbourhood) >= 5:
            similar = same_neighbourhood

    return similar
        (df["room_type"] == room_type)
        & (df["neighbourhood_group"] == neighbourhood_group)
    ].copy()

    if neighbourhood:
        same_neighbourhood = similar[
            similar["neighbourhood"] == neighbourhood
        ]

        if len(same_neighbourhood) >= 5:
            similar = same_neighbourhood
def calculate_market_price(similar):
    if similar.empty:
        return None

    prices = similar["price"].dropna()

    if prices.empty:
        return None

    return {
        "count": len(prices),
        "median": prices.median(),
        "low": prices.quantile(0.25),
        "high": prices.quantile(0.75)
    }

    return similar

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
    similar_listings = find_similar_listings(
        comparison_data,
        room_type,
        neighbourhood_group,
        neighbourhood
    )

    market = calculate_market_price(similar_listings)

    st.subheader("مقارنة العقارات المشابهة")

    if market is None:
        st.info("لم نعثر على عقارات مشابهة.")
    else:
        st.write(f"عدد العقارات المشابهة: {market['count']:,}")

        m1, m2, m3 = st.columns(3)
        m1.metric("وسيط سعر السوق", f"${market['median']:,.0f}")
        m2.metric("الربع الأول", f"${market['low']:,.0f}")
        m3.metric("الربع الثالث", f"${market['high']:,.0f}")

        st.caption(
            "تعتمد المقارنة على نوع السكن والمنطقة، "
            "مع تفضيل الحي نفسه عند توفر 5 إعلانات على الأقل."
        )

        st.dataframe(
            similar_listings[
                ["neighbourhood", "room_type", "price",
                 "minimum_nights", "number_of_reviews"]
            ].sort_values("price").head(10),
            use_container_width=True
        )
    st.divider()

st.header("SmartStay Price Predictor")
st.write("أدخلي مواصفات العقار للحصول على سعر الليلة المتوقع.")

col1, col2 = st.columns(2)

with col1:
    neighbourhood_group = st.selectbox(
        "المنطقة",
        sorted(data["neighbourhood_group"].dropna().unique())
    )

    neighbourhood_options = sorted(
        data.loc[
            data["neighbourhood_group"] == neighbourhood_group,
            "neighbourhood"
        ].dropna().unique()
    )

    neighbourhood = st.selectbox(
        "الحي",
        neighbourhood_options
    )

    room_type = st.selectbox(
        "نوع السكن",
        ["Entire home/apt", "Private room", "Shared room"]
    )

    stay_type = st.selectbox(
        "نوع الإقامة",
        ["short (1-6)", "weekly (7-29)", "monthly+ (30+)"]
    )

with col2:
    number_of_reviews = st.number_input(
        "عدد التقييمات",
        min_value=0,
        max_value=629,
        value=5
    )

    calculated_host_listings_count = st.number_input(
        "عدد إعلانات المضيف",
        min_value=1,
        max_value=327,
        value=1
    )

    availability_365 = st.slider(
        "التوفر خلال السنة",
        min_value=0,
        max_value=365,
        value=44
    )

    distance_to_midtown_km = st.number_input(
        "المسافة إلى وسط مانهاتن (كم)",
        min_value=0.07,
        max_value=35.9,
        value=6.41,
        step=0.1
    )

if st.button("توقع سعر الليلة"):
    input_data = pd.DataFrame([{
        "neighbourhood_group": neighbourhood_group,
        "neighbourhood": neighbourhood,
        "room_type": room_type,
        "number_of_reviews": number_of_reviews,
        "calculated_host_listings_count": calculated_host_listings_count,
        "availability_365": availability_365,
        "distance_to_midtown_km": distance_to_midtown_km,
        "stay_type": stay_type
    }])

    predicted_price = model.predict(input_data)[0]

    st.metric(
        "السعر المتوقع لليلة",
        f"${predicted_price:,.2f}"
    )

    st.caption(
        "هذا تقدير إرشادي مبني على بيانات التدريب، "
        "وليس سعرًا مضمونًا أو توصية تسعير نهائية."
    )

    similar_listings = find_similar_listings(
        comparison_data,
        room_type,
        neighbourhood_group,
        neighbourhood
    )

    market = calculate_market_price(similar_listings)

    st.subheader("مقارنة العقارات المشابهة")

    if market is None:
        st.info("لم نعثر على عقارات مشابهة.")
    else:
        st.write(f"عدد العقارات المشابهة: {market['count']:,}")

        m1, m2, m3 = st.columns(3)

        m1.metric("وسيط سعر السوق", f"${market['median']:,.0f}")
        m2.metric("الربع الأول", f"${market['low']:,.0f}")
        m3.metric("الربع الثالث", f"${market['high']:,.0f}")

        st.dataframe(
            similar_listings[
                [
                    "neighbourhood",
                    "room_type",
                    "price",
                    "minimum_nights",
                    "number_of_reviews"
                ]
            ].sort_values("price").head(10),
            use_container_width=True
        )
