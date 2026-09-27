# -*- coding: utf-8 -*-
"""


@author: imara
Description: Streamlit interface for the AI Data Analyst application.

Handles CSV upload, data preview, interactive visualisation,
and natural-language analysis through the AI agent.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from agent import ask_agent


# Page config

st.set_page_config(
    page_title="AI Assisted Data Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Add title 
st.title("AI Assisted Data Analyst")

st.write(
    "Upload a CSV file to explore your data, uncover insights, and get answers from an AI-powered analyst."
)

# Upload the user data

st.header("Start by uploading your dataset 👇")

uploaded_file = st.file_uploader(
    "Upload CSV",
    type=["csv"]
)
    
# Add uploaded file into pandas data frame
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.success(
        f"Loaded {len(df):,} rows and {len(df.columns)} columns."
    )
     # 4 tab layout to make interactive   
    tab_data, tab_dashboard, tab_ai = st.tabs([
        "📋 Data Preview",
        "📊 Dashboard",
        "🤖 Ask AI"
    ])
    with tab_data:
        st.subheader("Data Preview")
        st.dataframe(df.head(5),
        width='stretch',
        hide_index=True
        )
        st.subheader("Column Information")

        column_info = pd.DataFrame({
            "Column": df.columns,
            "Data Type": df.dtypes.astype(str).values
        })
        
        st.dataframe(
            column_info,
            width='stretch',
            hide_index=True
        )
    with tab_dashboard:
        st.subheader("Dashboard")
        #Compute the stat of the data
        numeric_columns = len(df.select_dtypes(include="number").columns)

        text_columns = len(df.select_dtypes(exclude="number").columns)
        
        missing_values = int(df.isna().sum().sum())
        
        duplicate_rows = int(df.duplicated().sum())
        #diaplay the computed values on app
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Numeric Columns", numeric_columns)

        with col2:
            st.metric("Other Columns", text_columns)
        
        with col3:
            st.metric("Missing Values", missing_values)
        
        with col4:
            st.metric("Duplicate Rows", duplicate_rows)
        st.divider()

        st.subheader("Explore your data")

        numeric_cols = df.select_dtypes( include="number").columns.tolist()
        
        x_col = st.selectbox("Choose a category", df.columns)
        y_col = st.selectbox("Choose a measure", numeric_cols)
        # aggregate the data by summing up for  each category 
        chart_data = (df.groupby(x_col, as_index=False)[y_col].sum())
        chart_type = st.selectbox("Choose chart type",["Bar", "Line", "Pie"])
        if chart_type == "Bar":
            fig = px.bar(
                chart_data,
                x=x_col,
                y=y_col,
                title=f"{y_col} by {x_col}"
            )

        elif chart_type == "Line":
            fig = px.line(
                chart_data,
                x=x_col,
                y=y_col,
                markers=True,
                title=f"{y_col} by {x_col}"
            )
        
        elif chart_type == "Pie":
            fig = px.pie(
                chart_data,
                names=x_col,
                values=y_col,
                title=f"{y_col} by {x_col}"
            )
        st.plotly_chart(fig,width='stretch')
        
    with tab_ai:
        st.subheader("AI Analyst")       
        st.write(
            "Ask a question about your dataset in plain English. "
            "The AI analyst will generate SQL, analyse the data, "
            "and explain the result.")
        
        with st.form("ai_question_form"):
            question = st.text_input("Ask your data",
                placeholder="e.g. Which region has the highest total revenue?" )
        
            analyse = st.form_submit_button("Analyse", type="primary")
        if analyse and question:
            with st.spinner("Analysing your data..."):       
                answer, generated_sql, result = ask_agent(question, df)
            st.subheader("Insight")
            st.write(answer)
            if generated_sql is not None:
                with st.expander("View analysis details"):
                    st.code(generated_sql, language="sql")
                    st.dataframe(result, width='stretch', hide_index=True)
        
