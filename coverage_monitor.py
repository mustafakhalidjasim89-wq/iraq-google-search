import pandas as pd
from serpapi import GoogleSearch
import streamlit as st

# إعداد الصفحة
st.set_page_config(
    page_title="المحلل والباحث الشامل - SerpApi", page_icon="🔍", layout="wide"
)

st.title("🔍 محرك البحث والتحليل الشامل (Universal Search & Sentiment Analyzer)")
st.markdown(
    "ابحث عن أي موضوع، منتج، أو خدمة، وقم بتحليل واستخراج النتائج وتنظيمها تلقائياً."
)

# الشريط الجانبي للإعدادات العامة
st.sidebar.header("⚙️ إعدادات البحث")

# 1. مفتاح API
serpapi_key = st.secrets.get("SERPAPI_KEY", "")
if not serpapi_key:
    serpapi_key = st.sidebar.text_input(
        "SerpApi API Key",
        type="password",
        help="أدخل مفتاح SerpApi هنا أو ضع قيمته في Secrets",
    )

# 2. نص البحث الحر
query_input = st.sidebar.text_input(
    "عبارة البحث (Search Query)",
    value="أسعار السيارت المستعملة في بغداد",
    help="أدخل أي عبارة بحث تريد تحليل نتائجها",
)

# 3. إعدادات النطاق الجغرافي واللغة
col_lang, col_country = st.sidebar.columns(2)

country_options = {
    "العراق 🇮🇶": ("iq", "Iraq"),
    "السعودية 🇸🇦": ("sa", "Saudi Arabia"),
    "الإمارات 🇦🇪": ("ae", "United Arab Emirates"),
    "مصر 🇪🇬": ("eg", "Egypt"),
    "عالمي (All)": ("", ""),
}

selected_country_label = st.sidebar.selectbox(
    "الدولة المتهدفة (Location):", list(country_options.keys())
)
gl_code, location_name = country_options[selected_country_label]

lang_options = {"العربية": "ar", "English": "en", "جميع اللغات": ""}
selected_lang_label = st.sidebar.selectbox(
    "لغة البحث (Language):", list(lang_options.keys())
)
hl_code = lang_options[selected_lang_label]

max_results = st.sidebar.slider(
    "عدد النتائج المطلوبة", min_value=5, max_value=100, value=20
)


def fetch_universal_search(
    query: str, api_key: str, gl: str, location: str, hl: str, max_res: int
):
    """جلب نتائج البحث العامة من Google عبر SerpApi بناءً على الفلاتر."""
    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
    }

    if gl:
        params["gl"] = gl
    if location:
        params["location"] = location
    if hl:
        params["hl"] = hl

    try:
        search = GoogleSearch(params)
        results = search.get_dict()

        if "error" in results:
            st.error(f"خطأ في استجابة SerpApi: {results['error']}")
            return []

        organic_results = results.get("organic_results", [])

        extracted_data = []
        for item in organic_results[:max_res]:
            extracted_data.append(
                {
                    "العنوان (Title)": item.get("title", ""),
                    "المقتطف (Snippet)": item.get("snippet", ""),
                    "الرابط (Link)": item.get("link", ""),
                    "المصدر (Domain)": item.get("displayed_link", ""),
                    "الترتيب (Rank)": item.get("position", ""),
                }
            )

        return extracted_data

    except Exception as e:
        st.error(f"حدث خطأ أثناء الاتصال بالخادم: {str(e)}")
        return []


def analyze_general_data(data_list):
    """تحليل عام للبيانات واستخراج إحصائيات المواقع المصدرة."""
    df = pd.DataFrame(data_list)
    return df


# تنفيذ البحث
if st.button("🚀 بدء البحث وتحليل النتائج", type="primary"):
    if not serpapi_key:
        st.error(
            "يرجى إدخال مفتاح SerpApi في الشريط الجانبي أو إضافته في Streamlit Secrets."
        )
    elif not query_input.strip():
        st.warning("يرجى كتابة عبارة البحث أولاً.")
    else:
        with st.spinner("جاري جلب نتائج البحث وتحليل البيانات..."):
            raw_data = fetch_universal_search(
                query_input,
                serpapi_key,
                gl_code,
                location_name,
                hl_code,
                max_results,
            )

        if raw_data:
            df = analyze_general_data(raw_data)

            # عرض الإحصائيات السريعة
            col1, col2 = st.columns(2)
            col1.metric("إجمالي النتائج المستخرجة", len(df))
            col2.metric("عدد المواقع الفريدة (Unique Domains)", df["المصدر (Domain)"].nunique())

            st.markdown("---")
            st.subheader("📊 جدول النتائج المنظم")

            # عرض الجدول التفاعلي
            st.dataframe(
                df,
                column_config={
                    "الرابط (Link)": st.column_config.LinkColumn(
                        "الرابط (Link)"
                    )
                },
                use_container_width=True,
            )

            # زر تحميل الملف CSV
            csv_data = df.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label="📥 تحميل النتائج بصيغة CSV",
                data=csv_data,
                file_name="search_results_report.csv",
                mime="text/csv",
            )
        else:
            st.warning(
                "لم يتم العثور على نتائج. جرب تغيير عبارة البحث أو تقليل الفلاتر."
            )
