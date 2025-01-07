# Linux Kernel Build and Test Dashboard

## Overview
The `app.py` script is a Streamlit application designed to visualize and analyze Linux kernel build and test data. It provides interactive dashboards and generates reports based on YAML configuration files.

## Features
- Interactive dashboards for visualizing build and test data.
- Heatmaps, pie charts, line charts, and scatter plots for data analysis.
- Report generation with embedded plots.

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/EeshanV/Device-Test-Analysis.git
   ```

2. **Navigate to the project directory:**
   ```bash
   cd Device-Test-Analysis
   ```

3. **Install the required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run the Streamlit application:**
   ```bash
   streamlit run Main_Dashboard.py
   ```

2. **Interact with the dashboard:**
   - Use the sidebar to filter data by build names, test names, job names, architectures and Devices.
   - Visualize the data using various plots:
     - **Toolchain vs Job Name and Architecture Heatmap**
     - **Target Architecture Distribution Pie Chart**
     - **Toolchain Distribution Bar Chart**
     - **Builds vs Tests Scatter Plot**
     - **Number of Tests per Job Line Chart**

## Dependencies
The application relies on the following Python packages:
- streamlit
- streamlit-extras
- pandas
- plotly
- PyYAML
- requests
- beautifulsoup4
- xlsxwriter
- kaleido

These are listed in the `requirements.txt` file and can be installed using `pip`.
