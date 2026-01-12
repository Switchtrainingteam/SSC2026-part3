import json
import pandas as pd

# Load the initial data from CSVs to embed as default state
lob_df = pd.read_csv('SSC 2026 Data.xlsx - LOB Comparison.csv')
region_df = pd.read_csv('SSC 2026 Data.xlsx - Regional Comparison.csv')

# Convert dataframes to list of dictionaries for JSON serialization
regional_data = region_df.to_dict(orient='records')
lob_data = lob_df.to_dict(orient='records')

initial_data = {
    "regional": regional_data,
    "lob": lob_data
}

# Read the original HTML template
with open('index.html', 'r') as f:
    html_content = f.read()

# 1. Inject SheetJS library for Excel parsing in the <head>
sheetjs_script = '<script src="https://cdn.sheetjs.com/xlsx-latest/package/dist/xlsx.full.min.js"></script>'
html_content = html_content.replace('</head>', f'{sheetjs_script}\n</head>')

# 2. Inject File Input in the Header
upload_button_html = """
        <div class="header">
            <div>
                <h1>Performance Dashboard</h1>
                <p style="color: #666;">Data Source: SSC 2026 Data.xlsx</p>
            </div>
            <div style="text-align: right;">
                <label for="uploadFile" style="background: #3498db; color: white; padding: 10px 20px; border-radius: 5px; cursor: pointer; display: inline-block;">
                    <i class="fas fa-file-excel"></i> Upload Excel File
                </label>
                <input type="file" id="uploadFile" accept=".xlsx, .xls" style="display: none;" />
                <p id="fileName" style="font-size: 0.8rem; margin-top: 5px; color: #666;"></p>
            </div>
        </div>
"""
# Replace the existing header div with our new one
# We use regex or simple string replacement if the structure is known. 
# Since I know the exact string from previous step:
old_header = """<div class="header">
            <h1>Performance Dashboard</h1>
            <p style="color: #666;">Data Source: SSC 2026 Data.xlsx</p>
        </div>"""
html_content = html_content.replace(old_header, upload_button_html)

# 3. Inject the Main Logic Script before </body>
# This script handles: 
#   - Parsing the initial JSON data
#   - Rendering Charts (Chart.js)
#   - Calculating totals for Cards
#   - Handling File Upload and re-rendering
main_script = f"""
<script>
    // --- 1. Initial Data (Embedded from Python) ---
    const initialData = {json.dumps(initial_data)};

    // --- 2. State & Chart Instances ---
    let regionChartInstance = null;
    let lobChartInstance = null;

    // --- 3. Initialization ---
    document.addEventListener('DOMContentLoaded', () => {{
        processAndRender(initialData.regional, initialData.lob);
        
        // File Upload Event Listener
        document.getElementById('uploadFile').addEventListener('change', handleFileUpload);
    }});

    // --- 4. File Upload Handler ---
    function handleFileUpload(event) {{
        const file = event.target.files[0];
        if (!file) return;

        document.getElementById('fileName').textContent = file.name;

        const reader = new FileReader();
        reader.onload = function(e) {{
            const data = new Uint8Array(e.target.result);
            const workbook = XLSX.read(data, {{type: 'array'}});

            // Parse specific sheets
            // Assuming sheet names match the provided structure roughly
            // We look for sheets that likely contain "Regional" or "LOB"
            
            let regionalSheetName = workbook.SheetNames.find(n => n.toLowerCase().includes('regional'));
            let lobSheetName = workbook.SheetNames.find(n => n.toLowerCase().includes('lob') || n.toLowerCase().includes('comparison'));

            // Fallback: If not found, assume index 0 and 1 if available
            if (!regionalSheetName) regionalSheetName = workbook.SheetNames[1]; // Often 2nd sheet
            if (!lobSheetName) lobSheetName = workbook.SheetNames[0];      // Often 1st sheet

            const newRegionalData = XLSX.utils.sheet_to_json(workbook.Sheets[regionalSheetName]);
            const newLobData = XLSX.utils.sheet_to_json(workbook.Sheets[lobSheetName]);

            // Re-render dashboard
            processAndRender(newRegionalData, newLobData);
        }};
        reader.readAsArrayBuffer(file);
    }}

    // --- 5. Main Processing & Render Function ---
    function processAndRender(regionalData, lobData) {{
        renderCards(regionalData);
        renderTable(regionalData);
        renderRegionChart(regionalData);
        renderLobChart(lobData);
    }}

    // --- 6. Render Cards ---
    function renderCards(data) {{
        let totalHeadcount = 0;
        let totalPass = 0;
        let totalFail = 0;

        data.forEach(row => {{
            // Clean keys just in case (trim spaces)
            const headcount = row['Total Headcount'] || row['Total_Headcount'] || 0;
            const pass = row['Pass'] || 0;
            const fail = row['Fail'] || 0;

            totalHeadcount += parseInt(headcount);
            totalPass += parseInt(pass);
            totalFail += parseInt(fail);
        }});

        const passRate = totalHeadcount > 0 ? ((totalPass / totalHeadcount) * 100).toFixed(1) + '%' : '0%';

        // Update DOM
        // Assuming cards are in specific order: Headcount, Pass, Fail, Rate
        // We select by card-info h3
        const values = document.querySelectorAll('.card-info h3');
        if(values.length >= 4) {{
            values[0].textContent = totalHeadcount;
            values[1].textContent = totalPass;
            values[2].textContent = totalFail;
            values[3].textContent = passRate;
        }}
    }}

    // --- 7. Render Table ---
    function renderTable(data) {{
        const tbody = document.querySelector('table tbody');
        tbody.innerHTML = ''; // Clear existing

        data.forEach(row => {{
            const region = row['Region'];
            const hc = row['Total Headcount'];
            const pass = row['Pass'];
            const fail = row['Fail'];
            const rate = hc > 0 ? ((pass / hc) * 100).toFixed(1) + '%' : '0%';

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${{region}}</td>
                <td>${{hc}}</td>
                <td><span class="badge badge-green">${{pass}}</span></td>
                <td><span class="badge badge-red">${{fail}}</span></td>
                <td>${{rate}}</td>
            `;
            tbody.appendChild(tr);
        }});
    }}

    // --- 8. Render Region Chart ---
    function renderRegionChart(data) {{
        const ctx = document.getElementById('regionChart').getContext('2d');
        
        const labels = data.map(d => d.Region);
        const passData = data.map(d => d.Pass);
        const failData = data.map(d => d.Fail);

        if (regionChartInstance) regionChartInstance.destroy();

        regionChartInstance = new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: labels,
                datasets: [
                    {{
                        label: 'Pass',
                        data: passData,
                        backgroundColor: '#2ecc71'
                    }},
                    {{
                        label: 'Fail',
                        data: failData,
                        backgroundColor: '#e74c3c'
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{ beginAtZero: true }}
                }}
            }}
        }});
    }}

    // --- 9. Render LOB Chart ---
    function renderLobChart(data) {{
        // Data Structure: Result (e.g. "iPhone (Pass)"), Central, Northern...
        // Need to aggregate by Product
        
        const products = {{}}; // {{ "iPhone": {{ pass: 0, fail: 0 }}, ... }}

        data.forEach(row => {{
            const resultStr = row['Result']; // "iPhone (Pass)"
            
            // Basic parsing assuming format "Product (Status)"
            let product = "";
            let status = "";
            
            if (resultStr.includes('(')) {{
                const parts = resultStr.split('(');
                product = parts[0].trim();
                status = parts[1].replace(')', '').trim().toLowerCase();
            }} else {{
                product = resultStr;
                status = "unknown";
            }}

            // Sum up all region columns
            // We assume other columns are regions
            let count = 0;
            for (let key in row) {{
                if (key !== 'Result') {{
                    count += parseInt(row[key] || 0);
                }}
            }}

            if (!products[product]) products[product] = {{ pass: 0, fail: 0 }};
            if (status === 'pass') products[product].pass += count;
            else if (status === 'fail') products[product].fail += count;
        }});

        const labels = Object.keys(products);
        const passData = labels.map(p => products[p].pass);
        const failData = labels.map(p => products[p].fail);

        const ctx = document.getElementById('lobChart').getContext('2d');

        if (lobChartInstance) lobChartInstance.destroy();

        lobChartInstance = new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: labels,
                datasets: [
                    {{
                        label: 'Pass',
                        data: passData,
                        backgroundColor: '#2ecc71'
                    }},
                    {{
                        label: 'Fail',
                        data: failData,
                        backgroundColor: '#e74c3c'
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{ beginAtZero: true }}
                }}
            }}
        }});
    }}
</script>
"""

html_content = html_content.replace('</body>', f'{main_script}\n</body>')

# Save the final HTML
with open('dashboard.html', 'w') as f:
    f.write(html_content)
