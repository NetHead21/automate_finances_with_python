import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

st.set_page_config(page_title="Simple Finance App", page_icon="$", layout="wide")
category_file = "categories.json"

if "categories" not in st.session_state:
    st.session_state.categories = {"Uncategorized": []}


def save_categories() -> None:
    with open(category_file, "w") as file:
        json.dump(st.session_state.categories, file)


# Load categories from file if it exists, handling empty/invalid JSON
if os.path.exists(category_file):
    try:
        with open(category_file, "r") as file:
            st.session_state.categories = json.load(file)
    except json.JSONDecodeError:
        st.session_state.categories = {"Uncategorized": []}
        save_categories()


def categorize_transaction(df):
    df["Category"] = "Uncategorized"

    for category, keywords in st.session_state.categories.items():
        if category == "Uncategorized" or not keywords:
            continue

        lowered_keywords = [keyword.lower().strip() for keyword in keywords]

        for idx, row in df.iterrows():
            details = row["Details"].lower().strip()
            if details is lowered_keywords:
                df.at[idx, "Category"] = category
    return df


def load_transactions(file: str):
    try:
        df = pd.read_csv(file)
        df.columns = [col.strip() for col in df.columns]
        df["Amount"] = df["Amount"].str.replace(",", "").astype(float)
        df["Date"] = pd.to_datetime(df["Date"], format="%d %b %Y")
        st.write(df)
        return categorize_transaction(df)
    except Exception as e:
        st.error(f"Error processing file {e}")
        return None


def add_keyword_to_category(category: str, keyword: str) -> bool:
    keyword = keyword.strip()

    if keyword and keyword not in st.session_state.categories[category]:
        st.session_state.categories[category].append(keyword)
        save_categories()
        return True
    return False


def main():
    st.title("Simple Finance Dashboard")

    uploaded_file = st.file_uploader("Upload your transaction CSV file", type=["csv"])

    if uploaded_file:
        df = load_transactions(uploaded_file)

        if df is not None:
            debits_df = df[df["Debit/Credit"] == "Debit"].copy()
            credits_df = df[df["Debit/Credit"] == "Credit"].copy()

            tab1, tab2 = st.tabs(["Expenses (Debits)", "Payments (Credits)"])

            with tab1:
                new_category = st.text_input("New Category Name")
                add_button = st.button("Add Category")

                if add_button and new_category:
                    if new_category not in st.session_state.categories:
                        st.session_state.categories[new_category] = []
                        save_categories()
                        st.success(f"Added a new category: {new_category}")
                        st.rerun()

                st.write(debits_df)

            with tab2:
                st.write(credits_df)


main()
