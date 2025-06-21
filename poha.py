import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import math

def format_indian_currency(amount):
    if not isinstance(amount, (int, float)) or pd.isna(amount) or math.isinf(amount):
        return "N/A"
    s = f"{abs(amount):.2f}"
    i, d = s.split('.')
    if len(i) > 3:
        last3, rem = i[-3:], i[:-3]
        groups = [rem[max(0, j-2):j] for j in range(len(rem), 0, -2)]
        groups.reverse()
        i = ','.join(groups) + ',' + last3
    return f"₹{'-' + i if amount < 0 else i}"

def format_crore(amount):
    try:
        return f"₹{amount/1e7:,.2f} Cr"
    except:
        return "N/A"

st.set_page_config(page_title="Poha Manufacturing Financial Dashboard", page_icon="🌾", layout="wide")

# Optimized CSS
st.markdown("""
<style>
    [data-testid="stSidebar"] { position: relative !important; left: 0 !important; margin-left: 0 !important; width: 350px !important; min-width: 350px !important; }
    [data-testid="stSidebar"][aria-expanded="false"] { width: 50px !important; min-width: 50px !important; }
    .main .block-container { padding: 1rem; max-width: none; overflow-x: auto; }
    .metric-container { background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0; min-height: 120px; display: flex; flex-direction: column; justify-content: space-between; }
    .metric-title { font-size: 0.875rem; color: #262730; margin-bottom: 0.25rem; }
    .metric-value { font-size: 1.25rem; font-weight: bold; color: #262730; margin-bottom: 0.25rem; word-wrap: break-word; }
    .metric-delta { font-size: 0.75rem; margin-top: 0.25rem; word-wrap: break-word; }
    .tooltip { position: relative; display: inline-block; cursor: pointer; }
    .tooltip .tooltiptext { visibility: hidden; width: 250px; background-color: #555; color: white; text-align: left; border-radius: 6px; padding: 8px; position: absolute; z-index: 1; bottom: 125%; left: 50%; margin-left: -125px; opacity: 0; transition: opacity 0.3s; font-size: 11px; line-height: 1.3; }
    .tooltip:hover .tooltiptext { visibility: visible; opacity: 1; }
    .warning-box { background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 0.5rem; padding: 1rem; margin: 1rem 0; color: #856404; }
    .summary-table { max-width: 900px; margin: auto; }
</style>
""", unsafe_allow_html=True)

# Optimized sidebar inputs
st.sidebar.header("⚙️ Input Parameters")
inputs = {}

# Streamlined input collection
sidebar_sections = [
    ("Operational Assumptions", [("hours_per_day", "Production Hours per Day", 5, 24, 10), ("days_per_month", "Operational Days per Month", 1, 31, 24)]),
    ("Production & Yield", [("paddy_rate_kg_hr", "Paddy Processing Rate (kg/hr)", 100, 5000, 1000, 10), ("paddy_yield", "Paddy to Poha Yield (%)", 50.0, 80.0, 65.0, 0.1)]),
    ("Financial Assumptions (INR)", [("paddy_rate", "Paddy Rate (INR/kg)", 0.1, 100.0, 22.0, 0.1), ("poha_price", "Poha Selling Price (INR/kg)", 0.1, 100.0, 45.0, 0.1), ("byproduct_rate_kg", "Byproduct Rate (INR/kg)", 0.0, 50.0, 7.0, 0.1)]),
    ("Capital Expenditure (Capex)", [("land_cost", "Land Cost", 0, 10000000, 0, 10000), ("civil_work_cost", "Civil Work Cost", 0, 10000000, 0, 10000), ("machinery_cost", "Machinery Cost", 0, 50000000, 7000000, 10000), ("machinery_useful_life_years", "Useful Life (Years)", 1, 50, 15)]),
    ("Operating Costs", [("packaging_cost", "Packaging Material (per kg paddy)", 0.0, 10.0, 0.5, 0.01), ("fuel_cost", "Fuel/Power Variable (per kg paddy)", 0.0, 10.0, 0.0, 0.01), ("other_var_cost", "Other Variable Costs (per kg paddy)", 0.0, 10.0, 0.0, 0.01), ("rent_per_month", "Rent", 0, 2000000, 300000, 1000), ("labor_per_month", "Labor Wages and Salaries", 0, 2000000, 400000, 1000), ("electricity_per_month", "Electricity (Fixed)", 0, 1000000, 150000, 1000), ("security_ssc_insurance_per_month", "Security, SSC & Insurance", 0, 1000000, 300000, 1000), ("misc_per_month", "Misc Overheads", 0, 1000000, 300000, 1000)]),
    ("Funding & Tax", [("equity_contrib", "Equity Contribution (%)", 0.0, 100.0, 30.0, 0.1), ("interest_rate", "Interest Rate (%)", 0.0, 50.0, 9.0, 0.01), ("tax_rate_percent", "Corporate Tax Rate (%)", 0.0, 50.0, 25.0, 0.1)]),
    ("Working Capital Days", [("rm_inventory_days", "Raw Material Inventory Days", 0, 365, 72), ("fg_inventory_days", "Finished Goods Inventory Days", 0, 365, 20), ("debtor_days", "Debtor Days (Receivables)", 0, 365, 45), ("creditor_days", "Creditor Days (Payables)", 0, 365, 5)])
]

for section, fields in sidebar_sections:
    with st.sidebar.expander(section, expanded=True):
        for field in fields:
            if len(field) == 5:
                inputs[field[0]] = st.number_input(field[1], field[2], field[3], field[4])
            else:
                inputs[field[0]] = st.number_input(field[1], field[2], field[3], field[4], field[5])

# Special slider for byproduct
with st.sidebar.expander("Production & Yield", expanded=False):
    inputs['byproduct_sale_percent'] = st.slider("Byproduct Sold (% of Paddy Input)", 0.0, 40.0, 32.0, 0.1, help="Percentage of original paddy input sold as byproduct")

# Optimized financial model
def run_financial_model(i):
    capex = i['land_cost'] + i['civil_work_cost'] + i['machinery_cost']
    if any(x <= 0 for x in [i['paddy_yield'], i['poha_price'], capex]):
        return {'error': 'Paddy Yield, Poha Price, and Capex must be greater than 0.'}
    
    # Production calculations (optimized variable names)
    dpc, mpc, apc = i['paddy_rate_kg_hr'] * i['hours_per_day'], 0, 0
    mpc, apc = dpc * i['days_per_month'], dpc * i['days_per_month'] * 12
    dpp, mpp, app = dpc * (i['paddy_yield'] / 100), 0, 0
    mpp, app = dpp * i['days_per_month'], dpp * i['days_per_month'] * 12
    
    # Byproduct calculations
    dbs_target, dbg = dpc * (i['byproduct_sale_percent'] / 100), dpc - dpp
    dbs, mbs, absold = min(dbs_target, dbg), 0, 0
    mbs, absold = dbs * i['days_per_month'], dbs * i['days_per_month'] * 12
    byproduct_limit_hit = dbs_target > dbg
    
    # Revenue and costs
    tdr = (dpp * i['poha_price']) + (dbs * i['byproduct_rate_kg'])
    tmr, tar = tdr * i['days_per_month'], tdr * i['days_per_month'] * 12
    acogs, agp = apc * i['paddy_rate'], tar - apc * i['paddy_rate']
    
    # Operating costs
    tvc_kg = i['packaging_cost'] + i['fuel_cost'] + i['other_var_cost']
    avoc = apc * tvc_kg
    tmfo = sum([i['rent_per_month'], i['labor_per_month'], i['electricity_per_month'], i['security_ssc_insurance_per_month'], i['misc_per_month']])
    afoc, toe = tmfo * 12, tmfo * 12 + avoc
    tad = (i['machinery_cost'] + i['civil_work_cost']) / i['machinery_useful_life_years']
    ebit = agp - toe - tad
    
    # Working capital
    dcb, dcop, drb = acogs / 365, (acogs + avoc) / app, tar / 365
    rmiv, fgiv = dcb * i['rm_inventory_days'], dpp * dcop * i['fg_inventory_days']
    ar, ap = drb * i['debtor_days'], dcb * i['creditor_days']
    tca, tcl, nwc = rmiv + fgiv + ar, ap, rmiv + fgiv + ar - ap
    
    # Financing
    iec, tdc = capex * (i['equity_contrib'] / 100), capex * (1 - i['equity_contrib'] / 100)
    aief, iowc = tdc * (i['interest_rate'] / 100), max(0, nwc) * (i['interest_rate'] / 100)
    aie, ebt = aief + iowc, ebit - aief - iowc
    tax, np = max(0, ebt) * (i['tax_rate_percent'] / 100), ebt - max(0, ebt) * (i['tax_rate_percent'] / 100)
    
    # Ratios
    tafr, ce = capex + tca, capex + tca - tcl
    roce = (ebit / ce) * 100 if ce != 0 else float('inf')
    npm, ebitda = (np / tar) * 100 if tar > 0 else 0, ebit + tad
    ebitda_m = (ebitda / tar) * 100 if tar > 0 else 0
    roe, gpm = (np / iec) * 100 if iec > 0 else float('inf'), (agp / tar) * 100 if tar > 0 else 0
    cm, cmp = agp - avoc, ((agp - avoc) / tar) * 100 if tar > 0 else 0
    
    # Breakeven
    rm_cost_kg = i['paddy_rate']
    tvc_kg_total = rm_cost_kg + tvc_kg
    prp_kg = i['poha_price'] * (i['paddy_yield'] / 100)
    brp_kg = i['byproduct_rate_kg'] * min(i['byproduct_sale_percent'] / 100, (100 - i['paddy_yield']) / 100)
    rp_kg = prp_kg + brp_kg
    cmp_kg = rp_kg - tvc_kg_total
    tfc_be = afoc + tad + aie
    bev_kg = tfc_be / cmp_kg if cmp_kg > 0 else float('inf')
    
    return {**i, **{k: v for k, v in locals().items() if not k.startswith('i')}}

# Key ratios info (shortened)
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

# Run model
results = run_financial_model(inputs)

if 'error' in results:
    st.error(results['error'])
else:
    # Warning display
    if results.get('byproduct_limit_hit', False):
        st.markdown(f"""
        <div class="warning-box">
            <strong>⚠️ Byproduct Constraint Warning:</strong><br>
            You're trying to sell {results['byproduct_sale_percent']:.1f}% of paddy input as byproduct 
            ({results['dbs_target']:,.0f} kg/day), but only {results['dbg']:,.0f} kg/day 
            is available after poha production. Sales capped at maximum available.
        </div>
        """, unsafe_allow_html=True)

    # KPIs in 3 rows (OPTIMIZED LAYOUT)
    st.header("📈 Key Performance Indicators (Annual)")
    
    # Row 1: 3 columns
    col1, col2, col3 = st.columns(3)
    custom_metric(col1, "Revenue", format_indian_currency(results['tar']), "", "Revenue")
    custom_metric(col2, "COGS", format_indian_currency(results['acogs']), "", "COGS")
    custom_metric(col3, "Gross Margin", f"{results['gpm']:.1f}%", format_indian_currency(results['agp']), "Gross Margin")
    
    # Row 2: 3 columns
    col4, col5, col6 = st.columns(3)
    custom_metric(col4, "Contribution Margin", f"{results['cmp']:.1f}%", format_indian_currency(results['cm']), "Contribution Margin")
    custom_metric(col5, "Net Profit", format_indian_currency(results['np']), f"{results['npm']:.1f}% Margin", "Net Profit")
    custom_metric(col6, "EBITDA", format_indian_currency(results['ebitda']), f"{results['ebitda_m']:.1f}% Margin", "EBITDA")
    
    # Row 3: 2 columns
    col7, col8 = st.columns(2)
    custom_metric(col7, "ROCE", f"{results['roce']:.1f}%", "", "ROCE")
    custom_metric(col8, "ROE", f"{results['roe']:.1f}%", "", "ROE")
    
    st.divider()
    
    # REDUCED WIDTH SUMMARY TABLE
    st.header("📊 Daily, Monthly, and Annual Summary")
    summary_data = {
        "Metric": ["Paddy Consumption (kg)", "Poha Production (kg)", "Byproduct Generated (kg)", "Byproduct Sold (kg)", "Total Revenue", "COGS", "Gross Profit"],
        "Daily": [f"{results['dpc']:,.0f}", f"{results['dpp']:,.0f}", f"{results['dbg']:,.0f}", f"{results['dbs']:,.0f}", format_indian_currency(results['tdr']), format_indian_currency(results['acogs']/365), format_indian_currency(results['agp']/365)],
        "Monthly": [f"{results['mpc']:,.0f}", f"{results['mpp']:,.0f}", f"{results['dbg'] * results['days_per_month']:,.0f}", f"{results['mbs']:,.0f}", format_indian_currency(results['tmr']), format_indian_currency(results['acogs']/12), format_indian_currency(results['agp']/12)],
        "Annual": [f"{results['apc']:,.0f}", f"{results['app']:,.0f}", f"{results['dbg'] * results['days_per_month'] * 12:,.0f}", f"{results['absold']:,.0f}", format_indian_currency(results['tar']), format_indian_currency(results['acogs']), format_indian_currency(results['agp'])]
    }
    
    st.markdown('<div class="summary-table">', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(summary_data), hide_index=True, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # ADJUSTED BREAKEVEN ANALYSIS LAYOUT
    st.header("💡 Breakeven Analysis")
    col1, col2 = st.columns([1.3, 0.7])  # Move graph closer to text
    
    with col1:
        st.metric("Breakeven Volume (Paddy)", f"{results['bev_kg']:,.0f} kg")
        st.metric("Breakeven Revenue", format_indian_currency(results['bev_kg'] * results['rp_kg']))
        st.metric("Contribution Margin per kg Paddy", format_indian_currency(results['cmp_kg']))
    
    with col2:
        max_prod = results.get('apc', 0)
        max_vol = max(max_prod, results['bev_kg']) * 1.5 if results['bev_kg'] != float('inf') else max_prod * 1.5
        vols = np.linspace(0, max_vol, 100)
        rev_line = vols * results['rp_kg']
        cost_line = results['tfc_be'] + (vols * results['tvc_kg_total'])
        be_df = pd.DataFrame({'Paddy Volume (kg)': vols, 'Total Revenue': rev_line, 'Total Costs': cost_line})
        fig = px.line(be_df, x='Paddy Volume (kg)', y=['Total Revenue', 'Total Costs'], title="Visual Breakeven Analysis", markers=True)
        if results['bev_kg'] != float('inf'):
            fig.add_vline(x=results['bev_kg'], line_dash="dash", line_color="red", annotation_text="Breakeven Point")
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Sensitivity analysis (kept compact)
    st.header("🔬 Sensitivity Analysis")
    sensitivity_variable = st.selectbox("Select variable to analyze:", ("Poha Selling Price", "Paddy Rate", "Paddy to Poha Yield", "Byproduct Sale %"))
    sensitivity_range = st.slider("Select sensitivity range (% change from base):", -50, 50, (-20, 20))
    
    base_value_map = {"Poha Selling Price": 'poha_price', "Paddy Rate": 'paddy_rate', "Paddy to Poha Yield": 'paddy_yield', "Byproduct Sale %": 'byproduct_sale_percent'}
    var_key = base_value_map[sensitivity_variable]
    base_value = inputs[var_key]
    
    range_values = np.linspace(base_value * (1 + sensitivity_range[0] / 100), base_value * (1 + sensitivity_range[1] / 100), 11)
    sensitivity_results_list = [run_financial_model({**inputs, var_key: val}) for val in range_values]
    
    sensitivity_data = []
    for val, res in zip(range_values, sensitivity_results_list):
        if 'error' in res:
            net_profit_str, net_profit_num = "Error", np.nan
        else:
            net_profit_str, net_profit_num = format_crore(res['np']), res['np']
        sensitivity_data.append({sensitivity_variable: val, "Net Profit (Cr)": net_profit_str, "Net Profit": net_profit_num})
    
    sensitivity_df = pd.DataFrame(sensitivity_data)
    col_sens1, col_sens2 = st.columns([1.2, 1])
    
    with col_sens1:
        st.dataframe(sensitivity_df[[sensitivity_variable, 'Net Profit (Cr)']], use_container_width=True, hide_index=True)
    
    with col_sens2:
        plot_df = sensitivity_df.dropna(subset=["Net Profit"])
        fig_sens = px.line(plot_df, x=sensitivity_variable, y='Net Profit', title=f"Impact of {sensitivity_variable} on Net Profit", markers=True, labels={'Net Profit': 'Net Profit (INR)'})
        st.plotly_chart(fig_sens, use_container_width=True)
    
    st.divider()
    
    # REDUCED WIDTH FINANCIAL STATEMENTS
    col_pnl, col_bs = st.columns([1.3, 0.7])  # Adjusted widths
    
    with col_pnl:
        st.header("💰 Annual Profit & Loss Statement")
        pnl_data = {
            "Metric": ["Total Revenue", "COGS", "**Gross Profit**", "Fixed OpEx", "Variable OpEx", "Depreciation", "**EBIT**", "Total Interest", "**EBT**", "Taxes", "**Net Profit**"],
            "Amount (INR)": [format_indian_currency(results['tar']), f"({format_indian_currency(results['acogs'])})", f"**{format_indian_currency(results['agp'])}**", f"({format_indian_currency(results['afoc'])})", f"({format_indian_currency(results['avoc'])})", f"({format_indian_currency(results['tad'])})", f"**{format_indian_currency(results['ebit'])}**", f"({format_indian_currency(results['aie'])})", f"**{format_indian_currency(results['ebt'])}**", f"({format_indian_currency(results['tax'])})", f"**{format_indian_currency(results['np'])}**"]
        }
        pnl_df = pd.DataFrame(pnl_data)
        st.dataframe(pnl_df, hide_index=True, use_container_width=True)
        st.download_button("Download P&L as CSV", pnl_df.to_csv(index=False).encode('utf-8'), "poha_pnl.csv", "text/csv")
    
    with col_bs:
        st.header("💼 Balance Sheet & Working Capital")
        bs_data = {
            "Item": ["Total Capex", "Equity Contribution", "Debt Component", "**Total Assets**", "RM Inventory", "FG Inventory", "Receivables", "Payables", "**Net Working Capital**", "**Capital Employed**"],
            "Amount (INR)": [format_indian_currency(results['capex']), format_indian_currency(results['iec']), format_indian_currency(results['tdc']), f"**{format_indian_currency(results['tafr'])}**", format_indian_currency(results['rmiv']), format_indian_currency(results['fgiv']), format_indian_currency(results['ar']), f"({format_indian_currency(results['ap'])})", f"**{format_indian_currency(results['nwc'])}**", f"**{format_indian_currency(results['ce'])}**"]
        }
        st.dataframe(pd.DataFrame(bs_data), hide_index=True, use_container_width=True)
    
    st.divider()
    
    # Compact detailed calculations
    st.header("Detailed Calculation Breakdowns")
    with st.expander("Production Flow Details"):
        st.markdown(f"**Daily Paddy:** `{results['paddy_rate_kg_hr']:,.0f} kg/hr × {results['hours_per_day']} hrs = {results['dpc']:,.0f} kg`")
        st.markdown(f"**Daily Poha:** `{results['dpc']:,.0f} kg × {results['paddy_yield']:.1f}% = {results['dpp']:,.0f} kg`")
        st.markdown(f"**Daily Byproduct Generated:** `{results['dpc']:,.0f} - {results['dpp']:,.0f} = {results['dbg']:,.0f} kg`")
        st.markdown(f"**Actual Byproduct Sold:** `min({results['dbs_target']:,.0f}, {results['dbg']:,.0f}) = {results['dbs']:,.0f} kg`")
    
    with st.expander("Revenue & Cost Breakdown"):
        dpr, dbr = results['dpp'] * results['poha_price'], results['dbs'] * results['byproduct_rate_kg']
        st.markdown(f"**Daily Poha Revenue:** `{results['dpp']:,.0f} kg × ₹{results['poha_price']:.2f} = {format_indian_currency(dpr)}`")
        st.markdown(f"**Daily Byproduct Revenue:** `{results['dbs']:,.0f} kg × ₹{results['byproduct_rate_kg']:.2f} = {format_indian_currency(dbr)}`")
        st.markdown(f"**Total Variable Cost:** `₹{results['tvc_kg']:.2f} per kg paddy`")
        st.markdown(f"**Annual Variable Costs:** `{results['apc']:,.0f} kg × ₹{results['tvc_kg']:.2f} = {format_indian_currency(results['avoc'])}`")

st.success("Dashboard loaded successfully with optimized layout and reduced code length!")
