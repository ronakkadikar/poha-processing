import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- Page and Layout Configuration ---
# Set sidebar to be open by default for a static layout experience
st.set_page_config(
    page_title="Poha Manufacturing Dashboard", 
    page_icon="🌾", 
    layout="wide",
    initial_sidebar_state="expanded" 
)

# --- Simplified CSS for a Static, Fixed Layout ---
# This CSS creates a permanent left margin to account for the open sidebar.
# The main content area will no longer shift or resize.
st.markdown("""
<style>
    /* Define a fixed width for the sidebar */
    [data-testid="stSidebar"] {
        width: 320px !important;
        min-width: 320px !important;
    }

    /* Create a fixed margin on the left of the main content area to prevent overlap */
    div.main {
        margin-left: 320px;
    }

    /* General content styling */
    .block-container {
        padding: 1rem 2rem; /* Adjusted padding for better spacing */
        max-width: 100% !important;
    }

    /* Custom metric styling */
    .metric-container {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
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

    /* Warning box */
    .warning-box {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border: 1px solid #f39c12; border-radius: 8px; padding: 1rem;
        margin: 1rem 0; color: #8b4513; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- Utility Functions ---
def format_crore(amount):
    try:
        return f"₹{amount/1e7:,.2f} Cr"
    except:
        return "N/A"

def format_currency(amount):
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
    except:
        return "N/A"

# --- Configuration Dictionaries ---
CONFIG = {
    "Operational": {
        "hours_per_day": {"label": "Production Hours/Day", "type": "number", "min_value": 5, "max_value": 24, "value": 10, "step": 1},
        "days_per_month": {"label": "Operational Days/Month", "type": "number", "min_value": 1, "max_value": 31, "value": 24, "step": 1}
    },
    "Production": {
        "paddy_rate_kg_hr": {"label": "Paddy Rate (kg/hr)", "type": "number", "value": 1000, "step": 10},
        "paddy_yield": {"label": "Poha Yield (%)", "type": "number", "min_value": 50.0, "max_value": 80.0, "value": 65.0, "step": 0.1},
        "byproduct_sale_percent": {"label": "Byproduct Sale (%)", "type": "slider", "min_value": 0.0, "max_value": 40.0, "value": 32.0, "step": 0.1}
    },
    "Pricing": {
        "paddy_rate": {"label": "Paddy Rate (₹/kg)", "type": "number", "value": 22.0, "step": 0.1},
        "poha_price": {"label": "Poha Price (₹/kg)", "type": "number", "value": 45.0, "step": 0.1},
        "byproduct_rate_kg": {"label": "Byproduct Rate (₹/kg)", "type": "number", "value": 7.0, "step": 0.1}
    },
    "Capex": {
        "land_cost": {"label": "Land Cost", "type": "number", "value": 0, "step": 10000},
        "civil_work_cost": {"label": "Civil Work", "type": "number", "value": 0, "step": 10000},
        "machinery_cost": {"label": "Machinery", "type": "number", "value": 7000000, "step": 10000},
        "machinery_useful_life_years": {"label": "Useful Life (Years)", "type": "number", "value": 15, "step": 1}
    },
    "Operating Costs": {
        "packaging_cost": {"label": "Packaging (₹/kg)", "type": "number", "value": 0.5, "step": 0.01},
        "fuel_cost": {"label": "Fuel/Power (₹/kg)", "type": "number", "value": 0.0, "step": 0.01},
        "other_var_cost": {"label": "Other Variable (₹/kg)", "type": "number", "value": 0.0, "step": 0.01},
        "rent_per_month": {"label": "Rent/Month", "type": "number", "value": 300000, "step": 1000},
        "labor_per_month": {"label": "Labor/Month", "type": "number", "value": 400000, "step": 1000},
        "electricity_per_month": {"label": "Electricity/Month", "type": "number", "value": 150000, "step": 1000},
        "security_ssc_insurance_per_month": {"label": "Security & Insurance/Month", "type": "number", "value": 300000, "step": 1000},
        "misc_per_month": {"label": "Misc Overheads/Month", "type": "number", "value": 300000, "step": 1000}
    },
    "Finance": {
        "equity_contrib": {"label": "Equity (%)", "type": "number", "min_value": 0.0, "max_value": 100.0, "value": 30.0, "step": 0.1},
        "interest_rate": {"label": "Interest Rate (%)", "type": "number", "value": 9.0, "step": 0.01},
        "tax_rate_percent": {"label": "Tax Rate (%)", "type": "number", "min_value": 0.0, "max_value": 50.0, "value": 25.0, "step": 0.1}
    },
    "Working Capital": {
        "rm_inventory_days": {"label": "RM Inventory Days", "type": "number", "value": 72, "step": 1},
        "fg_inventory_days": {"label": "FG Inventory Days", "type": "number", "value": 20, "step": 1},
        "debtor_days": {"label": "Debtor Days", "type": "number", "value": 45, "step": 1},
        "creditor_days": {"label": "Creditor Days", "type": "number", "value": 5, "step": 1}
    }
}

RATIOS_INFO = {
    "Revenue": {"formula": "Poha Sales + Byproduct Sales", "explanation": "Total income from all products"},
    "COGS": {"formula": "Paddy Consumption × Paddy Rate", "explanation": "Direct material costs"},
    "Gross Margin": {"formula": "(Revenue - COGS) / Revenue × 100", "explanation": "Profitability after materials"},
    "Contribution Margin": {"formula": "(Revenue - COGS - Variable) / Revenue × 100", "explanation": "Profitability after variable costs"},
    "Net Profit": {"formula": "EBT - Taxes", "explanation": "Final bottom-line profit"},
    "EBITDA": {"formula": "EBIT + Depreciation", "explanation": "Operating profit before non-cash items"},
    "ROCE": {"formula": "(EBIT / Capital Employed) × 100", "explanation": "Return on capital efficiency"},
    "ROE": {"formula": "(Net Profit / Equity) × 100", "explanation": "Return to shareholders"}
}

# --- Sidebar Rendering ---
def render_sidebar():
    inputs = {}
    st.sidebar.header("⚙️ Parameters")
    for section, params in CONFIG.items():
        with st.sidebar.expander(section, expanded=True):
            for key, config in params.items():
                config_copy = config.copy()
                input_type = config_copy.pop("type")
                if input_type == "number":
                    inputs[key] = st.number_input(**config_copy)
                elif input_type == "slider":
                    inputs[key] = st.slider(**config_copy)
    return inputs

# --- Financial Calculation Engine ---
def calculate_financials(inputs):
    total_capex = inputs['land_cost'] + inputs['civil_work_cost'] + inputs['machinery_cost']
    if any(v <= 0 for v in [inputs['paddy_yield'], inputs['poha_price'], total_capex]):
        return {'error': 'Invalid inputs: Yield, Price, and Capex must be > 0'}
    
    daily_paddy = inputs['paddy_rate_kg_hr'] * inputs['hours_per_day']
    monthly_paddy = daily_paddy * inputs['days_per_month']
    annual_paddy = monthly_paddy * 12
    daily_poha = daily_paddy * (inputs['paddy_yield'] / 100)
    monthly_poha = daily_poha * inputs['days_per_month']
    annual_poha = monthly_poha * 12
    daily_byproduct_target = daily_paddy * (inputs['byproduct_sale_percent'] / 100)
    daily_byproduct_gen = daily_paddy - daily_poha
    daily_byproduct_sold = min(daily_byproduct_target, daily_byproduct_gen)
    monthly_byproduct_sold = daily_byproduct_sold * inputs['days_per_month']
    annual_byproduct_sold = monthly_byproduct_sold * 12
    byproduct_limit_hit = daily_byproduct_target > daily_byproduct_gen
    daily_revenue = (daily_poha * inputs['poha_price']) + (daily_byproduct_sold * inputs['byproduct_rate_kg'])
    monthly_revenue = daily_revenue * inputs['days_per_month']
    annual_revenue = monthly_revenue * 12
    annual_cogs = annual_paddy * inputs['paddy_rate']
    gross_profit = annual_revenue - annual_cogs
    var_cost_per_kg = inputs['packaging_cost'] + inputs['fuel_cost'] + inputs['other_var_cost']
    annual_var_costs = annual_paddy * var_cost_per_kg
    monthly_fixed_opex = sum([inputs[k] for k in ['rent_per_month', 'labor_per_month', 'electricity_per_month', 
                                                  'security_ssc_insurance_per_month', 'misc_per_month']])
    annual_fixed_opex = monthly_fixed_opex * 12
    total_opex = annual_fixed_opex + annual_var_costs
    annual_depreciation = (inputs['machinery_cost'] + inputs['civil_work_cost']) / inputs['machinery_useful_life_years'] if inputs['machinery_useful_life_years'] > 0 else 0
    ebit = gross_profit - total_opex - annual_depreciation
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
    equity = total_capex * (inputs['equity_contrib'] / 100)
    debt = total_capex - equity
    interest_fixed = debt * (inputs['interest_rate'] / 100)
    interest_wc = max(0, net_working_capital) * (inputs['interest_rate'] / 100)
    total_interest = interest_fixed + interest_wc
    ebt = ebit - total_interest
    taxes = max(0, ebt) * (inputs['tax_rate_percent'] / 100)
    net_profit = ebt - taxes
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
        **inputs, 'total_capex': total_capex, 'daily_paddy': daily_paddy, 'monthly_paddy': monthly_paddy, 
        'annual_paddy': annual_paddy, 'daily_poha': daily_poha, 'monthly_poha': monthly_poha, 'annual_poha': annual_poha,
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

# --- Reusable Metric Component ---
def custom_metric(col, label, value, sub_value, info_key):
    formula, explanation = RATIOS_INFO[info_key].values()
    try:
        # Handle cases where sub_value might be empty string
        numeric_str = str(sub_value).replace('%', '').replace(' Margin', '').replace('₹', '').replace(',', '').strip()
        numeric_value = float(numeric_str) if numeric_str else 0
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

# --- Main Dashboard Rendering ---
def render_dashboard(inputs):
    results = calculate_financials(inputs)
    
    if 'error' in results:
        st.error(results['error'])
        return
    
    if results['byproduct_limit_hit']:
        st.markdown(f"""
        <div class="warning-box">
            <strong>⚠️ Byproduct Constraint:</strong> Trying to sell {results['byproduct_sale_percent']:.1f}% 
            ({results['daily_byproduct_target']:,.0f} kg/day) but only {results['daily_byproduct_gen']:,.0f} kg/day is generated.
            <br><strong>Suggestion:</strong> Reduce 'Byproduct Sale %' in the sidebar to be less than the available amount.
        </div>
        """, unsafe_allow_html=True)
    
    st.header("📈 Key Performance Indicators")
    
    # Reorganized KPI grid into 3 rows (3-3-2)
    row1_col1, row1_col2, row1_col3 = st.columns(3)
    custom_metric(row1_col1, "Revenue", format_currency(results['annual_revenue']), "", "Revenue")
    custom_metric(row1_col2, "COGS", format_currency(results['annual_cogs']), "", "COGS")
    custom_metric(row1_col3, "Gross Margin", f"{results['gross_margin']:.1f}%", format_currency(results['gross_profit']), "Gross Margin")
    
    row2_col1, row2_col2, row2_col3 = st.columns(3)
    custom_metric(row2_col1, "Contribution Margin", f"{results['contribution_margin_pct']:.1f}%", format_currency(results['contribution_margin']), "Contribution Margin")
    custom_metric(row2_col2, "Net Profit", format_currency(results['net_profit']), f"{results['net_profit_margin']:.1f}% Margin", "Net Profit")
    custom_metric(row2_col3, "EBITDA", format_currency(results['ebitda']), f"{results['ebitda_margin']:.1f}% Margin", "EBITDA")

    row3_col1, row3_col2, _ = st.columns(3) # Use 3 columns to align with rows above
    custom_metric(row3_col1, "ROCE", f"{results['roce']:.1f}%", "", "ROCE")
    custom_metric(row3_col2, "ROE", f"{results['roe']:.1f}%", "", "ROE")
    
    st.divider()
    
    st.header("📊 Production & Financial Summary")
    summary_data = {
        "Metric": ["Paddy Consumption (kg)", "Poha Production (kg)", "Byproduct Generated (kg)", "Byproduct Sold (kg)", "Total Revenue", "COGS", "Gross Profit"],
        "Daily": [f"{results['daily_paddy']:,.0f}", f"{results['daily_poha']:,.0f}", f"{results['daily_byproduct_gen']:,.0f}", f"{results['daily_byproduct_sold']:,.0f}", format_currency(results['daily_revenue']), format_currency(results['annual_cogs']/365), format_currency(results['gross_profit']/365)],
        "Monthly": [f"{results['monthly_paddy']:,.0f}", f"{results['monthly_poha']:,.0f}", f"{results['daily_byproduct_gen'] * results['days_per_month']:,.0f}", f"{results['monthly_byproduct_sold']:,.0f}", format_currency(results['monthly_revenue']), format_currency(results['annual_cogs']/12), format_currency(results['gross_profit']/12)],
        "Annual": [f"{results['annual_paddy']:,.0f}", f"{results['annual_poha']:,.0f}", f"{results['daily_byproduct_gen'] * results['days_per_month'] * 12:,.0f}", f"{results['annual_byproduct_sold']:,.0f}", format_currency(results['annual_revenue']), format_currency(results['annual_cogs']), format_currency(results['gross_profit'])]
    }
    
    # Using column_config to adjust DataFrame column widths
    st.dataframe(
        pd.DataFrame(summary_data), 
        hide_index=True, 
        use_container_width=True,
        column_config={
            "Metric": st.column_config.Column(width="medium"),
            "Daily": st.column_config.Column(width="small"),
            "Monthly": st.column_config.Column(width="small"),
            "Annual": st.column_config.Column(width="small"),
        }
    )
    
    st.divider()
    
    st.header("💡 Breakeven Analysis")
    col_be_select, _ = st.columns([1, 2])
    with col_be_select:
        breakeven_metric = st.selectbox("Select Breakeven Metric:", ["EBITDA", "Net Profit (PAT)"])
    
    rm_cost = results['paddy_rate']
    total_var_cost = rm_cost + results['total_var_cost_per_kg']
    poha_rev = results['poha_price'] * (results['paddy_yield'] / 100)
    byproduct_rev = results['byproduct_rate_kg'] * min(results['byproduct_sale_percent'] / 100, (100 - results['paddy_yield']) / 100)
    rev_per_kg = poha_rev + byproduct_rev
    contribution_per_kg = rev_per_kg - total_var_cost
    
    if breakeven_metric == "EBITDA":
        fixed_costs = results['annual_fixed_opex']
        target_metric = "EBITDA"
    else:
        fixed_costs = results['annual_fixed_opex'] + results['annual_depreciation'] + results['total_interest']
        target_metric = "Net Profit"
    
    breakeven_vol = fixed_costs / contribution_per_kg if contribution_per_kg > 0 else float('inf')
    
    col_be1, col_be2 = st.columns(2)
    with col_be1:
        st.metric(f"Breakeven Volume ({target_metric})", f"{breakeven_vol:,.0f} kg Paddy/Year")
        st.metric("Breakeven Revenue", format_currency(breakeven_vol * rev_per_kg if breakeven_vol != float('inf') else 0))
        st.metric("Contribution per kg Paddy", format_currency(contribution_per_kg))
    
    with col_be2:
        max_vol = max(results['annual_paddy'], breakeven_vol) * 1.5 if breakeven_vol != float('inf') else results['annual_paddy'] * 1.5
        volumes = np.linspace(0, max_vol, 100)
        revenue_line = volumes * rev_per_kg
        cost_line = fixed_costs + (volumes * total_var_cost)
        be_df = pd.DataFrame({'Paddy Volume (kg)': volumes, 'Total Revenue': revenue_line, 'Total Costs': cost_line})
        fig = px.line(be_df, x='Paddy Volume (kg)', y=['Total Revenue', 'Total Costs'], title=f"Breakeven Analysis - {target_metric}")
        if breakeven_vol != float('inf') and breakeven_vol < max_vol:
            fig.add_vline(x=breakeven_vol, line_dash="dash", line_color="red", annotation_text="Breakeven")
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    st.header("🔬 Sensitivity Analysis")
    var_options = ("Poha Selling Price", "Paddy Rate", "Paddy to Poha Yield", "Byproduct Sale %")
    sensitivity_var = st.selectbox("Variable to analyze:", var_options)
    sensitivity_range = st.slider("Sensitivity range (% change):", -50, 50, (-20, 20))
    
    var_key = {"Poha Selling Price": 'poha_price', "Paddy Rate": 'paddy_rate', 
               "Paddy to Poha Yield": 'paddy_yield', "Byproduct Sale %": 'byproduct_sale_percent'}[sensitivity_var]
    base_val = inputs[var_key]
    range_vals = np.linspace(base_val * (1 + sensitivity_range[0] / 100), base_val * (1 + sensitivity_range[1] / 100), 11)
    
    sens_data = []
    for val in range_vals:
        res = calculate_financials({**inputs, var_key: val})
        net_profit = res.get('net_profit', np.nan)
        sens_data.append({sensitivity_var: val, "Net Profit (Cr)": format_crore(net_profit) if 'error' not in res else "Error", "Net Profit": net_profit})
    
    sens_df = pd.DataFrame(sens_data)
    col_sens1, col_sens2 = st.columns([1, 1.2])
    with col_sens1:
        st.dataframe(sens_df[[sensitivity_var, 'Net Profit (Cr)']], use_container_width=True, hide_index=True)
    with col_sens2:
        plot_df = sens_df.dropna(subset=["Net Profit"])
        if not plot_df.empty:
            fig_sens = px.line(plot_df, x=sensitivity_var, y='Net Profit', title=f"Impact of {sensitivity_var} on Net Profit", markers=True)
            st.plotly_chart(fig_sens, use_container_width=True)
    
    st.divider()
    
    col_pnl, col_bs = st.columns([1.2, 1])
    with col_pnl:
        st.header("💰 Profit & Loss Statement")
        pnl_data = {
            "Metric": ["Total Revenue", "COGS", "**Gross Profit**", "Fixed OpEx", "Variable OpEx", "Depreciation", "**EBIT**", "Total Interest", "**EBT**", "Taxes", "**Net Profit**"],
            "Amount (INR)": [format_currency(results['annual_revenue']), f"({format_currency(results['annual_cogs'])})", format_currency(results['gross_profit']),
                             f"({format_currency(results['annual_fixed_opex'])})", f"({format_currency(results['annual_var_costs'])})",
                             f"({format_currency(results['annual_depreciation'])})", format_currency(results['ebit']),
                             f"({format_currency(results['total_interest'])})", format_currency(results['ebt']),
                             f"({format_currency(results['taxes'])})", format_currency(results['net_profit'])]
        }
        pnl_df = pd.DataFrame(pnl_data)
        st.dataframe(pnl_df, hide_index=True, use_container_width=True, column_config={"Metric": st.column_config.Column(width="medium"), "Amount (INR)": st.column_config.Column(width="small")})
        st.download_button("📥 Download P&L", pnl_df.to_csv(index=False).encode('utf-8'), "poha_pnl.csv", "text/csv")
    
    with col_bs:
        st.header("💼 Balance Sheet")
        bs_data = {
            "Item": ["Total Capex", "Equity", "Debt", "**Total Assets**", "RM Inventory", "FG Inventory", "Receivables", "Payables", "**Net Working Capital**", "**Capital Employed**"],
            "Amount (INR)": [format_currency(results['total_capex']), format_currency(results['equity']), format_currency(results['debt']), format_currency(results['total_assets']),
                             format_currency(results['rm_inventory']), format_currency(results['fg_inventory']),
                             format_currency(results['receivables']), f"({format_currency(results['payables'])})",
                             format_currency(results['net_working_capital']), format_currency(results['capital_employed'])]
        }
        st.dataframe(pd.DataFrame(bs_data), hide_index=True, use_container_width=True, column_config={"Item": st.column_config.Column(width="medium"), "Amount (INR)": st.column_config.Column(width="small")})
    
    st.divider()
    
    st.header("🔍 Detailed Calculation Breakdowns")
    with st.expander("Production Flow Analysis"):
        st.markdown(f"**Daily Paddy Processing:** `{results['paddy_rate_kg_hr']:,.0f} kg/hr × {results['hours_per_day']} hrs = {results['daily_paddy']:,.0f} kg`")
        st.markdown(f"**Daily Poha Output:** `{results['daily_paddy']:,.0f} kg × {results['paddy_yield']:.1f}% = {results['daily_poha']:,.0f} kg`")
    with st.expander("Revenue Structure"):
        poha_rev = results['daily_poha'] * results['poha_price']
        byproduct_rev = results['daily_byproduct_sold'] * results['byproduct_rate_kg']
        st.markdown(f"**Poha Revenue:** `{results['daily_poha']:,.0f} kg × ₹{results['poha_price']:.2f} = {format_currency(poha_rev)}`")
    with st.expander("Cost Structure Analysis"):
        st.markdown(f"**Raw Material Cost:** `₹{results['paddy_rate']:.2f}/kg × {results['annual_paddy']:,.0f} kg = {format_currency(results['annual_cogs'])}`")
    with st.expander("Working Capital Details"):
        st.markdown(f"**Net Working Capital:** `{format_currency(results['current_assets'])} - {format_currency(results['payables'])} = {format_currency(results['net_working_capital'])}`")
    with st.expander("Financial Ratios & Returns"):
        st.markdown(f"**ROCE:** `{format_currency(results['ebit'])} ÷ {format_currency(results['capital_employed'])} = {results['roce']:.1f}%`")
    with st.expander("Financing Structure"):
        st.markdown(f"**Total Capital Requirement:** {format_currency(results['total_capex'] + results['net_working_capital'])}")

# --- Main Execution ---
inputs = render_sidebar()
render_dashboard(inputs)
st.success("✅ Dashboard loaded successfully with a static layout!")
