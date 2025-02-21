import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np
import pandas as pd
from fpdf import FPDF
import io
import os

# Set Streamlit page title
st.set_page_config(page_title="Deceleration Report Generator", layout="wide")


def generate_pdf(data):
    pdf = FPDF("L", "mm", "A4")
    pdf.add_font('OpenSans', '', 'OpenSans.ttf', uni=True)
    
    # Compute per-category statistics
    category_stats = data.groupby("Kategória")[["ĽDK", "PDK"]].agg(["median", "min", "max"])
    category_medians = category_stats[("ĽDK", "median")].add(category_stats[("PDK", "median")]).div(2).to_dict()
    category_mins = category_stats[("ĽDK", "min")].combine(category_stats[("PDK", "min")], min).to_dict()
    category_maxs = category_stats[("ĽDK", "max")].combine(category_stats[("PDK", "max")], max).to_dict()

    for row in data.itertuples(index=True, name="Row"):
        pdf.add_page()
        pdf.set_font('OpenSans', '', 16)

        pdf.cell(0, 10, row.Meno, ln=1, align="C", border=False)
        pdf.cell(0, 10, row.Tím, ln=1, align="C", border=False)
        pdf.cell(0, 10, row.Pozícia, ln=1, align="C", border=False)
        pdf.cell(0, 10, row.Kategória, ln=1, align="C", border=False)

        left_value = row.ĽDK
        right_value = row.PDK
        mean_value = (left_value + right_value) / 2
        diff_percentage = abs((right_value - left_value) / left_value) * 100
        
        category_median = category_medians.get(row.Kategória, 8)  # Default median to 8 if missing
        category_min = category_mins.get(row.Kategória, 6) - 1
        category_max = category_maxs.get(row.Kategória, 10) + 1

        # Create the plot
        fig, ax = plt.subplots(figsize=(6, 4))
        x_left, x_right, y_value = row.ĽDK, row.PDK, 3

        ax.scatter(x_left, y_value, color='blue', s=200, label='Ľavá (m/s²)', marker='s')
        ax.vlines(x_left, ymin=0, ymax=y_value, colors='blue', linestyles='dashed')
        ax.scatter(x_right, y_value, color='green', s=200, label='Pravá (m/s²)', marker='v')
        ax.vlines(x_right, ymin=0, ymax=y_value, colors='green', linestyles='dashed')

        if left_value > right_value:
            ax.text(x_left + 0.6, y_value, f'{left_value} m/s²', color='blue', fontsize=12, ha='center')
            ax.text(x_right - 0.6, y_value, f'{right_value} m/s²', color='green', fontsize=12, ha='center')
        else:
            ax.text(x_left - 0.6, y_value, f'{left_value} m/s²', color='blue', fontsize=12, ha='center')
            ax.text(x_right + 0.6, y_value, f'{right_value} m/s²', color='green', fontsize=12, ha='center')

        ax.hlines(y_value, x_left, x_right, colors='black', linestyles='dashed')
        ax.text(mean_value, y_value + 1, f'{diff_percentage:.0f}% rozdiel', fontsize=12, ha='center')
        ax.axvline(category_median, color='red', linewidth=3, label=f'Medián ({category_median:.2f} m/s²)')

        ax.set_xlim(category_min, category_max)
        ax.set_xticks(np.arange(category_min, category_max + 1, 1))
        ax.set_ylim(0, 6)
        ax.set_xlabel('Decelerácia (m/s²)', fontsize=12)
        ax.legend(loc='upper left')

        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png', dpi=300, bbox_inches='tight')
        plt.close()
        
        img_buf.seek(0)
        pdf.image(img_buf, x=48.5, y=50, w=200)
    
    output_buffer = io.BytesIO()
    pdf.output(output_buffer)
    output_buffer.seek(0)
    return output_buffer

# Streamlit UI
st.title("Deceleration Report Generator")


# Download button for template Excel file
template_path = "template.xlsx"
if os.path.exists(template_path):
    with open(template_path, "rb") as file:
        st.download_button(
            label="Download Template Excel File",
            data=file,
            file_name="template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.write("### Data Preview:")
    st.dataframe(df.head())
    
    if st.button("Generate Report"):
        pdf_file = generate_pdf(df)
        st.download_button(
            label="Download PDF",
            data=pdf_file,
            file_name="export.pdf",
            mime="application/pdf"
        )
