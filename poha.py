import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- Page and Layout Configuration ---
st.set_page_config(
    page_title="Poha Manufacturing Dashboard", 
    page_icon="🌾", 
    layout="wide",
    initial_sidebar_state="expanded" 
)

# --- CSS for a Static, Fixed Layout ---
st.markdown("""
<style>
    /* Define a fixed width for the sidebar */
    [data-testid="stSidebar"] {
        width: 320px !important;
        min-width: 320px !important;
    }

    /* Create a fixed margin on the left of the main content to prevent overlap */
    div.main {
        margin-left: 320px;
    }

    /* General content styling */
    .block-container {
        padding: 1rem 2rem;
        max-width: 100% !important;
    }
    .st-expander {
        border: 1px solid #e6e6e6;
        border-radius: 10px;
    }
    .st-expander p {
        font-size: 15px;
        line-height: 1.6;
    }
    .st-expander .st-emotion-cache-1hver4l { /* Expander header */
        font-size: 18px;
    }

    /* Custom metric styling */
    .metric-container {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1rem; border-radius: 10px; margin: 0.5rem 0;
        min-height: 120px; display: flex; flex-direction: column;
        justify-content: space-between; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease;
    }
    .metric-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }
    .metric-title { font-size: 0.875rem; color: #2c3e50; font-weight: 600; }
    .metric-value { font-size: 1.25rem; font-weight: bold; color: #2c3e50; }
    .metric-delta { font-size: 0.75rem; font-weight: 500; }
    
    /* Tooltip styling */
    .tooltip { position: relative; cursor: pointer; }
    .tooltip .tooltiptext {
        visibility: hidden; width: 280px; background-color: #34495e; color: white;
        text-align: left; border-radius: 8px; padding: 10px; position: absolute;
        z-index: 1000; bottom: 125%; left: 50%; margin-left: -140px; opacity: 0;
        transition: opacity 0.3s; font-size: 12px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    .tooltip:hover .tooltiptext { visibility: visible; opacity: 1; }

    /* Warning box styling */
    .warning-box {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border: 1px solid #f39c12; border-radius: 8px; padding: 1rem;
        margin: 1rem 0; color: #8b4513; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- Utility Functions ---
def format_currency(amount):
    try:
        if amount == 0: return "₹0.00"
        amount_str = f"{abs(amount):.2f}"
        integer_part, decimal_part = amount_str.split('.')
        last_three = integer_part[-3:]
        remaining = integer_part[:-3]
        if remaining:
            groups = [remaining[max(0, i-2):i] for i in range(len(remaining), 0, -2)][::-1]
            formatted = ','.join(groups) + ',' + last_three
        else:
            formatted = last_three
        return f"₹{('-' if amount < 0 else '')}{formatted}.{decimal_part}"
    except: return "N/A"

# --- Configuration Dictionaries ---
RATIOS_INFO = {
    "Revenue": {"formula": "Poha Sales + Byproduct Sales", "explanation": "Total income generated from selling all products."},
    "COGS": {"formula": "Annual Paddy Consumption × Paddy Rate", "explanation": "The direct cost of raw materials (paddy) consumed."},
    "Gross Margin": {"formula": "(Revenue - COGS) / Revenue × 100", "explanation": "Profitability after accounting for the direct cost of goods sold."},
    "Contribution Margin": {"formula": "(Revenue - All Variable Costs) / Revenue × 100", "explanation": "Profitability after all costs that vary with production."},
    "Net Profit": {"formula": "Earnings Before Tax - Taxes", "explanation": "The final bottom-line profit after all expenses, interest, and taxes."},
    "EBITDA": {"formula": "EBIT + Depreciation", "explanation": "Operating profit before non-cash items (depreciation) and financing/tax costs."},
    "ROCE": {"formula": "(EBIT / Capital Employed) × 100", "explanation": "Return on Capital Employed, measuring profitability relative to capital invested."},
    "ROE": {"formula": "(Net Profit / Equity) × 100", "explanation": "Return on Equity, showing the return generated for shareholders' investment."}
}

CONFIG = {
    "Operational": {"hours_per_day": {"label": "Production Hours/Day", "type": "number", "min_value": 5, "max_value": 24, "value": 10, "step": 1}, "days_per_month": {"label": "Operational Days/Month", "type": "number", "min_value": 1, "max_value": 31, "value": 24, "step": 1}},
    "Production": {"paddy_rate_kg_hr": {"label": "Paddy Processing Rate (kg/hr)", "type": "number", "value": 1000, "step": 10}, "paddy_yield": {"label": "Poha Yield (%)", "type": "number", "min_value": 50.0, "max_value": 80.0, "value": 65.0, "step": 0.1}, "byproduct_sale_percent": {"label": "Byproduct Sale (%)", "type": "slider", "min_value": 0.0, "max_value": 40.0, "value": 32.0, "step": 0.1}},
    "Pricing": {"paddy_rate": {"label": "Paddy Purchase Rate (₹/kg)", "type": "number", "value": 22.0, "step": 0.1}, "poha_price": {"label": "Poha Selling Price (₹/kg)", "type": "number", "value": 45.0, "step": 0.1}, "byproduct_rate_kg": {"label": "Byproduct Selling Rate (₹/kg)", "type": "number", "value": 7.0, "step": 0.1}},
    "Capex": {"land_cost": {"label": "Land Cost", "type": "number", "value": 0, "step": 10000}, "civil_work_cost": {"label": "Civil Work Cost", "type": "number", "value": 0, "step": 10000}, "machinery_cost": {"label": "Machinery Cost", "type": "number", "value": 7000000, "step": 10000}, "machinery_useful_life_years": {"label": "Useful Life (Years)", "type": "number", "value": 15, "step": 1}},
    "Operating Costs": {"packaging_cost": {"label": "Packaging (₹/kg of paddy)", "type": "number", "value": 0.5, "step": 0.01}, "fuel_cost": {"label": "Fuel/Power (₹/kg of paddy)", "type": "number", "value": 0.0, "step": 0.01}, "other_var_cost": {"label": "Other Variable (₹/kg of paddy)", "type": "number", "value": 0.0, "step": 0.01}, "rent_per_month": {"label": "Rent/Month", "type": "number", "value": 300000, "step": 1000}, "labor_per_month": {"label": "Labor/Month", "type": "number", "value": 400000, "step": 1000}, "electricity_per_month": {"label": "Electricity/Month", "type": "number", "value": 150000, "step": 1000}, "security_ssc_insurance_per_month": {"label": "Security & Insurance/Month", "type": "number", "value": 300000, "step": 1000}, "misc_per_month": {"label": "Misc Overheads/Month", "type": "number", "value": 300000, "step": 1000}},
    "Finance": {"equity_contrib": {"label": "Equity Contribution (%)", "type": "number", "min_value": 0.0, "max_value": 100.0, "value": 30.0, "step": 0.1}, "interest_rate": {"label": "Interest Rate (%)", "type": "number", "value": 9.0, "step": 0.01}, "tax_rate_percent": {"label": "Corporate Tax Rate (%)", "type": "number", "min_value": 0.0, "max_value": 50.0, "value": 25.0, "step": 0.1}},
    "Working Capital": {"rm_inventory_days": {"label": "RM Inventory Days", "type": "number", "value": 72, "step": 1}, "fg_inventory_days": {"label": "FG Inventory Days", "type": "number", "value": 20, "step": 1}, "debtor_days": {"label": "Debtor Days (Receivables)", "type": "number", "value": 45, "step": 1}, "creditor_days": {"label": "Creditor Days (Payables)", "type": "number", "value": 5, "step": 1}}
}

# --- Sidebar Rendering ---
def render_sidebar():
    inputs = {}
    st.sidebar.header("⚙️ Parameters")
    for section, params in CONFIG.items():
        with st.sidebar.expander(section, expanded=True):
            for key, config in params.items():
                input_type = config["type"]
                label = config["label"]
                value = config.get("value")
                kwargs = {k: v for k, v in config.items() if k not in ["type", "label", "value"]}
                if input_type == "number": inputs[key] = st.number_input(label, value=value, **kwargs)
                elif input_type == "slider": inputs[key] = st.slider(label, value=value, **kwargs)
    return inputs

# --- Financial Calculation Engine ---
def calculate_financials(inputs):
    # This function remains the same as your provided version
    total_capex = inputs['land_cost'] + inputs['civil_work_cost'] + inputs['machinery_cost']
    if any(v <= 0 for v in [inputs['paddy_yield'], inputs['poha_price'], total_capex]): return {'error': 'Invalid inputs: Yield, Price, and Capex must be > 0'}
    daily_paddy = inputs['paddy_rate_kg_hr'] * inputs['hours_per_day']
    annual_paddy = daily_paddy * inputs['days_per_month'] * 12
    annual_poha = annual_paddy * (inputs['paddy_yield'] / 100)
    daily_byproduct_gen = daily_paddy - (daily_paddy * (inputs['paddy_yield'] / 100))
    daily_byproduct_target = daily_paddy * (inputs['byproduct_sale_percent'] / 100)
    daily_byproduct_sold = min(daily_byproduct_target, daily_byproduct_gen)
    annual_byproduct_sold = daily_byproduct_sold * inputs['days_per_month'] * 12
    byproduct_limit_hit = daily_byproduct_target > daily_byproduct_gen
    annual_poha_revenue = annual_poha * inputs['poha_price']
    annual_byproduct_revenue = annual_byproduct_sold * inputs['byproduct_rate_kg']
    annual_revenue = annual_poha_revenue + annual_byproduct_revenue
    annual_cogs = annual_paddy * inputs['paddy_rate']
    gross_profit = annual_revenue - annual_cogs
    var_cost_per_kg = inputs['packaging_cost'] + inputs['fuel_cost'] + inputs['other_var_cost']
    annual_var_costs = annual_paddy * var_cost_per_kg
    annual_fixed_opex = sum([inputs[k] for k in ['rent_per_month', 'labor_per_month', 'electricity_per_month', 'security_ssc_insurance_per_month', 'misc_per_month']]) * 12
    annual_depreciation = (inputs['machinery_cost'] + inputs['civil_work_cost']) / inputs['machinery_useful_life_years'] if inputs['machinery_useful_life_years'] > 0 else 0
    ebit = gross_profit - annual_var_costs - annual_fixed_opex - annual_depreciation
    daily_cogs = annual_cogs / 365
    daily_poha_production = annual_poha / (inputs['days_per_month'] * 12)
    daily_prod_cost = (annual_cogs + annual_var_costs) / annual_poha if annual_poha > 0 else 0
    daily_rev = annual_revenue / 365
    rm_inventory = daily_cogs * inputs['rm_inventory_days']
    fg_inventory = (daily_poha_production * daily_prod_cost) * inputs['fg_inventory_days']
    receivables = daily_rev * inputs['debtor_days']
    payables = daily_cogs * inputs['creditor_days']
    current_assets = rm_inventory + fg_inventory + receivables
    interest_fixed = (total_capex * (1 - inputs['equity_contrib'] / 100)) * (inputs['interest_rate'] / 100)
    net_working_capital = current_assets - payables
    interest_wc = max(0, net_working_capital) * (inputs['interest_rate'] / 100)
    total_interest = interest_fixed + interest_wc
    ebt = ebit - total_interest
    taxes = max(0, ebt) * (inputs['tax_rate_percent'] / 100)
    net_profit = ebt - taxes
    equity = total_capex * (inputs['equity_contrib'] / 100)
    debt = total_capex - equity
    capital_employed = total_capex + net_working_capital
    roce = (ebit / capital_employed) * 100 if capital_employed != 0 else float('inf')
    net_profit_margin = (net_profit / annual_revenue) * 100 if annual_revenue > 0 else 0
    ebitda = ebit + annual_depreciation
    ebitda_margin = (ebitda / annual_revenue) * 100 if annual_revenue > 0 else 0
    roe = (net_profit / equity) * 100 if equity > 0 else float('inf')
    gross_margin = (gross_profit / annual_revenue) * 100 if annual_revenue > 0 else 0
    contribution_margin = annual_revenue - annual_cogs - annual_var_costs
    contribution_margin_pct = (contribution_margin / annual_revenue) * 100 if annual_revenue > 0 else 0
    return {**inputs, 'total_capex': total_capex, 'daily_paddy': daily_paddy, 'annual_paddy': annual_paddy, 'annual_poha': annual_poha, 'daily_byproduct_gen': daily_byproduct_gen, 'daily_byproduct_sold': daily_byproduct_sold, 'annual_byproduct_sold': annual_byproduct_sold, 'daily_byproduct_target': daily_byproduct_target, 'byproduct_limit_hit': byproduct_limit_hit, 'annual_revenue': annual_revenue, 'annual_poha_revenue': annual_poha_revenue, 'annual_byproduct_revenue': annual_byproduct_revenue, 'annual_cogs': annual_cogs, 'gross_profit': gross_profit, 'annual_var_costs': annual_var_costs, 'annual_fixed_opex': annual_fixed_opex, 'annual_depreciation': annual_depreciation, 'ebit': ebit, 'net_working_capital': net_working_capital, 'equity': equity, 'debt': debt, 'total_interest': total_interest, 'ebt': ebt, 'taxes': taxes, 'net_profit': net_profit, 'roce': roce, 'net_profit_margin': net_profit_margin, 'ebitda': ebitda, 'ebitda_margin': ebitda_margin, 'roe': roe, 'gross_margin': gross_margin, 'contribution_margin': contribution_margin, 'contribution_margin_pct': contribution_margin_pct, 'total_var_cost_per_kg': var_cost_per_kg, 'rm_inventory': rm_inventory, 'fg_inventory': fg_inventory, 'receivables': receivables, 'payables': payables, 'current_assets': current_assets, 'capital_employed': capital_employed, 'total_assets': total_capex + current_assets, 'daily_cogs': daily_cogs, 'daily_prod_cost': daily_prod_cost, 'daily_rev': daily_rev, 'interest_fixed': interest_fixed, 'interest_wc': interest_wc}

# --- Reusable Metric Component ---
def custom_metric(col, label, value, sub_value, info_key):
    formula, explanation = RATIOS_INFO[info_key].values()
    color = 'green' if (isinstance(sub_value, (int, float)) and sub_value >= 0) or ('Margin' not in str(sub_value) and str(sub_value) != "") else 'red'
    with col: st.markdown(f"""<div class="metric-container"><div class="tooltip"><div class="metric-title">{label} ℹ️</div><span class="tooltiptext"><strong>Formula:</strong> {formula}<br><strong>Explanation:</strong> {explanation}</span></div><div class="metric-value">{value}</div><div class="metric-delta" style="color: {color};">{sub_value}</div></div>""", unsafe_allow_html=True)

# --- Detailed Breakdowns Rendering Function ---
def render_detailed_breakdowns(results):
    st.header("🔍 Detailed Calculation Breakdowns")

    with st.expander("Revenue Calculation (Annual)"):
        st.markdown(f"""
        <p>Total revenue is the sum of income from selling the primary product (Poha) and any byproducts.</p>
        <strong>1. Poha Revenue:</strong>
        <ul>
            <li><b>Calculation:</b> Annual Poha Production ({format_currency(results['annual_poha'])}) &times; Poha Price per kg ({format_currency(results['poha_price'])}) = <b>{format_currency(results['annual_poha_revenue'])}</b></li>
        </ul>
        <strong>2. Byproduct Revenue:</strong>
        <ul>
            <li><b>Calculation:</b> Annual Byproduct Sold ({format_currency(results['annual_byproduct_sold'])}) &times; Byproduct Price per kg ({format_currency(results['byproduct_rate_kg'])}) = <b>{format_currency(results['annual_byproduct_revenue'])}</b></li>
        </ul>
        <strong>3. Final Calculation:</strong>
        <ul>
            <li><b>Total Annual Revenue:</b> Poha Revenue ({format_currency(results['annual_poha_revenue'])}) + Byproduct Revenue ({format_currency(results['annual_byproduct_revenue'])}) = <b>{format_currency(results['annual_revenue'])}</b></li>
        </ul>
        """, unsafe_allow_html=True)

    with st.expander("Working Capital Calculation"):
        st.markdown(f"""
        <p>Working capital is the cash needed to fund day-to-day operations. It's calculated by subtracting operating current liabilities from operating current assets.</p>
        <strong>1. Calculate Current Assets (Money tied up in operations):</strong>
        <ul>
            <li><b>Raw Material Inventory:</b> Daily COGS ({format_currency(results['daily_cogs'])}) &times; {results['rm_inventory_days']} days = <b>{format_currency(results['rm_inventory'])}</b></li>
            <li><b>Finished Goods Inventory:</b> Daily Production Cost ({format_currency(results['daily_prod_cost'])}) &times; {results['fg_inventory_days']} days = <b>{format_currency(results['fg_inventory'])}</b></li>
            <li><b>Accounts Receivable:</b> Daily Revenue ({format_currency(results['daily_rev'])}) &times; {results['debtor_days']} days = <b>{format_currency(results['receivables'])}</b></li>
            <li><b>Total Current Assets:</b> {format_currency(results['rm_inventory'])} + {format_currency(results['fg_inventory'])} + {format_currency(results['receivables'])} = <b>{format_currency(results['current_assets'])}</b></li>
        </ul>
        <strong>2. Calculate Current Liabilities (Credit received from suppliers):</strong>
        <ul>
            <li><b>Accounts Payable:</b> Daily COGS ({format_currency(results['daily_cogs'])}) &times; {results['creditor_days']} days = <b>{format_currency(results['payables'])}</b></li>
        </ul>
        <strong>3. Final Calculation:</strong>
        <ul>
            <li><b>Net Working Capital (NWC):</b> Total Current Assets ({format_currency(results['current_assets'])}) - Accounts Payable ({format_currency(results['payables'])}) = <b>{format_currency(results['net_working_capital'])}</b></li>
        </ul>
        """, unsafe_allow_html=True)

    with st.expander("Interest Cost Calculation (Annual)"):
        st.markdown(f"""
        <p>Interest is calculated on both the term loan for capital assets (CAPEX) and the loan required for working capital.</p>
        <strong>1. Interest on Term Loan (CAPEX Loan):</strong>
        <ul>
            <li><b>Total Debt:</b> Total CAPEX ({format_currency(results['total_capex'])}) &times; (100% - {results['equity_contrib']}% Equity) = <b>{format_currency(results['debt'])}</b></li>
            <li><b>Interest on Debt:</b> {format_currency(results['debt'])} &times; {results['interest_rate']}% = <b>{format_currency(results['interest_fixed'])}</b></li>
        </ul>
        <strong>2. Interest on Working Capital Loan:</strong>
        <ul>
            <li><b>Interest on NWC:</b> Net Working Capital ({format_currency(results['net_working_capital'])}) &times; {results['interest_rate']}% = <b>{format_currency(results['interest_wc'])}</b></li>
        </ul>
        <strong>3. Final Calculation:</strong>
        <ul>
            <li><b>Total Annual Interest:</b> Interest on Debt ({format_currency(results['interest_fixed'])}) + Interest on NWC ({format_currency(results['interest_wc'])}) = <b>{format_currency(results['total_interest'])}</b></li>
        </ul>
        """, unsafe_allow_html=True)
    
    with st.expander("Return on Capital Employed (ROCE) Calculation"):
        st.markdown(f"""
        <p>ROCE measures how efficiently a company is using its capital to generate profits.</p>
        <strong>1. Calculate Capital Employed:</strong>
        <ul>
            <li><b>Total CAPEX:</b> Sum of Land, Civil, and Machinery costs = <b>{format_currency(results['total_capex'])}</b></li>
            <li><b>Net Working Capital (NWC):</b> (Calculated above) = <b>{format_currency(results['net_working_capital'])}</b></li>
            <li><b>Total Capital Employed:</b> Total CAPEX ({format_currency(results['total_capex'])}) + NWC ({format_currency(results['net_working_capital'])}) = <b>{format_currency(results['capital_employed'])}</b></li>
        </ul>
        <strong>2. Calculate EBIT (Earnings Before Interest & Tax):</strong>
        <ul>
            <li><b>EBIT:</b> (See P&L Statement) = <b>{format_currency(results['ebit'])}</b></li>
        </ul>
        <strong>3. Final Calculation:</strong>
        <ul>
            <li><b>ROCE:</b> (EBIT / Capital Employed) &times; 100 = ({format_currency(results['ebit'])} / {format_currency(results['capital_employed'])}) &times; 100 = <b>{results['roce']:.2f}%</b></li>
        </ul>
        """, unsafe_allow_html=True)

# --- Main Dashboard Rendering ---
def render_dashboard(inputs):
    results = calculate_financials(inputs)
    if 'error' in results: st.error(results['error']); return
    if results['byproduct_limit_hit']: st.markdown(f"""<div class="warning-box"><strong>⚠️ Byproduct Constraint:</strong> Trying to sell {results['byproduct_sale_percent']:.1f}% ({results['daily_byproduct_target']:,.0f} kg/day) but only {results['daily_byproduct_gen']:,.0f} kg/day is generated. <br><strong>Suggestion:</strong> Reduce 'Byproduct Sale %' in the sidebar to be less than the available amount.</div>""", unsafe_allow_html=True)
    st.header("📈 Key Performance Indicators")
    row1_col1, row1_col2, row1_col3 = st.columns(3)
    custom_metric(row1_col1, "Annual Revenue", format_currency(results['annual_revenue']), "", "Revenue")
    custom_metric(row1_col2, "Annual COGS", format_currency(results['annual_cogs']), "", "COGS")
    custom_metric(row1_col3, "Gross Margin", f"{results['gross_margin']:.1f}%", format_currency(results['gross_profit']), "Gross Margin")
    row2_col1, row2_col2, row2_col3 = st.columns(3)
    custom_metric(row2_col1, "Contribution Margin", f"{results['contribution_margin_pct']:.1f}%", format_currency(results['contribution_margin']), "Contribution Margin")
    custom_metric(row2_col2, "Net Profit (PAT)", format_currency(results['net_profit']), f"{results['net_profit_margin']:.1f}% Margin", "Net Profit")
    custom_metric(row2_col3, "EBITDA", format_currency(results['ebitda']), f"{results['ebitda_margin']:.1f}% Margin", "EBITDA")
    row3_col1, row3_col2, _ = st.columns(3)
    custom_metric(row3_col1, "ROCE", f"{results['roce']:.1f}%", "", "ROCE")
    custom_metric(row3_col2, "ROE", f"{results['roe']:.1f}%", "", "ROE")
    st.divider()
    st.header("📊 Production & Financial Summary")
    summary_data = {"Metric": ["Paddy Consumption (kg)", "Poha Production (kg)", "Byproduct Generated (kg)", "Byproduct Sold (kg)", "Total Revenue", "COGS", "Gross Profit"], "Daily": [f"{results['daily_paddy']:,.0f}", f"{results['annual_poha']/(results['days_per_month']*12):,.0f}", f"{results['daily_byproduct_gen']:,.0f}", f"{results['daily_byproduct_sold']:,.0f}", format_currency(results['annual_revenue']/365), format_currency(results['annual_cogs']/365), format_currency(results['gross_profit']/365)], "Monthly": [f"{results['daily_paddy']*results['days_per_month']:,.0f}", f"{results['annual_poha']/12:,.0f}", f"{results['daily_byproduct_gen']*results['days_per_month']:,.0f}", f"{results['daily_byproduct_sold']*results['days_per_month']:,.0f}", format_currency(results['annual_revenue']/12), format_currency(results['annual_cogs']/12), format_currency(results['gross_profit']/12)], "Annual": [f"{results['annual_paddy']:,.0f}", f"{results['annual_poha']:,.0f}", f"{results['daily_byproduct_gen']*results['days_per_month']*12:,.0f}", f"{results['annual_byproduct_sold']:,.0f}", format_currency(results['annual_revenue']), format_currency(results['annual_cogs']), format_currency(results['gross_profit'])]}
    st.dataframe(pd.DataFrame(summary_data), hide_index=True, use_container_width=True, column_config={"Metric": st.column_config.Column(width="medium"), "Daily": st.column_config.Column(width="small"), "Monthly": st.column_config.Column(width="small"), "Annual": st.column_config.Column(width="small")})
    st.divider()
    st.header("💡 Breakeven Analysis")
    col_be_select, _ = st.columns([1, 2])
    with col_be_select: breakeven_metric = st.selectbox("Select Breakeven Metric:", ["EBITDA", "Net Profit (PAT)"])
    rm_cost = results['paddy_rate']
    total_var_cost = rm_cost + results['total_var_cost_per_kg']
    poha_rev = results['poha_price'] * (results['paddy_yield'] / 100)
    byproduct_rev = results['byproduct_rate_kg'] * min(results['byproduct_sale_percent'] / 100, (100 - results['paddy_yield']) / 100)
    rev_per_kg = poha_rev + byproduct_rev
    contribution_per_kg = rev_per_kg - total_var_cost
    if breakeven_metric == "EBITDA": fixed_costs, target_metric = results['annual_fixed_opex'], "EBITDA"
    else: fixed_costs, target_metric = results['annual_fixed_opex'] + results['annual_depreciation'] + results['total_interest'], "Net Profit"
    breakeven_vol = fixed_costs / contribution_per_kg if contribution_per_kg > 0 else float('inf')
    with st.expander("How is this calculated?"):
        st.markdown(f"""<p>The breakeven point is where Total Revenue equals Total Costs. The formula is: <b>Breakeven Volume = Total Fixed Costs / Contribution Margin per Unit</b>.</p><ul><li><b>Selected Metric:</b> {target_metric}</li><li><b>Total Fixed Costs to Cover:</b> {format_currency(fixed_costs)}</li><li><b>Contribution Margin per kg of Paddy:</b> (Revenue per kg - Variable Costs per kg) = ({format_currency(rev_per_kg)} - {format_currency(total_var_cost)}) = <b>{format_currency(contribution_per_kg)}</b></li><li><b>Breakeven Calculation:</b> {format_currency(fixed_costs)} / {format_currency(contribution_per_kg)} = <b>{breakeven_vol:,.0f} kg</b></li></ul>""", unsafe_allow_html=True)
    col_be1, col_be2 = st.columns(2)
    with col_be1:
        st.metric(f"Breakeven Volume ({target_metric})", f"{breakeven_vol:,.0f} kg Paddy/Year")
        st.metric("Breakeven Revenue", format_currency(breakeven_vol * rev_per_kg if breakeven_vol != float('inf') else 0))
    with col_be2:
        max_vol = max(results['annual_paddy'], breakeven_vol) * 1.5 if breakeven_vol != float('inf') else results['annual_paddy'] * 1.5
        volumes = np.linspace(0, max_vol, 100)
        revenue_line, cost_line = volumes * rev_per_kg, fixed_costs + (volumes * total_var_cost)
        be_df = pd.DataFrame({'Paddy Volume (kg)': volumes, 'Total Revenue': revenue_line, 'Total Costs': cost_line})
        fig = px.line(be_df, x='Paddy Volume (kg)', y=['Total Revenue', 'Total Costs'], title=f"Breakeven Analysis - {target_metric}")
        if breakeven_vol != float('inf') and breakeven_vol < max_vol: fig.add_vline(x=breakeven_vol, line_dash="dash", line_color="red", annotation_text="Breakeven")
        st.plotly_chart(fig, use_container_width=True)
    st.divider()

    # --- SENSITIVITY ANALYSIS ---
    st.header("🔬 Sensitivity Analysis")
    var_options = ("Poha Selling Price", "Paddy Purchase Rate", "Paddy to Poha Yield", "Interest Rate")
    sensitivity_var = st.selectbox("Variable to analyze:", var_options)
    sensitivity_range = st.slider("Sensitivity range (% change from base value):", -50, 50, (-20, 20))
    
    var_key = {"Poha Selling Price": 'poha_price', "Paddy Purchase Rate": 'paddy_rate', "Paddy to Poha Yield": 'paddy_yield', "Interest Rate": 'interest_rate'}[sensitivity_var]
    base_val = inputs[var_key]
    range_vals = np.linspace(base_val * (1 + sensitivity_range[0] / 100), base_val * (1 + sensitivity_range[1] / 100), 11)
    
    sens_data = []
    for val in range_vals:
        res = calculate_financials({**inputs, var_key: val})
        sens_data.append({sensitivity_var: val, "Net Profit": res.get('net_profit', np.nan)})
    
    sens_df = pd.DataFrame(sens_data).dropna()
    col_sens1, col_sens2 = st.columns([1, 1.5])
    with col_sens1:
        st.dataframe(sens_df.style.format({sensitivity_var: '{:,.2f}', 'Net Profit': '{:,.0f}'}), use_container_width=True, hide_index=True)
    with col_sens2:
        if not sens_df.empty:
            fig_sens = px.line(sens_df, x=sensitivity_var, y='Net Profit', title=f"Impact of {sensitivity_var} on Net Profit", markers=True, labels={'Net Profit': 'Net Profit (₹)', sensitivity_var: f'Value of {sensitivity_var}'})
            fig_sens.update_traces(marker=dict(size=8), line=dict(width=3))
            st.plotly_chart(fig_sens, use_container_width=True)
    st.divider()
    
    col_pnl, col_bs = st.columns([1.2, 1])
    with col_pnl:
        st.header("💰 Profit & Loss Statement (Annual)")
        pnl_data = {"Metric": ["Total Revenue", "COGS", "**Gross Profit**", "Variable OpEx", "Fixed OpEx", "Depreciation", "**EBIT**", "Total Interest", "**EBT**", "Taxes", "**Net Profit (PAT)**"], "Amount (INR)": [format_currency(results['annual_revenue']), f"({format_currency(results['annual_cogs'])})", format_currency(results['gross_profit']), f"({format_currency(results['annual_var_costs'])})", f"({format_currency(results['annual_fixed_opex'])})", f"({format_currency(results['annual_depreciation'])})", format_currency(results['ebit']), f"({format_currency(results['total_interest'])})", format_currency(results['ebt']), f"({format_currency(results['taxes'])})", format_currency(results['net_profit'])]}
        pnl_df = pd.DataFrame(pnl_data)
        st.dataframe(pnl_df, hide_index=True, use_container_width=True, column_config={"Metric": st.column_config.Column(width="medium"), "Amount (INR)": st.column_config.Column(width="small")})
    with col_bs:
        st.header("💼 Balance Sheet")
        bs_data = {"Item": ["Total Capex", "Equity", "Debt", "**Total Assets**", "RM Inventory", "FG Inventory", "Receivables", "Payables", "**Net Working Capital**", "**Capital Employed**"], "Amount (INR)": [format_currency(results['total_capex']), format_currency(results['equity']), format_currency(results['debt']), format_currency(results['total_assets']), format_currency(results['rm_inventory']), format_currency(results['fg_inventory']), format_currency(results['receivables']), f"({format_currency(results['payables'])})", format_currency(results['net_working_capital']), format_currency(results['capital_employed'])]}
        st.dataframe(pd.DataFrame(bs_data), hide_index=True, use_container_width=True, column_config={"Item": st.column_config.Column(width="medium"), "Amount (INR)": st.column_config.Column(width="small")})
    st.divider()
    render_detailed_breakdowns(results)

# --- Main Execution ---
if __name__ == "__main__":
    inputs = render_sidebar()
    render_dashboard(inputs)
