import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import math

# CSS for responsive sidebar and layout
st.markdown("""
<style>
 /* Sidebar styling */
 [data-testid="stSidebar"] {
 position: fixed;
 top: 0;
 left: 0;
 z-index: 99;
 }
 
 /* Sidebar width when expanded */
 [data-testid="stSidebar"][aria-expanded="true"] {
 width: 300px !important;
 min-width: 300px !important;
 }
 
 /* Sidebar width when collapsed */
 [data-testid="stSidebar"][aria-expanded="false"] {
 width: 50px !important;
 min-width: 50px !important;
 }
 
 /* Main content area */
 .main .block-container {
 padding: 1rem;
 max-width: 100%;
 transition: width 0.3s ease, margin-left 0.3s ease;
 box-sizing: border-box;
 }
 
 /* Adjust main content width based on sidebar state */
 [data-testid="stSidebar"][aria-expanded="true"] ~ .main .block-container {
 margin-left: 300px;
 width: calc(100% - 300px);
 }
 
 [data-testid="stSidebar"][aria-expanded="false"] ~ .main .block-container {
 margin-left: 50px;
 width: calc(100% - 50px);
 }
 
 /* Metric container */
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
 }
 .metric-value {
 font-size: 1.25rem;
 font-weight: bold;
 color: #262730;
 }
 .metric-delta {
 font-size: 0.75rem;
 color: inherit;
 }
 
 /* Tooltip */
 .tooltip {
 position: relative;
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
 }
 .tooltip:hover .tooltiptext {
 visibility: visible;
 opacity: 1;
 }
 
 /* Warning box */
 .warning-box {
 background-color: #fff3cd;
 border: 1px solid #ffeaa7;
 border-radius: 0.5rem;
 padding: 1rem;
 margin: 1rem 0;
 color: #856404;
 }
 
 /* Responsive adjustments */
 @media (max-width: 768px) {
 [data-testid="stSidebar"][aria-expanded="true"] {
 width: 250px !important;
 }
 [data-testid="stSidebar"][aria-expanded="true"] ~ .main .block-container {
 margin-left: 250px;
 width: calc(100% - 250px);
 }
 }
 
 /* Ensure charts and tables are responsive */
 .js-plotly-plot, .stDataFrame {
 width: 100% !important;
 }
</style>
""", unsafe_allow_html=True)

# Formatting functions
def format_crore(amount):
    try:
        return f"₹{amount/1e7:,.2f} Cr"
    except Exception:
        return "N/A"

def format_indian_currency(amount):
    try:
        if amount == 0:
            return "₹0.00"
        amount_str = f"{abs(amount):.2f}"
        integer_part, decimal_part = amount_str.split('.')
        if len(integer_part) > 3:
            last_three = integer_part[-3:]
            remaining = integer_part[:-3]
            groups = [remaining[max(0, i-2):i] for i in range(len(remaining), 0, -2)]
            groups.reverse()
            formatted = ','.join(groups) + ',' + last_three
        else:
            formatted = integer_part
        return f"₹{('-' if amount < 0 else '')}{formatted}.{decimal_part}"
    except Exception:
        return "N/A"

# Input configuration
INPUT_CONFIG = {
    "Operational Assumptions": {
        "hours_per_day": {"label": "Production Hours per Day", "type": "number", "min_value": 5, "max_value": 24, "value": 10, "step": 1},
        "days_per_month": {"label": "Operational Days per Month", "type": "number", "min_value": 1, "max_value": 31, "value": 24, "step": 1}
    },
    "Production & Yield": {
        "paddy_rate_kg_hr": {"label": "Paddy Processing Rate (kg/hr)", "type": "number", "value": 1000, "step": 10},
        "paddy_yield": {"label": "Paddy to Poha Yield (%)", "type": "number", "min_value": 50.0, "max_value": 80.0, "value": 65.0, "step": 0.1},
        "byproduct_sale_percent": {"label": "Byproduct Sold (% of Paddy Input)", "type": "slider", "min_value": 0.0, "max_value": 40.0, "value": 32.0, "step": 0.1, "help": "Percentage of original paddy input sold as byproduct"}
    },
    "Financial Assumptions (INR)": {
        "paddy_rate": {"label": "Paddy Rate (INR/kg)", "type": "number", "value": 22.0, "step": 0.1},
        "poha_price": {"label": "Poha Selling Price (INR/kg)", "type": "number", "value": 45.0, "step": 0.1},
        "byproduct_rate_kg": {"label": "Byproduct Rate (INR/kg)", "type": "number", "value": 7.0, "step": 0.1}
    },
    "Capital Expenditure (Capex)": {
        "land_cost": {"label": "Land Cost", "type": "number", "value": 0, "step": 10000},
        "civil_work_cost": {"label": "Civil Work Cost", "type": "number", "value": 0, "step": 10000},
        "machinery_cost": {"label": "Machinery Cost", "type": "number", "value": 7000000, "step": 10000},
        "machinery_useful_life_years": {"label": "Useful Life (Years)", "type": "number", "value": 15, "step": 1}
    },
    "Operating Costs": {
        "packaging_cost": {"label": "Packaging Material (per kg paddy)", "type": "number", "value": 0.5, "step": 0.01},
        "fuel_cost": {"label": "Fuel/Power Variable (per kg paddy)", "type": "number", "value": 0.0, "step": 0.01},
        "other_var_cost": {"label": "Other Variable Costs (per kg paddy)", "type": "number", "value": 0.0, "step": 0.01},
        "rent_per_month": {"label": "Rent", "type": "number", "value": 300000, "step": 1000},
        "labor_per_month": {"label": "Labor Wages and Salaries", "type": "number", "value": 400000, "step": 1000},
        "electricity_per_month": {"label": "Electricity (Fixed)", "type": "number", "value": 150000, "step": 1000},
        "security_ssc_insurance_per_month": {"label": "Security, SSC & Insurance", "type": "number", "value": 300000, "step": 1000},
        "misc_per_month": {"label": "Misc Overheads", "type": "number", "value": 300000, "step": 1000}
    },
    "Funding & Tax": {
        "equity_contrib": {"label": "Equity Contribution (%)", "type": "number", "min_value": 0.0, "max_value": 100.0, "value": 30.0, "step": 0.1},
        "interest_rate": {"label": "Interest Rate (%)", "type": "number", "value": 9.0, "step": 0.01},
        "tax_rate_percent": {"label": "Corporate Tax Rate (%)", "type": "number", "min_value": 0.0, "max_value": 50.0, "value": 25.0, "step": 0.1}
    },
    "Working Capital Days": {
        "rm_inventory_days": {"label": "Raw Material Inventory Days", "type": "number", "value": 72, "step": 1},
        "fg_inventory_days": {"label": "Finished Goods Inventory Days", "type": "number", "value": 20, "step": 1},
        "debtor_days": {"label": "Debtor Days (Receivables)", "type": "number", "value": 45, "step": 1},
        "creditor_days": {"label": "Creditor Days (Payables)", "type": "number", "value": 5, "step": 1}
    }
}

# Key ratios for tooltips
KEY_RATIOS_INFO = {
    "Revenue": {"formula": "Revenue = Poha Sales + Byproduct Sales", "explanation": "Total income from all product sales."},
    "COGS": {"formula": "COGS = Paddy Consumption × Paddy Rate", "explanation": "Direct cost of raw materials consumed."},
    "Gross Margin": {"formula": "GM = (Revenue - COGS) / Revenue × 100", "explanation": "Profitability after direct material costs."},
    "Contribution Margin": {"formula": "CM = (Revenue - COGS - Variable Costs) / Revenue × 100", "explanation": "Profitability after all variable costs."},
    "Net Profit": {"formula": "Net Profit = EBT - Taxes", "explanation": "The final 'bottom line' profit after all costs."},
    "EBITDA": {"formula": "EBITDA = EBIT + Depreciation", "explanation": "Operational profitability before non-cash expenses."},
    "ROCE": {"formula": "ROCE = (EBIT / Capital Employed) × 100", "explanation": "Effectiveness of capital in generating profits."},
    "ROE": {"formula": "ROE = (Net Profit / Equity) × 100", "explanation": "Profitability relative to shareholder equity."}
}

# Page configuration
st.set_page_config(page_title="Poha Manufacturing Financial Dashboard", page_icon="🌾", layout="wide")

# Sidebar inputs
def render_sidebar():
    inputs = {}
    st.sidebar.header("⚙️ Input Parameters")
    for section, params in INPUT_CONFIG.items():
        with st.sidebar.expander(section, expanded=True):
            for key, config in params.items():
                # Create a copy of config to avoid modifying the original
                config_copy = config.copy()
                input_type = config_copy.pop("type")
                if input_type == "number":
                    inputs[key] = st.number_input(**config_copy)
                elif input_type == "slider":
                    inputs[key] = st.slider(**config_copy)
    return inputs

# Financial model
def run_financial_model(inputs):
    total_capex = inputs['land_cost'] + inputs['civil_work_cost'] + inputs['machinery_cost']
    if any(v <= 0 for v in [inputs['paddy_yield'], inputs['poha_price'], total_capex]):
        return {'error': 'Paddy Yield, Poha Price, and Capex must be greater than 0.'}
    
    # Production
    daily_paddy = inputs['paddy_rate_kg_hr'] * inputs['hours_per_day']
    monthly_paddy = daily_paddy * inputs['days_per_month']
    annual_paddy = monthly_paddy * 12
    
    daily_poha = daily_paddy * (inputs['paddy_yield'] / 100)
    monthly_poha = daily_poha * inputs['days_per_month']
    annual_poha = monthly_poha * 12
    
    # Byproduct
    daily_byproduct_target = daily_paddy * (inputs['byproduct_sale_percent'] / 100)
    daily_byproduct_gen = daily_paddy - daily_poha
    daily_byproduct_sold = min(daily_byproduct_target, daily_byproduct_gen)
    monthly_byproduct_sold = daily_byproduct_sold * inputs['days_per_month']
    annual_byproduct_sold = monthly_byproduct_sold * 12
    byproduct_limit_hit = daily_byproduct_target > daily_byproduct_gen
    
    # Revenue
    daily_revenue = (daily_poha * inputs['poha_price']) + (daily_byproduct_sold * inputs['byproduct_rate_kg'])
    monthly_revenue = daily_revenue * inputs['days_per_month']
    annual_revenue = monthly_revenue * 12
    
    # COGS
    annual_cogs = annual_paddy * inputs['paddy_rate']
    gross_profit = annual_revenue - annual_cogs
    
    # Operating costs
    var_cost_per_kg = inputs['packaging_cost'] + inputs['fuel_cost'] + inputs['other_var_cost']
    annual_var_costs = annual_paddy * var_cost_per_kg
    monthly_fixed_opex = sum([inputs[k] for k in ['rent_per_month', 'labor_per_month', 'electricity_per_month', 
                                                  'security_ssc_insurance_per_month', 'misc_per_month']])
    annual_fixed_opex = monthly_fixed_opex * 12
    total_opex = annual_fixed_opex + annual_var_costs
    
    # Depreciation
    annual_depreciation = (inputs['machinery_cost'] + inputs['civil_work_cost']) / inputs['machinery_useful_life_years']
    
    # EBIT
    ebit = gross_profit - total_opex - annual_depreciation
    
    # Working capital
    daily_cogs = annual_cogs / 365
    daily_prod_cost = (annual_cogs + annual_var_costs) / annual_poha if annual_poha > 0 else 0
    daily_rev = annual_revenue / 365
    rm_inventory = daily_cogs * inputs['rm_inventory_days']
    fg_inventory = (daily_poha * daily_prod_cost) * inputs['fg_inventory_days']
    receivables = daily_rev * inputs['debtor_days']
    payables = daily_cogs * inputs['creditor_days']
    current_assets = rm_inventory + fg_inventory + receivables
    current_liabilities = payables
    net_working_capital = current_assets - current_liabilities
    
    # Financing
    equity = total_capex * (inputs['equity_contrib'] / 100)
    debt = total_capex - equity
    interest_fixed = debt * (inputs['interest_rate'] / 100)
    interest_wc = max(0, net_working_capital) * (inputs['interest_rate'] / 100)
    total_interest = interest_fixed + interest_wc
    
    # Taxes
    ebt = ebit - total_interest
    taxes = max(0, ebt) * (inputs['tax_rate_percent'] / 100)
    net_profit = ebt - taxes
    
    # Ratios
    total_assets = total_capex + current_assets
    capital_employed = total_assets - current_liabilities
    roce = (ebit / capital_employed) * 100 if capital_employed != 0 else float('inf')
    net_profit_margin = (net_profit / annual_revenue) * 100 if annual_revenue > 0 else 0
    ebitda = ebit + annual_depreciation
    ebitda_margin = (ebitda / annual_revenue) * 100 if annual_revenue > 0 else 0
    roe = (net_profit / equity) * 100 if equity > 0 else float('inf')
    gross_margin = (gross_profit / annual_revenue) * 100 if annual_revenue > 0 else 0
    contribution_margin = gross_profit - annual_var_costs
    contribution_margin_pct = (contribution_margin / annual_revenue) * 100 if annual_revenue > 0 else 0
    
    return {
        **inputs,
        'total_capex': total_capex, 'daily_paddy': daily_paddy, 'monthly_paddy': monthly_paddy, 'annual_paddy': annual_paddy,
        'daily_poha': daily_poha, 'monthly_poha': monthly_poha, 'annual_poha': annual_poha,
        'daily_byproduct_gen': daily_byproduct_gen, 'daily_byproduct_sold': daily_byproduct_sold,
        'daily_byproduct_target': daily_byproduct_target, 'monthly_byproduct_sold': monthly_byproduct_sold,
        'annual_byproduct_sold': annual_byproduct_sold, 'byproduct_limit_hit': byproduct_limit_hit,
        'daily_revenue': daily_revenue, 'monthly_revenue': monthly_revenue, 'annual_revenue': annual_revenue,
        'annual_cogs': annual_cogs, 'gross_profit': gross_profit, 'annual_var_costs': annual_var_costs,
        'annual_fixed_opex': annual_fixed_opex, 'total_opex': total_opex, 'annual_depreciation': annual_depreciation,
        'ebit': ebit, 'net_working_capital': net_working_capital, 'equity': equity, 'debt': debt,
        'total_interest': total_interest, 'ebt': ebt, 'taxes': taxes, 'net_profit': net_profit,
        'roce': roce, 'net_profit_margin': net_profit_margin, 'ebitda': ebitda, 'ebitda_margin': ebitda_margin,
        'roe': roe, 'gross_margin': gross_margin, 'contribution_margin': contribution_margin,
        'contribution_margin_pct': contribution_margin_pct, 'total_var_cost_per_kg': var_cost_per_kg,
        'rm_inventory': rm_inventory, 'fg_inventory': fg_inventory, 'receivables': receivables, 'payables': payables,
        'current_assets': current_assets, 'total_assets': total_assets, 'capital_employed': capital_employed
    }

# Custom metric display
def custom_metric(col, label, value, sub_value, info_key):
    formula, explanation = KEY_RATIOS_INFO[info_key].values()
    try:
        numeric_value = float(str(sub_value).replace('%', '').replace(' Margin', '').replace('₹', '').replace(',', '').strip())
    except:
        numeric_value = 0
    color = 'green' if numeric_value >= 0 else 'red'
    
    with col:
        st.markdown(f"""
        <div class="metric-container">
            <div class="tooltip">
                <div class="metric-title">{label} ℹ️</div>
                <span class="tooltiptext"><strong>Formula:</strong> {formula}<br><strong>Explanation:</strong> {explanation}</span>
            </div>
            <div class="metric-value">{value}</div>
            <div class="metric-delta" style="color: {color};">{sub_value}</div>
        </div>
        """, unsafe_allow_html=True)

# Main dashboard
def render_dashboard(inputs):
    results = run_financial_model(inputs)
    
    if 'error' in results:
        st.error(results['error'])
        return
    
    # Byproduct warning
    if results['byproduct_limit_hit']:
        st.markdown(f"""
        <div class="warning-box">
            <strong>⚠️ Byproduct Constraint Warning:</strong><br>
            You're trying to sell {results['byproduct_sale_percent']:.1f}% of paddy input as byproduct 
            ({results['daily_byproduct_target']:,.0f} kg/day), but only {results['daily_byproduct_gen']:,.0f} kg/day 
            is available. Sales capped at maximum available.<br><br>
            <strong>Suggestion:</strong> Reduce byproduct sale percentage or adjust poha yield.
        </div>
        """, unsafe_allow_html=True)
    
    # KPIs
    st.header("📈 Key Performance Indicators (Annual)")
    col1, col2, col3, col4 = st.columns(4)
    custom_metric(col1, "Revenue", format_indian_currency(results['annual_revenue']), "", "Revenue")
    custom_metric(col2, "COGS", format_indian_currency(results['annual_cogs']), "", "COGS")
    custom_metric(col3, "Gross Margin", f"{results['gross_margin']:.1f}%", format_indian_currency(results['gross_profit']), "Gross Margin")
    custom_metric(col4, "Contribution Margin", f"{results['contribution_margin_pct']:.1f}%", format_indian_currency(results['contribution_margin']), "Contribution Margin")
    
    col5, col6, col7, col8 = st.columns(4)
    custom_metric(col5, "Net Profit", format_indian_currency(results['net_profit']), f"{results['net_profit_margin']:.1f}% Margin", "Net Profit")
    custom_metric(col6, "EBITDA", format_indian_currency(results['ebitda']), f"{results['ebitda_margin']:.1f}% Margin", "EBITDA")
    custom_metric(col7, "ROCE", f"{results['roce']:.1f}%", "", "ROCE")
    custom_metric(col8, "ROE", f"{results['roe']:.1f}%", "", "ROE")
    
    st.divider()
    
    # Summary table
    st.header("📊 Daily, Monthly, and Annual Summary")
    summary_data = {
        "Metric": ["Paddy Consumption (kg)", "Poha Production (kg)", "Byproduct Generated (kg)", "Byproduct Sold (kg)", "Total Revenue", "COGS", "Gross Profit"],
        "Daily": [f"{results['daily_paddy']:,.0f}", f"{results['daily_poha']:,.0f}", f"{results['daily_byproduct_gen']:,.0f}", 
                  f"{results['daily_byproduct_sold']:,.0f}", format_indian_currency(results['daily_revenue']), 
                  format_indian_currency(results['annual_cogs']/365), format_indian_currency(results['gross_profit']/365)],
        "Monthly": [f"{results['monthly_paddy']:,.0f}", f"{results['monthly_poha']:,.0f}", 
                    f"{results['daily_byproduct_gen'] * results['days_per_month']:,.0f}", f"{results['monthly_byproduct_sold']:,.0f}", 
                    format_indian_currency(results['monthly_revenue']), format_indian_currency(results['annual_cogs']/12), 
                    format_indian_currency(results['gross_profit']/12)],
        "Annual": [f"{results['annual_paddy']:,.0f}", f"{results['annual_poha']:,.0f}", 
                   f"{results['daily_byproduct_gen'] * results['days_per_month'] * 12:,.0f}", f"{results['annual_byproduct_sold']:,.0f}", 
                   format_indian_currency(results['annual_revenue']), format_indian_currency(results['annual_cogs']), 
                   format_indian_currency(results['gross_profit'])]
    }
    st.dataframe(pd.DataFrame(summary_data), hide_index=True, use_container_width=True)
    
    st.divider()
    
    # Breakeven analysis
    st.header("💡 Breakeven Analysis")
    rm_cost = results['paddy_rate']
    total_var_cost = rm_cost + results['total_var_cost_per_kg']
    poha_rev = results['poha_price'] * (results['paddy_yield'] / 100)
    byproduct_rev = results['byproduct_rate_kg'] * min(results['byproduct_sale_percent'] / 100, (100 - results['paddy_yield']) / 100)
    rev_per_kg = poha_rev + byproduct_rev
    cm_per_kg = rev_per_kg - total_var_cost
    fixed_costs = results['annual_fixed_opex'] + results['annual_depreciation'] + results['total_interest']
    breakeven_vol = fixed_costs / cm_per_kg if cm_per_kg > 0 else float('inf')
    
    col_be1, col_be2 = st.columns(2)
    with col_be1:
        st.metric("Breakeven Volume (Paddy)", f"{breakeven_vol:,.0f} kg")
        st.metric("Breakeven Revenue", format_indian_currency(breakeven_vol * rev_per_kg if breakeven_vol != float('inf') else 0))
        st.metric("Contribution Margin per kg Paddy", format_indian_currency(cm_per_kg))
    
    with col_be2:
        max_vol = max(results['annual_paddy'], breakeven_vol) * 1.5 if breakeven_vol != float('inf') else results['annual_paddy'] * 1.5
        volumes = np.linspace(0, max_vol, 100)
        revenue_line = volumes * rev_per_kg
        cost_line = fixed_costs + (volumes * total_var_cost)
        be_df = pd.DataFrame({'Paddy Volume (kg)': volumes, 'Total Revenue': revenue_line, 'Total Costs': cost_line})
        fig = px.line(be_df, x='Paddy Volume (kg)', y=['Total Revenue', 'Total Costs'], title="Visual Breakeven Analysis")
        if breakeven_vol != float('inf'):
            fig.add_vline(x=breakeven_vol, line_dash="dash", line_color="red", annotation_text="Breakeven Point")
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Sensitivity analysis
    st.header("🔬 Sensitivity Analysis")
    var_options = ("Poha Selling Price", "Paddy Rate", "Paddy to Poha Yield", "Byproduct Sale %")
    sensitivity_var = st.selectbox("Select variable to analyze:", var_options)
    sensitivity_range = st.slider("Select sensitivity range (% change from base):", -50, 50, (-20, 20))
    
    var_key = {"Poha Selling Price": 'poha_price', "Paddy Rate": 'paddy_rate', 
               "Paddy to Poha Yield": 'paddy_yield', "Byproduct Sale %": 'byproduct_sale_percent'}[sensitivity_var]
    base_val = inputs[var_key]
    range_vals = np.linspace(base_val * (1 + sensitivity_range[0] / 100), base_val * (1 + sensitivity_range[1] / 100), 11)
    
    sens_data = []
    for val in range_vals:
        res = run_financial_model({**inputs, var_key: val})
        net_profit = res.get('net_profit', np.nan)
        sens_data.append({sensitivity_var: val, "Net Profit (Cr)": format_crore(net_profit) if 'error' not in res else "Error", "Net Profit": net_profit})
    
    sens_df = pd.DataFrame(sens_data)
    col_sens1, col_sens2 = st.columns([1.2, 1])
    with col_sens1:
        st.dataframe(sens_df[[sensitivity_var, 'Net Profit (Cr)']], use_container_width=True, hide_index=True)
    with col_sens2:
        plot_df = sens_df.dropna(subset=["Net Profit"])
        if not plot_df.empty:
            fig_sens = px.line(plot_df, x=sensitivity_var, y='Net Profit', title=f"Impact of {sensitivity_var} on Net Profit", markers=True)
            st.plotly_chart(fig_sens, use_container_width=True)
    
    st.divider()
    
    # Financial statements
    col_pnl, col_bs = st.columns([1.2, 1])
    with col_pnl:
        st.header("💰 Annual Profit & Loss Statement")
        pnl_data = {
            "Metric": ["Total Revenue", "COGS", "**Gross Profit**", "Fixed OpEx", "Variable OpEx", "Depreciation", 
                       "**EBIT**", "Total Interest", "**EBT**", "Taxes", "**Net Profit**"],
            "Amount (INR)": [format_indian_currency(results['annual_revenue']), 
                             f"({format_indian_currency(results['annual_cogs'])})",
                             format_indian_currency(results['gross_profit']),
                             f"({format_indian_currency(results['annual_fixed_opex'])})",
                             f"({format_indian_currency(results['annual_var_costs'])})",
                             f"({format_indian_currency(results['annual_depreciation'])})",
                             format_indian_currency(results['ebit']),
                             f"({format_indian_currency(results['total_interest'])})",
                             format_indian_currency(results['ebt']),
                             f"({format_indian_currency(results['taxes'])})",
                             format_indian_currency(results['net_profit'])]
        }
        pnl_df = pd.DataFrame(pnl_data)
        st.dataframe(pnl_df, hide_index=True, use_container_width=True)
        st.download_button("Download P&L as CSV", pnl_df.to_csv(index=False).encode('utf-8'), "poha_pnl.csv", "text/csv")
    
    with col_bs:
        st.header("💼 Balance Sheet & Working Capital")
        bs_data = {
            "Item": ["Total Capex", "Equity Contribution", "Debt Component", "**Total Assets**", "RM Inventory", "FG Inventory",
                     "Receivables", "Payables", "**Net Working Capital**", "**Capital Employed**"],
            "Amount (INR)": [format_indian_currency(results['total_capex']),
                             format_indian_currency(results['equity']),
                             format_indian_currency(results['debt']),
                             format_indian_currency(results['total_assets']),
                             format_indian_currency(results['rm_inventory']),
                             format_indian_currency(results['fg_inventory']),
                             format_indian_currency(results['receivables']),
                             f"({format_indian_currency(results['payables'])})",
                             format_indian_currency(results['net_working_capital']),
                             format_indian_currency(results['capital_employed'])]
        }
        st.dataframe(pd.DataFrame(bs_data), hide_index=True, use_container_width=True)
    
    st.divider()
    
    # Detailed calculations
    st.header("Detailed Calculation Breakdowns")
    with st.expander("Production Flow Details"):
        st.markdown(f"**Daily Paddy Consumption:** `{results['paddy_rate_kg_hr']:,.0f} kg/hr * {results['hours_per_day']} hrs = {results['daily_paddy']:,.0f} kg`")
        st.markdown(f"**Daily Poha Production:** `{results['daily_paddy']:,.0f} kg * {results['paddy_yield']:.1f}% = {results['daily_poha']:,.0f} kg`")
        st.markdown(f"**Daily Byproduct Generated:** `{results['daily_paddy']:,.0f} kg - {results['daily_poha']:,.0f} kg = {results['daily_byproduct_gen']:,.0f} kg`")
        st.markdown(f"**Target Byproduct Sales:** `{results['daily_paddy']:,.0f} kg * {results['byproduct_sale_percent']:.1f}% = {results['daily_byproduct_target']:,.0f} kg`")
        st.markdown(f"**Actual Byproduct Sold:** `min({results['daily_byproduct_target']:,.0f}, {results['daily_byproduct_gen']:,.0f}) = {results['daily_byproduct_sold']:,.0f} kg`")
    
    with st.expander("Revenue Breakdown"):
        poha_rev = results['daily_poha'] * results['poha_price']
        byproduct_rev = results['daily_byproduct_sold'] * results['byproduct_rate_kg']
        st.markdown(f"**Poha Revenue:** `{results['daily_poha']:,.0f} kg * ₹{results['poha_price']:.2f} = {format_indian_currency(poha_rev)}`")
        st.markdown(f"**Byproduct Revenue:** `{results['daily_byproduct_sold']:,.0f} kg * ₹{results['byproduct_rate_kg']:.2f} = {format_indian_currency(byproduct_rev)}`")
        st.markdown(f"**Total Daily Revenue:** `{format_indian_currency(poha_rev)} + {format_indian_currency(byproduct_rev)} = {format_indian_currency(results['daily_revenue'])}`")
    
    with st.expander("Variable Cost Calculation"):
        st.markdown(f"**Packaging Cost:** `₹{results['packaging_cost']:.2f} per kg paddy`")
        st.markdown(f"**Fuel/Power Cost:** `₹{results['fuel_cost']:.2f} per kg paddy`")
        st.markdown(f"**Other Variable Cost:** `₹{results['other_var_cost']:.2f} per kg paddy`")
        st.markdown(f"**Total Variable Cost:** `₹{results['total_var_cost_per_kg']:.2f} per kg paddy`")
        st.markdown(f"**Annual Variable Costs:** `{results['annual_paddy']:,.0f} kg * ₹{results['total_var_cost_per_kg']:.2f} = {format_indian_currency(results['annual_var_costs'])}`")

# Render the dashboard
inputs = render_sidebar()
render_dashboard(inputs)
st.success("Dashboard loaded with responsive sidebar and optimized code!")
