import yaml
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from fpdf import FPDF
import tempfile
import os
import plotly.io as pio

with open('linux-6.12.y-plan.yml', 'r') as file:
    data = yaml.safe_load(file)

job_data = []
for job in data['jobs']:
    job_name = job['name']
    for build in job.get('builds', []):
        build_name = build.get('build_name', 'Unnamed Build')
        for test in job.get('tests', []):
            test_devices = test.get('tests', [])
            for test_name in test_devices:
                job_data.append({
                    'job_name': job_name,
                    'build_name': build_name,
                    'test_name': test_name,
                    'target_arch': build.get('target_arch', 'Unknown'),
                    'toolchain': build.get('toolchain', 'Unknown')
                })


df = pd.DataFrame(job_data)

st.title("Linux Kernel Build and Test Dashboard")

build_names = df['build_name'].unique()
test_names = df['test_name'].unique()
job_names = df['job_name'].unique()
arch_names = df['target_arch'].unique()

selected_build_names = st.sidebar.multiselect(
    "Select Build Names",
    build_names
)

if selected_build_names:
    test_names = df[df['build_name'].isin(selected_build_names)]['test_name'].unique()

selected_test_names = st.sidebar.multiselect(
    "Select Test Names",
    test_names
)

if selected_test_names:
    job_names = df[
        (df['build_name'].isin(selected_build_names)) &
        (df['test_name'].isin(selected_test_names))
    ]['job_name'].unique()

selected_job_names = st.sidebar.multiselect(
    "Select Job Names",
    job_names
)

selected_arch_names = st.sidebar.multiselect(
    "Select Architectures",
    arch_names
)

filtered_df = df

if selected_build_names:
    filtered_df = filtered_df[filtered_df['build_name'].isin(selected_build_names)]

if selected_test_names:
    filtered_df = filtered_df[filtered_df['test_name'].isin(selected_test_names)]

if selected_job_names:
    filtered_df = filtered_df[filtered_df['job_name'].isin(selected_job_names)]

if selected_arch_names:
    filtered_df = filtered_df[filtered_df['target_arch'].isin(selected_arch_names)]

heatmap_data = filtered_df.groupby(['job_name', 'target_arch', 'toolchain']).size().reset_index(name='count')
heatmap_data['job_arch'] = heatmap_data['job_name'] + ' (' + heatmap_data['target_arch'] + ')'
heatmap_pivot = heatmap_data.pivot(index='job_arch', columns='toolchain', values='count').fillna(0)

toolchain_heatmap = go.Figure(data=go.Heatmap(
    z=heatmap_pivot.values,
    x=heatmap_pivot.columns,
    y=heatmap_pivot.index,
    colorscale='Viridis',
    textfont={"size": 12},
    hoverongaps=False,
    hovertemplate="Toolchain: %{x}<br>Job (Arch): %{y}<br>Count: %{z}<extra></extra>",
    showscale=True,
    xgap=3,
    ygap=3
))

toolchain_heatmap.update_layout(
    title='Toolchain vs Job Name and Architecture Heatmap',
    height=1000,
    xaxis_title='Toolchain',
    yaxis_title='Job Name (Architecture)',
    margin=dict(l=250, r=100, t=60, b=80),
    xaxis=dict(
        showgrid=True,
        gridcolor='rgba(128, 128, 128, 0.2)',
        tickangle=45,
        showline=True,
        linewidth=1,
        linecolor='rgba(128, 128, 128, 0.2)',
        mirror=True
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor='rgba(128, 128, 128, 0.2)',
        showline=True,
        linewidth=1,
        linecolor='rgba(128, 128, 128, 0.2)',
        mirror=True
    ),
    plot_bgcolor='black',
    paper_bgcolor='black',
)

arch_counts = filtered_df['target_arch'].value_counts()
arch_pie = px.pie(
    filtered_df, 
    names='target_arch', 
    title='Target Architecture Distribution',
    values=filtered_df['target_arch'].map(arch_counts),
    hover_data={
        'target_arch': True,
        'count': filtered_df['target_arch'].map(arch_counts)
    },
    color_discrete_sequence=px.colors.qualitative.Plotly
).update_traces(
    textinfo='percent+value',
    hovertemplate="Architecture: %{label}<br>Count: %{value}<br>Percentage: %{percent}<extra></extra>"
)

arch_pie.update_layout(
    showlegend=True,
    legend_title="Architecture",
    legend=dict(
        font=dict(size=12),
        itemsizing='constant'
    )
)

test_count_line = px.line(
    filtered_df.groupby('job_name').size().reset_index(name='test_count'),
    x='job_name', y='test_count', title='Number of Tests per Job',
    template='plotly_dark'
)

build_test_scatter = px.scatter(
    filtered_df, x='build_name', y='test_name', color='toolchain',
    hover_data=['job_name'], title='Builds vs Tests',
    height=1000, width=1000,
    template='plotly_dark'
)

def generate_pdf_report_with_plots(filtered_df, toolchain_heatmap, arch_pie, build_test_scatter, test_count_line):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    temp_dir = tempfile.mkdtemp()
    heatmap_path = os.path.join(temp_dir, "heatmap.png")
    pie_path = os.path.join(temp_dir, "pie.png")
    scatter_path = os.path.join(temp_dir, "scatter.png")
    line_path = os.path.join(temp_dir, "line.png")

    pio.write_image(toolchain_heatmap, heatmap_path, format='png')
    pio.write_image(arch_pie, pie_path, format='png')
    pio.write_image(build_test_scatter, scatter_path, format='png')
    pio.write_image(test_count_line, line_path, format='png')

    pdf.image(heatmap_path, x=10, y=None, w=180)
    pdf.add_page()
    pdf.image(pie_path, x=10, y=None, w=180)
    pdf.add_page()
    pdf.image(scatter_path, x=10, y=None, w=180)
    pdf.add_page()
    pdf.image(line_path, x=10, y=None, w=180)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_file.name)

    os.remove(heatmap_path)
    os.remove(pie_path)
    os.remove(scatter_path)
    os.remove(line_path)
    os.rmdir(temp_dir)

    return temp_file.name

if st.button("Generate PDF"):
    if not filtered_df.empty:
        pdf_file_path = generate_pdf_report_with_plots(filtered_df, toolchain_heatmap, arch_pie, build_test_scatter, test_count_line)
        with open(pdf_file_path, "rb") as pdf_file:
            st.download_button(
                label="Download PDF",
                data=pdf_file,
                file_name="filtered_report.pdf",
                mime="application/pdf"
            )
        os.remove(pdf_file_path)
    else:
        st.warning("No data available to generate a report.")

st.plotly_chart(toolchain_heatmap, use_container_width=True)
st.plotly_chart(arch_pie, use_container_width=True)
st.plotly_chart(build_test_scatter, use_container_width=True)
st.plotly_chart(test_count_line, use_container_width=True)