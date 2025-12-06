import streamlit as st
import polars as pl

# ========= UI HEADER =========
st.markdown("""
<div style='background-color:#1e3d59; padding:18px; border-radius:12px; text-align:center;'>
    <h1 style='color:white;'>Sunil Kumar Talabhaktula</h1>
    <h3 style='color:#f5f0e1;'>High-Performance CSV Processing Tool (Polars)</h3>
</div><br>
""", unsafe_allow_html=True)

# ========= POLARS CSV LOADING =========
uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

if uploaded_file:

    # Load only once per file
    if "loaded_file" not in st.session_state or st.session_state.loaded_file != uploaded_file.name:

        df = pl.read_csv(uploaded_file, infer_schema_length=50000)

        # 🔥 Replace all nulls with empty strings globally
        df = df.fill_null("")

        st.session_state.df = df
        st.session_state.loaded_file = uploaded_file.name
        st.session_state.merge_active = True
        st.session_state.filter_active = True

    df = st.session_state.df

    st.write(f"### Total Rows in Uploaded File: **{df.height()}**")

    st.write("### Preview:")
    st.dataframe(df.head().to_pandas())

    sorted_columns = sorted(df.columns)

    # ========= STEP 2: MERGING =========
    if st.session_state.merge_active:

        st.write("## 🔧 Merge Columns")

        merge_cols = st.multiselect("Select columns to merge:", sorted_columns)
        new_col = st.text_input("New merged column name:")

        if st.button("Merge"):

            if merge_cols and new_col.strip():

                df = df.with_columns(
                    pl.concat_str([pl.col(c).cast(str) for c in merge_cols], separator=" ").alias(new_col)
                )

                # Remove double spaces + trim
                df = df.with_columns(pl.col(new_col).str.replace_all(r"\s+", " ").str.strip()_chars())

                st.session_state.df = df
                st.session_state.new_col = ""
                st.success(f"Merged column created: {new_col}")

            else:
                st.warning("Select columns and enter a column name.")

        if st.radio("Merge more columns?", ("Yes", "No")) == "No":
            st.session_state.merge_active = False

    # ========= STEP 3: FILTERING =========
    if not st.session_state.merge_active and st.session_state.filter_active:

        st.write("## 🔍 Filter Data")

        filter_col = st.selectbox("Column to filter:", sorted_columns)

        col_values = df[filter_col].fill_null("").to_list()

        unique_vals = sorted(set([v if v != "" else "(Blank)" for v in col_values]))

        filter_vals = st.multiselect("Select values to keep:", unique_vals)

        if st.button("Apply Filter"):

            mask = None

            # Blank handling
            if "(Blank)" in filter_vals:
                blank_mask = (pl.col(filter_col) == "") | pl.col(filter_col).is_null()
                mask = blank_mask

            # Non-blanks
            real_vals = [v for v in filter_vals if v != "(Blank)"]
            if real_vals:
                non_blank_mask = pl.col(filter_col).is_in(real_vals)
                mask = non_blank_mask if mask is None else (mask | non_blank_mask)

            if mask is not None:
                df = df.filter(mask)
                st.session_state.df = df
                st.success("Filter applied!")
                st.dataframe(df.head().to_pandas())
            else:
                st.warning("Select at least one value to filter.")

        if st.radio("Filter more?", ("Yes", "No")) == "No":
            st.session_state.filter_active = False

    # ========= STEP 4: OUTPUT + EXPORT =========
    if not st.session_state.filter_active and not st.session_state.merge_active:

        st.write("## ✅ Final Output")

        df = st.session_state.df
        st.write(f"### Total Rows After Processing: **{df.height()}**")

        sorted_columns = sorted(df.columns)

        col_choice = st.radio("Choose output columns:", ("All Columns", "Select Columns"))

        if col_choice == "All Columns":
            final_df = df
        else:
            selected = st.multiselect("Select output columns:", sorted_columns, default=sorted_columns)
            final_df = df.select(selected)

        # Export to CSV
        csv_data = final_df.write_csv()

        st.download_button("⬇️ Download CSV", csv_data, "processed_output.csv", "text/csv")

        output_path = st.text_input("Enter path to save file:")

        if st.button("Save"):
            try:
                with open(output_path, "wb") as f:
                    f.write(csv_data)
                st.success("File saved successfully!")
            except Exception as e:
                st.error(f"Error: {e}")
