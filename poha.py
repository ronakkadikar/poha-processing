import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import math

def format_indian_currency(amount):
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

def format_crore(amount):
    try:
        return f"₹{amount/1e7:,.2f} Cr"
    except Exception:
        return "N/A"

st.set_page_config(page_title="Poha Manufacturing Financial Dashboard", page_icon="🌾", layout="wide")

# Optimized CSS for responsiveness and compactness
st.markdown('''
<style>
/* General styling */
body { margin: 0; padding: 0; }
.main .block-container { padding: 1rem; max-width: 100%; }
h1 { font-size: 1.8rem; margin-bottom: 0.5rem; }
h2 { font-size: 1.4rem; margin-bottom: 0.5rem; }
h3 { font-size: 1.2rem; margin-bottom: 0.5rem; }
p { margin: 0.3rem 0; }

/* Sidebar styling */
.sidebar .sidebar-content {
    width: 200px !important; /* Reduced sidebar width */
    padding: 0.5rem;
    font-size: 0.85rem;
}
.sidebar .stSlider > div > div > div > div { height: 0.8rem; }
.sidebar .stNumberInput > div > input { padding: 0.3rem; font-size: 0.85rem; }
.sidebar .stSelectbox > div > div { padding: 0.3rem; font-size: 0.85rem; }
.sidebar .stExpander { margin-bottom: 0.3rem; }
.sidebar .stExpander > div > div { padding: 0.5rem; }

/* Tooltip styling */
.tooltip-container { position: relative; display: inline-block; cursor: help; margin-left: 3px; }
.tooltip-icon { color: #007bff; font-weight: bold; font-size: 12px; }
.tooltip-text {
    visibility: hidden;
    width: 280px;
    background-color: #333;
    color: #fff;
    text-align: left;
    border-radius: 4px;
    padding: 8px;
    position: absolute;
    z-index: 1;
    bottom: 125%;
    left: 50%;
    margin-left: -140px;
    opacity: 0;
    transition: opacity 0.3s;
    font-size: 12px;
    line-height: 1.3;
    box-shadow: 0 3px 6px rgba(0,0,0,0.2);
}
.tooltip-text::after {
    content: " ";
    position: absolute;
    top: 100%;
    left: 50%;
    margin-left: -5px;
    border-width: 5px;
    border-style: solid;
    border-color: #333 transparent transparent transparent;
}
.tooltip-container:hover .tooltip-text { visibility: visible; opacity: 1; }

/* Metric styling */
div[data-testid="column"] > div > div > p { font-size: 0.85rem; line-height: 1.1; }
div[data-testid="column"] > div > div > p:nth-child(2) { font-size: 1.2rem; font-weight: bold; }
div[data-testid="column"] > div > div > p:nth-child(3) { font-size: 0.8rem; }

/* Dataframe styling */
div[data-testid="stDataFrame"] { font-size: 0.9rem; }
div[data-testid="stDataFrame"] th { font-size: 0.9rem; padding: 0.5rem; }
div[data-testid="stDataFrame"] td { padding: 0.5rem; }

/* Responsive adjustments */
@media (max-width: 768px) {
    h1 { font-size: 1.5rem; }
    h2 { font-size: 1.2rem; }
    h3 { font-size: 1rem; }
    .main .block-container { padding: 0.5rem; }
    .sidebar .sidebar-content { width: 180px !important; }
    div[data-testid="column"] { margin-bottom: 0.5rem; }
    div[data-testid="stDataFrame"] { font-size: 0.8rem; }
    .tooltip-text { width: 200px; margin-left: -100px; font-size: 11px; }
}
@media (max-width: 480px) {
    h1 { font-size: 1.2rem; }
    h2 { font-size: 1rem; }
    h3 { font-size: 0.9rem; }
    .sidebar .sidebar-content { width: 160px !important; font-size: 0.75rem; }
    div[data-testid="column"] > div > div > p { font-size: 0.75rem; }
    div[data-testid="column"] > div > div > p:nth-child(2) { font-size: 1rem; }
    div[data-testid="stDataFrame"] { font-size: 0.7rem; }
}
</style>
''', unsafe_allow_html=True)

def run_financial_model(inputs):
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
    roi = (net_profit / total_capex) * 100 if total_capex > 0 else float('inf')
    roe = (net_profit / initial_equity_contribution) * 100 if initial_equity_contribution > 0 else float('inf')
    gross_profit_margin = (annual_gross_profit / total_annual_revenue) * 100 if total_annual_revenue > 0 else 0

    return {**inputs, **locals()}

key_ratios_info = {
    "Net Profit": {"formula": "Net Profit = EBT - Taxes", "explanation": "The final 'bottom line' profit after all costs."},
    "EBITDA": {"formula": "EBITDA = EBIT + Depreciation", "explanation": "Operational profitability before non-cash expenses."},
    "ROI": {"formula": "ROI = (Net Profit / Total Capex) * 100", "explanation": "Return on initial capital expenditure."},
    "ROCE": {"formula": "ROCE = (EBIT / Capital Employed) * 100", "explanation": "Effectiveness of capital in generating profits."},
    "ROE": {"formula": "ROE = (Net Profit / Equity) * 100", "explanation": "Profitability relative to shareholder equity."}
}

def custom_metric(col, label, value, sub_value, info_key):
    formula, explanation = key_ratios_info[info_key].values()
    tooltip_content = f"<b>Formula:</b> {formula}<br><br><b>Explanation:</b> {explanation}"
    try: numeric_value = float(sub_value.replace('%', '').replace(' Margin', '').strip())
    except: numeric_value = 0
    color = 'green' if numeric_value >= 0 else 'red'
    with col:
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 3px;">
                <p style="font-size: 0.85rem; color: grey; margin-bottom: 0px; line-height: 1.1;">{label}</p>
                <span class="tooltip-container"><span class="tooltip-icon">❓</span><span class="tooltip-text">{tooltip_content}</span></span>
            </div>
            <p style="font-size: 1.2rem; font-weight: bold; margin-top: 0px; margin-bottom: 0px; line-height: 1.1;">{value}</p>
            <p style="font-size: 0.8rem; color: {color}; margin-top: 0px; line-height: 1.1;">{sub_value}</p>
            """, unsafe_allow_html=True)

st.title("🌾 Poha Manufacturing Financial Dashboard")
st.markdown("### A Comprehensive Financial Model", unsafe_allow_html=True)

scenarios = {
    'Base Case': {'paddy_rate': 21.5, 'poha_price': 45.0, 'paddy_yield': 62.0, 'interest_rate': 9.0, 'equity_contrib': 30.0, 'packaging_cost': 0.5, 'fuel_cost': 0.0, 'other_var_cost': 0.0, 'byproduct_rate_kg': 5.0},
    'Optimistic': {'paddy_rate': 20.0, 'poha_price': 48.0, 'paddy_yield': 65.0, 'interest_rate': 8.5, 'equity_contrib': 40.0, 'packaging_cost': 0.4, 'fuel_cost': 0.0, 'other_var_cost': 0.0, 'byproduct_rate_kg': 6.0},
    'Pessimistic': {'paddy_rate': 25.0, 'poha_price': 42.0, 'paddy_yield': 60.0, 'interest_rate': 10.0, 'equity_contrib': 20.0, 'packaging_cost': 0.6, 'fuel_cost': 0.0, 'other_var_cost': 0.0, 'byproduct_rate_kg': 4.0}
}
st.sidebar.header("⚙️ Inputs")
if 'scenario_choice' not in st.session_state: st.session_state.scenario_choice = 'Base Case'
def update_scenario():
    scenario_name = st.session_state.scenario_choice
    if scenario_name in scenarios:
        for key, value in scenarios[scenario_name].items(): st.session_state[key] = value
for key in scenarios['Base Case']:
    if key not in st.session_state: st.session_state[key] = scenarios['Base Case'][key]
st.sidebar.selectbox("Scenario", list(scenarios.keys()), key='scenario_choice', on_change=update_scenario)

all_inputs = {}
with st.sidebar.expander("Operations", True):
    all_inputs['hours_per_day'] = st.slider("Hours/Day", 5, 24, 10, help="Production hours per day")
    all_inputs['days_per_month'] = st.slider("Days/Month", 1, 31, 24, help="Operational days per month")
with st.sidebar.expander("Production", True):
    all_inputs['poha_rate_kg_hr'] = st.number_input("Poha Rate (kg/hr)", value=800, help="Production rate")
    all_inputs['paddy_yield'] = st.number_input("Paddy Yield (%)", key='paddy_yield', help="Poha yield from paddy")
    all_inputs['byproduct_sale_percent'] = st.number_input("Byproduct Sold (%)", value=34.0, help="Byproduct sold")
with st.sidebar.expander("Financials (INR)", True):
    all_inputs['paddy_rate'] = st.number_input("Paddy Rate/kg", key='paddy_rate', help="Cost of paddy")
    all_inputs['poha_price'] = st.number_input("Poha Price/kg", key='poha_price', help="Selling price of poha")
    all_inputs['byproduct_rate_kg'] = st.number_input("Byproduct Rate/kg", key='byproduct_rate_kg', help="Byproduct price")
with st.sidebar.expander("Capex", True):
    all_inputs['land_cost'] = st.number_input("Land Cost", value=0, help="Cost of land")
    all_inputs['civil_work_cost'] = st.number_input("Civil Cost", value=0, help="Civil work cost")
    all_inputs['machinery_cost'] = st.number_input("Machinery Cost", value=7000000, help="Machinery cost")
    all_inputs['machinery_useful_life_years'] = st.number_input("Life (Years)", value=15, help="Machinery life")
with st.sidebar.expander("Op. Costs", True):
    st.markdown("##### Var Costs/kg")
    all_inputs['packaging_cost'] = st.number_input("Packaging", key='packaging_cost', help="Packaging cost")
    all_inputs['fuel_cost'] = st.number_input("Fuel", key='fuel_cost', help="Fuel cost")
    all_inputs['other_var_cost'] = st.number_input("Other Var", key='other_var_cost', help="Other variable costs")
    st.markdown("##### Fixed Costs/Month")
    all_inputs['rent_per_month'] = st.number_input("Rent", value=300000, help="Monthly rent")
    all_inputs['labor_per_month'] = st.number_input("Labor", value=400000, help="Labor wages")
    all_inputs['electricity_per_month'] = st.number_input("Electricity", value=150000, help="Fixed electricity")
    all_inputs['security_ssc_insurance_per_month'] = st.number_input("Security/Ins", value=300000, help="Security & insurance")
    all_inputs['misc_per_month'] = st.number_input("Misc", value=300000, help="Miscellaneous costs")
with st.sidebar.expander("Funding & Tax", True):
    all_inputs['equity_contrib'] = st.slider("Equity (%)", 0.0, 100.0, key='equity_contrib', help="Equity contribution")
    all_inputs['interest_rate'] = st.number_input("Interest (%)", key='interest_rate', help="Loan interest rate")
    all_inputs['tax_rate_percent'] = st.slider("Tax (%)", 0.0, 50.0, 25.0, help="Corporate tax rate")
with st.sidebar.expander("Working Capital", True):
    all_inputs['rm_inventory_days'] = st.number_input("RM Inv Days", value=72, help="Raw material inventory days")
    all_inputs['fg_inventory_days'] = st.number_input("FG Inv Days", value=20, help="Finished goods inventory days")
    all_inputs['debtor_days'] = st.number_input("Debtor Days", value=45, help="Receivables days")
    all_inputs['creditor_days'] = st.number_input("Creditor Days", value=5, help="Payables days")

results = run_financial_model(all_inputs)

if 'error' in results:
    st.error(results['error'])
else:
    st.header("📈 Key Performance Indicators")
    col1, col2, col3 = st.columns(3)
    custom_metric(col1, "Net Profit", format_indian_currency(results['net_profit']), f"{results['net_profit_margin']:.2f}% Margin", "Net Profit")
    custom_metric(col2, "EBITDA", format_indian_currency(results['ebitda']), f"{results['ebitda_margin']:.2f}% Margin", "EBITDA")
    custom_metric(col3, "ROI", f"{results['roi']:.2f}%", "", "ROI")
    col4, col5 = st.columns(2)
    custom_metric(col4, "ROCE", f"{results['roce']:.2f}%", "", "ROCE")
    custom_metric(col5, "ROE", f"{results['roe']:.2f}%", "", "ROE")

    st.divider()
    st.header("📊 Daily, Monthly, Annual")
    summary_data = {
        "Metric": ["Poha Production (kg)", "Paddy Consumption (kg)", "Revenue", "COGS", "Gross Profit"],
        "Daily": [f"{results['daily_poha_production']:,.0f}", f"{results['daily_paddy_consumption']:,.0f}", format_indian_currency(results['total_daily_revenue']), format_indian_currency(results['daily_cogs']), format_indian_currency(results['daily_gross_profit'])],
        "Monthly": [f"{results['monthly_poha_production']:,.0f}", f"{results['monthly_paddy_consumption']:,.0f}", format_indian_currency(results['total_monthly_revenue']), format_indian_currency(results['monthly_cogs']), format_indian_currency(results['monthly_gross_profit'])],
        "Annual": [f"{results['annual_poha_production']:,.0f}", f"{results['annual_paddy_consumption']:,.0f}", format_indian_currency(results['total_annual_revenue']), format_indian_currency(results['annual_cogs']), format_indian_currency(results['annual_gross_profit'])]
    }
    st.dataframe(pd.DataFrame(summary_data), hide_index=True, use_container_width=True)

    st.divider()
    st.header("💡 Breakeven Analysis")
    rm_cost_per_kg_poha_output = results['paddy_rate'] / (results['paddy_yield'] / 100) if results['paddy_yield'] > 0 else float('inf')
    total_variable_cost_per_kg = rm_cost_per_kg_poha_output + results['total_variable_cost_per_kg_poha']
    contribution_margin_per_kg = results['poha_price'] - total_variable_cost_per_kg
    total_fixed_costs_for_breakeven = results['annual_fixed_operating_costs'] + results['total_annual_depreciation'] + results['annual_interest_expense']
    breakeven_volume_kg = total_fixed_costs_for_breakeven / contribution_margin_per_kg if contribution_margin_per_kg > 0 else float('inf')
    col_be1, col_be2 = st.columns([1, 1])
    with col_be1:
        st.metric("Breakeven Volume", f"{breakeven_volume_kg:,.0f} kg")
        st.metric("Breakeven Revenue", format_indian_currency(breakeven_volume_kg * results['poha_price']))
    with col_be2:
        max_production = results.get('annual_poha_production', 0)
        max_volume = max(max_production, breakeven_volume_kg) * 1.5 if breakeven_volume_kg != float('inf') else max_production * 1.5
        volumes = np.linspace(0, max_volume, 100)
        total_revenue_line = volumes * results['poha_price']
        total_cost_line = total_fixed_costs_for_breakeven + (volumes * total_variable_cost_per_kg)
        be_df = pd.DataFrame({'Volume (kg)': volumes, 'Revenue': total_revenue_line, 'Costs': total_cost_line})
        fig = px.line(be_df, x='Volume (kg)', y=['Revenue', 'Costs'], title="Breakeven Analysis", markers=True)
        fig.update_layout(autosize=True)
        if breakeven_volume_kg != float('inf'):
            fig.add_vline(x=breakeven_volume_kg, line_dash="dash", line_color="red", annotation_text="Breakeven")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.header("🔬 Sensitivity Analysis")
    sensitivity_variable = st.selectbox("Variable:", ("Poha Selling Price", "Paddy Rate", "Paddy to Poha Yield"))
    sensitivity_range = st.slider("Range (%):", -50, 50, (-20, 20))
    base_value_map = {"Poha Selling Price": 'poha_price', "Paddy Rate": 'paddy_rate', "Paddy to Poha Yield": 'paddy_yield'}
    var_key = base_value_map[sensitivity_variable]
    base_value = all_inputs[var_key]
    range_values = np.linspace(base_value * (1 + sensitivity_range[0] / 100), base_value * (1 + sensitivity_range[1] / 100), 11)
    sensitivity_results_list = [run_financial_model({**all_inputs, var_key: val}) for val in range_values]
    sensitivity_data = []
    for val, res in zip(range_values, sensitivity_results_list):
        if 'error' in res:
            net_profit_str = "Error"
            net_profit_num = np.nan
        else:
            net_profit_str = format_crore(res['net_profit'])
            net_profit_num = res['net_profit']
        sensitivity_data.append({sensitivity_variable: val, "Net Profit (Cr)": net_profit_str, "Net Profit": net_profit_num})
    sensitivity_df = pd.DataFrame(sensitivity_data)
    col_sens1, col_sens2 = st.columns([1, 1])
    with col_sens1:
        st.dataframe(sensitivity_df[[sensitivity_variable, 'Net Profit (Cr)']], use_container_width=True, hide_index=True)
    with col_sens2:
        plot_df = sensitivity_df.dropna(subset=["Net Profit"])
        fig_sens = px.line(plot_df, x=sensitivity_variable, y='Net Profit', title=f"Impact of {sensitivity_variable}", markers=True, labels={'Net Profit': 'Net Profit (INR)'})
        fig_sens.update_layout(autosize=True)
        st.plotly_chart(fig_sens, use_container_width=True)

    st.divider()
    col_pnl, col_bs = st.columns([1, 1])
    with col_pnl:
        st.header("💰 Annual P&L")
        pnl_data = {
            "Metric": ["Revenue", "COGS", "**Gross Profit**", "Fixed OpEx", "Variable OpEx", "Depreciation", "**EBIT**", "Interest", "**EBT**", "Taxes", "**Net Profit**"],
            "Amount": [
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
        st.download_button("Download P&L", pnl_df.to_csv(index=False).encode('utf-8'), "poha_pnl.csv", "text/csv")
    with col_bs:
        st.header("💼 Balance Sheet")
        bs_data = {
            "Item": ["Capex", "Equity", "Debt", "**Assets**", "RM Inventory", "FG Inventory", "Receivables", "Payables", "**Net WC**", "**Capital Employed**"],
            "Amount": [
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

    st.divider()
    st.header("🔍 Calculation Details")
    with st.expander("Interest Details"):
        st.markdown("##### Debt Interest")
        st.markdown(f"`{format_indian_currency(results['total_debt_component'])} * {results['interest_rate']:.2f}% = {format_indian_currency(results['annual_interest_expense_fixed_assets'])}`")
        st.markdown("##### WC Interest")
        if results['net_working_capital'] > 0:
            st.markdown(f"`{format_indian_currency(results['net_working_capital'])} * {results['interest_rate']:.2f}% = {format_indian_currency(results['interest_on_working_capital'])}`")
        else:
            st.markdown("`No WC interest.`")
        st.markdown("##### Total Interest")
        st.markdown(f"`{format_indian_currency(results['annual_interest_expense_fixed_assets'])} + {format_indian_currency(results['interest_on_working_capital'])} = {format_indian_currency(results['annual_interest_expense'])}`")
    with st.expander("ROCE Details"):
        st.markdown("##### ROCE")
        st.markdown(f"`{format_indian_currency(results['operating_income_ebit'])} / {format_indian_currency(results['capital_employed'])} = {results['roce']:.2f}%`")
        st.markdown("##### Capital Employed")
        st.markdown(f"`{format_indian_currency(results['total_assets_for_roce'])} - {format_indian_currency(results['total_current_liabilities'])} = {format_indian_currency(results['capital_employed'])}`")
        st.markdown("##### Total Assets")
        st.markdown(f"`{format_indian_currency(results['total_capex'])} + {format_indian_currency(results['total_current_assets'])} = {format_indian_currency(results['total_assets_for_roce'])}`")
    st.success("Dashboard loaded!")
