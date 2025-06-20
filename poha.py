import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import math

# --- UTILITY AND SETUP FUNCTIONS ---

def format_indian_currency(amount):
    """Format a number into Indian currency style with ₹ symbol."""
    if not isinstance(amount, (int, float)) or pd.isna(amount) or math.isinf(amount):
        return "N/A"
    amount_str = f"{abs(amount):.2f}"
    parts = amount_str.split('.')
    integer_part, decimal_part = parts[0], parts[1]
    if len(integer_part) > 3:
        last_three = integer_part[-3:]
        remaining_part = integer_part[:-3]
        groups = [remaining_part[max(0, i-2):i] for i in range(len(remaining_part), 0, -2)]
        groups.reverse()
        formatted_amount = ','.join(groups) + ',' + last_three
    else:
        formatted_amount = integer_part
    if amount < 0:
        formatted_amount = '-' + formatted_amount
    return f"₹{formatted_amount}"

st.set_page_config(page_title="Poha Manufacturing Financial Dashboard", page_icon="🌾", layout="wide")

# Custom CSS for tooltips
st.markdown('''
<style>
.tooltip-container { position: relative; display: inline-block; cursor: help; margin-left: 5px; }
.tooltip-icon { color: #007bff; font-weight: bold; font-size: 14px; }
.tooltip-text { visibility: hidden; width: 320px; background-color: #333; color: #fff; text-align: left; border-radius: 6px; padding: 10px; position: absolute; z-index: 1; bottom: 125%; left: 50%; margin-left: -160px; opacity: 0; transition: opacity 0.3s; font-size: 14px; line-height: 1.4; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
.tooltip-text::after { content: " "; position: absolute; top: 100%; left: 50%; margin-left: -5px; border-width: 5px; border-style: solid; border-color: #333 transparent transparent transparent; }
.tooltip-container:hover .tooltip-text { visibility: visible; opacity: 1; }
</style>
''', unsafe_allow_html=True)

# --- FINANCIAL MODEL CALCULATION FUNCTION ---
def run_financial_model(inputs):
    """Calculate financial metrics based on input parameters."""
    # Unpack inputs
    hours_per_day = inputs['hours_per_day']
    days_per_month = inputs['days_per_month']
    poha_rate_kg_hr = inputs['poha_rate_kg_hr']
    paddy_yield = inputs['paddy_yield']
    byproduct_sale_percent = inputs['byproduct_sale_percent']
    paddy_rate = inputs['paddy_rate']
    poha_price = inputs['poha_price']
    byproduct_rate_kg = inputs['byproduct_rate_kg']
    land_cost = inputs['land_cost']
    civil_work_cost = inputs['civil_work_cost']
    machinery_cost = inputs['machinery_cost']
    machinery_useful_life_years = inputs['machinery_useful_life_years']
    packaging_cost = inputs['packaging_cost']
    fuel_cost = inputs['fuel_cost']
    other_var_cost = inputs['other_var_cost']
    rent_per_month = inputs['rent_per_month']
    labor_per_month = inputs['labor_per_month']
    electricity_per_month = inputs['electricity_per_month']
    security_ssc_insurance_per_month = inputs['security_ssc_insurance_per_month']
    misc_per_month = inputs['misc_per_month']
    equity_contrib = inputs['equity_contrib']
    interest_rate = inputs['interest_rate']
    tax_rate_percent = inputs['tax_rate_percent']
    rm_inventory_days = inputs['rm_inventory_days']
    fg_inventory_days = inputs['fg_inventory_days']
    debtor_days = inputs['debtor_days']
    creditor_days = inputs['creditor_days']

    # Calculations
    total_capex = land_cost + civil_work_cost + machinery_cost
    if any(v is None or (isinstance(v, (int, float)) and v <= 0) for v in [paddy_yield, poha_price, total_capex]):
        return {'error': 'Paddy Yield, Poha Price, and Capex must be greater than 0.'}

    daily_poha_production = poha_rate_kg_hr * hours_per_day
    monthly_poha_production = daily_poha_production * days_per_month
    annual_poha_production = monthly_poha_production * 12
    daily_paddy_consumption = (poha_rate_kg_hr / (paddy_yield / 100)) * hours_per_day if paddy_yield > 0 else 0
    monthly_paddy_consumption = daily_paddy_consumption * days_per_month
    annual_paddy_consumption = monthly_paddy_consumption * 12
    daily_byproduct_sold = (daily_paddy_consumption - daily_poha_production) * (byproduct_sale_percent / 100)
    monthly_byproduct_sold = daily_byproduct_sold * days_per_month
    annual_byproduct_sold = monthly_byproduct_sold * 12
    
    total_daily_revenue = (daily_poha_production * poha_price) + (daily_byproduct_sold * byproduct_rate_kg)
    total_monthly_revenue = (monthly_poha_production * poha_price) + (monthly_byproduct_sold * byproduct_rate_kg)
    total_annual_revenue = (annual_poha_production * poha_price) + (annual_byproduct_sold * byproduct_rate_kg)
    
    daily_cogs = daily_paddy_consumption * paddy_rate
    monthly_cogs = monthly_paddy_consumption * paddy_rate
    annual_cogs = annual_paddy_consumption * paddy_rate
    daily_gross_profit = total_daily_revenue - daily_cogs
    monthly_gross_profit = total_monthly_revenue - monthly_cogs
    annual_gross_profit = total_annual_revenue - annual_cogs

    total_variable_cost_per_kg_poha = packaging_cost + fuel_cost + other_var_cost
    annual_variable_operating_costs_total = annual_poha_production * total_variable_cost_per_kg_poha
    
    total_monthly_fixed_opex = rent_per_month + labor_per_month + electricity_per_month + security_ssc_insurance_per_month + misc_per_month
    annual_fixed_operating_costs = total_monthly_fixed_opex * 12
    total_operating_expenses_for_pnl = annual_fixed_operating_costs + annual_variable_operating_costs_total

    total_annual_depreciation = (machinery_cost + civil_work_cost) / machinery_useful_life_years if machinery_useful_life_years > 0 else 0
    operating_income_ebit = annual_gross_profit - total_operating_expenses_for_pnl - total_annual_depreciation

    daily_cogs_basis = annual_cogs / 365
    daily_cost_of_production = (annual_cogs + annual_variable_operating_costs_total) / annual_poha_production if annual_poha_production > 0 else 0
    daily_revenue_basis = total_annual_revenue / 365
    rm_inventory_value = daily_cogs_basis * rm_inventory_days
    fg_inventory_value = (daily_poha_production * daily_cost_of_production) * fg_inventory_days if daily_poha_production > 0 else 0
    accounts_receivable = daily_revenue_basis * debtor_days
    accounts_payable = daily_cogs_basis * creditor_days
    total_current_assets = rm_inventory_value + fg_inventory_value + accounts_receivable
    total_current_liabilities = accounts_payable
    net_working_capital = total_current_assets - total_current_liabilities

    initial_equity_contribution = total_capex * (equity_contrib / 100)
    total_debt_component = total_capex - initial_equity_contribution
    annual_interest_expense_fixed_assets = total_debt_component * (interest_rate / 100)
    interest_on_working_capital = max(0, net_working_capital) * (interest_rate / 100)
    annual_interest_expense = annual_interest_expense_fixed_assets + interest_on_working_capital

    earnings_before_tax_ebt = operating_income_ebit - annual_interest_expense
    taxes = max(0, earnings_before_tax_ebt) * (tax_rate_percent / 100)
    net_profit = earnings_before_tax_ebt - taxes

    total_assets_for_roce = total_capex + total_current_assets
    capital_employed = total_assets_for_roce - total_current_liabilities
    roce = (operating_income_ebit / capital_employed) * 100 if capital_employed != 0 else float('inf')
    net_profit_margin = (net_profit / total_annual_revenue) * 100 if total_annual_revenue > 0 else 0
    ebitda = operating_income_ebit + total_annual_depreciation
    ebitda_margin = (ebitda / total_annual_revenue) * 100 if total_annual_revenue > 0 else 0
    roe = (net_profit / initial_equity_contribution) * 100 if initial_equity_contribution > 0 else float('inf')
    gross_profit_margin = (annual_gross_profit / total_annual_revenue) * 100 if total_annual_revenue > 0 else 0

    return {**inputs, **locals()}

# --- Key Ratio Definitions (ROI Removed) ---
key_ratios_info = {
    "Net Profit": {"formula": "Net Profit = EBT - Taxes", "explanation": "The final 'bottom line' profit after all costs."},
    "EBITDA": {"formula": "EBITDA = EBIT + Depreciation", "explanation": "Measures operational profitability before non-cash expenses."},
    "ROCE": {"formula": "ROCE = (EBIT / Capital Employed) * 100", "explanation": "Measures how effectively capital is used to generate profits."},
    "ROE": {"formula": "ROE = (Net Profit / Initial Equity) * 100", "explanation": "Shows profitability relative to shareholder equity."}
}

# --- Custom Metric Display Function ---
def custom_metric(col, label, value, sub_value, info_key):
    """Display a metric with a tooltip in a specified column."""
    formula, explanation = key_ratios_info[info_key].values()
    tooltip_content = f"<b>Formula:</b> {formula}<br><br><b>Explanation:</b> {explanation}"
    try:
        numeric_value = float(sub_value.replace('%', '').replace(' Margin', '').strip())
    except:
        numeric_value = 0
    color = 'green' if numeric_value >= 0 else 'red'
    with col:
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 5px;">
                <p style="font-size: 14px; color: grey; margin-bottom: 0px; line-height: 1.2;">{label}</p>
                <span class="tooltip-container"><span class="tooltip-icon">❓</span><span class="tooltip-text">{tooltip_content}</span></span>
            </div>
            <p style="font-size: 24px; font-weight: bold; margin-top: 0px; margin-bottom: 0px; line-height: 1.2;">{value}</p>
            <p style="font-size: 14px; color: {color}; margin-top: 0px; line-height: 1.2;">{sub_value}</p>
            """, unsafe_allow_html=True)

# --- APP LAYOUT ---
st.title("🌾 Poha Manufacturing Financial Dashboard")
st.markdown("### A Comprehensive Financial Model for Decision Making")

# --- SCENARIO MANAGEMENT ---
scenarios = {
    'Base Case': {'paddy_rate': 21.5, 'poha_price': 45.0, 'paddy_yield': 62.0, 'interest_rate': 9.0, 'equity_contrib': 30.0, 'packaging_cost': 0.5, 'fuel_cost': 0.0, 'other_var_cost': 0.0, 'byproduct_rate_kg': 5.0},
    'Optimistic': {'paddy_rate': 20.0, 'poha_price': 48.0, 'paddy_yield': 65.0, 'interest_rate': 8.5, 'equity_contrib': 40.0, 'packaging_cost': 0.4, 'fuel_cost': 0.0, 'other_var_cost': 0.0, 'byproduct_rate_kg': 6.0},
    'Pessimistic': {'paddy_rate': 25.0, 'poha_price': 42.0, 'paddy_yield': 60.0, 'interest_rate': 10.0, 'equity_contrib': 20.0, 'packaging_cost': 0.6, 'fuel_cost': 0.0, 'other_var_cost': 0.0, 'byproduct_rate_kg': 4.0}
}
st.sidebar.header("⚙️ Input Parameters")
if 'scenario_choice' not in st.session_state:
    st.session_state.scenario_choice = 'Base Case'

def update_scenario():
    scenario_name = st.session_state.scenario_choice
    if scenario_name in scenarios:
        for key, value in scenarios[scenario_name].items():
            st.session_state[key] = value

for key in scenarios['Base Case']:
    if key not in st.session_state:
        st.session_state[key] = scenarios['Base Case'][key]
st.sidebar.selectbox("Select Scenario", list(scenarios.keys()), key='scenario_choice', on_change=update_scenario)

# --- SIDEBAR INPUTS ---
all_inputs = {}
with st.sidebar.expander("Operational Assumptions", True):
    all_inputs['hours_per_day'] = st.slider("Production Hours per Day", 5, 24, 10)
    all_inputs['days_per_month'] = st.slider("Operational Days per Month", 1, 31, 24)
with st.sidebar.expander("Production & Yield", True):
    all_inputs['poha_rate_kg_hr'] = st.number_input("Poha Rate (kg/hr)", value=800)
    all_inputs['paddy_yield'] = st.number_input("Paddy to Poha Yield (%)", key='paddy_yield')
    all_inputs['byproduct_sale_percent'] = st.number_input("Byproduct Sold (%)", value=34.0)
with st.sidebar.expander("Financial Assumptions (INR)", True):
    all_inputs['paddy_rate'] = st.number_input("Paddy Rate (INR/kg)", key='paddy_rate')
    all_inputs['poha_price'] = st.number_input("Poha Selling Price (INR/kg)", key='poha_price')
    all_inputs['byproduct_rate_kg'] = st.number_input("Byproduct Rate (INR/kg)", key='byproduct_rate_kg')
with st.sidebar.expander("Capital Expenditure (Capex)", True):
    all_inputs['land_cost'] = st.number_input("Land Cost", value=0)
    all_inputs['civil_work_cost'] = st.number_input("Civil Work Cost", value=0)
    all_inputs['machinery_cost'] = st.number_input("Machinery Cost", value=7000000)
    all_inputs['machinery_useful_life_years'] = st.number_input("Useful Life (Years)", value=15)
with st.sidebar.expander("Operating Costs", True):
    st.markdown("##### Granular Variable Costs (per kg)")
    all_inputs['packaging_cost'] = st.number_input("Packaging Material", key='packaging_cost')
    all_inputs['fuel_cost'] = st.number_input("Fuel/Power (Variable)", key='fuel_cost')
    all_inputs['other_var_cost'] = st.number_input("Other Variable Costs", key='other_var_cost')
    st.markdown("##### Detailed Fixed Costs (Monthly)")
    all_inputs['rent_per_month'] = st.number_input("Rent", value=300000)
    all_inputs['labor_per_month'] = st.number_input("Labor Wages and Salaries", value=400000)
    all_inputs['electricity_per_month'] = st.number_input("Electricity (Fixed)", value=150000)
    all_inputs['security_ssc_insurance_per_month'] = st.number_input("Security, SSC & Insurance", value=300000)
    all_inputs['misc_per_month'] = st.number_input("Misc Overheads", value=300000)
with st.sidebar.expander("Funding & Tax", True):
    all_inputs['equity_contrib'] = st.slider("Equity Contribution (%)", 0.0, 100.0, key='equity_contrib')
    all_inputs['interest_rate'] = st.number_input("Interest Rate (%)", key='interest_rate')
    all_inputs['tax_rate_percent'] = st.slider("Corporate Tax Rate (%)", 0.0, 50.0, 25.0)
with st.sidebar.expander("Working Capital Days", True):
    all_inputs['rm_inventory_days'] = st.number_input("RM Inventory Days", value=72)
    all_inputs['fg_inventory_days'] = st.number_input("FG Inventory Days", value=20)
    all_inputs['debtor_days'] = st.number_input("Debtor Days", value=45)
    all_inputs['creditor_days'] = st.number_input("Creditor Days", value=5)

# --- MAIN DASHBOARD LOGIC & DISPLAY ---
results = run_financial_model(all_inputs)

if 'error' in results:
    st.error(results['error'])
else:
    # --- KPI DISPLAY (ROI Removed) ---
    st.header("📈 Key Performance Indicators (Annual)")
    col1, col2, col3, col4 = st.columns(4)
    custom_metric(col1, "Net Profit", format_indian_currency(results['net_profit']), f"{results['net_profit_margin']:.2f}% Margin", "Net Profit")
    custom_metric(col2, "EBITDA", format_indian_currency(results['ebitda']), f"{results['ebitda_margin']:.2f}% Margin", "EBITDA")
    custom_metric(col3, "ROCE", f"{results['roce']:.2f}%", "", "ROCE")
    custom_metric(col4, "ROE", f"{results['roe']:.2f}%", "", "ROE")

    # --- Daily, Monthly, Annual Summary ---
    st.markdown("---")
    st.header("📊 Daily, Monthly, and Annual Summary")
    summary_data = {
        "Metric": ["Poha Production (kg)", "Paddy Consumption (kg)", "Total Revenue", "COGS", "Gross Profit"],
        "Daily": [f"{results['daily_poha_production']:,.0f}", f"{results['daily_paddy_consumption']:,.0f}", format_indian_currency(results['total_daily_revenue']), format_indian_currency(results['daily_cogs']), format_indian_currency(results['daily_gross_profit'])],
        "Monthly": [f"{results['monthly_poha_production']:,.0f}", f"{results['monthly_paddy_consumption']:,.0f}", format_indian_currency(results['total_monthly_revenue']), format_indian_currency(results['monthly_cogs']), format_indian_currency(results['monthly_gross_profit'])],
        "Annual": [f"{results['annual_poha_production']:,.0f}", f"{results['annual_paddy_consumption']:,.0f}", format_indian_currency(results['total_annual_revenue']), format_indian_currency(results['annual_cogs']), format_indian_currency(results['annual_gross_profit'])]
    }
    st.dataframe(pd.DataFrame(summary_data), hide_index=True, use_container_width=True)

    # --- BREAKEVEN ANALYSIS ---
    st.markdown("---")
    st.header("💡 Breakeven Analysis")
    rm_cost_per_kg_poha_output = results['paddy_rate'] / (results['paddy_yield'] / 100) if results['paddy_yield'] > 0 else float('inf')
    total_variable_cost_per_kg = rm_cost_per_kg_poha_output + results['total_variable_cost_per_kg_poha']
    contribution_margin_per_kg = results['poha_price'] - total_variable_cost_per_kg
    total_fixed_costs_for_breakeven = results['annual_fixed_operating_costs'] + results['total_annual_depreciation'] + results['annual_interest_expense']
    breakeven_volume_kg = total_fixed_costs_for_breakeven / contribution_margin_per_kg if contribution_margin_per_kg > 0 else float('inf')
    col_be1, col_be2 = st.columns(2)
    with col_be1:
        st.metric("Breakeven Volume", f"{breakeven_volume_kg:,.0f} kg")
        st.metric("Breakeven Revenue", format_indian_currency(breakeven_volume_kg * results['poha_price']))
    with col_be2:
        max_production = results.get('annual_poha_production', 0)
        max_volume = max(max_production, breakeven_volume_kg) * 1.5 if breakeven_volume_kg != float('inf') else max_production * 1.5
        volumes = np.linspace(0, max_volume, 100)
        total_revenue_line = volumes * results['poha_price']
        total_cost_line = total_fixed_costs_for_breakeven + (volumes * total_variable_cost_per_kg)
        be_df = pd.DataFrame({'Production Volume (kg)': volumes, 'Total Revenue': total_revenue_line, 'Total Costs': total_cost_line})
        fig = px.line(be_df, x='Production Volume (kg)', y=['Total Revenue', 'Total Costs'], title="Visual Breakeven Analysis", markers=True)
        if breakeven_volume_kg != float('inf'):
            fig.add_vline(x=breakeven_volume_kg, line_dash="dash", line_color="red", annotation_text="Breakeven Point")
        st.plotly_chart(fig, use_container_width=True)

    # --- SENSITIVITY ANALYSIS ---
    st.markdown("---")
    st.header("🔬 Sensitivity Analysis")
    sensitivity_variable = st.selectbox("Select variable to analyze:", ("Poha Selling Price", "Paddy Rate", "Paddy to Poha Yield"))
    sensitivity_range = st.slider("Select sensitivity range (% change from base):", -50, 50, (-20, 20))
    base_value_map = {"Poha Selling Price": 'poha_price', "Paddy Rate": 'paddy_rate', "Paddy to Poha Yield": 'paddy_yield'}
    var_key = base_value_map[sensitivity_variable]
    base_value = all_inputs[var_key]
    range_values = np.linspace(base_value * (1 + sensitivity_range[0] / 100), base_value * (1 + sensitivity_range[1] / 100), 11)
    sensitivity_results_list = [run_financial_model({**all_inputs, var_key: val}) for val in range_values]

    # Prepare numeric data for the plot
    numeric_sensitivity_data = []
    for val, res in zip(range_values, sensitivity_results_list):
        if 'error' not in res:
            numeric_sensitivity_data.append({sensitivity_variable: val, 'Net Profit': res['net_profit']})
    numeric_sensitivity_df = pd.DataFrame(numeric_sensitivity_data)

    # Prepare formatted data for the table
    formatted_sensitivity_data = []
    for val, res in zip(range_values, sensitivity_results_list):
        if 'error' in res:
            net_profit_str = "Error: Invalid Input"
        else:
            net_profit_str = format_indian_currency(res['net_profit'])
        formatted_sensitivity_data.append({sensitivity_variable: val, 'Net Profit': net_profit_str})
    formatted_sensitivity_df = pd.DataFrame(formatted_sensitivity_data)

    col_sens1, col_sens2 = st.columns(2)
    with col_sens1:
        st.dataframe(
            formatted_sensitivity_df,
            column_config={
                sensitivity_variable: st.column_config.NumberColumn(format="%.2f"),
                "Net Profit": st.column_config.TextColumn()
            },
            use_container_width=True
        )
    with col_sens2:
        if not numeric_sensitivity_df.empty:
            fig_sens = px.line(numeric_sensitivity_df, x=sensitivity_variable, y='Net Profit', title=f"Impact of {sensitivity_variable} on Net Profit", markers=True)
            st.plotly_chart(fig_sens, use_container_width=True)
        else:
            st.write("No valid data points for plotting due to input errors.")

    # --- P&L and Balance Sheet ---
    st.markdown("---")
    col_pnl, col_bs = st.columns(2)
    with col_pnl:
        st.header("💰 Annual Profit & Loss Statement")
        pnl_data = {
            "Metric": ["Total Revenue", "COGS", "**Gross Profit**", "Fixed OpEx", "Variable OpEx", "Depreciation", "**EBIT**", "Total Interest", "**EBT**", "Taxes", "**Net Profit**"],
            "Amount (INR)": [
                format_indian_currency(results['total_annual_revenue']),
                f"({format_indian_currency(results['annual_cogs'])})",
                f"**{format_indian_currency(results['annual_gross_profit'])}**",
                f"({format_indian_currency(results['annual_fixed_operating_costs'])})",
                f"({format_indian_currency(results['annual_variable_operating_costs_total'])})",
                f"({format_indian_currency(results['total_annual_depreciation'])})",
                f"**{format_indian_currency(results['operating_income_ebit'])}**",
                f"({format_indian_currency(results['annual_interest_expense'])})",
                f"**{format_indian_currency(results['earnings_before_tax_ebt'])}**",
                f"({format_indian_currency(results['taxes'])})",
                f"**{format_indian_currency(results['net_profit'])}**"
            ]
        }
        pnl_df = pd.DataFrame(pnl_data)
        st.dataframe(pnl_df, hide_index=True, use_container_width=True)
        st.download_button("Download P&L as CSV", pnl_df.to_csv(index=False).encode('utf-8'), "poha_pnl.csv", "text/csv")
    with col_bs:
        st.header("💼 Balance Sheet & Working Capital")
        bs_data = {
            "Item": ["Total Capex", "Equity Contribution", "Debt Component", "**Total Assets**", "RM Inventory", "FG Inventory", "Receivables", "Payables", "**Net Working Capital**", "**Capital Employed**"],
            "Amount (INR)": [
                format_indian_currency(results['total_capex']),
                format_indian_currency(results['initial_equity_contribution']),
                format_indian_currency(results['total_debt_component']),
                f"**{format_indian_currency(results['total_assets_for_roce'])}**",
                format_indian_currency(results['rm_inventory_value']),
                format_indian_currency(results['fg_inventory_value']),
                format_indian_currency(results['accounts_receivable']),
                f"({format_indian_currency(results['accounts_payable'])})",
                f"**{format_indian_currency(results['net_working_capital'])}**",
                f"**{format_indian_currency(results['capital_employed'])}**"
            ]
        }
        st.dataframe(pd.DataFrame(bs_data), hide_index=True, use_container_width=True)
        
    # --- Detailed Calculation Breakdowns ---
    st.markdown("---")
    st.header("Detailed Calculation Breakdowns")
    with st.expander("Interest Calculation Details"):
        st.markdown("##### 1. Interest on Debt for Fixed Assets")
        st.markdown(f"**Formula:** `Debt Portion of Capex * Interest Rate`")
        st.markdown(f"`{format_indian_currency(results['total_debt_component'])} * {results['interest_rate']:.2f}% = {format_indian_currency(results['annual_interest_expense_fixed_assets'])}`")
        st.markdown("##### 2. Interest on Working Capital")
        st.markdown(f"**Formula:** `Net Working Capital * Interest Rate` (if NWC > 0)")
        if results['net_working_capital'] > 0:
            st.markdown(f"`{format_indian_currency(results['net_working_capital'])} * {results['interest_rate']:.2f}% = {format_indian_currency(results['interest_on_working_capital'])}`")
        else:
            st.markdown("`Net Working Capital is not positive, so no interest is charged.`")
        st.markdown("##### 3. Total Annual Interest Expense")
        st.markdown(f"**Formula:** `Interest on Debt + Interest on Working Capital`")
        st.markdown(f"`{format_indian_currency(results['annual_interest_expense_fixed_assets'])} + {format_indian_currency(results['interest_on_working_capital'])} = {format_indian_currency(results['annual_interest_expense'])}`")
    
    with st.expander("ROCE & Capital Employed Calculation"):
        st.markdown("##### 1. ROCE (Return on Capital Employed)")
        st.markdown(f"**Formula:** `EBIT / Capital Employed`")
        st.markdown(f"`{format_indian_currency(results['operating_income_ebit'])} / {format_indian_currency(results['capital_employed'])} = {results['roce']:.2f}%`")
        st.markdown("##### 2. Capital Employed")
        st.markdown(f"**Formula:** `Total Assets - Current Liabilities`")
        st.markdown(f"`{format_indian_currency(results['total_assets_for_roce'])} - {format_indian_currency(results['total_current_liabilities'])} = {format_indian_currency(results['capital_employed'])}`")
        st.markdown("##### 3. Total Assets")
        st.markdown(f"**Formula:** `Total Capex + Total Current Assets`")
        st.markdown(f"`{format_indian_currency(results['total_capex'])} + {format_indian_currency(results['total_current_assets'])} = {format_indian_currency(results['total_assets_for_roce'])}`")
        st.markdown("*(Note: Total Capex is used at its gross initial value for this calculation.)*")
    
    st.success("Dashboard loaded successfully!")
