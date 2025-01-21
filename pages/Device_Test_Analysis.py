import streamlit as st
import pandas as pd
import plotly.express as px
import yaml
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import plotly.graph_objects as go
from jinja2 import Template
import json
import plotly.io as pio
import tempfile
import os
from dashboard_module import generate_device_analysis_report

BASE_URL = "https://people.linaro.org/~naresh.kamboju/lkft-common/tuxconfig/"

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
        response = requests.get(file_path)
        response.raise_for_status()
        return yaml.safe_load(response.text)
    except Exception as e:
        st.error(f"Error loading YAML file: {e}")
        return None

def extract_data(yaml_data, file_name):
    """
    Extracts device and test information from YAML data.

    Args:
        yaml_data (dict): The parsed YAML data.
        file_name (str): The name of the YAML file.

    Returns:
        pd.DataFrame: A DataFrame containing device and test information.
    """
    data = []
    
    for job in yaml_data.get('jobs', []):
        job_name = job.get('name', 'Unknown')
        
        for test in job.get('tests', []):
            device = test.get('device', 'unspecified')
            if device == 'unspecified':
                continue
            tests = test.get('tests', [])
            if not isinstance(tests, list):
                tests = [tests]
            
            for test_name in tests:
                if test_name is not None:
                    data.append({
                        'device': device,
                        'test': str(test_name),
                        'file': file_name,
                        'level': 'job'
                    })
        
        for build in job.get('builds', []):
            build_name = build.get('build_name', '')
            
            for test in build.get('tests', []):
                device = test.get('device', 'unspecified')
                if device == 'unspecified':
                    continue
                tests = test.get('tests', [])
                if not isinstance(tests, list):
                    tests = [tests]
                
                for test_name in tests:
                    if test_name is not None:
                        data.append({
                            'device': device,
                            'test': str(test_name),
                            'file': file_name,
                            'level': 'build'
                        })
            
            if build.get('targets'):
                targets = build.get('targets', [])
                if isinstance(targets, list):
                    devices = set()
                    for test in build.get('tests', []):
                        device = test.get('device', 'unspecified')
                        if device != 'unspecified':
                            devices.add(device)
                    
                    for target in targets:
                        for device in devices:
                            data.append({
                                'device': device,
                                'test': str(target),
                                'file': file_name,
                                'level': 'target'
                            })
    
    return pd.DataFrame(data)

def create_dynamic_filename(base_name, components):
    """
    Creates a dynamic filename by joining the base name with components.

    Args:
        base_name (str): The base name for the file.
        components (list): A list of components to include in the filename.

    Returns:
        str: A dynamically generated filename.
    """
    components_str = "_".join(filter(None, components))
    return f"{base_name}_{components_str}.html"

def main():
    """
    Main function to run the Streamlit application for device and test analysis.

    This function sets up the Streamlit page configuration, fetches YAML files from a predefined URL,
    processes the data to extract device and test information, and displays interactive visualizations
    and filters for user interaction. It also provides functionality to generate and download an HTML
    report based on the filtered data.

    Workflow:
    1. Set up the Streamlit page layout and title.
    2. Fetch YAML files from the specified BASE_URL.
    3. Load and parse each YAML file to extract relevant data.
    4. Concatenate all extracted data into a single DataFrame.
    5. Display filters in the sidebar for devices and tests.
    6. Generate and display visualizations:
       - Bar chart for the number of tests per device.
       - Bar chart for the number of devices per test.
       - Heatmap for device coverage across configuration files.
    7. Provide expandable sections for detailed device and test analysis.
    8. Allow users to generate and download an HTML report of the analysis.

    Raises:
        Streamlit errors and warnings for data fetching and processing issues.
    """
    st.set_page_config(page_title="Linux Kernel Device and Test Analysis",layout="wide", page_icon="favicon.ico")
    st.title("Device and Test Analysis")
    
    yaml_files = get_yaml_files_from_url(BASE_URL)
    if not yaml_files:
        st.error("No YAML files found")
        return
    
    all_data = pd.DataFrame()
    for file in yaml_files:
        yaml_data = load_yaml_data(file)
        if yaml_data:
            file_name = file.split('/')[-1]
            df = extract_data(yaml_data, file_name)
            if not df.empty:
                all_data = pd.concat([all_data, df])
    
    if all_data.empty:
        st.error("No data found")
        return
    
    st.sidebar.header("Filters")
    
    devices = sorted(all_data['device'].unique())
    selected_devices = st.sidebar.multiselect("Select Devices", devices)
    
    tests = sorted(all_data['test'].unique())
    selected_tests = st.sidebar.multiselect("Select Tests", tests)
    
    filtered_data = all_data
    if selected_devices:
        filtered_data = filtered_data[filtered_data['device'].isin(selected_devices)]
    if selected_tests:
        filtered_data = filtered_data[filtered_data['test'].isin(selected_tests)]
    
    col1, col2 = st.columns(2)
    
    with col1:
        device_test_counts = filtered_data.groupby('device')['test'].nunique().sort_values(ascending=True)
        height = max(400, len(device_test_counts) * 30)
        fig1 = px.bar(
            x=device_test_counts.values,
            y=device_test_counts.index,
            orientation='h',
            title='Number of Tests per Device',
            labels={'x': 'Number of Tests', 'y': 'Device'},
            template='plotly_dark',
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        fig1.update_layout(
            height=height,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.2)',
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
                mirror=True,
                tickmode='linear'
            ),
            font=dict(size=14),
            margin=dict(l=200)
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        test_device_counts = filtered_data.groupby('test')['device'].nunique().sort_values(ascending=True)
        height = max(400, len(test_device_counts) * 30)
        fig2 = px.bar(
            x=test_device_counts.values,
            y=test_device_counts.index,
            orientation='h',
            title='Number of Devices per Test',
            labels={'x': 'Number of Devices', 'y': 'Test'},
            template='plotly_dark',
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        fig2.update_layout(
            height=height,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.2)',
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
                mirror=True,
                tickmode='linear'
            ),
            font=dict(size=14),
            margin=dict(l=200)
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    pivot_data = pd.crosstab(
        filtered_data['device'],
        filtered_data['file']
    )
    fig3 = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns,
        y=pivot_data.index,
        colorscale=[[0, 'white'], [1, 'red']],
        text=pivot_data.values,
        texttemplate='%{text}',
        textfont={"size": 12},
        hoverongaps=False,
        hovertemplate="File: %{x}<br>Device: %{y}<br>Count: %{z}<extra></extra>",
        showscale=True,
        xgap=3,
        ygap=3
    ))
    fig3.update_layout(
        title='Device Coverage Heatmap',
        height=800,
        width=1200,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
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
        font=dict(size=14)
    )
    st.plotly_chart(fig3, use_container_width=True)
    
    st.markdown("---")
    
    st.subheader("Device Analysis")
    for device in sorted(filtered_data['device'].unique()):
        device_count = len(filtered_data[filtered_data['device'] == device].drop_duplicates())
        with st.expander(f"Device: {device} ({device_count})"):
            search_test = st.text_input(
                "Search tests",
                key=f"search_test_{device}"
            )
            
            device_data = filtered_data[filtered_data['device'] == device]
            device_table = (
                device_data[['test', 'file']]
                .drop_duplicates()
                .sort_values(['test', 'file'])
                .reset_index(drop=True)
            )
            
            if search_test:
                device_table = device_table[
                    device_table['test'].str.contains(search_test, case=False) |
                    device_table['file'].str.contains(search_test, case=False)
                ]
            
            device_table.index = device_table.index + 1
            device_table = device_table.reset_index().rename(columns={'index': 'S.No'})
            
            st.dataframe(
                device_table,
                column_config={
                    "S.No": st.column_config.NumberColumn(
                        "S.No",
                        help="Serial Number",
                        format="%d"
                    ),
                    "test": "Test Name",
                    "file": "Configuration File"
                },
                hide_index=True,
                use_container_width=True
            )
    
    st.subheader("Test Analysis")
    for test in sorted(filtered_data['test'].unique()):
        test_count = len(filtered_data[filtered_data['test'] == test].drop_duplicates())
        with st.expander(f"Test: {test} ({test_count})"):
            search_device = st.text_input(
                "Search devices",
                key=f"search_device_{test}"
            )
            
            test_data = filtered_data[filtered_data['test'] == test]
            test_table = (
                test_data[['device', 'file']]
                .drop_duplicates()
                .sort_values(['device', 'file'])
                .reset_index(drop=True)
            )
            
            if search_device:
                test_table = test_table[
                    test_table['device'].str.contains(search_device, case=False) |
                    test_table['file'].str.contains(search_device, case=False)
                ]
            
            test_table.index = test_table.index + 1
            test_table = test_table.reset_index().rename(columns={'index': 'S.No'})
            
            st.dataframe(
                test_table,
                column_config={
                    "S.No": st.column_config.NumberColumn(
                        "S.No",
                        help="Serial Number",
                        format="%d"
                    ),
                    "device": "Device Name",
                    "file": "Configuration File"
                },
                hide_index=True,
                use_container_width=True
            )
    

    if st.button("Generate Report"):
        if not filtered_data.empty:
            html_file_path = generate_device_analysis_report(
                filtered_data,
                fig1,
                fig2,
                fig3
            )
                
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            html_filename = create_dynamic_filename('device_analysis_report', [
                "_".join(selected_devices),
                "_".join(selected_tests)
            ])
            html_filename = excel_filename.replace('.xlsx', '.html')

            st.download_button(
                label="Download Report",
                data=html_content,
                file_name=html_filename,
                mime="text/html"
            )

            os.remove(html_file_path)
        else:
            st.warning("No data available to generate a report.")

if __name__ == "__main__":
    main() 
