import re
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="PF Saathi",
    page_icon="🔐",
    layout="wide"
)

# ---------- DESIGN ----------
st.markdown("""
<style>
.stApp {
    background-color: #F4F7FB;
    color: #172B4D;
}
[data-testid="stSidebar"] {
    background-color: #10243A;
}
[data-testid="stSidebar"] * {
    color: #F3F7FC;
}
/* Main content text only */
section[data-testid="stMain"] p,
section[data-testid="stMain"] label,
section[data-testid="stMain"] h1,
section[data-testid="stMain"] h2,
section[data-testid="stMain"] h3,
section[data-testid="stMain"] [data-testid="stMetricLabel"],
section[data-testid="stMain"] [data-testid="stMetricValue"] {
    color: #172B4D !important;
}

/* Sidebar text */
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2 {
    color: #F3F7FC !important;
}
}
h1, h2, h3 {
    color: #10243A !important;
    font-weight: 700 !important;
}
div[data-testid="stMetric"] {
    background: #FFFFFF;
    padding: 18px;
    border-radius: 14px;
    border: 1px solid #DCE5EF;
}
.block-container {
    padding-top: 2rem;
    max-width: 1200px;
}
.stButton > button {
    background-color: #087F70;
    color: white !important;
    border-radius: 9px;
    border: none;
    font-weight: 600;
}
.stButton > button:hover {
    background-color: #06675C;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ---------- SYNTHETIC DEMO DATA ----------
def get_demo_data():
    return pd.DataFrame({
        "Month": [
            "2026-01", "2026-02", "2026-03", "2026-04",
            "2026-05", "2026-06", "2026-07", "2026-08"  
        ],
        "Employer": [
            "Company A", "Company A", "Company A", "Company A",
            "Company A", "Company B", "Company B", "Company B"
        ],
        "Expected_PF": [1800, 1800, 1800, 1800, 1800, 2000, 2000, 2000],
        "Posted_PF":   [1800, 1800, 0, 1800, 1800, 2000, 2000, 1500],
        "Posting_Status": [
            "Posted", "Posted", "Not found", "Posted",
            "Posted", "Posted", "Posted", "Posted"
        ]
    })


def analyze_ledger(data):
    data = data.copy()
    data["Difference"] = data["Expected_PF"] - data["Posted_PF"]

    def classify(row):
        if row["Posting_Status"] == "Not found" and row["Posted_PF"] == 0:
            return "Potential missing contribution", "Medium"
        if row["Expected_PF"] == row["Posted_PF"]:
            return "Amounts match", "High"
        if row["Posted_PF"] == 0:
            return "Unexplained difference", "Low"
        return "Amount difference", "Medium"

    results = data.apply(classify, axis=1, result_type="expand")
    data["Classification"] = results[0]
    data["Confidence"] = results[1]
    data["Explanation"] = data.apply(
        lambda r: (
            "Amounts match in the supplied records."
            if r["Difference"] == 0 else
            "Verify the official passbook, wage basis, posting date, "
            "and employer records. The difference alone does not establish the cause."
        ),
        axis=1
    )
    return data


def generate_query(row):
    return (
        f"Subject: Request to verify PF contribution for {row['Month']}\n\n"
        f"Hello {row['Employer']} team,\n\n"
        f"I am reviewing my PF contribution records for {row['Month']}. "
        f"My current records show an expected amount of "
        f"Rs. {row['Expected_PF']:,.2f} and a recorded amount of "
        f"Rs. {row['Posted_PF']:,.2f}.\n\n"
        "Could you please help me verify these details and clarify "
        "whether any posting or record updates are pending?\n\n"
        "Thank you for your assistance."
    )


def detect_scam(message):
    credential_pattern = (
        r"\b(otp|one[- ]time password|password|pin|passcode)\b"
    )
    pressure_pattern = (
        r"\b(urgent|immediately|speed up|expedite|"
        r"avoid delay|claim will be blocked)\b"
    )

    if re.search(credential_pattern, message, re.I):
        level = "HIGH RISK"
        reason = "The message mentions a credential such as an OTP or password."
        advice = "Never share an OTP or password with a caller. Verify independently."
    elif re.search(pressure_pattern, message, re.I):
        level = "CAUTION"
        reason = "The message uses urgency or pressure tactics."
        advice = "Pause and verify the request using official channels."
    else:
        level = "NO WARNING TRIGGERED"
        reason = "The basic rules found no listed warning signs."
        advice = "This is not proof that the message is safe."

    # Do not print or retain the original message in application state.
    redacted = re.sub(r"\b\d{4,8}\b", "[REDACTED NUMBER]", message)
    return level, reason, advice, redacted


# ---------- SESSION STATE ----------
if "language" not in st.session_state:
    st.session_state.language = "English"
if "demo_mode" not in st.session_state:
    st.session_state.demo_mode = False

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("# 🔐 PF Saathi")
    st.caption("Understand your PF. Stay protected.")
    st.divider()

    page = st.radio(
        "NAVIGATION",
        [
            "Welcome",
            "Dashboard",
            "Contribution Analyzer",
            "Claims Tracker",
            "Neutral Query Generator",
            "Scam Defence",
            "Ask PF Saathi",
            "Official Services"
        ]
    )

    st.divider()
    st.selectbox(
        "🌐 Language",
        ["English", "हिन्दी", "తెలుగు"],
        key="language"
    )
    st.caption("DEMO MODE • Synthetic data only")

# ---------- WELCOME ----------
if page == "Welcome":
    st.markdown("# Welcome to PF Saathi 👋")
    st.subheader("Your provident fund, made easier to understand.")
    st.write(
        "Review contribution records, understand possible discrepancies, "
        "prepare neutral queries, and learn how to recognise credential scams."
    )

    st.info(
        "This hackathon prototype uses fictional records. "
        "It does not log in to or retrieve data from actual EPFO accounts."
    )

    left, right = st.columns(2)
    with left:
        if st.button("Explore Demo Dashboard", type="primary", use_container_width=True):
            st.session_state.demo_mode = True
            st.rerun()
    with right:
        st.link_button(
            "Visit Official EPFO Website",
            "https://www.epfindia.gov.in/",
            use_container_width=True
        )

    st.markdown("### What you can do")
    a, b, c = st.columns(3)
    a.markdown("#### 📊 Understand\nCompare expected and recorded contributions.")
    b.markdown("#### 📝 Take action\nPrepare a clear, neutral query.")
    c.markdown("#### 🛡️ Stay safe\nCheck messages for common scam warning signs.")

# ---------- DASHBOARD ----------
elif page == "Dashboard":
    df = analyze_ledger(get_demo_data())
    st.title("Your PF Dashboard")
    st.caption("Illustrative figures from fictional demo records.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Expected contributions", f"₹{df['Expected_PF'].sum():,.0f}")
    c2.metric("Recorded contributions", f"₹{df['Posted_PF'].sum():,.0f}")
    c3.metric("Total difference", f"₹{df['Difference'].sum():,.0f}")

    st.markdown("### Contribution overview")
    st.write("Expected vs Recorded Contributions")
    st.write("### Expected vs Recorded Contributions")
    for _, row in df[["Month", "Expected_PF", "Posted_PF"]].iterrows():
        st.write(
            f"**{row['Month']}** | "
            f"Expected: ₹{row['Expected_PF']:,.0f} | "
            f"Posted: ₹{row['Posted_PF']:,.0f}")

    issues = df[df["Difference"] != 0]
    st.markdown("### Items to review")
    st.dataframe(
        issues[["Month", "Employer", "Difference", "Classification", "Confidence"]],
        use_container_width=True,
        hide_index=True
    )

    st.warning(
        "A difference is a signal to investigate, not proof of non-payment "
        "or employer wrongdoing."
    )

# ---------- CONTRIBUTION ANALYZER ----------
elif page == "Contribution Analyzer":
    st.title("📊 Contribution Analyzer")
    st.write("Explore the fictional contribution ledger.")

    df = analyze_ledger(get_demo_data())
    st.write(df.to_string(index=False))

    st.markdown("### Inspect one month")
    selected_month = st.selectbox("Choose a month", df["Month"].tolist())
    row = df[df["Month"] == selected_month].iloc[0]

    st.write(f"**Classification:** {row['Classification']}")
    st.write(f"**Confidence:** {row['Confidence']}")
    st.write(f"**Explanation:** {row['Explanation']}")
    st.write(f"**Difference:** ₹{row['Difference']:,.2f}")

    st.caption(
        "Classification is rule-based and limited by the evidence in this demo. "
        "It is not an official EPFO determination."
    )

    st.download_button(
        "Download demo analysis as CSV",
        df.to_csv(index=False).encode("utf-8"),
        file_name="pf_saathi_demo_analysis.csv",
        mime="text/csv"
    )

# ---------- CLAIMS TRACKER ----------
elif page == "Claims Tracker":
    st.title("📄 Claims Tracker")
    st.caption("Fictional example statuses. No live EPFO claim is being checked.")

    claims = pd.DataFrame({
        "Demo Claim ID": ["DEMO-001", "DEMO-002", "DEMO-003"],
        "Claim Type": ["Transfer", "Withdrawal", "Profile correction"],
        "Demo Status": ["Pending review", "Information needed", "Draft not submitted"],
        "Suggested Next Step": [
            "Check the official portal for current status.",
            "Review the official portal for any stated requirement.",
            "Check the official process for correcting profile details."
        ]
    })
    st.write(claims.to_string(index=False))

    st.info(
        "These statuses are examples, not actual claim records or verified "
        "processing-time predictions."
    )

# ---------- QUERY GENERATOR ----------
elif page == "Neutral Query Generator":
    st.title("📝 Neutral Query Generator")
    st.write("Create a polite draft based on a fictional ledger discrepancy.")

    df = analyze_ledger(get_demo_data())
    issues = df[df["Difference"] != 0]

    month = st.selectbox("Select a month", issues["Month"].tolist())
    row = issues[issues["Month"] == month].iloc[0]
    draft = generate_query(row)

    st.text_area("Your draft", draft, height=260)
    st.download_button(
        "Download query draft",
        draft,
        file_name="pf_saathi_query_draft.txt",
        mime="text/plain"
    )
    st.caption("Review all details before sending. No query is sent automatically.")

# ---------- SCAM DEFENCE ----------
elif page == "Scam Defence":
    st.title("🛡️ OTP Scam Defence")
    st.write(
        "Test the detector with fictional messages. Never paste a real OTP, "
        "password, account number, or sensitive personal information."
    )

    example = st.selectbox(
        "Try an example",
        [
            "Select an example...",
            "Your PF claim will speed up. Share your OTP immediately.",
            "Please check your claim status on the official portal.",
            "URGENT: Your claim will be blocked unless you act immediately."
        ]
    )

    message = st.text_area(
        "Or enter a fictional message",
        value="" if example == "Select an example..." else example,
        height=100
    )

    if st.button("Check message", type="primary"):
        if not message.strip():
            st.warning("Enter a fictional test message first.")
        else:
            level, reason, advice, redacted = detect_scam(message)
            if level == "HIGH RISK":
                st.error(level)
            elif level == "CAUTION":
                st.warning(level)
            else:
                st.info(level)

            st.write("**Why:**", reason)
            st.write("**Recommended action:**", advice)
            st.write("**Redacted preview:**", redacted)

    st.caption(
        "This rule-based detector is only a demonstration. It does not guarantee "
        "that a message is safe, and this prototype does not persist messages."
    )

# ---------- CHATBOT ----------
elif page == "Ask PF Saathi":
    st.title("💬 Ask PF Saathi")
    st.write("Ask a question about the demo features.")

    question = st.text_input(
        "Your question",
        placeholder="Example: Why can my PF amount look different?"
    )

    if st.button("Ask"):
        q = question.lower()
        if any(word in q for word in ["otp", "scam", "password", "fraud"]):
            answer = (
                "Never share an OTP, password, or PIN with a caller. "
                "Verify requests independently through official channels."
            )
        elif any(word in q for word in ["missing", "difference", "contribution", "amount"]):
            answer = (
                "Compare the expected and recorded amounts, then verify the "
                "official passbook, wage basis, posting dates, and employer records. "
                "A discrepancy alone does not establish the cause."
            )
        elif any(word in q for word in ["claim", "pending", "transfer", "withdrawal"]):
            answer = (
                "Check the current status and any stated requirement through the "
                "official EPFO portal. This demo cannot access live claim records."
            )
        elif any(word in q for word in ["dob", "date of birth", "name", "correct"]):
            answer = (
                "Check the official EPFO process for profile corrections and "
                "the documents required for your specific case."
            )
        else:
            answer = (
                "I can help with contribution differences, claim terminology, "
                "profile-correction guidance, and common scam warning signs. "
                "For account-specific answers, check official EPFO services."
            )
        st.markdown("**PF Saathi says:**")
        st.write(answer)

    st.caption(
        "This first version uses predefined rules, not a live AI model or official account data."
    )

# ---------- OFFICIAL SERVICES ----------
elif page == "Official Services":
    st.title("🏛️ Official EPFO Services")
    st.write(
        "Use the official government website for actual account access, "
        "claim details, and official transactions."
    )

    st.link_button(
        "Open EPFO Official Website",
        "https://www.epfindia.gov.in/"
    )
    st.link_button(
        "Open EPFO Member Portal",
        "https://unifiedportal-mem.epfindia.gov.in/memberinterface/"
    )

    st.warning(
        "Check that you are on the genuine official website before entering "
        "credentials. PF Saathi does not collect your EPFO password or OTP."
    )

st.divider()
st.caption(
    "PF Saathi • IMPACTX 2026 prototype • Fictional demo data • "
    "Not an official EPFO service"
)
