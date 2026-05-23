import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Carbon Estimator",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 Supply Chain Carbon Estimator")

CATEGORIES    = ['Raw Materials','Manufacturing','Logistics','Energy','Services']
SUBCATEGORIES = {
    'Raw Materials':  ['Steel','Aluminum','Plastic','Cotton','Wood','Glass','Rubber','Copper'],
    'Manufacturing':  ['Electronics','Textiles','Automotive','Food Processing','Chemicals','Packaging','Furniture'],
    'Logistics':      ['Sea Freight','Air Freight','Road Freight','Rail Freight'],
    'Energy':         ['Coal Power','Natural Gas','Renewable','Nuclear'],
    'Services':       ['Data Centers','Office Operations','Business Travel'],
}
COUNTRIES     = ['China','USA','Germany','India','Vietnam','Bangladesh',
                 'Brazil','Mexico','South Korea','Taiwan']
TRANSPORTS    = ['Sea Freight','Air Freight','Road Freight','Rail Freight']
SUPPLIER_TYPES= ['Tier 1','Tier 2','Tier 3']

#  Sidebar 
st.sidebar.header("Procurement Details")

company_name    = st.sidebar.text_input("Company Name", "Acme Corp")
category        = st.sidebar.selectbox("Category", CATEGORIES)
subcategory     = st.sidebar.selectbox("Subcategory", SUBCATEGORIES[category])
supplier_country= st.sidebar.selectbox("Supplier Country", COUNTRIES)
supplier_type   = st.sidebar.selectbox("Supplier Tier", SUPPLIER_TYPES)
transport_mode  = st.sidebar.selectbox("Transport Mode", TRANSPORTS)

st.sidebar.markdown("**📦 Quantity & Distance**")
quantity_kg     = st.sidebar.number_input("Quantity (kg)", 10.0, 100000.0, 500.0, step=50.0)
distance_km     = st.sidebar.number_input("Shipping Distance (km)", 100.0, 20000.0, 5000.0, step=100.0)

st.sidebar.markdown("**🌱 Supplier Sustainability**")
renewable_pct   = st.sidebar.slider("Renewable Energy %", 0.0, 100.0, 30.0, 1.0)
has_iso14001    = st.sidebar.checkbox("ISO 14001 Certified", False)
has_cdp_rating  = st.sidebar.checkbox("CDP Rated", False)
supplier_age    = st.sidebar.slider("Supplier Age (years)", 1, 40, 10)

estimate_btn = st.sidebar.button("Estimate Emissions", type="primary",
                                  use_container_width=True)

# Main 
if estimate_btn:
    payload = {
        "company_name":     company_name,
        "category":         category,
        "subcategory":      subcategory,
        "supplier_country": supplier_country,
        "supplier_type":    supplier_type,
        "transport_mode":   transport_mode,
        "quantity_kg":      quantity_kg,
        "distance_km":      distance_km,
        "renewable_pct":    renewable_pct,
        "has_iso14001":     int(has_iso14001),
        "has_cdp_rating":   int(has_cdp_rating),
        "supplier_age_yrs": supplier_age,
    }

    with st.spinner("Estimating carbon footprint..."):
        try:
            resp   = requests.post(f"{API_URL}/estimate", json=payload)
            result = resp.json()
        except Exception as e:
            st.error(f"API connection failed: {e}")
            st.stop()

    # ESG tier banner
    tier_colors = {"Green": "#27ae60", "Yellow": "#f39c12", "Red": "#e74c3c"}
    tier  = result['esg_tier']
    color = tier_colors.get(tier, "gray")

    st.markdown(
        f"<div style='background:{color};padding:16px;border-radius:10px;"
        f"text-align:center;color:white;font-size:22px;font-weight:600'>"
        f"ESG TIER: {tier} — Risk Score: {result['carbon_risk_score']:.1f}/100</div>",
        unsafe_allow_html=True
    )
    st.markdown("")

    # Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total CO2e",       f"{result['predicted_co2_kg']:.1f} kg")
    c2.metric("CO2 per kg",       f"{result['co2_per_kg']:.3f} kg/kg")
    c3.metric("Risk Score",       f"{result['carbon_risk_score']:.1f}/100")
    c4.metric("Reduction Potential", f"{result['estimated_reduction_potential_pct']}%")

    st.divider()
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Emission Breakdown")

        # Estimate split for visualisation
        transport_est = result['predicted_co2_kg'] * 0.3
        production_est= result['predicted_co2_kg'] * 0.7

        fig = go.Figure(go.Pie(
            labels=['Production', 'Transport'],
            values=[production_est, transport_est],
            hole=0.4,
            marker_colors=['#e74c3c', '#3498db']
        ))
        fig.update_layout(height=280, margin=dict(t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("Reduction Actions")
        actions = result['top_reduction_actions']
        if actions:
            for i, action in enumerate(actions):
                st.markdown(f"**{i+1}.** {action}")
        else:
            st.success("This supplier group has low carbon risk. No major actions required.")

        st.markdown("")
        st.info(
            f"**Estimated reduction potential:** "
            f"{result['estimated_reduction_potential_pct']}% "
            f"by implementing all recommended actions"
        )

    # Transport comparison
    st.divider()
    st.subheader("Transport Mode Carbon Comparison")
    transport_factors = {
        'Air Freight': 0.602,
        'Road Freight': 0.096,
        'Rail Freight': 0.028,
        'Sea Freight': 0.016,
    }
    transport_co2 = {
        mode: factor * quantity_kg * distance_km / 1000
        for mode, factor in transport_factors.items()
    }
    fig2 = go.Figure(go.Bar(
        x=list(transport_co2.keys()),
        y=list(transport_co2.values()),
        marker_color=['#e74c3c','#e67e22','#27ae60','#3498db'],
        text=[f"{v:.1f} kg" for v in transport_co2.values()],
        textposition='outside'
    ))
    fig2.update_layout(
        title=f"CO2e by Transport Mode for {quantity_kg:.0f}kg over {distance_km:.0f}km",
        yaxis_title="kg CO2e",
        height=320,
        margin=dict(t=40, b=20)
    )
    st.plotly_chart(fig2, use_container_width=True)

