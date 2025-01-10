import streamlit as st
import pandas as pd
import plotly.express as px
import yaml
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://people.linaro.org/~naresh.kamboju/lkft-common/tuxconfig/"

@st.cache_data
def get_yaml_files_from_url(url):
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
    try:
        response = requests.get(file_path)
        response.raise_for_status()
        return yaml.safe_load(response.text)
    except Exception as e:
        st.error(f"Error loading YAML file: {e}")
        return None

def extract_data(yaml_data, file_name):
    data = []
    
    for job in yaml_data.get('jobs', []):
        job_name = job.get('name', 'Unknown')
        
        for test in job.get('tests', []):
            device = test.get('device')
            if not device:
                continue
                
            tests = test.get('tests', [])
            if not isinstance(tests, list):
                tests = [tests]
            
            for test_name in tests:
                if test_name:
                    data.append({
                        'device': device,
                        'test': str(test_name),
                        'file': file_name
                    })
        
        for build in job.get('builds', []):
            build_name = build.get('build_name', '')
            
            for test in build.get('tests', []):
                device = test.get('device')
                if not device:
                    continue
                    
                tests = test.get('tests', [])
                if not isinstance(tests, list):
                    tests = [tests]
                
                for test_name in tests:
                    if test_name:
                        data.append({
                            'device': device,
                            'test': str(test_name),
                            'file': file_name
                        })
            
            if build.get('targets'):
                targets = build.get('targets', [])
                if isinstance(targets, list):
                    for target in targets:
                        if 'test' in target.lower() or target in ['perf', 'kselftest']:
                            devices = set()
                            for test in build.get('tests', []):
                                device = test.get('device')
                                if device:
                                    devices.add(device)
                            
                            for device in devices:
                                data.append({
                                    'device': device,
                                    'test': target,
                                    'file': file_name
                                })
    
    return pd.DataFrame(data)

def main():
    st.set_page_config(layout="wide")
    
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
        st.metric("Total Devices", len(filtered_data['device'].unique()))
    with col2:
        st.metric("Total Tests", len(filtered_data['test'].unique()))
    
    st.subheader("Device Analysis")
    for device in sorted(filtered_data['device'].unique()):
        with st.expander(f"Device: {device}"):
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
        with st.expander(f"Test: {test}"):
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

if __name__ == "__main__":
    main() 