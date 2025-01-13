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

def generate_device_analysis_report(filtered_data, fig1, fig2, fig3):
    fig1.update_layout(
        template='plotly',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='black', size=12),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)',
            tickfont=dict(color='black'),
            title_font=dict(color='black')
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)',
            tickfont=dict(color='black'),
            title_font=dict(color='black')
        ),
        title_font=dict(color='black')
    )

    fig2.update_layout(
        width=1200,
        template='plotly',
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
            mirror=True
        ),
        title='Number of Devices per Test',
        height=1600,
        font=dict(color='black', size=14)
    )

    fig3.update_layout(
        width=1200,
        template='plotly',
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
        title='Device Coverage Heatmap',
        height=800,
        font=dict(color='black', size=14)
    )

    plots_data = {}
    
    plots_data['device_test_counts'] = json.loads(pio.to_json(fig1))
    plots_data['test_device_counts'] = json.loads(pio.to_json(fig2))
    plots_data['coverage_heatmap'] = json.loads(pio.to_json(fig3))
    
    device_analysis = {}
    test_analysis = {}
    
    for device in sorted(filtered_data['device'].unique()):
        device_data = filtered_data[filtered_data['device'] == device]
        device_table = (
            device_data[['test', 'file']]
            .drop_duplicates()
            .sort_values(['test', 'file'])
            .reset_index(drop=True)
        )
        device_analysis[device] = device_table.to_dict('records')
    
    for test in sorted(filtered_data['test'].unique()):
        test_data = filtered_data[filtered_data['test'] == test]
        test_table = (
            test_data[['device', 'file']]
            .drop_duplicates()
            .sort_values(['device', 'file'])
            .reset_index(drop=True)
        )
        test_analysis[test] = test_table.to_dict('records')
    
    template = Template('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Device and Test Analysis Report</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #ffffff;
                color: #333333;
            }
            .plot-container {
                background-color: white;
                padding: 20px;
                margin: 20px 0;
                border-radius: 5px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .metrics-container {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 20px;
                margin: 20px 0;
            }
            .metric-card {
                background-color: white;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
            }
            .metric-value {
                font-size: 24px;
                font-weight: bold;
                color: #0066cc;
            }
            .metric-label {
                color: #333333;
                margin-top: 5px;
                font-weight: 500;
            }
            h1, h2 {
                color: #333333;
                margin-bottom: 20px;
            }
            .analysis-section {
                background-color: white;
                padding: 20px;
                margin: 20px 0;
                border-radius: 5px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .search-box {
                margin: 10px 0;
                padding: 8px;
                width: 100%;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            table {
                width: 100%;
                margin-top: 10px;
                border-collapse: collapse;
            }
            th {
                background-color: #f8f9fa;
                color: #333333;
                font-weight: 600;
                padding: 12px 8px;
                border-bottom: 2px solid #dee2e6;
            }
            td {
                padding: 10px 8px;
                border-bottom: 1px solid #dee2e6;
                color: #333333;
            }
            tr:hover {
                background-color: #f8f9fa;
            }
            .accordion-button {
                color: #333333;
                font-weight: 500;
            }
            .accordion-button:not(.collapsed) {
                background-color: #e7f1ff;
                color: #0066cc;
            }
        </style>
    </head>
    <body>
        <h1 class="text-center mb-4">Device and Test Analysis Report</h1>
        
        <div class="metrics-container">
            <div class="metric-card">
                <div class="metric-value">{{ metrics.total_devices }}</div>
                <div class="metric-label">Total Devices</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ metrics.total_tests }}</div>
                <div class="metric-label">Total Tests</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ metrics.total_files }}</div>
                <div class="metric-label">Configuration Files</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ metrics.total_mappings }}</div>
                <div class="metric-label">Total Mappings</div>
            </div>
        </div>

        <div class="plot-container">
            <div id="device_test_counts"></div>
        </div>
        
        <div class="plot-container">
            <div id="test_device_counts"></div>
        </div>
        
        <div class="plot-container">
            <div id="coverage_heatmap"></div>
        </div>

        <div class="analysis-section">
            <h2>Device Analysis</h2>
            <div class="accordion" id="deviceAccordion">
                {% for device, records in device_analysis.items() %}
                <div class="accordion-item">
                    <h2 class="accordion-header" id="device-heading-{{ loop.index }}">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" 
                                data-bs-target="#device-collapse-{{ loop.index }}">
                            Device: {{ device }}
                        </button>
                    </h2>
                    <div id="device-collapse-{{ loop.index }}" class="accordion-collapse collapse" 
                         data-bs-parent="#deviceAccordion">
                        <div class="accordion-body">
                            <input type="text" class="search-box" placeholder="Search tests..."
                                   onkeyup="filterTable(this, 'device-table-{{ loop.index }}')">
                            <table id="device-table-{{ loop.index }}">
                                <thead>
                                    <tr>
                                        <th>S.No</th>
                                        <th>Test Name</th>
                                        <th>Configuration File</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for record in records %}
                                    <tr>
                                        <td>{{ loop.index }}</td>
                                        <td>{{ record.test }}</td>
                                        <td>{{ record.file }}</td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="analysis-section">
            <h2>Test Analysis</h2>
            <div class="accordion" id="testAccordion">
                {% for test, records in test_analysis.items() %}
                <div class="accordion-item">
                    <h2 class="accordion-header" id="test-heading-{{ loop.index }}">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" 
                                data-bs-target="#test-collapse-{{ loop.index }}">
                            Test: {{ test }}
                        </button>
                    </h2>
                    <div id="test-collapse-{{ loop.index }}" class="accordion-collapse collapse" 
                         data-bs-parent="#testAccordion">
                        <div class="accordion-body">
                            <input type="text" class="search-box" placeholder="Search devices..."
                                   onkeyup="filterTable(this, 'test-table-{{ loop.index }}')">
                            <table id="test-table-{{ loop.index }}">
                                <thead>
                                    <tr>
                                        <th>S.No</th>
                                        <th>Device Name</th>
                                        <th>Configuration File</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for record in records %}
                                    <tr>
                                        <td>{{ loop.index }}</td>
                                        <td>{{ record.device }}</td>
                                        <td>{{ record.file }}</td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <script>
            var plots_data = {{ plots_data|tojson }};
            
            Plotly.newPlot('device_test_counts', plots_data.device_test_counts.data, plots_data.device_test_counts.layout);
            Plotly.newPlot('test_device_counts', plots_data.test_device_counts.data, plots_data.test_device_counts.layout);
            Plotly.newPlot('coverage_heatmap', plots_data.coverage_heatmap.data, plots_data.coverage_heatmap.layout);

            function filterTable(input, tableId) {
                var filter = input.value.toLowerCase();
                var table = document.getElementById(tableId);
                var rows = table.getElementsByTagName("tr");

                for (var i = 1; i < rows.length; i++) {
                    var show = false;
                    var cells = rows[i].getElementsByTagName("td");
                    for (var j = 0; j < cells.length; j++) {
                        var cell = cells[j];
                        if (cell) {
                            var text = cell.textContent || cell.innerText;
                            if (text.toLowerCase().indexOf(filter) > -1) {
                                show = true;
                                break;
                            }
                        }
                    }
                    rows[i].style.display = show ? "" : "none";
                }
            }
        </script>
    </body>
    </html>
    ''')
    
    metrics = {
        'total_devices': len(filtered_data['device'].unique()),
        'total_tests': len(filtered_data['test'].unique()),
        'total_files': len(filtered_data['file'].unique()),
        'total_mappings': len(filtered_data)
    }
    
    template_vars = {
        'plots_data': plots_data,
        'device_analysis': device_analysis,
        'test_analysis': test_analysis,
        'metrics': metrics
    }
    
    html_content = template.render(**template_vars)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as f:
        f.write(html_content)
        return f.name

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
                    
            st.download_button(
                label="Download Report",
                data=html_content,
                file_name="device_analysis_report.html",
                mime="text/html"
            )
                
            os.remove(html_file_path)
        else:
            st.warning("No data available to generate a report.")

if __name__ == "__main__":
    main() 