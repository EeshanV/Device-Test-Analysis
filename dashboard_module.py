import plotly.express as px
import json
import plotly.io as pio
import tempfile
from jinja2 import Template

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


########################################################

def generate_device_analysis_report(filtered_data, fig1, fig2, fig3):
    """
    Generates an HTML report for device and test analysis.

    Args:
        filtered_data (pd.DataFrame): The filtered data for analysis.
        fig1 (go.Figure): Plotly figure for device test counts.
        fig2 (go.Figure): Plotly figure for test device counts.
        fig3 (go.Figure): Plotly figure for device coverage heatmap.

    Returns:
        str: The file path to the generated HTML report.
    """
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
