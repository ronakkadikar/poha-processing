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

# CORRECTED CSS for proper sidebar behavior
st.markdown("""
<style>
    /* Ensure sidebar is always visible and accessible */
    [data-testid="stSidebar"] {
        position: relative !important;
        left: 0 !important;
        margin-left: 0 !important;
    }
    
    /* Control sidebar width when expanded */
    [data-testid="stSidebar"][aria-expanded="true"] {
        width: 350px !important;
        min-width: 350px !important;
    }
    
    /* Sidebar when collapsed */
    [data-testid="stSidebar"][aria-expanded="false"] {
        width: 50px !important;
        min-width: 50px !important;
    }
    
    /* Main content area responsive adjustment */
    .main .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: none;
    }
    
    /* Adjust main content width based on sidebar state */
    .main {
        transition: margin-left 0.3s ease;
    }
    
    /* When sidebar is expanded, reduce main content width */
    [data-testid="stSidebar"][aria-expanded="true"] ~ .main {
        margin-left: 0px;
    }
    
    /* Ensure content doesn't overflow */
    .main .block-container {
        overflow-x: auto;
    }
    
    /* Responsive columns for smaller screens */
    @media (max-width: 1200px) {
        [data-testid="stSidebar"][aria-expanded="true"] {
            width: 300px !important;
            min-width: 300px !important;
        }
    }
    
    /* Metric container styles */
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .metric-title {
        font-size: 0.875rem;
        color: #262730;
        margin-bottom: 0.25rem;
    }
    .metric-value {
        font-size: 1.25rem;
        font-weight: bold;
        color: #262730;
        margin-bottom: 0.25rem;
        word-wrap: break-word;
    }
    .metric-delta {
        font-size: 0.75rem;
        margin-top: 0.25rem;
        word-wrap: break-word;
    }
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: pointer;
    }
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 250px;
        background-color: #555;
        color: white;
        text-align: left;
        border-radius: 6px;
        padding: 8px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -125px;
        opacity: 0;
        transition: opacity 0.3s;
        font-size: 11px;
        line-height: 1.3;
    }
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
        color: #856404;
    }
    
    /* Responsive table and chart adjustments */
    .stDataFrame {
        font-size: 0.85rem;
    }
    
    /* Ensure plotly charts are responsive */
    .js-plotly-plot {
        width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

st.sidebar.header("⚙️ Input Parameters")

with st.sidebar.expander("Operational Assumptions", expanded=True):
    st.markdown("#### Shift Details")
    hours_per_day = st.number_input("Production Hours per Day", min_value=5, max_value=24, value=10, step=1)
    days_per_month = st.number_input("Operational Days per Month", min_value=1, max_value=31, value=24, step=1)

with st.sidebar.expander("Production & Yield", expanded=True):
    st.markdown("#### Plant Input (Paddy)")
    paddy_rate_kg_hr = st.number_input("Paddy Processing Rate (kg/hr)", value=1000, step=10)
    
    st.markdown("#### Yield & Byproduct")
    paddy_yield = st.number_input("Paddy to Poha Yield (%)", min_value=50.0, max_value=80.0, value=65.0, step=0.1)
    
    st.markdown("#### Byproduct Sales (% of Paddy Input)")
    byproduct_sale_percent = st.slider(
        "Byproduct Sold (% of Paddy Input)", 
        min_value=0.0, 
        max_value=40.0, 
        value=32.0, 
        step=0.1,
        help="Percentage of original paddy input sold as byproduct (accounts for dirt/grit losses)"
    )

with st.sidebar.expander("Financial Assumptions (INR)", expanded=True):
    st.markdown("#### Market Rates")
    paddy_rate = st.number_input("Paddy Rate (INR/kg)", value=22.0, step=0.1)
    poha_price = st.number_input("Poha Selling Price (INR/kg)", value=45.0, step=0.1)
    byproduct_rate_kg = st.number_input("Byproduct Rate (INR/kg)", value=7.0, step=0.1)

with st.sidebar.expander("Capital Expenditure (Capex)", expanded=True):
    st.markdown("#### Investment")
    land_cost = st.number_input("Land Cost", value=0, step=10000)
    civil_work_cost = st.number_input("Civil Work Cost", value=0, step=10000)
    machinery_cost = st.number_input("Machinery Cost", value=7000000, step=10000)
    machinery_useful_life_years = st.number_input("Useful Life (Years)", value=15, step=1)

with st.sidebar.expander("Operating Costs", expanded=True):
    st.markdown("##### Variable Costs (per kg of Paddy Input)")
    packaging_cost = st.number_input("Packaging Material (per kg paddy)", value=0.5, step=0.01)
    fuel_cost = st.number_input("Fuel/Power Variable (per kg paddy)", value=0.0, step=0.01)
    other_var_cost = st.number_input("Other Variable Costs (per kg paddy)", value=0.0, step=0.01)
    
    st.markdown("##### Fixed Costs (Monthly)")
    rent_per_month = st.number_input("Rent", value=300000, step=1000)
    labor_per_month = st.number_input("Labor Wages and Salaries", value=400000, step=1000)
    electricity_per_month = st.number_input("Electricity (Fixed)", value=150000, step=1000)
    security_ssc_insurance_per_month = st.number_input("Security, SSC & Insurance", value=300000, step=1000)
    misc_per_month = st.number_input("Misc Overheads", value=300000, step=1000)

with st.sidebar.expander("Funding & Tax", expanded=True):
    st.markdown("#### Structure")
    equity_contrib = st.number_input("Equity Contribution (%)", min_value=0.0, max_value=100.0, value=30.0, step=0.1)
    interest_rate = st.number_input("Interest Rate (%)", value=9.0, step=0.01)
    tax_rate_percent = st.number_input("Corporate Tax Rate (%)", min_value=0.0, max_value=50.0, value=25.0, step=0.1)

with st.sidebar.expander("Working Capital Days", expanded=True):
    st.markdown("#### Inventory & Receivables")
    rm_inventory_days = st.number_input("Raw Material Inventory Days", value=72, step=1)
    fg_inventory_days = st.number_input("Finished Goods Inventory Days", value=20, step=1)
    debtor_days = st.number_input("Debtor Days (Receivables)", value=45, step=1)
    creditor_days = st.number_input("Creditor Days (Payables)", value=5, step=1)

# Collect all inputs
all_inputs = {k: v for k, v in locals().items() if k in [
    'hours_per_day', 'days_per_month', 'paddy_rate_kg_hr', 'paddy_yield', 'byproduct_sale_percent',
    'paddy_rate', 'poha_price', 'byproduct_rate_kg', 'land_cost', 'civil_work_cost', 'machinery_cost',
    'machinery_useful_life_years', 'packaging_cost', 'fuel_cost', 'other_var_cost', 'rent_per_month',
    'labor_per_month', 'electricity_per_month', 'security_ssc_insurance_per_month', 'misc_per_month',
    'equity_contrib', 'interest_rate', 'tax_rate_percent', 'rm_inventory_days', 'fg_inventory_days',
    'debtor_days', 'creditor_days'
]}

def run_financial_model(inputs):
    # Validation
    total_capex = inputs['land_cost'] + inputs['civil_work_cost'] + inputs['machinery_cost']
    if any(v <= 0 for v in [inputs['paddy_yield'], inputs['poha_price'], total_capex]):
        return {'error': 'Paddy Yield, Poha Price, and Capex must be greater than 0.'}
    
    # Production calculations
    daily_paddy_consumption = inputs['paddy_rate_kg_hr'] * inputs['hours_per_day']
    monthly_paddy_consumption = daily_paddy_consumption * inputs['days_per_month']
    annual_paddy_consumption = monthly_paddy_consumption * 12
    
    # Poha production
    daily_poha_production = daily_paddy_consumption * (inputs['paddy_yield'] / 100)
    monthly_poha_production = daily_poha_production * inputs['days_per_month']
    annual_poha_production = monthly_poha_production * 12
    
    # Byproduct calculations
    daily_byproduct_sold_target = daily_paddy_consumption * (inputs['byproduct_sale_percent'] / 100)
    daily_byproduct_generated = daily_paddy_consumption - daily_poha_production
    daily_byproduct_sold = min(daily_byproduct_sold_target, daily_byproduct_generated)
    
    monthly_byproduct_sold = daily_byproduct_sold * inputs['days_per_month']
    annual_byproduct_sold = monthly_byproduct_sold * 12
    byproduct_limit_hit = daily_byproduct_sold_target > daily_byproduct_generated
    
    # Revenue calculations
    total_daily_revenue = (daily_poha_production * inputs['poha_price']) + (daily_byproduct_sold * inputs['byproduct_rate_kg'])
    total_monthly_revenue = total_daily_revenue * inputs['days_per_month']
    total_annual_revenue = total_monthly_revenue * 12
    
    # COGS (paddy cost only)
    annual_cogs = annual_paddy_consumption * inputs['paddy_rate']
    
    # Gross profit
    annual_gross_profit = total_annual_revenue - annual_cogs
    
    # Variable operating costs
    total_variable_cost_per_kg_paddy = inputs['packaging_cost'] + inputs['fuel_cost'] + inputs['other_var_cost']
    annual_variable_operating_costs_total = annual_paddy_consumption * total_variable_cost_per_kg_paddy
    
    # Fixed operating costs
    total_monthly_fixed_opex = sum([inputs['rent_per_month'], inputs['labor_per_month'], 
                                   inputs['electricity_per_month'], inputs['security_ssc_insurance_per_month'], 
                                   inputs['misc_per_month']])
    annual_fixed_operating_costs = total_monthly_fixed_opex * 12
    
    # Total operating expenses
    total_operating_expenses_for_pnl = annual_fixed_operating_costs + annual_variable_operating_costs_total
    
    # Depreciation
    total_annual_depreciation = (inputs['machinery_cost'] + inputs['civil_work_cost']) / inputs['machinery_useful_life_years']
    
    # EBIT
    operating_income_ebit = annual_gross_profit - total_operating_expenses_for_pnl - total_annual_depreciation
    
    # Working capital calculations
    daily_cogs_basis = annual_cogs / 365
    daily_cost_of_production = (annual_cogs + annual_variable_operating_costs_total) / annual_poha_production
    daily_revenue_basis = total_annual_revenue / 365
    
    rm_inventory_value = daily_cogs_basis * inputs['rm_inventory_days']
    fg_inventory_value = (daily_poha_production * daily_cost_of_production) * inputs['fg_inventory_days']
    accounts_receivable = daily_revenue_basis * inputs['debtor_days']
    accounts_payable = daily_cogs_basis * inputs['creditor_days']
    
    total_current_assets = rm_inventory_value + fg_inventory_value + accounts_receivable
    total_current_liabilities = accounts_payable
    net_working_capital = total_current_assets - total_current_liabilities
    
    # Financing calculations
    initial_equity_contribution = total_capex * (inputs['equity_contrib'] / 100)
    total_debt_component = total_capex - initial_equity_contribution
    
    # Interest calculations
    annual_interest_expense_fixed_assets = total_debt_component * (inputs['interest_rate'] / 100)
    interest_on_working_capital = max(0, net_working_capital) * (inputs['interest_rate'] / 100)
    annual_interest_expense = annual_interest_expense_fixed_assets + interest_on_working_capital
    
    # Tax calculations
    earnings_before_tax_ebt = operating_income_ebit - annual_interest_expense
    taxes = max(0, earnings_before_tax_ebt) * (inputs['tax_rate_percent'] / 100)
    net_profit = earnings_before_tax_ebt - taxes
    
    # Financial ratios
    total_assets_for_roce = total_capex + total_current_assets
    capital_employed = total_assets_for_roce - total_current_liabilities
    
    # Key metrics
    roce = (operating_income_ebit / capital_employed) * 100 if capital_employed != 0 else float('inf')
    net_profit_margin = (net_profit / total_annual_revenue) * 100 if total_annual_revenue > 0 else 0
    ebitda = operating_income_ebit + total_annual_depreciation
    ebitda_margin = (ebitda / total_annual_revenue) * 100 if total_annual_revenue > 0 else 0
    roe = (net_profit / initial_equity_contribution) * 100 if initial_equity_contribution > 0 else float('inf')
    gross_profit_margin = (annual_gross_profit / total_annual_revenue) * 100 if total_annual_revenue > 0 else 0
    
    # Contribution Margin calculation
    contribution_margin = annual_gross_profit - annual_variable_operating_costs_total
    contribution_margin_percent = (contribution_margin / total_annual_revenue) * 100 if total_annual_revenue > 0 else 0
    
    return {**inputs, **{k: v for k, v in locals().items() if not k.startswith('inputs')}}

# Key ratios information for tooltips
key_ratios_info = {
    "Revenue": {"formula": "Revenue = Poha Sales + Byproduct Sales", "explanation": "Total income from all product sales."},
    "COGS": {"formula": "COGS = Paddy Consumption × Paddy Rate", "explanation": "Direct cost of raw materials consumed."},
    "Gross Margin": {"formula": "GM = (Revenue - COGS) / Revenue × 100", "explanation": "Profitability after direct material costs."},
    "Contribution Margin": {"formula": "CM = (Revenue - COGS - Variable Costs) / Revenue × 100", "explanation": "Profitability after all variable costs."},
    "Net Profit": {"formula": "Net Profit = EBT - Taxes", "explanation": "The final 'bottom line' profit after all costs."},
    "EBITDA": {"formula": "EBITDA = EBIT + Depreciation", "explanation": "Operational profitability before non-cash expenses."},
    "ROCE": {"formula": "ROCE = (EBIT / Capital Employed) × 100", "explanation": "Effectiveness of capital in generating profits."},
    "ROE": {"formula": "ROE = (Net Profit / Equity) × 100", "explanation": "Profitability relative to shareholder equity."}
}

def custom_metric(col, label, value, sub_value, info_key):
    formula, explanation = key_ratios_info[info_key].values()
    tooltip_content = f"<strong>Formula:</strong> {formula}<br><strong>Explanation:</strong> {explanation}"
    
    try:
        numeric_value = float(sub_value.replace('%', '').replace(' Margin', '').strip())
    except:
        numeric_value = 0
    
    color = 'green' if numeric_value >= 0 else 'red'
    
    with col:
        st.markdown(f"""
        <div class="metric-container">
            <div class="tooltip">
                <div class="metric-title">{label} ℹ️</div>
                <span class="tooltiptext">{tooltip_content}</span>
            </div>
            <div class="metric-value">{value}</div>
            <div class="metric-delta" style="color: {color};">{sub_value}</div>
        </div>
        """, unsafe_allow_html=True)

# Run the financial model
results = run_financial_model(all_inputs)

if 'error' in results:
    st.error(results['error'])
else:
    # Display warning if byproduct limit is hit
    if results.get('byproduct_limit_hit', False):
        st.markdown(f"""
        <div class="warning-box">
            <strong>⚠️ Byproduct Constraint Warning:</strong><br>
            You're trying to sell {results['byproduct_sale_percent']:.1f}% of paddy input as byproduct 
            ({results['daily_byproduct_sold_target']:,.0f} kg/day), but only {results['daily_byproduct_generated']:,.0f} kg/day 
            is available after poha production. Sales capped at maximum available.
            <br><br>
            <strong>Suggestion:</strong> Consider reducing the byproduct sale percentage or adjusting the poha yield.
        </div>
        """, unsafe_allow_html=True)
    
    # Enhanced KPIs with Revenue, COGS, GM, CM
    st.header("📈 Key Performance Indicators (Annual)")
    
    col1, col2, col3, col4 = st.columns(4)
    custom_metric(col1, "Revenue", format_indian_currency(results['total_annual_revenue']), "", "Revenue")
    custom_metric(col2, "COGS", format_indian_currency(results['annual_cogs']), "", "COGS")
    custom_metric(col3, "Gross Margin", f"{results['gross_profit_margin']:.1f}%", format_indian_currency(results['annual_gross_profit']), "Gross Margin")
    custom_metric(col4, "Contribution Margin", f"{results['contribution_margin_percent']:.1f}%", format_indian_currency(results['contribution_margin']), "Contribution Margin")
    
    col5, col6, col7, col8 = st.columns(4)
    custom_metric(col5, "Net Profit", format_indian_currency(results['net_profit']), f"{results['net_profit_margin']:.1f}% Margin", "Net Profit")
    custom_metric(col6, "EBITDA", format_indian_currency(results['ebitda']), f"{results['ebitda_margin']:.1f}% Margin", "EBITDA")
    custom_metric(col7, "ROCE", f"{results['roce']:.1f}%", "", "ROCE")
    custom_metric(col8, "ROE", f"{results['roe']:.1f}%", "", "ROE")
    
    st.divider()
    
    # Summary table with byproduct details
    st.header("📊 Daily, Monthly, and Annual Summary")
    
    summary_data = {
        "Metric": ["Paddy Consumption (kg)", "Poha Production (kg)", "Byproduct Generated (kg)", "Byproduct Sold (kg)", "Total Revenue", "COGS", "Gross Profit"],
        "Daily": [f"{results['daily_paddy_consumption']:,.0f}", f"{results['daily_poha_production']:,.0f}", 
                 f"{results['daily_byproduct_generated']:,.0f}", f"{results['daily_byproduct_sold']:,.0f}",
                 format_indian_currency(results['total_daily_revenue']), format_indian_currency(results['annual_cogs']/365),
                 format_indian_currency(results['annual_gross_profit']/365)],
        "Monthly": [f"{results['monthly_paddy_consumption']:,.0f}", f"{results['monthly_poha_production']:,.0f}",
                   f"{results['daily_byproduct_generated'] * results['days_per_month']:,.0f}", f"{results['monthly_byproduct_sold']:,.0f}",
                   format_indian_currency(results['total_monthly_revenue']), format_indian_currency(results['annual_cogs']/12),
                   format_indian_currency(results['annual_gross_profit']/12)],
        "Annual": [f"{results['annual_paddy_consumption']:,.0f}", f"{results['annual_poha_production']:,.0f}",
                  f"{results['daily_byproduct_generated'] * results['days_per_month'] * 12:,.0f}", f"{results['annual_byproduct_sold']:,.0f}",
                  format_indian_currency(results['total_annual_revenue']), format_indian_currency(results['annual_cogs']),
                  format_indian_currency(results['annual_gross_profit'])]
    }
    
    st.dataframe(pd.DataFrame(summary_data), hide_index=True, use_container_width=True)
    
    st.divider()
    
    # Breakeven analysis
    st.header("💡 Breakeven Analysis")
    
    # Calculate breakeven based on paddy input
    rm_cost_per_kg_paddy = results['paddy_rate']
    total_variable_cost_per_kg_paddy = rm_cost_per_kg_paddy + results['total_variable_cost_per_kg_paddy']
    
    # Revenue per kg of paddy input
    poha_revenue_per_kg_paddy = results['poha_price'] * (results['paddy_yield'] / 100)
    byproduct_revenue_per_kg_paddy = results['byproduct_rate_kg'] * min(
        results['byproduct_sale_percent'] / 100,
        (100 - results['paddy_yield']) / 100
    )
    revenue_per_kg_paddy = poha_revenue_per_kg_paddy + byproduct_revenue_per_kg_paddy
    
    contribution_margin_per_kg_paddy = revenue_per_kg_paddy - total_variable_cost_per_kg_paddy
    
    total_fixed_costs_for_breakeven = results['annual_fixed_operating_costs'] + results['total_annual_depreciation'] + results['annual_interest_expense']
    
    breakeven_volume_kg_paddy = total_fixed_costs_for_breakeven / contribution_margin_per_kg_paddy if contribution_margin_per_kg_paddy > 0 else float('inf')
    
    col_be1, col_be2 = st.columns(2)
    
    with col_be1:
        st.metric("Breakeven Volume (Paddy)", f"{breakeven_volume_kg_paddy:,.0f} kg")
        st.metric("Breakeven Revenue", format_indian_currency(breakeven_volume_kg_paddy * revenue_per_kg_paddy))
        st.metric("Contribution Margin per kg Paddy", format_indian_currency(contribution_margin_per_kg_paddy))
    
    with col_be2:
        # Breakeven chart
        max_production = results.get('annual_paddy_consumption', 0)
        max_volume = max(max_production, breakeven_volume_kg_paddy) * 1.5 if breakeven_volume_kg_paddy != float('inf') else max_production * 1.5
        
        volumes = np.linspace(0, max_volume, 100)
        total_revenue_line = volumes * revenue_per_kg_paddy
        total_cost_line = total_fixed_costs_for_breakeven + (volumes * total_variable_cost_per_kg_paddy)
        
        be_df = pd.DataFrame({
            'Paddy Volume (kg)': volumes,
            'Total Revenue': total_revenue_line,
            'Total Costs': total_cost_line
        })
        
        fig = px.line(be_df, x='Paddy Volume (kg)', y=['Total Revenue', 'Total Costs'], 
                     title="Visual Breakeven Analysis", markers=True)
        
        if breakeven_volume_kg_paddy != float('inf'):
            fig.add_vline(x=breakeven_volume_kg_paddy, line_dash="dash", line_color="red", 
                         annotation_text="Breakeven Point")
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Sensitivity analysis
    st.header("🔬 Sensitivity Analysis")
    
    sensitivity_variable = st.selectbox("Select variable to analyze:", 
                                      ("Poha Selling Price", "Paddy Rate", "Paddy to Poha Yield", "Byproduct Sale %"))
    sensitivity_range = st.slider("Select sensitivity range (% change from base):", -50, 50, (-20, 20))
    
    base_value_map = {
        "Poha Selling Price": 'poha_price',
        "Paddy Rate": 'paddy_rate',
        "Paddy to Poha Yield": 'paddy_yield',
        "Byproduct Sale %": 'byproduct_sale_percent'
    }
    
    var_key = base_value_map[sensitivity_variable]
    base_value = all_inputs[var_key]
    
    range_values = np.linspace(
        base_value * (1 + sensitivity_range[0] / 100),
        base_value * (1 + sensitivity_range[1] / 100),
        11
    )
    
    sensitivity_results_list = [run_financial_model({**all_inputs, var_key: val}) for val in range_values]
    
    sensitivity_data = []
    for val, res in zip(range_values, sensitivity_results_list):
        if 'error' in res:
            net_profit_str = "Error"
            net_profit_num = np.nan
        else:
            net_profit_str = format_crore(res['net_profit'])
            net_profit_num = res['net_profit']
        
        sensitivity_data.append({
            sensitivity_variable: val,
            "Net Profit (Cr)": net_profit_str,
            "Net Profit": net_profit_num
        })
    
    sensitivity_df = pd.DataFrame(sensitivity_data)
    
    col_sens1, col_sens2 = st.columns([1.2, 1])
    
    with col_sens1:
        st.dataframe(
            sensitivity_df[[sensitivity_variable, 'Net Profit (Cr)']],
            use_container_width=True,
            hide_index=True
        )
    
    with col_sens2:
        plot_df = sensitivity_df.dropna(subset=["Net Profit"])
        fig_sens = px.line(
            plot_df,
            x=sensitivity_variable,
            y='Net Profit',
            title=f"Impact of {sensitivity_variable} on Net Profit",
            markers=True,
            labels={'Net Profit': 'Net Profit (INR)'}
        )
        st.plotly_chart(fig_sens, use_container_width=True)
    
    st.divider()
    
    # Financial statements
    col_pnl, col_bs = st.columns([1.2, 1])
    
    with col_pnl:
        st.header("💰 Annual Profit & Loss Statement")
        
        pnl_data = {
            "Metric": [
                "Total Revenue",
                "COGS",
                "**Gross Profit**",
                "Fixed OpEx",
                "Variable OpEx",
                "Depreciation",
                "**EBIT**",
                "Total Interest",
                "**EBT**",
                "Taxes",
                "**Net Profit**"
            ],
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
            "Item": [
                "Total Capex",
                "Equity Contribution",
                "Debt Component",
                "**Total Assets**",
                "RM Inventory",
                "FG Inventory",
                "Receivables",
                "Payables",
                "**Net Working Capital**",
                "**Capital Employed**"
            ],
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
    
    st.divider()
    
    # Detailed calculations
    st.header("Detailed Calculation Breakdowns")
    
    with st.expander("Production Flow Details"):
        st.markdown("##### 1. Paddy Input to Poha Output")
        st.markdown(f"**Daily Paddy Consumption:** `{results['paddy_rate_kg_hr']:,.0f} kg/hr * {results['hours_per_day']} hrs = {results['daily_paddy_consumption']:,.0f} kg`")
        st.markdown(f"**Daily Poha Production:** `{results['daily_paddy_consumption']:,.0f} kg * {results['paddy_yield']:.1f}% = {results['daily_poha_production']:,.0f} kg`")
        st.markdown(f"**Daily Byproduct Generated:** `{results['daily_paddy_consumption']:,.0f} kg - {results['daily_poha_production']:,.0f} kg = {results['daily_byproduct_generated']:,.0f} kg`")
        
        st.markdown("##### 2. Byproduct Sales")
        st.markdown(f"**Target Byproduct Sales:** `{results['daily_paddy_consumption']:,.0f} kg * {results['byproduct_sale_percent']:.1f}% = {results['daily_byproduct_sold_target']:,.0f} kg`")
        st.markdown(f"**Maximum Available:** `{results['daily_byproduct_generated']:,.0f} kg`")
        st.markdown(f"**Actual Byproduct Sold:** `min({results['daily_byproduct_sold_target']:,.0f}, {results['daily_byproduct_generated']:,.0f}) = {results['daily_byproduct_sold']:,.0f} kg`")
    
    with st.expander("Revenue Breakdown"):
        st.markdown("##### Daily Revenue Components")
        daily_poha_revenue = results['daily_poha_production'] * results['poha_price']
        daily_byproduct_revenue = results['daily_byproduct_sold'] * results['byproduct_rate_kg']
        
        st.markdown(f"**Poha Revenue:** `{results['daily_poha_production']:,.0f} kg * ₹{results['poha_price']:.2f} = {format_indian_currency(daily_poha_revenue)}`")
        st.markdown(f"**Byproduct Revenue:** `{results['daily_byproduct_sold']:,.0f} kg * ₹{results['byproduct_rate_kg']:.2f} = {format_indian_currency(daily_byproduct_revenue)}`")
        st.markdown(f"**Total Daily Revenue:** `{format_indian_currency(daily_poha_revenue)} + {format_indian_currency(daily_byproduct_revenue)} = {format_indian_currency(results['total_daily_revenue'])}`")
    
    with st.expander("Variable Cost Calculation"):
        st.markdown("##### Variable Costs (Per kg Paddy)")
        st.markdown(f"**Packaging Cost:** `₹{results['packaging_cost']:.2f} per kg paddy`")
        st.markdown(f"**Fuel/Power Cost:** `₹{results['fuel_cost']:.2f} per kg paddy`")
        st.markdown(f"**Other Variable Cost:** `₹{results['other_var_cost']:.2f} per kg paddy`")
        st.markdown(f"**Total Variable Cost:** `₹{results['total_variable_cost_per_kg_paddy']:.2f} per kg paddy`")
        st.markdown(f"**Annual Variable Costs:** `{results['annual_paddy_consumption']:,.0f} kg * ₹{results['total_variable_cost_per_kg_paddy']:.2f} = {format_indian_currency(results['annual_variable_operating_costs_total'])}`")

st.success("Dashboard loaded successfully with fixed sidebar and responsive layout!")
