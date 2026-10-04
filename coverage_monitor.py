import pandas as pd
from serpapi import GoogleSearch
import streamlit as st

# Setup page config
st.set_page_config(
    page_title="Iraq Network Coverage Monitor", page_icon="📡", layout="wide"
)

st.title("📡 Iraq Telecom Network Coverage & Sentiment Monitor")
st.markdown(
    "Track public complaints, network outages, and 4G/5G coverage issues across Iraqi provinces."
)

# Sidebar - API Key Configuration
st.sidebar.header("Configuration")

# Fetch API Key from Streamlit Secrets or manual input
serpapi_key = st.secrets.get("SERPAPI_KEY", "")

if not serpapi_key:
    serpapi_key = st.sidebar.text_input(
        "SerpApi Key", type="password", help="Enter your SerpApi API Key"
    )

query_input = st.sidebar.text_input(
    "Search Query",
    value='site:facebook.com OR site:twitter.com "ضعف التغطية" OR "ماكو شبكة" OR "بطيء" "4G" OR "5G"',
)

max_results = st.sidebar.slider(
    "Max Results", min_value=5, max_value=50, value=15
)


def fetch_network_issues(query: str, api_key: str, max_res: int = 15):
    """Fetch search results related to telecom issues in Iraq via SerpApi."""
    params = {
        "engine": "google",
        "q": query,
        "location": "Iraq",
        "hl": "ar",
        "gl": "iq",
        "google_domain": "google.com.iq",
        "api_key": api_key,
    }

    search = GoogleSearch(params)
    results = search.get_dict()
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


def analyze_and_classify(data_list):
    """Classify regions, defect types, and priority levels from Arabic search snippets."""
    classified_records = []

    regions = [
        "بغداد",
        "البصرة",
        "أربيل",
        "النجف",
        "كربلاء",
        "المنصور",
        "الكرادة",
        "الزيونة",
        "حي الجامعة",
        "الموصل",
        "كركوك",
        "السليمانية",
        "دهوك",
        "الانبار",
        "ديالى",
    ]

    outage_keywords = [
        "انقطاع",
        "فاصل",
        "توقف",
        "ماكو شبكة",
        "لا توجد خدمة",
        "قطع",
    ]
    speed_keywords = ["بطيء", "ضعيف", "تذبذب", "بطء", "تحميل"]

    for item in data_list:
        text = f"{item['Title']} {item['Snippet']}"

        # Geo-extraction
        found_region = "غير محدد"
        for reg in regions:
            if reg in text:
                found_region = reg
                break

        # Issue classification & severity
        issue_type = "عامة / استفسار"
        severity = "P3 - Low"

        if any(kw in text for kw in outage_keywords):
            issue_type = "انقطاع تام / تغطية (Outage)"
            severity = "P1 - Critical"
        elif any(kw in text for kw in speed_keywords):
            issue_type = "بطء وسوء جودة (Low Speed)"
            severity = "P2 - Medium"

        classified_records.append(
            {
                "Region / Area": found_region,
                "Issue Type": issue_type,
                "Priority": severity,
                "Title": item["Title"],
                "Snippet": item["Snippet"],
                "Link": item["Link"],
            }
        )

    return pd.DataFrame(classified_records)


# Main App Flow
if st.button("🔍 Run Search & Analysis", type="primary"):
    if not serpapi_key:
        st.error(
            "Please provide a SerpApi Key in Streamlit Secrets or in the sidebar."
        )
    else:
        with st.spinner("Fetching data from SerpApi..."):
            raw_data = fetch_network_issues(
                query_input, serpapi_key, max_results
            )

        if raw_data:
            df = analyze_and_classify(raw_data)

            # Display metrics
            p1_count = len(df[df["Priority"] == "P1 - Critical"])
            p2_count = len(df[df["Priority"] == "P2 - Medium"])

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Issues Found", len(df))
            col2.metric("Critical Outages (P1)", p1_count)
            col3.metric("Performance Issues (P2)", p2_count)

            st.subheader("📊 Classified Audit Report")
            st.dataframe(df, use_container_width=True)

            # Download CSV
            csv_data = df.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label="📥 Download CSV Report",
                data=csv_data,
                file_name="iraq_coverage_report.csv",
                mime="text/csv",
            )
        else:
            st.warning("No search results returned for this query.")
