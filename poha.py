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
def format_crore(amount):
    try: return f"₹{amount/1e7:,.2f} Cr"
    except: return "N/A"

def format_currency(amount):
    try:
        if amount == 0: return "₹0.00"
        amount_str = f"{abs(amount):.2f}"
        integer_part, decimal_part = amount_str.split('.')
        last_three = integer_part[-3:]
        remaining = integer_part[:-3]
        if remaining:
            formatted = ','.join([remaining[max(0, i-2):i] for i in range(len(remaining), 0, -2)][::-1]) + ',' + last_three
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
    "ROCE": {"formula": "(EBIT / Capital Employed) × 100", "explanation": "Return on Capital Employed, measuring how efficiently capital is used to generate profit."},
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
    byproduct_limit_hit = daily_byproduct_target > daily_byproduct_gen
    annual_poha_revenue = annual_poha * inputs['poha_price']
    annual_byproduct_revenue = daily_byproduct_sold * inputs['days_per_month'] * 12 * inputs['byproduct_rate_kg']
    annual_revenue = annual_poha_revenue + annual_byproduct_revenue
    annual_cogs = annual_paddy * inputs['paddy_rate']
    gross_profit = annual_revenue - annual_cogs
    var_cost_per_kg = inputs['packaging_cost'] + inputs['fuel_cost'] + inputs['other_var_cost']
    annual_var_costs = annual_paddy * var_cost_per_kg
    annual_fixed_opex = sum([inputs[k] for k in ['rent_per_month', 'labor_per_month', 'electricity_per_month', 'security_ssc_insurance_per_month', 'misc_per_month']]) * 12
    annual_depreciation = (inputs['machinery_cost'] + inputs['civil_work_cost']) / inputs['machinery_useful_life_years'] if inputs['machinery_useful_life_years'] > 0 else 0
    ebit = gross_profit - annual_var_costs - annual_fixed_opex - annual_depreciation
    daily_cogs = annual_cogs / 365
    daily_poha = annual_poha / (inputs['days_per_month'] * 12)
    daily_prod_cost = (annual_cogs + annual_var_costs) / annual_poha if annual_poha > 0 else 0
    daily_rev = annual_revenue / 365
    rm_inventory = daily_cogs * inputs['rm_inventory_days']
    fg_inventory = (daily_poha * daily_prod_cost) * inputs['fg_inventory_days']
    receivables = daily_rev * inputs['debtor_days']
    payables = daily_cogs * inputs['creditor_days']
    current_assets = rm_inventory + fg_inventory + receivables
    net_working_capital = current_assets - payables
    equity = total_capex * (inputs['equity_contrib'] / 100)
    debt = total_capex - equity
    total_interest = (debt + max(0, net_working_capital)) * (inputs['interest_rate'] / 100)
    ebt = ebit - total_interest
    taxes = max(0, ebt) * (inputs['tax_rate_percent'] / 100)
    net_profit = ebt - taxes
    capital_employed = total_capex + net_working_capital
    roce = (ebit / capital_employed) * 100 if capital_employed != 0 else float('inf')
    net_profit_margin = (net_profit / annual_revenue) * 100 if annual_revenue > 0 else 0
    ebitda = ebit + annual_depreciation
    ebitda_margin = (ebitda / annual_revenue) * 100 if annual_revenue > 0 else 0
    roe = (net_profit / equity) * 100 if equity > 0 else float('inf')
    gross_margin = (gross_profit / annual_revenue) * 100 if annual_revenue > 0 else 0
    contribution_margin = annual_revenue - annual_cogs - annual_var_costs
    contribution_margin_pct = (contribution_margin / annual_revenue) * 100 if annual_revenue > 0 else 0
    return {**inputs, 'total_capex': total_capex, 'daily_paddy': daily_paddy, 'annual_paddy': annual_paddy, 'annual_poha': annual_poha, 'daily_byproduct_gen': daily_byproduct_gen, 'daily_byproduct_sold': daily_byproduct_sold, 'daily_byproduct_target': daily_byproduct_target, 'byproduct_limit_hit': byproduct_limit_hit, 'annual_revenue': annual_revenue, 'annual_cogs': annual_cogs, 'gross_profit': gross_profit, 'annual_var_costs': annual_var_costs, 'annual_fixed_opex': annual_fixed_opex, 'annual_depreciation': annual_depreciation, 'ebit': ebit, 'net_working_capital': net_working_capital, 'equity': equity, 'debt': debt, 'total_interest': total_interest, 'ebt': ebt, 'taxes': taxes, 'net_profit': net_profit, 'roce': roce, 'net_profit_margin': net_profit_margin, 'ebitda': ebitda, 'ebitda_margin': ebitda_margin, 'roe': roe, 'gross_margin': gross_margin, 'contribution_margin': contribution_margin, 'contribution_margin_pct': contribution_margin_pct, 'total_var_cost_per_kg': var_cost_per_kg, 'rm_inventory': rm_inventory, 'fg_inventory': fg_inventory, 'receivables': receivables, 'payables': payables, 'current_assets': current_assets, 'capital_employed': capital_employed, 'total_assets': total_capex + current_assets}

# --- Reusable Metric Component ---
def custom_metric(col, label, value, sub_value, info_key):
    formula, explanation = RATIOS_INFO[info_key].values()
    color = 'green' if (isinstance(sub_value, (int, float)) and sub_value >= 0) or ('Margin' not in str(sub_value) and str(sub_value) != "") else 'red'
    with col: st.markdown(f"""<div class="metric-container"><div class="tooltip"><div class="metric-title">{label} ℹ️</div><span class="tooltiptext"><strong>Formula:</strong> {formula}<br><strong>Explanation:</strong> {explanation}</span></div><div class="metric-value">{value}</div><div class="metric-delta" style="color: {color};">{sub_value}</div></div>""", unsafe_allow_html=True)

# --- Detailed Breakdowns Rendering Function ---
def render_detailed_breakdowns(results):
    st.header("🔍 Detailed Calculation Breakdowns")
    with st.expander("Production Flow Analysis"):
        st.markdown(f"""- **Daily Paddy Processing:** `{results['paddy_rate_kg_hr']:,.0f} kg/hr × {results['hours_per_day']} hrs = {results['daily_paddy']:,.0f} kg`  
          *This is the total raw material processed daily based on machine capacity and operational hours.*
        - **Daily Poha Output:** `{results['daily_paddy']:,.0f} kg × {results['paddy_yield']:.1f}% = {results['annual_poha'] / (results['days_per_month'] * 12):,.0f} kg`  
          *This is the actual finished product (poha) produced daily after accounting for the yield percentage.*""")
    with st.expander("Revenue Structure (Annual)"):
        st.markdown(f"""- **Poha Revenue:** `{results['annual_poha']:,.0f} kg × ₹{results['poha_price']:.2f} = {format_currency(results['annual_poha'] * results['poha_price'])}`  
          *This is the total income generated from selling poha annually.*
        - **Byproduct Revenue:** `{results['daily_byproduct_sold'] * results['days_per_month'] * 12:,.0f} kg × ₹{results['byproduct_rate_kg']:.2f} = {format_currency(results['annual_revenue'] - (results['annual_poha'] * results['poha_price']))}`  
          *This is the total income from selling the byproduct (e.g., husk, bran) annually.*""")
    with st.expander("Cost Structure Analysis (Annual)"):
        st.markdown(f"""- **Raw Material Cost (COGS):** `{results['annual_paddy']:,.0f} kg × ₹{results['paddy_rate']:.2f} = {format_currency(results['annual_cogs'])}`  
          *This is the total cost of paddy consumed annually.*
        - **Variable Costs:** `₹{results['total_var_cost_per_kg']:.2f}/kg × {results['annual_paddy']:,.0f} kg = {format_currency(results['annual_var_costs'])}`  
          *These are costs like packaging and fuel that vary directly with production volume.*
        - **Fixed Operating Expenses:** `Sum of rent, labor, electricity, etc. × 12 = {format_currency(results['annual_fixed_opex'])}`  
          *These are regular operational costs that do not change with production volume.*""")
    with st.expander("Working Capital Details"):
        st.markdown(f"""- **Net Working Capital:** `{format_currency(results['current_assets'])} - {format_currency(results['payables'])} = {format_currency(results['net_working_capital'])}`  
          *This represents the funds required to run day-to-day operations (inventory, receivables minus payables).*
        - **Current Assets:** `RM Inventory + FG Inventory + Receivables = {format_currency(results['current_assets'])}`  
          *This is the value of assets expected to be converted to cash within one year.*""")
    with st.expander("Financing and Returns"):
        st.markdown(f"""- **Capital Employed:** `Total CAPEX + Net Working Capital = {format_currency(results['capital_employed'])}`  
          *This is the total capital invested in the business from all sources.*
        - **ROCE:** `EBIT / Capital Employed = {results['roce']:.1f}%`  
          *This ratio measures how efficiently the total capital is being used to generate operating profit.*""")

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
    summary_data = {"Metric": ["Paddy Consumption (kg)", "Poha Production (kg)", "Byproduct Generated (kg)", "Byproduct Sold (kg)", "Total Revenue", "COGS", "Gross Profit"], "Daily": [f"{results['daily_paddy']:,.0f}", f"{results['annual_poha']/(results['days_per_month']*12):,.0f}", f"{results['daily_byproduct_gen']:,.0f}", f"{results['daily_byproduct_sold']:,.0f}", format_currency(results['annual_revenue']/365), format_currency(results['annual_cogs']/365), format_currency(results['gross_profit']/365)], "Monthly": [f"{results['daily_paddy']*results['days_per_month']:,.0f}", f"{results['annual_poha']/12:,.0f}", f"{results['daily_byproduct_gen']*results['days_per_month']:,.0f}", f"{results['daily_byproduct_sold']*results['days_per_month']:,.0f}", format_currency(results['annual_revenue']/12), format_currency(results['annual_cogs']/12), format_currency(results['gross_profit']/12)], "Annual": [f"{results['annual_paddy']:,.0f}", f"{results['annual_poha']:,.0f}", f"{results['daily_byproduct_gen']*results['days_per_month']*12:,.0f}", f"{results['daily_byproduct_sold']*results['days_per_month']*12:,.0f}", format_currency(results['annual_revenue']), format_currency(results['annual_cogs']), format_currency(results['gross_profit'])]}
    st.dataframe(pd.DataFrame(summary_data), hide_index=True, use_container_width=True, column_config={"Metric": st.column_config.Column(width="medium"), "Daily": st.column_config.Column(width="small"), "Monthly": st.column_config.Column(width="small"), "Annual": st.column_config.Column(width="small")})
    st.divider()
    col_pnl, col_bs = st.columns([1.2, 1])
    with col_pnl:
        st.header("💰 Profit & Loss Statement (Annual)")
        pnl_data = {"Metric": ["Total Revenue", "COGS", "**Gross Profit**", "Variable OpEx", "Fixed OpEx", "Depreciation", "**EBIT**", "Total Interest", "**EBT**", "Taxes", "**Net Profit (PAT)**"], "Amount (INR)": [format_currency(results['annual_revenue']), f"({format_currency(results['annual_cogs'])})", format_currency(results['gross_profit']), f"({format_currency(results['annual_var_costs'])})", f"({format_currency(results['annual_fixed_opex'])})", f"({format_currency(results['annual_depreciation'])})", format_currency(results['ebit']), f"({format_currency(results['total_interest'])})", format_currency(results['ebt']), f"({format_currency(results['taxes'])})", format_currency(results['net_profit'])]}
        pnl_df = pd.DataFrame(pnl_data)
        st.dataframe(pnl_df, hide_index=True, use_container_width=True, column_config={"Metric": st.column_config.Column(width="medium"), "Amount (INR)": st.column_config.Column(width="small")})
        st.download_button("📥 Download P&L", pnl_df.to_csv(index=False).encode('utf-8'), "poha_pnl.csv", "text/csv")
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

