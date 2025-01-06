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
                        test_names = test.get('tests', [])
                        if not isinstance(test_names, list):
                            test_names = [str(test_names)] if test_names else []
                        
                        for test_name in test_names:
                            job_data.append({
                                'job_name': job_name,
                                'build_name': build_name,
                                'test_name': test_name,
                                'target_arch': build.get('target_arch', 'Unknown'),
                                'toolchain': build.get('toolchain', 'Unknown')
                            })
    return job_data

def create_test_count_graph(yaml_files):
    test_counts = []
    test_details = []
    
    for yaml_file in yaml_files:
        data = load_yaml_data(yaml_file)
        if data:
            job_data = extract_job_data(data)
            if job_data:
                df = pd.DataFrame(job_data)
                unique_tests = df['test_name'].nunique()
                filename = yaml_file.split('/')[-1]
                
                test_counts.append({
                    'filename': filename,
                    'test_count': unique_tests
                })
                
                test_list = df['test_name'].unique().tolist()
                test_details.append({
                    'File': filename,
                    'Test Count': unique_tests,
                    'Tests': ', '.join(sorted(test_list))
                })
    
    return pd.DataFrame(test_counts), pd.DataFrame(test_details)

def main():
    st.title("Test Count Analysis")
    
    BASE_URL = "https://people.linaro.org/~naresh.kamboju/lkft-common/tuxconfig/"
    yaml_files = get_yaml_files_from_url(BASE_URL)
    
    if yaml_files:
        with st.spinner("Analyzing test counts across files..."):
            df_counts, df_details = create_test_count_graph(yaml_files)
            
            if not df_counts.empty:
                fig = px.line(
                    df_counts,
                    x='filename',
                    y='test_count',
                    title='Number of Unique Tests per File',
                    markers=True
                )
                
                fig.update_layout(
                    xaxis_title="File",
                    yaxis_title="Number of Unique Tests",
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
                    height=600,
                    showlegend=False,
                    hovermode='x unified',
                    font=dict(size=14),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.subheader("Summary Statistics")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Average Tests per File", 
                             f"{df_counts['test_count'].mean():.1f}")
                with col2:
                    st.metric("Maximum Tests", 
                             int(df_counts['test_count'].max()))
                with col3:
                    st.metric("Total Unique Files", 
                             len(df_counts))
                
                st.subheader("Detailed Test Information")
                search_term = st.text_input("Search for specific tests:")
                if search_term:
                    filtered_details = df_details[
                        df_details['Tests'].str.contains(search_term, case=False, na=False)
                    ]
                else:
                    filtered_details = df_details
                
                st.dataframe(filtered_details, use_container_width=True)
            else:
                st.warning("No test information found.")
    else:
        st.error("No YAML files found at the specified URL")

if __name__ == "__main__":
    main() 