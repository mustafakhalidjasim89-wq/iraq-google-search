import pandas as pd
from serpapi import GoogleSearch
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Iraq Telecom Coverage Monitor", page_icon="📡", layout="wide"
)

st.title("📡 العراق - مراقب تغطية وجودة شبكات الاتصالات")
st.markdown(
    "تتبع شكاوى التغطية، انقطاعات الخدمة، وسوء جودة الإنترنت (4G/5G/FTTH) عبر محرك البحث والمنصات المحلية."
)

# Sidebar Controls
st.sidebar.header("إعدادات البحث والتحليل")

# 1. API Key handling (Streamlit Secrets or Manual Input)
serpapi_key = st.secrets.get("SERPAPI_KEY", "")

if not serpapi_key:
    serpapi_key = st.sidebar.text_input(
        "SerpApi API Key",
        type="password",
        help="أدخل مفتاح SerpApi هنا أو ضع قيمته في Secrets",
    )

# 2. Preset search suggestions for Iraq telecom
search_preset = st.sidebar.selectbox(
    "نماذج استعلام جاهزة:",
    [
        "تغطية آسياسيل وزين العراق (عام)",
        "ضعف تغطية 4G و 5G بغداد",
        "انقطاع خدمة الإنترنت وإيرثلنك",
        "استعلام مخصص...",
    ],
)

default_queries = {
    "تغطية آسياسيل وزين العراق (عام)": 'مشكلة تغطية OR "ضعف الشبكة" OR "ماكو شبكة" آسياسيل OR زين',
    "ضعف تغطية 4G و 5G بغداد": 'ضعف التغطية OR "انقطاع الخدمة" 4G OR 5G بغداد',
    "انقطاع خدمة الإنترنت وإيرثلنك": 'انقطاع الإنترنت OR "بطء الخدمة" إيرثلنك OR FTTH',
    "استعلام مخصص...": "ضعف التغطية 4G بغداد",
}

selected_query = default_queries[search_preset]

if search_preset == "استعلام مخصص...":
    query_input = st.sidebar.text_input(
        "عبارة البحث المخصصة", value=selected_query
    )
else:
    query_input = st.sidebar.text_input("عبارة البحث", value=selected_query)

max_results = st.sidebar.slider(
    "عدد النتائج المطلوب فحصها", min_value=5, max_value=50, value=20
)


def fetch_network_issues(query: str, api_key: str, max_res: int = 20):
    """Fetch search results from Google via SerpApi targeted for Iraq."""
    params = {
        "engine": "google",
        "q": query,
        "location": "Iraq",
        "hl": "ar",
        "gl": "iq",
        "api_key": api_key,
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()

        # Check for API error response
        if "error" in results:
            st.error(f"خطأ في استجابة SerpApi: {results['error']}")
            return []

        organic_results = results.get("organic_results", [])

        extracted_data = []
        for item in organic_results[:max_res]:
            extracted_data.append(
                {
                    "Title": item.get("title", ""),
                    "Snippet": item.get("snippet", ""),
                    "Link": item.get("link", ""),
                    "Source": item.get("displayed_link", ""),
                }
            )

        return extracted_data

    except Exception as e:
        st.error(f"حدث خطأ أثناء الاتصال بالخادم: {str(e)}")
        return []


def analyze_and_classify(data_list):
    """Classify regions, operators, issue types, and priority levels from Arabic text snippets."""
    classified_records = []

    # Iraqi Geographical Entities
    provinces = [
        "بغداد",
        "البصرة",
        "أربيل",
        "النجف",
        "كربلاء",
        "الموصل",
        "نينوى",
        "كركوك",
        "السليمانية",
        "دهوك",
        "الانبار",
        "الرمادي",
        "ديالى",
        "بعقوبة",
        "بابل",
        "الحلة",
        "ذي قار",
        "الناصرية",
        "ميسان",
        "العمارة",
        "الديوانية",
        "المثنى",
        "واسط",
        "الكوت",
        "المنصور",
        "الكرادة",
        "الزيونة",
        "حي الجامعة",
        "الشعب",
        "الدورة",
    ]

    # Telecom Operators in Iraq
    operators = {
        "آسياسيل": ["آسياسيل", "Asiacell"],
        "زين العراق": ["زين", "Zain"],
        "كورك": ["كورك", "Korek"],
        "إيرثلنك": ["إيرثلنك", "Earthlink"],
        "سوفت بنك / ضوئي": ["FTTH", "الضوئي", "كيبل ضوئي"],
    }

    # Defect Keywords & Severity Mapping
    outage_keywords = [
        "انقطاع",
        "فاصل",
        "توقف",
        "ماكو شبكة",
        "لا توجد خدمة",
        "قطع",
        "طافية",
        "فاصلة",
    ]
    speed_keywords = [
        "بطيء",
        "ضعيف",
        "تذبذب",
        "بطء",
        "تحميل",
        "رديء",
        "ضعف الشبكة",
    ]

    for item in data_list:
        text = f"{item['Title']} {item['Snippet']}"

        # 1. Location Detection
        found_region = "غير محدد / عام"
        for reg in provinces:
            if reg in text:
                found_region = reg
                break

        # 2. Operator Detection
        found_operator = "غير محدد"
        for op_name, keywords in operators.items():
            if any(kw.lower() in text.lower() for kw in keywords):
                found_operator = op_name
                break

        # 3. Issue Classification & Severity Level
        issue_type = "استفسار / منشور عام"
        severity = "P3 - منخفض"

        if any(kw in text for kw in outage_keywords):
            issue_type = "انقطاع تام / تغطية (Outage)"
            severity = "P1 - حرج"
        elif any(kw in text for kw in speed_keywords):
            issue_type = "بطء وسوء جودة (Low Speed)"
            severity = "P2 - متوسط"

        classified_records.append(
            {
                "المحافظة / المنطقة": found_region,
                "الشركة / المزود": found_operator,
                "نوع المشكلة": issue_type,
                "مستوى الأولوية": severity,
                "العنوان": item["Title"],
                "المقتطف (Snippet)": item["Snippet"],
                "الرابط": item["Link"],
            }
        )

    return pd.DataFrame(classified_records)


# Main Interface Execution
if st.button("🚀 تشغيل البحث والتحليل الميداني", type="primary"):
    if not serpapi_key:
        st.error(
            "يرجى إدخال مفتاح SerpApi في الشريط الجانبي أو إضافته في Streamlit Secrets."
        )
    else:
        with st.spinner("جاري جلب البيانات وتحليلها..."):
            raw_data = fetch_network_issues(
                query_input, serpapi_key, max_results
            )

        if raw_data:
            df = analyze_and_classify(raw_data)

            # High-level Metrics Summary
            p1_count = len(df[df["مستوى الأولوية"] == "P1 - حرج"])
            p2_count = len(df[df["مستوى الأولوية"] == "P2 - متوسط"])
            p3_count = len(df[df["مستوى الأولوية"] == "P3 - منخفض"])

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("إجمالي النتائج", len(df))
            col2.metric("اعطال حرجة (P1)", p1_count)
            col3.metric("مشاكل جودة (P2)", p2_count)
            col4.metric("استفسارات عامة (P3)", p3_count)

            st.markdown("---")
            st.subheader("📊 جدول الشكاوى والمشاكل المصنفة")

            # Interactive DataFrame
            st.dataframe(
                df,
                column_config={"الرابط": st.column_config.LinkColumn("الرابط")},
                use_container_width=True,
            )

            # Export to CSV Button
            csv_data = df.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label="📥 تحميل التقرير بصيغة CSV",
                data=csv_data,
                file_name="iraq_network_coverage_report.csv",
                mime="text/csv",
            )
        else:
            st.warning(
                "لم يتم العثور على نتائج matching لهذا الاستعلام. جرب اختيار استعلام أوسع من القائمة الجاهزة."
            )
