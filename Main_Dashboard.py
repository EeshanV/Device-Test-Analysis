import yaml
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import tempfile
import os
import plotly.io as pio
from io import BytesIO
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from streamlit import runtime
from streamlit_extras.switch_page_button import switch_page
from jinja2 import Template
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_COLOR_SCHEME = px.colors.qualitative.Plotly

st.set_page_config(page_title="Linux Kernel Build and Test Dashboard", layout="wide")

@st.cache_data
def get_yaml_files_from_url(url):
    """
    Fetches a list of YAML file URLs from a given base URL.

    Args:
        url (str): The base URL to fetch YAML files from.

    Returns:
        list: A list of full URLs to YAML files.

    Raises:
        Exception: If there is an error fetching the YAML files.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        yaml_files = [a['href'] for a in soup.find_all('a', href=True) 
                     if a['href'].endswith(('.yml', '.yaml'))]
        return [urljoin(url, file) for file in yaml_files]
    except Exception as e:
        logger.error(f"Error fetching YAML files from URL: {e}")
        st.error(f"Error fetching YAML files: {e}")
        return []

@st.cache_data
def load_yaml_data(file_path):
    """
    Loads and parses YAML data from a given file path.

    Args:
        file_path (str): The path to the YAML file.

    Returns:
        dict: Parsed YAML data.

    Raises:
        Exception: If there is an error loading the YAML file.
    """
    try:
        if file_path.startswith(('http://', 'https://')):
            response = requests.get(file_path)
            response.raise_for_status()
            logger.info(f"Loading YAML file from URL: {file_path}")
            return yaml.safe_load(response.text)
        else:
            with open(file_path, 'r') as file:
                logger.info(f"Loading local YAML file: {file_path}")
                return yaml.safe_load(file)
    except Exception as e:
        logger.error(f"Error loading YAML file: {e}")
        st.error(f"Error loading YAML file: {e}")
        return None

@st.cache_data
def extract_job_data(data):
    """
    Extracts job, build, and test information from the parsed YAML data.

    Args:
        data (dict): The parsed YAML data containing job information.

    Returns:
        list: A list of dictionaries, each containing job, build, and test details.
    """
    job_data = []
    if data:
        for job in data.get('jobs', []):
            job_name = job['name']
            for build in job.get('builds', []):
                build_name = build.get('build_name', 'Unnamed Build')
                for test in job.get('tests', []):
                    device = test.get('device', 'Unknown')
                    test_names = test.get('tests', [])
                    
                    if isinstance(test_names, list):
                        for test_name in test_names:
                            job_data.append({
                                'job_name': job_name,
                                'build_name': build_name,
                                'test_name': test_name,
                                'device': device,
                                'target_arch': build.get('target_arch', 'Unknown'),
                                'toolchain': build.get('toolchain', 'Unknown')
                            })
    return job_data

def create_arch_pie_chart(filtered_df):
    """
    Creates a pie chart showing the distribution of target architectures.

    Args:
        filtered_df (pd.DataFrame): The filtered DataFrame containing job data.

    Returns:
        plotly.graph_objects.Figure: A Plotly pie chart figure.
    """
    arch_counts = filtered_df['target_arch'].value_counts().reset_index()
    arch_counts.columns = ['target_arch', 'count']
    return px.pie(
        arch_counts,
        names='target_arch',
        values='count',
        title='Target Architecture Distribution',
        hover_data={'count': True},
        color_discrete_sequence=DEFAULT_COLOR_SCHEME
    ).update_traces(
        textinfo='percent+value',
        hovertemplate="Architecture: %{label}<br>Count: %{value}<br>Percentage: %{percent}<extra></extra>"
    )

def create_toolchain_heatmap(filtered_df):
    """
    Creates a heatmap showing the relationship between toolchains, job names, and architectures.

    Args:
        filtered_df (pd.DataFrame): The filtered DataFrame containing job data.

    Returns:
        plotly.graph_objects.Figure: A Plotly heatmap figure.
    """
    heatmap_data = filtered_df.groupby(['job_name', 'target_arch', 'toolchain']).size().reset_index(name='count')
    heatmap_data['job_arch'] = heatmap_data['job_name'] + ' (' + heatmap_data['target_arch'] + ')'
    heatmap_pivot = heatmap_data.pivot(index='job_arch', columns='toolchain', values='count').fillna(0)
    return go.Figure(data=go.Heatmap(
        z=heatmap_pivot.values,
        x=heatmap_pivot.columns,
        y=heatmap_pivot.index,
        colorscale=[[0, 'white'], [1, 'red']],
        text=heatmap_pivot.values,
        texttemplate='%{text}',
        textfont={"size": 12},
        hoverongaps=False,
        hovertemplate="Toolchain: %{x}<br>Job (Arch): %{y}<br>Count: %{z}<extra></extra>",
        showscale=True,
        xgap=3,
        ygap=3
    )).update_layout(
        title='Toolchain vs Job Name and Architecture Heatmap',
        height=1000,
        width=1200,
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
            autorange='reversed',
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)',
            showline=True,
            linewidth=1,
            linecolor='rgba(128, 128, 128, 0.2)',
            mirror=True
        ),
        font=dict(size=14),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

def create_test_count_line_chart(filtered_df):
    """
    Creates a line chart showing the number of tests per job.

    Args:
        filtered_df (pd.DataFrame): The filtered DataFrame containing job data.

    Returns:
        plotly.graph_objects.Figure: A Plotly line chart figure.
    """
    return px.line(
        filtered_df.groupby('job_name').size().reset_index(name='test_count'),
        x='job_name', y='test_count', title='Number of Tests per Job',
        template='plotly_dark'
    )

def create_build_test_scatter(filtered_df):
    """
    Creates a scatter plot showing the relationship between builds and tests.

    Args:
        filtered_df (pd.DataFrame): The filtered DataFrame containing job data.

    Returns:
        plotly.graph_objects.Figure: A Plotly scatter plot figure.
    """
    scatter_fig = px.scatter(
        filtered_df,
        x='build_name',
        y='test_name',
        color='target_arch',
        hover_data={
            'job_name': True,
            'toolchain': True,
            'target_arch': True,
            'test_count': True
        },
        title='Builds vs Tests',
        height=1000,
        width=1200,
        template='plotly_dark'
    ).update_traces(
        marker=dict(size=10),
        textposition='top center',
        hovertemplate="<b>Build:</b> %{x}<br>" +
                      "<b>Test:</b> %{y}<br>" +
                      "<b>Job Name:</b> %{customdata[0]}<br>" +
                      "<b>Toolchain:</b> %{customdata[1]}<br>" +
                      "<b>Target Arch:</b> %{customdata[2]}<br>" +
                      "<b>Test Count:</b> %{customdata[3]}<extra></extra>",
    ).update_layout(
        legend_title_text='Target Architecture',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return scatter_fig

def create_toolchain_bar_chart(filtered_df):
    """
    Creates a bar chart showing the distribution of toolchains.

    Args:
        filtered_df (pd.DataFrame): The filtered DataFrame containing job data.

    Returns:
        plotly.graph_objects.Figure: A Plotly bar chart figure.
    """
    toolchain_counts = filtered_df['toolchain'].value_counts().reset_index()
    toolchain_counts.columns = ['toolchain', 'count']

    return px.bar(
        toolchain_counts,
        x='toolchain',
        y='count',
        title='Toolchain Distribution',
        labels={'toolchain': 'Toolchain', 'count': 'Number of Jobs'},
        color='toolchain',
        color_discrete_sequence=px.colors.qualitative.Safe,
    ).update_layout(
        xaxis={'categoryorder': 'total descending'},
        yaxis_title='Number of Jobs',
        xaxis_title='Toolchain',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

def validate_yaml_data(data):
    """
    Validates the structure of the parsed YAML data.

    Args:
        data (dict): The parsed YAML data.

    Returns:
        bool: True if the data is valid, False otherwise.
    """
    if not data or 'jobs' not in data:
        st.error("Invalid YAML structure: 'jobs' key not found.")
        return False
    return True

BASE_URL = "https://people.linaro.org/~naresh.kamboju/lkft-common/tuxconfig/"
yaml_files = get_yaml_files_from_url(BASE_URL)

if yaml_files:
    selected_yaml = st.sidebar.selectbox(
        "Select YAML File",
        yaml_files,
        format_func=lambda x: x.split('/')[-1]
    )
    data = load_yaml_data(selected_yaml)
else:
    st.error("No YAML files found at the specified URL")
    data = None

if validate_yaml_data(data):
    job_data = extract_job_data(data)
    df = pd.DataFrame(job_data)
else:
    df = pd.DataFrame()

st.title("Linux Kernel Build and Test Dashboard")

build_names = df['build_name'].unique()
test_names = df['test_name'].unique()
job_names = df['job_name'].unique()
arch_names = df['target_arch'].unique()
device_names = df['device'].unique()

selected_build_names = st.sidebar.multiselect("Select Build Names", build_names)
if selected_build_names:
    test_names = df[df['build_name'].isin(selected_build_names)]['test_name'].unique()

selected_test_names = st.sidebar.multiselect("Select Test Names", test_names)
if selected_test_names:
    job_names = df[df['test_name'].isin(selected_test_names)]['job_name'].unique()

selected_job_names = st.sidebar.multiselect("Select Job Names", job_names)
if selected_job_names:
    arch_names = df[df['job_name'].isin(selected_job_names)]['target_arch'].unique()

selected_arch_names = st.sidebar.multiselect("Select Architectures", arch_names)
if selected_arch_names:
    device_names = df[df['target_arch'].isin(selected_arch_names)]['device'].unique()

selected_device_names = st.sidebar.multiselect("Select Devices", device_names)

filtered_df = df
if selected_build_names:
    filtered_df = filtered_df[filtered_df['build_name'].isin(selected_build_names)]
if selected_test_names:
    filtered_df = filtered_df[filtered_df['test_name'].isin(selected_test_names)]
if selected_job_names:
    filtered_df = filtered_df[filtered_df['job_name'].isin(selected_job_names)]
if selected_arch_names:
    filtered_df = filtered_df[filtered_df['target_arch'].isin(selected_arch_names)]
if selected_device_names:
    filtered_df = filtered_df[filtered_df['device'].isin(selected_device_names)]

filtered_df = filtered_df.assign(
    test_count=filtered_df.groupby('build_name')['test_name'].transform('count')
)

if not filtered_df.empty:
    with st.spinner("Generating plots..."):
        arch_pie = create_arch_pie_chart(filtered_df)
        toolchain_heatmap = create_toolchain_heatmap(filtered_df)
        test_count_line = create_test_count_line_chart(filtered_df)
        build_test_scatter = create_build_test_scatter(filtered_df)
        toolchain_bar = create_toolchain_bar_chart(filtered_df)

    st.plotly_chart(toolchain_heatmap, use_container_width=True)
    st.plotly_chart(arch_pie, use_container_width=True)
    st.plotly_chart(toolchain_bar, use_container_width=True)
    
    st.plotly_chart(build_test_scatter, use_container_width=True)
    st.plotly_chart(test_count_line, use_container_width=True)
else:
    st.warning("No data available for the selected filters.")

excel_buffer = BytesIO()
with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
    filtered_df.to_excel(writer, index=False, sheet_name='Filtered Data')
excel_data = excel_buffer.getvalue()

st.sidebar.download_button(
    label="Download Excel",
    data=excel_data,
    file_name='filtered_data.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)

csv_data = filtered_df.to_csv(index=False).encode('utf-8')
st.sidebar.download_button(
    label="Download CSV",
    data=csv_data,
    file_name='filtered_data.csv',
    mime='text/csv'
)

@st.cache_data
def get_filtered_data(df, selected_build_names, selected_test_names, selected_job_names, selected_arch_names, selected_device_names):
    """
    Filters the DataFrame based on selected criteria.

    Args:
        df (pd.DataFrame): The original DataFrame containing job data.
        selected_build_names (list): List of selected build names.
        selected_test_names (list): List of selected test names.
        selected_job_names (list): List of selected job names.
        selected_arch_names (list): List of selected architectures.
        selected_device_names (list): List of selected devices.

    Returns:
        pd.DataFrame: A filtered DataFrame based on the selected criteria.
    """
    filtered_df = df.copy()
    
    mask = pd.Series(True, index=filtered_df.index)
    
    if selected_build_names:
        mask &= filtered_df['build_name'].isin(selected_build_names)
    if selected_test_names:
        mask &= filtered_df['test_name'].isin(selected_test_names)
    if selected_job_names:
        mask &= filtered_df['job_name'].isin(selected_job_names)
    if selected_arch_names:
        mask &= filtered_df['target_arch'].isin(selected_arch_names)
    if selected_device_names:
        mask &= filtered_df['device'].isin(selected_device_names)
    
    return filtered_df.loc[mask].copy()

filtered_df = get_filtered_data(df, selected_build_names, selected_test_names, selected_job_names, selected_arch_names, selected_device_names)

def generate_filtered_dashboard(filtered_df, toolchain_heatmap, arch_pie, build_test_scatter, test_count_line, toolchain_bar):
    """
    Generates an HTML report for the filtered dashboard.

    Args:
        filtered_df (pd.DataFrame): The filtered DataFrame for analysis.
        toolchain_heatmap (go.Figure): Plotly figure for toolchain heatmap.
        arch_pie (go.Figure): Plotly figure for architecture pie chart.
        build_test_scatter (go.Figure): Plotly figure for build-test scatter plot.
        test_count_line (go.Figure): Plotly figure for test count line chart.
        toolchain_bar (go.Figure): Plotly figure for toolchain bar chart.

    Returns:
        str: The file path to the generated HTML report.
    """
    toolchain_heatmap.update_layout(
        template='plotly',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='black', size=12),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)',
            tickfont=dict(color='black'),
            title_font=dict(color='black'),
            tickangle=45
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)',
            tickfont=dict(color='black'),
            title_font=dict(color='black')
        ),
        title_font=dict(color='black'),
        height=800
    )

    arch_pie.update_layout(
        template='plotly',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='black', size=12),
        title_font=dict(color='black'),
        legend=dict(
            font=dict(color='black'),
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='rgba(128, 128, 128, 0.2)',
            borderwidth=1
        ),
        height=600
    )

    build_test_scatter.update_layout(
        template='plotly',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='black', size=12),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)',
            tickfont=dict(color='black'),
            title_font=dict(color='black'),
            tickangle=45
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)',
            tickfont=dict(color='black'),
            title_font=dict(color='black')
        ),
        title_font=dict(color='black'),
        legend=dict(
            font=dict(color='black'),
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='rgba(128, 128, 128, 0.2)',
            borderwidth=1
        ),
        height=800
    )

    test_count_line.update_layout(
        template='plotly',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='black', size=12),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)',
            tickfont=dict(color='black'),
            title_font=dict(color='black'),
            tickangle=45
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)',
            tickfont=dict(color='black'),
            title_font=dict(color='black')
        ),
        title_font=dict(color='black'),
        height=600
    )

    toolchain_bar.update_layout(
        template='plotly',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='black', size=12),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)',
            tickfont=dict(color='black'),
            title_font=dict(color='black'),
            tickangle=45
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)',
            tickfont=dict(color='black'),
            title_font=dict(color='black')
        ),
        title_font=dict(color='black'),
        legend=dict(
            font=dict(color='black'),
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='rgba(128, 128, 128, 0.2)',
            borderwidth=1
        ),
        height=600
    )

    toolchain_heatmap.update_traces(
        colorscale='RdBu',
        showscale=True,
        colorbar=dict(
            tickfont=dict(color='black'),
            title=dict(text='Count', font=dict(color='black'))
        )
    )

    arch_pie.update_traces(
        textfont=dict(color='black'),
        marker=dict(colors=px.colors.qualitative.Set3)
    )

    build_test_scatter.update_traces(
        marker=dict(size=8),
        selector=dict(mode='markers')
    )

    test_count_line.update_traces(
        line=dict(width=2),
        marker=dict(size=8)
    )

    toolchain_bar.update_traces(
        marker_color=px.colors.qualitative.Set3,
        selector=dict(type='bar')
    )

    plots_data = {}
    
    plots_data['arch_pie'] = json.loads(pio.to_json(arch_pie))
    plots_data['toolchain_heatmap'] = json.loads(pio.to_json(toolchain_heatmap))
    plots_data['build_test_scatter'] = json.loads(pio.to_json(build_test_scatter))
    plots_data['test_count_line'] = json.loads(pio.to_json(test_count_line))
    plots_data['toolchain_bar'] = json.loads(pio.to_json(toolchain_bar))
    
    template = Template('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Linux Kernel Build and Test Dashboard - Filtered Report</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f0f2f6;
            }
            .plot-container {
                background-color: white;
                padding: 20px;
                margin: 20px 0;
                border-radius: 5px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1 {
                color: #262730;
                text-align: center;
            }
            .filters-info {
                background-color: white;
                padding: 15px;
                margin: 20px 0;
                border-radius: 5px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
        </style>
    </head>
    <body>
        <h1>Linux Kernel Build and Test Dashboard - Filtered Report</h1>
        
        <div class="filters-info">
            <h3>Applied Filters:</h3>
            <ul>
                <li>Total Records: {{ filtered_df|length }}</li>
                <li>Unique Architectures: {{ architectures|join(', ') }}</li>
                <li>Unique Toolchains: {{ toolchains|join(', ') }}</li>
                <li>Unique Devices: {{ devices|join(', ') }}</li>
                <li>Unique Build Names: {{ build_names|join(', ') }}</li>
            </ul>
        </div>
        
        <div class="plot-container">
            <div id="toolchain_heatmap"></div>
        </div>
        
        <div class="plot-container">
            <div id="arch_pie"></div>
        </div>
        
        <div class="plot-container">
            <div id="toolchain_bar"></div>
        </div>
        
        <div class="plot-container">
            <div id="build_test_scatter"></div>
        </div>
        
        <div class="plot-container">
            <div id="test_count_line"></div>
        </div>
        
        <script>
            var plots_data = {{ plots_data|tojson }};
            
            Plotly.newPlot('toolchain_heatmap', plots_data.toolchain_heatmap.data, plots_data.toolchain_heatmap.layout);
            Plotly.newPlot('arch_pie', plots_data.arch_pie.data, plots_data.arch_pie.layout);
            Plotly.newPlot('toolchain_bar', plots_data.toolchain_bar.data, plots_data.toolchain_bar.layout);
            Plotly.newPlot('build_test_scatter', plots_data.build_test_scatter.data, plots_data.build_test_scatter.layout);
            Plotly.newPlot('test_count_line', plots_data.test_count_line.data, plots_data.test_count_line.layout);
        </script>
    </body>
    </html>
    ''')
    
    template_vars = {
        'plots_data': plots_data,
        'filtered_df': filtered_df.to_dict('records'),
        'architectures': filtered_df['target_arch'].unique().tolist(),
        'toolchains': filtered_df['toolchain'].unique().tolist(),
        'devices': filtered_df['device'].unique().tolist(),
        'build_names': filtered_df['build_name'].unique().tolist()
    }
    
    html_content = template.render(**template_vars)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as f:
        f.write(html_content)
        return f.name

col1, col2 = st.columns(2)
with col1:
    if st.button("Generate Report"):
        if not filtered_df.empty:
            html_file_path = generate_filtered_dashboard(
                filtered_df,
                toolchain_heatmap,
                arch_pie,
                build_test_scatter,
                test_count_line,
                toolchain_bar
            )
            
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
                
            st.download_button(
                label="Download Report",
                data=html_content,
                file_name="report.html",
                mime="text/html"
            )
            
            os.remove(html_file_path)
        else:
            st.warning("No data available to generate a report.")

