import streamlit as st
import pandas as pd
import plotly.express as px
import yaml
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

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
        if file_path.startswith(('http://', 'https://')):
            response = requests.get(file_path)
            response.raise_for_status()
            return yaml.safe_load(response.text)
        else:
            with open(file_path, 'r') as file:
                return yaml.safe_load(file)
    except Exception as e:
        st.error(f"Error loading YAML file: {e}")
        return None

@st.cache_data
def extract_job_data(data):
    job_data = []
    if data:
        for job in data.get('jobs', []):
            job_name = job['name']
            for build in job.get('builds', []):
                build_name = build.get('build_name', 'Unnamed Build')
                test_lists = []
                if 'tests' in job:
                    test_lists.append(job['tests'])
                if 'tests' in build:
                    test_lists.append(build['tests'])
                
                for test_list in test_lists:
                    for test in test_list:
                        device = test.get('device', 'Unknown')
                        if isinstance(device, dict):
                            device = device.get('name', 'Unknown')
                        elif not device:
                            device = 'Unknown'
                            
                        test_names = test.get('tests', [])
                        if not isinstance(test_names, list):
                            test_names = [str(test_names)] if test_names else []
                        
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

def create_device_count_graph(yaml_files):
    device_counts = []
    
    for yaml_file in yaml_files:
        data = load_yaml_data(yaml_file)
        if data:
            job_data = extract_job_data(data)
            if job_data:
                df = pd.DataFrame(job_data)
                if 'device' in df.columns:
                    unique_devices = df['device'].nunique()
                    filename = yaml_file.split('/')[-1]
                    device_counts.append({
                        'filename': filename,
                        'device_count': unique_devices
                    })
    
    if device_counts:
        df_counts = pd.DataFrame(device_counts)
        
        fig = px.line(
            df_counts,
            x='filename',
            y='device_count',
            title='Number of Devices',
            markers=True
        )
        
        fig.update_layout(
            xaxis_title="File",
            yaxis_title="Number of Devices",
            xaxis_tickangle=45,
            height=600,
            showlegend=False,
            hovermode='x unified'
        )
        
        return fig
    return None

def main():
    st.title("Device Analysis Dashboard")
    
    BASE_URL = "https://people.linaro.org/~naresh.kamboju/lkft-common/tuxconfig/"
    yaml_files = get_yaml_files_from_url(BASE_URL)
    
    if yaml_files:
        with st.spinner("Analyzing device counts across files..."):
            fig = create_device_count_graph(yaml_files)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No device information found.")
            
            data = []
            for yaml_file in yaml_files:
                yaml_data = load_yaml_data(yaml_file)
                if yaml_data:
                    job_data = extract_job_data(yaml_data)
                    if job_data:
                        df = pd.DataFrame(job_data)
                        if 'device' in df.columns:
                            devices = df['device'].unique().tolist()
                            data.append({
                                'File': yaml_file.split('/')[-1],
                                'Device Count': len(devices),
                                'Devices': ', '.join(devices)
                            })
            
            if data:
                df_details = pd.DataFrame(data)
                st.subheader("Detailed Information")
                st.dataframe(df_details, use_container_width=True)
            else:
                st.warning("No device information available in the data.")
    else:
        st.error("No YAML files found at the specified URL")

if __name__ == "__main__":
    main() 