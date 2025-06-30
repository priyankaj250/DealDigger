import streamlit as st
import pandas as pd
from thefuzz import fuzz
from scraper.blinkit_scraper import blinkit_scraper
from scraper.zepto_scraper import zepto_scraper

st.set_page_config(page_title="DealDigger", layout="wide")

st.title("🔎 DealDigger Price Comparison")
st.write("Compare prices of products between Blinkit and Zepto automatically!")

# --- Helper: Render HTML Table ---
def render_product_table(df, header_color):
    if df.empty:
        return "<p>No products found.</p>"

    rows = ""
    for _, row in df.iterrows():
        price = str(row["price"]).replace("₹₹", "₹")
        rows += (
            "<tr>"
            f"<td><img src='{row['image']}' width='80'></td>"
            f"<td>{row['name']}</td>"
            f"<td>{row['quantity']}</td>"
            f"<td>{price}</td>"
            f"<td><a href='{row['link']}' target='_blank'>View</a></td>"
            "</tr>"
        )

    html = (
            "<table style='width:90%; margin:auto; border-collapse: collapse;'>"
            "<thead>"
            "<tr style='background-color:" + header_color + "; color:white;'>"
                                                            "<th>Image</th>"
                                                            "<th>Name</th>"
                                                            "<th>Quantity</th>"
                                                            "<th>Price</th>"
                                                            "<th>Link</th>"
                                                            "</tr>"
                                                            "</thead>"
                                                            "<tbody>"
            + rows +
            "</tbody>"
            "</table>"
    )
    return html

# --- Helper: Render Matched Product Pair Card ---
def render_matched_pair(blinkit, zepto):
    # Convert prices to numeric for comparison
    try:
        b_price = float(str(blinkit["Price"]).replace("₹", "").replace(",", "").strip())
    except:
        b_price = None

    try:
        z_price = float(str(zepto["Price"]).replace("₹", "").replace(",", "").strip())
    except:
        z_price = None

    cheaper_note = ""
    b_price_html = blinkit["Price"]
    z_price_html = zepto["Price"]

    if b_price is not None and z_price is not None:
        if b_price < z_price:
            cheaper_note = "<div style='color:green; font-weight:bold;'>↓ Cheaper on Blinkit</div>"
            b_price_html = f"<span style='color:green;'>₹{b_price}</span>"
            z_price_html = f"<span style='color:red;'>₹{z_price}</span>"
        elif z_price < b_price:
            cheaper_note = "<div style='color:green; font-weight:bold;'>↓ Cheaper on Zepto</div>"
            b_price_html = f"<span style='color:red;'>₹{b_price}</span>"
            z_price_html = f"<span style='color:green;'>₹{z_price}</span>"
        else:
            cheaper_note = "<div style='color:grey; font-weight:bold;'>Same Price on Both</div>"

    html = (
        "<div style='border:1px solid #ccc; border-radius:8px; padding:10px; margin:20px 0; background:#fff;'>"
        "<div style='display:flex; gap:20px;'>"

        "<div style='flex:1; text-align:center;'>"
        "<h4>Blinkit</h4>"
        f"<img src='{blinkit['Image']}' width='100'><br>"
        f"<b>{blinkit['Name']}</b><br>"
        f"{blinkit['Quantity']}<br>"
        f"{b_price_html}<br>"
        f"<a href='{blinkit['Link']}' target='_blank'>View</a>"
        "</div>"

        "<div style='flex:1; text-align:center;'>"
        "<h4>Zepto</h4>"
        f"<img src='{zepto['Image']}' width='100'><br>"
        f"<b>{zepto['Name']}</b><br>"
        f"{zepto['Quantity']}<br>"
        f"{z_price_html}<br>"
        f"<a href='{zepto['Link']}' target='_blank'>View</a>"
        "</div>"

        "</div>"
        f"<div style='text-align:center; margin-top:10px;'>{cheaper_note}</div>"
        "</div>"
    )

    return html

# --- Custom CSS ---
custom_css = """
<style>
table, th, td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: center;
}
tr:nth-child(even) {
    background-color: #ffffff;
}
th {
    background-color: #4CAF50;
    color: white;
}
a {
    color: #4CAF50;
    text-decoration: none;
    font-weight: bold;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- Search box ---
search_item = st.text_input("Enter product name to search:")

if st.button("Search") and search_item:
    # Scrape Blinkit
    with st.spinner("Scraping Blinkit..."):
        try:
            blinkit_products = blinkit_scraper(search_item)
        except Exception as e:
            st.error(f"Error running Blinkit scraper: {e}")
            blinkit_products = []
    blinkit_df = pd.DataFrame(blinkit_products) if blinkit_products else pd.DataFrame()

    # Scrape Zepto
    with st.spinner("Scraping Zepto..."):
        try:
            zepto_products = zepto_scraper(search_item)
        except Exception as e:
            st.error(f"Error running Zepto scraper: {e}")
            zepto_products = []
    zepto_df = pd.DataFrame(zepto_products) if zepto_products else pd.DataFrame()

    # Matching logic
    matches = []
    if not blinkit_df.empty and not zepto_df.empty:
        with st.spinner("Matching products..."):
            for _, b_row in blinkit_df.iterrows():
                best_score = 0
                best_match = None
                b_name = str(b_row["name"])
                b_qty = str(b_row["quantity"]).strip().lower()
                for _, z_row in zepto_df.iterrows():
                    z_name = str(z_row["name"])
                    z_qty = str(z_row["quantity"]).strip().lower()
                    score = fuzz.token_set_ratio(b_name, z_name)
                    qty_match = b_qty == z_qty
                    if score > best_score and qty_match:
                        best_score = score
                        best_match = z_row
                if best_match is not None and best_score >= 85:
                    matches.append({
                        "blinkit": {
                            "Name": b_row["name"],
                            "Quantity": b_row["quantity"],
                            "Price": str(b_row["price"]).replace("₹₹", "₹"),
                            "Image": b_row["image"],
                            "Link": b_row["link"]
                        },
                        "zepto": {
                            "Name": best_match["name"],
                            "Quantity": best_match["quantity"],
                            "Price": str(best_match["price"]).replace("₹₹", "₹"),
                            "Image": best_match["image"],
                            "Link": best_match["link"]
                        }
                    })

    # Show matched products
    if matches:
        st.header("🔗 Matched Products")
        for pair in matches:
            html_block = render_matched_pair(pair["blinkit"], pair["zepto"])
            st.markdown(html_block, unsafe_allow_html=True)
    else:
        st.warning("No matching products found.")

    # Expanders for additional products
    if not blinkit_df.empty:
        with st.expander("▶ For more products on Blinkit"):
            st.markdown(render_product_table(blinkit_df, "#4CAF50"), unsafe_allow_html=True)

    if not zepto_df.empty:
        with st.expander("▶ For more products on Zepto"):
            st.markdown(render_product_table(zepto_df, "#6A0DAD"), unsafe_allow_html=True)
