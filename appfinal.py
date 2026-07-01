import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Loan Underwriting & FICO Dashboard", page_icon="🏦", layout="wide")

st.title("🏦 Comprehensive Loan Underwriting & FICO Analysis Dashboard")
st.markdown("""
This professional-grade application utilizes the actual historical Freddie Mac loan origination dataset with explicit columns (`Credit Score`, `Original Debt-to-Income (DTI) Ratio`, `Original Loan-to-Value (LTV)`, etc.) to evaluate loan application safety and display full risk analytics.
""")

# Load data with caching
@st.cache_data
def load_data():
    files = ['sample_orig_2023.csv', 'sample_orig_2024.csv', 'sample_orig_2025.csv']
    dfs = []
    cols_to_use = [
        'Credit Score', 'Original Debt-to-Income (DTI) Ratio', 'Original Loan-to-Value (LTV)', 
        'Original UPB', 'Original Interest Rate', 'Property State', 'Loan Purpose', 'First Time Homebuyer Flag'
    ]
    for f in files:
        try:
            df_temp = pd.read_csv(f, usecols=cols_to_use)
            dfs.append(df_temp)
        except Exception as e:
            pass
    if not dfs:
        return pd.DataFrame(columns=cols_to_use)
    
    df_all = pd.concat(dfs, ignore_index=True)
    
    # Ensure types are numeric for quantitative columns
    for col in ['Credit Score', 'Original Debt-to-Income (DTI) Ratio', 'Original Loan-to-Value (LTV)', 'Original UPB', 'Original Interest Rate']:
        df_all[col] = pd.to_numeric(df_all[col], errors='coerce')
        
    # Clean missing values using Freddie Mac standard missing flags (9999 for FICO, 999 for DTI/LTV)
    df_all = df_all[
        (df_all['Credit Score'] != 9999) & (df_all['Credit Score'].notna()) &
        (df_all['Original Debt-to-Income (DTI) Ratio'] != 999) & (df_all['Original Debt-to-Income (DTI) Ratio'].notna()) &
        (df_all['Original Loan-to-Value (LTV)'] != 999) & (df_all['Original Loan-to-Value (LTV)'].notna())
    ]
    return df_all

with st.spinner("Analyzing historical loan data..."):
    df = load_data()

if df.empty:
    st.error("No data found or columns do not match. Please verify that the CSV files are placed in the app directory.")
else:
    # Sidebar input panel
    st.sidebar.header("📋 New Applicant Parameters")
    
    user_fico = st.sidebar.number_input("Credit Score (FICO):", min_value=300, max_value=850, value=720, step=1)
    user_dti = st.sidebar.slider("Debt-to-Income (DTI) Ratio (%):", min_value=0, max_value=100, value=35, step=1)
    user_ltv = st.sidebar.slider("Loan-to-Value (LTV) Ratio (%):", min_value=0, max_value=150, value=80, step=1)
    user_upb = st.sidebar.number_input("Requested Loan Amount ($):", min_value=5000, max_value=2000000, value=250000, step=5000)
    
    # Text/categorical dropdown filters for benchmarking
    unique_states = sorted(df['Property State'].dropna().unique().tolist())
    state_selection = st.sidebar.selectbox("Property State:", unique_states, index=unique_states.index('FL') if 'FL' in unique_states else 0)
    
    purpose_map = {'P': 'Purchase', 'C': 'Cash-out Refinance', 'N': 'No Cash-out Refinance'}
    purpose_selection = st.sidebar.selectbox("Loan Purpose:", list(purpose_map.values()))
    purpose_code = [k for k, v in purpose_map.items() if v == purpose_selection][0]
    
    first_time_selection = st.sidebar.selectbox("First Time Homebuyer?", ["No", "Yes"])
    first_time_flag = 'Y' if first_time_selection == "Yes" else 'N'

    # UNDERWRITING RISK ANALYSIS METRICS
    st.subheader("📊 Individual Component Risk Ratings")
    c1, c2, c3 = st.columns(3)
    
    # 1. Credit Score Evaluation
    if user_fico >= 740:
        fico_status, fico_color = "🟢 Excellent / Very Safe", "green"
    elif user_fico >= 670:
        fico_status, fico_color = "🟢 Good / Safe", "darkgreen"
    elif user_fico >= 620:
        fico_status, fico_color = "🟡 Fair / Borderline", "orange"
    else:
        fico_status, fico_color = "🔴 Poor / Not Safe", "red"
        
    c1.markdown(f"**Credit Score Status:**\n### <span style='color:{fico_color};'>{fico_status}</span>", unsafe_allow_html=True)
    c1.metric("Applicant FICO", f"{user_fico}")

    # 2. DTI Evaluation
    if user_dti <= 36:
        dti_status, dti_color = "🟢 Low Risk", "green"
    elif user_dti <= 45:
        dti_status, dti_color = "🟢 Moderate Risk", "darkgreen"
    elif user_dti <= 50:
        dti_status, dti_color = "🟡 High Risk / Edge Case", "orange"
    else:
        dti_status, dti_color = "🔴 Critical Risk / Too High", "red"
        
    c2.markdown(f"**Debt-to-Income Status:**\n### <span style='color:{dti_color};'>{dti_status}</span>", unsafe_allow_html=True)
    c2.metric("Applicant DTI", f"{user_dti}%")

    # 3. LTV Evaluation
    if user_ltv <= 80:
        ltv_status, ltv_color = "🟢 Safe (No PMI Needed)", "green"
    elif user_ltv <= 95:
        ltv_status, ltv_color = "🟢 Moderate (Private Mortgage Ins. Required)", "darkgreen"
    elif user_ltv <= 97:
        ltv_status, ltv_color = "🟡 High Risk", "orange"
    else:
        ltv_status, ltv_color = "🔴 Critical / Equity Too Low", "red"
        
    c3.markdown(f"**Loan-to-Value Status:**\n### <span style='color:{ltv_color};'>{ltv_status}</span>", unsafe_allow_html=True)
    c3.metric("Applicant LTV", f"{user_ltv}%")

    # OVERALL AUTOMATED UNDERWRITING SYSTEM (AUS) DECISION
    st.markdown("---")
    st.subheader("⚖️ Final Automated Underwriting Verdict")
    
    if user_fico < 620 or user_dti > 50 or user_ltv > 97:
        decision_title = "❌ APPLICATION DENIED / NOT SAFE"
        decision_color = "red"
        decision_desc = "The application does not meet baseline safe lending guidelines. High default hazard due to subprime credit score, excessive debt obligations, or insufficient equity protection."
    elif user_dti > 45 or user_ltv > 95 or user_fico < 670:
        decision_title = "⚠️ CONDITIONAL APPROVAL / MANUAL REVIEW REQUIRED"
        decision_color = "orange"
        decision_desc = "The loan presents mixed risk features. It qualifies for conditional approval subject to strict asset verification, manual underwriting review, or enhanced pricing adjustments (LLPAs)."
    else:
        decision_title = "✅ APPLICATION APPROVED / SAFE LENDING"
        decision_color = "green"
        decision_desc = "This profile is safe and highly reliable. It satisfies standard automated lending parameters for conventional acquisition."

    st.markdown(f"<div style='background-color:#f9f9f9; padding:20px; border-radius:10px; border-left:8px solid {decision_color};'>"
                f"<h2><span style='color:{decision_color};'>{decision_title}</span></h2>"
                f"<p style='font-size:16px;'>{decision_desc}</p>"
                f"</div>", unsafe_allow_html=True)

    # CREATE TABS FOR HISTORICAL DASHBOARD INTERFACES
    tab1, tab2, tab3 = st.tabs(["🎯 Applicant vs. Market Benchmarking", "📊 Macro Market Analytics", "🗺️ State-by-State Metrics"])
    
    with tab1:
        st.subheader("Real-Time Benchmarking against Historical Approved Loans")
        
        # Percentile checks
        fico_pct = (df['Credit Score'] < user_fico).mean() * 100
        dti_pct = (df['Original Debt-to-Income (DTI) Ratio'] > user_dti).mean() * 100
        ltv_pct = (df['Original Loan-to-Value (LTV)'] > user_ltv).mean() * 100
        
        b1, b2, b3 = st.columns(3)
        b1.metric("FICO Superiority", f"{fico_pct:.1f}%", help="Percentage of approved loans with a lower FICO score than this applicant.")
        b1.markdown(f"Applicant's score is stronger than **{fico_pct:.1f}%** of all historically accepted borrowers.")
        
        b2.metric("DTI Favorability", f"{dti_pct:.1f}%", help="Percentage of approved loans that had higher debt ratios than this applicant.")
        b2.markdown(f"Applicant's debt level is lower/safer than **{dti_pct:.1f}%** of approved historical records.")
        
        b3.metric("LTV Equity Position", f"{ltv_pct:.1f}%", help="Percentage of approved loans with higher leverage/higher LTV.")
        b3.markdown(f"Applicant puts down more equity than **{ltv_pct:.1f}%** of historical transactions.")

        # Benchmark within specific subset (Same State + Same Purpose)
        st.markdown("---")
        st.markdown(f"### Historical Benchmarks for **{state_selection}** for **{purpose_selection}** Loans")
        subset_df = df[(df['Property State'] == state_selection) & (df['Loan Purpose'] == purpose_code)]
        
        if not subset_df.empty:
            sub1, sub2, sub3, sub4 = st.columns(4)
            sub1.metric("Average Credit Score", f"{subset_df['Credit Score'].mean():.1f}")
            sub2.metric("Average Interest Rate", f"{subset_df['Original Interest Rate'].mean():.3f}%")
            sub3.metric("Average DTI Ratio", f"{subset_df['Original Debt-to-Income (DTI) Ratio'].mean():.1f}%")
            sub4.metric("Total Sampled Records", f"{len(subset_df):,}")
        else:
            st.info("No matching records found for this precise combination of State and Purpose.")

    with tab2:
        st.subheader("Historical Market Credit Profiles")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Portfolio Records", f"{len(df):,}")
        m2.metric("Global Mean Credit Score", f"{df['Credit Score'].mean():.1f}")
        m3.metric("Global Mean DTI Ratio", f"{df['Original Debt-to-Income (DTI) Ratio'].mean():.1f}%")
        m4.metric("Global Mean Interest Rate", f"{df['Original Interest Rate'].mean():.3f}%")
        
        # Charts
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # 1. Credit Score Distribution
        sns.histplot(df['Credit Score'], bins=30, kde=True, color='teal', ax=axes[0])
        axes[0].axvline(user_fico, color=fico_color, linestyle='--', linewidth=2.5, label=f"Applicant FICO ({user_fico})")
        axes[0].set_title("Distribution of Credit Scores for Approved Portfolio")
        axes[0].legend()
        
        # 2. Interest Rate vs Credit Score Range
        df['FICO_Tier'] = pd.cut(df['Credit Score'], bins=[300, 619, 669, 739, 850], 
                                 labels=['Subprime (<620)', 'Fair (620-669)', 'Good (670-739)', 'Excellent (740+)'])
        rate_by_tier = df.groupby('FICO_Tier', observed=False)['Original Interest Rate'].mean().reset_index()
        sns.barplot(x='FICO_Tier', y='Original Interest Rate', data=rate_by_tier, palette='viridis', ax=axes[1])
        axes[1].set_title("Average Offered Interest Rate by Credit Tier")
        axes[1].set_ylabel("Average Interest Rate (%)")
        axes[1].set_xlabel("Credit Score Tier")
        
        st.pyplot(fig)
        
        st.markdown("### Risk Matrix: Average DTI & Interest Rates by Credit Tier")
        summary_matrix = df.groupby('FICO_Tier', observed=False).agg({
            'Original Interest Rate': 'mean',
            'Original Debt-to-Income (DTI) Ratio': 'mean',
            'Original UPB': 'mean'
        }).reset_index()
        summary_matrix.columns = ['Credit Tier', 'Avg Interest Rate (%)', 'Avg DTI (%)', 'Avg Loan Volume ($)']
        st.dataframe(summary_matrix.style.format({
            'Avg Interest Rate (%)': '{:.3f}%',
            'Avg DTI (%)': '{:.1f}%',
            'Avg Loan Volume ($)': '${:,.2f}'
        }), use_container_width=True)

    with tab3:
        st.subheader("Regional State Metric Breakdown")
        state_stats = df.groupby('Property State').agg({
            'Credit Score': 'mean',
            'Original Interest Rate': 'mean',
            'Original UPB': 'mean'
        }).reset_index().sort_values(by='Credit Score', ascending=False)
        
        state_stats.columns = ['State', 'Average Credit Score', 'Average Interest Rate (%)', 'Average Loan Volume ($)']
        
        st.markdown("The table below shows loan attributes across different geographical states in the dataset:")
        st.dataframe(state_stats.style.format({
            'Average Credit Score': '{:.1f}',
            'Average Interest Rate (%)': '{:.3f}%',
            'Average Loan Volume ($)': '${:,.2f}'
        }), use_container_width=True, height=400)