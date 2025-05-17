import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

st.set_page_config(page_title="Simple Finance App", page_icon="$", layout="wide")
category_file = "categories.json"


def load_categories() -> dict:
    # Load categories from file if it exists, handling empty/invalid JSON
    if os.path.exists(category_file):
        try:
            with open(category_file, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            pass
    return {"Uncategorized": []}


if "categories" not in st.session_state:
    st.session_state.categories = load_categories()


def save_categories() -> None:
    with open(category_file, "w") as file:
        json.dump(st.session_state.categories, file)


def categorize_transaction(df):
    df["Category"] = "Uncategorized"

    categories = st.session_state.categories
    for category, keywords in categories.items():
        if category == "Uncategorized" or not keywords:
            continue

        lowered_keywords = [keyword.lower().strip() for keyword in keywords]

        mask = (
            df["Details"]
            .str.lower()
            .str.strip()
            .apply(
                lambda details: any(keyword in details for keyword in lowered_keywords)
            )
        )
        df.loc[mask, "Category"] = category
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
            debits_df = df[df["Debit/Credit"] == "Debit"]
            credits_df = df[df["Debit/Credit"] == "Credit"]

            st.session_state.debits_df = debits_df.copy()

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

                st.subheader("Your Expenses")
                edited_df = st.data_editor(
                    st.session_state.debits_df[
                        ["Date", "Details", "Amount", "Category"]
                    ],
                    column_config={
                        "Date": st.column_config.DateColumn(
                            "Date", format="DD/MM/YYYY"
                        ),
                        "Amount": st.column_config.NumberColumn(
                            "Amount", format="%.2f USD"
                        ),
                        "Category": st.column_config.SelectboxColumn(
                            "Category", options=list(st.session_state.categories.keys())
                        ),
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="category_editor",
                )

                save_button = st.button("Apply Changes", type="primary")

                if save_button:
                    for idx, row in edited_df.iterrows():
                        new_category = row["Category"]

                        if (
                            row["Category"]
                            == st.session_state.debits_df.at[idx, "Category"]
                        ):
                            continue

                        details = row["Details"]
                        st.session_state.debits_df.at[idx, "Category"] = new_category
                        add_keyword_to_category(new_category, details)

                st.subheader("Expense Summary")
                category_totals = (
                    st.session_state.debits_df.groupby("Category")["Amount"]
                    .sum()
                    .reset_index()
                )
                category_totals = category_totals.sort_values("Amount", ascending=False)

                st.dataframe(
                    category_totals,
                    column_config={
                        "Amount": st.column_config.NumberColumn(
                            "Amount", format="%.2f USD"
                        )
                    },
                    use_container_width=True,
                    hide_index=True,
                )

                fig = px.pie(
                    category_totals,
                    values="Amount",
                    names="Category",
                    title="Expenses by Category",
                )

                st.plotly_chart(fig, use_container_width=True)

            with tab2:
                st.subheader("Payments Summary")
                total_payments = credits_df["Amount"].sum()
                st.metric("Total Payments", f"{total_payments:,.2f} USD")
                st.write(credits_df)


main()
