import pandas as pd
from serpapi import GoogleSearch

# 1. إعداد مفتاح API الخاص بـ SerpApi
SERPAPI_KEY = "YOUR_SERPAPI_KEY_HERE"  # استبدل بمفتاحك الحقيقي


def fetch_network_issues(
    query: str, location: str = "Iraq", max_results: int = 10
):
    """سحب نتائج البحث المتعلقة بمشاكل التغطية في العراق باستخدام SerpApi."""
    params = {
        "engine": "google",
        "q": query,
        "location": location,
        "hl": "ar",  # اللغة العربية
        "gl": "iq",  # النطاق الجغرافي: العراق
        "google_domain": "google.com.iq",
        "api_key": SERPAPI_KEY,
    }

    print(f"جاري البحث عن: '{query}'...")
    search = GoogleSearch(params)
    results = search.get_dict()

    organic_results = results.get("organic_results", [])
    extracted_data = []

    for item in organic_results[:max_results]:
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
    """تحليل واستخراج تفاصيل المنطقة ونوع المشكلة من نصوص النتائج."""
    classified_records = []

    # قائمة بالمدن والمناطق العراقية الشائعة
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
    ]

    # مؤشرات أنواع الأعطال
    outage_keywords = ["انقطاع", "فاصل", "توقف", "ماكو شبكة", "لا توجد خدمة"]
    speed_keywords = ["بطيء", "ضعيف", "تذبذب", "بطء", "تحميل"]

    for item in data_list:
        text = f"{item['Title']} {item['Snippet']}"

        # 1. استخراج اسم المنطقة
        found_region = "غير محدد"
        for reg in regions:
            if reg in text:
                found_region = reg
                break

        # 2. تحديد نوع المشكلة والخطورة
        issue_type = "عامة / استفسار"
        severity = "P3 - منخفض"

        if any(kw in text for kw in outage_keywords):
            issue_type = "انقطاع تام / تغطية (Outage)"
            severity = "P1 - حرج"
        elif any(kw in text for kw in speed_keywords):
            issue_type = "بطء وسوء جودة (Low Speed)"
            severity = "P2 - متوسط"

        classified_records.append(
            {
                "المنطقة / الحي": found_region,
                "نوع المشكلة": issue_type,
                "مستوى الأولوية": severity,
                "العنوان": item["Title"][:50] + "...",
                "الرابط": item["Link"],
            }
        )

    return pd.DataFrame(classified_records)


# --- التشغيل الرئيسي ---
if __name__ == "__main__":
    # استعلام يركز على المنتديات وصفحات التواجد العراقي
    search_query = 'site:facebook.com OR site:twitter.com "ضعف التغطية" OR "ماكو شبكة" OR "بطيء" "4G" OR "5G"'

    # 1. جلب البيانات
    raw_data = fetch_network_issues(
        query=search_query, location="Iraq", max_results=15
    )

    if raw_data:
        # 2. معالجة وتصنيف البيانات
        df = analyze_and_classify(raw_data)

        # 3. عرض التقرير الميداني في التيرمينال
        print("\n=== تقرير شكاوى الشبكة الميداني (العراق) ===\n")
        print(df.to_string(index=False))

        # 4. حفظ النتائج في ملف CSV لفرق الـ Optimization/Drive Test
        df.to_csv("iraq_network_issues_report.csv", index=False, encoding="utf-8-sig")
        print("\nتم حفظ التقرير بنجاح في ملف: iraq_network_issues_report.csv")
    else:
        print("لم يتم العثور على نتائج جديدة.")
