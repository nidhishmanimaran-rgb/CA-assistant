"""Explicit financial inputs for reliable arithmetic without an API."""
import streamlit as st
from backend.calculator import calculate, format_calculation
from backend.errors import AppError


def render_calculator(context):
    st.subheader("Depreciation workbench")
    st.write("Choose an explicit method and enter the facts. These procedures work without an API key.")
    choices = {"Straight-line": "straight_line", "Reducing balance": "reducing_balance",
               "Revised estimate (prospective)": "revised_estimate"}
    label = st.selectbox("Depreciation method", tuple(choices), key="calc_method")
    method = choices[label]
    with st.form("depreciation_form"):
        values = {}
        if method == "straight_line":
            values["cost"] = st.text_input("Cost (INR)", value="850000", key="calc_cost")
            values["life"] = st.text_input("Useful life (years)", value="8", key="calc_life")
        else:
            values["opening"] = st.text_input("Opening carrying amount (INR)", value="850000", key="calc_opening")
            if method == "reducing_balance":
                values["rate"] = st.text_input("Annual reducing-balance rate (%)", value="20", key="calc_rate")
            else:
                values["remaining_life"] = st.text_input("Remaining useful life (years)", value="8", key="calc_remaining")
        values["residual"] = st.text_input("Residual value (INR)", value="50000", key="calc_residual")
        values["months"] = st.text_input("Months in use in this period", value="12", key="calc_months")
        submitted = st.form_submit_button("Calculate working notes")
    if submitted:
        try:
            result = calculate(method, **values)
            st.markdown(format_calculation(result, context.answer_format))
            import json
            st.download_button("Download calculation", json.dumps(result.as_dict(), indent=2),
                               file_name="ca-calculation.json", mime="application/json")
        except AppError as error:
            st.error(str(error))
    st.caption("This workbench calculates the selected procedure. It does not determine statutory depreciation rates, impairment, revaluation, disposal treatment or tax deductions.")
