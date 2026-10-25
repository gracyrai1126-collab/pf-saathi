import re
import pandas as pd
import streamlit as st
import os

st.set_page_config(
    page_title="PF Saathi",
    page_icon="🔐",
    layout="wide"
)
logo_path = r"C:\Users\DELL\.jupyter\pf-saathi\pf_saathi_logo.jpeg"

if os.path.exists(logo_path):
    st.sidebar.image(logo_path, use_container_width=True)
else:
    st.sidebar.warning("PF Saathi logo file not found.")

# ---------- DESIGN ----------
st.markdown("""

<style>
.stApp {
    background: #F4F7FB;
    color: #172B4D;
}

[data-testid="stSidebar"] {
    background: #10243A;
}

[data-testid="stSidebar"] * {
    color: #F3F7FC;
}

h1, h2, h3 {
    color: #10243A !important;
    font-weight: 700 !important;
}

p, label, [data-testid="stMetricLabel"] {
    color: #172B4D;
}

[data-testid="stMetric"] {
    background: #FFFFFF;
    padding: 18px;
    border-radius: 14px;
    border: 1px solid #DCE5EF;
    border-radius: 14px;
    padding: 18px;
}

[data-testid="stMetricValue"] {
    color: #10243A !important;
}

.stButton > button,
.stDownloadButton > button,
.stLinkButton > a {
    background: #087F70;
    color: #FFFFFF !important;
    border: none;
    border-radius: 9px;
    font-weight: 600;
}

.stButton > button:hover,
.stDownloadButton > button:hover,
.stLinkButton > a:hover {
    background: #06675C;
    color: #FFFFFF !important;
}

[data-testid="stDataFrame"],
[data-testid="stTable"] {
    background: #FFFFFF;
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
/* Fix only the Ask Your Employer draft text area */
div[data-testid="stTextArea"] textarea {
    background-color: #FFFFFF !important;
    color: #10243A !important;
    -webkit-text-fill-color: #10243A !important;
    caret-color: #10243A !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 10px !important;
}

/* Keep selected text readable */
div[data-testid="stTextArea"] textarea::selection {
    background-color: #BFE8E0 !important;
    color: #10243A !important;
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
            "Claims Tracker",
            "Ask Your Employer",
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
        st.link_button(
            "Visit Official EPFO Website",
            "https://www.epfindia.gov.in/",
            use_container_width=True
        )

    with right:
        if st.button(
            "Ask a Query",
            type="primary",
            use_container_width=True
        ):
            st.session_state["page_navigation"] = "Ask Your Employer"
            st.rerun()


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

    # Main summary cards
    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Expected contributions",
        f"₹{df['Expected_PF'].sum():,.0f}"
    )
    c2.metric(
        "Recorded contributions",
        f"₹{df['Posted_PF'].sum():,.0f}"
    )
    c3.metric(
        "Total difference",
        f"₹{df['Difference'].sum():,.0f}"
    )

    # Monthly contribution chart
    st.markdown("### Contribution overview")

    chart_data = df.set_index("Month")[["Expected_PF", "Posted_PF"]]
    st.bar_chart(chart_data, height=320)

    # Inspect a month using a dropdown
    st.markdown("### Inspect a month")

    months = df["Month"].tolist()

    selected_month = st.selectbox(
        "Choose a month",
        options=months,
        index=len(months) - 1
    )

    row = df[df["Month"] == selected_month].iloc[0]

    detail1, detail2, detail3 = st.columns(3)

    detail1.metric(
        "Expected",
        f"₹{row['Expected_PF']:,.0f}"
    )
    detail2.metric(
        "Posted",
        f"₹{row['Posted_PF']:,.0f}"
    )
    detail3.metric(
        "Difference",
        f"₹{row['Difference']:,.0f}"
    )

    if row["Difference"] > 0:
        st.warning(
            f"❗ Check {row['Month']}: "
            f"₹{row['Difference']:,.0f} difference. "
            "Verify the official passbook and employer records."
        )
    else:
        st.success(
            "The expected and recorded amounts match in this demo."
        )

    # Detailed monthly ledger
    st.markdown("### Complete contribution ledger")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    # Download the complete ledger
    st.download_button(
        "📥 Download contribution report (CSV)",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="pf_saathi_contribution_report.csv",
        mime="text/csv"
    )

    # Discrepancies to review
    issues = df[df["Difference"] != 0]

    st.markdown("### Items to review")

    if issues.empty:
        st.success("No discrepancies found in this demo.")
    else:
        st.dataframe(
            issues[
                [
                    "Month",
                    "Employer",
                    "Expected_PF",
                    "Posted_PF",
                    "Difference",
                    "Classification",
                    "Confidence"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

    st.warning(
        "A difference is a signal to investigate, not proof of "
        "non-payment or employer wrongdoing."
    )

    st.caption(
        "Classification is rule-based and limited by the evidence "
        "in this demo. It is not an official EPFO determination."
    )


# ---------- CLAIMS TRACKER ----------
elif page == "Claims Tracker":
    st.title("📄 Claims Tracker")
    st.caption(
        "Fictional example claims. These are not connected to EPFO."
    )

    stages = ["Draft", "Submitted", "Under review", "Approved", "Paid"]

    claims = [
        ("DEMO-001", "Transfer", "Under review"),
        ("DEMO-002", "Withdrawal", "Approved"),
        ("DEMO-003", "Profile correction", "Draft"),
    ]

    for claim_id, claim_type, current_stage in claims:
        with st.container(border=True):
            st.subheader(f"{claim_id} · {claim_type}")
            st.write(f"**Current stage:** {current_stage}")

            progress = (stages.index(current_stage) + 1) / len(stages)
            st.progress(progress)

            st.caption(" → ".join(stages))

    st.info(
        "Approved and Paid are different stages. "
        "Check the official EPFO portal for real claim status."
    )

# ---------- QUERY GENERATOR ----------
elif page == "Ask Your Employer":
    st.title("📝 Ask Your Employer")
    st.write("Create a polite draft based on a fictional ledger discrepancy.")

    df = analyze_ledger(get_demo_data())
    issues = df[df["Difference"] != 0]

    if issues.empty:
        st.success("No discrepancies were found in the demo data.")
    else:
        month = st.selectbox(
            "Select a month",
            issues["Month"].tolist()
        )
        row = issues[issues["Month"] == month].iloc[0]
        draft = generate_query(row)

        draft = st.text_area(
            "Your draft",
            value=draft,
            height=260
        )

        blocked_words = sorted(set(
            re.findall(
                r"\b(fraud|stole|steal|cheat|theft|illegal)\b",
                draft,
                flags=re.IGNORECASE
            )
        ))

        if blocked_words:
            st.error(
                "Please review accusatory wording before downloading: "
                + ", ".join(blocked_words)
            )

        st.download_button(
            "Download query draft",
            data=draft,
            file_name="pf_saathi_query_draft.txt",
            mime="text/plain",
            disabled=bool(blocked_words)
        )

        st.caption(
            "Nothing is sent automatically. Review the draft before sending it."
        )


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
