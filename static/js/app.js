// Network Configuration Generator JavaScript
class NetworkConfigApp {
    constructor() {
        this.isStaticDeployment = window.location.hostname.includes('github.io');
        this.initializeElements();
        this.loadExamples();
        this.bindEvents();
        
        // Handle static deployment
        if (this.isStaticDeployment) {
            this.setupStaticMode();
        }
    }
    
    setupStaticMode() {
        // Disable generate button and show message
        const generateBtn = document.getElementById('generateBtn');
        if (generateBtn) {
            generateBtn.disabled = true;
            generateBtn.textContent = '🚀 Generate Configuration (Requires Local Setup)';
        }
    }

    initializeElements() {
        this.form = document.getElementById('configForm');
        this.inputText = document.getElementById('inputText');
        this.generateBtn = document.getElementById('generateBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.copyBtn = document.getElementById('copyBtn');
        this.outputSection = document.getElementById('outputSection');
        this.analysisSection = document.getElementById('analysisSection');
        this.analysisContent = document.getElementById('analysisContent');
        this.examplesList = document.getElementById('examplesList');
    }

    bindEvents() {
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        this.clearBtn.addEventListener('click', () => this.clearAll());
        this.copyBtn.addEventListener('click', () => this.copyOutput());
    }    async handleSubmit(e) {
        e.preventDefault();
        
        const inputText = this.inputText.value.trim();
        if (!inputText) {
            this.showAlert('Please enter a test procedure.', 'warning');
            return;
        }

        // Handle static deployment
        if (this.isStaticDeployment) {
            this.showStaticMessage();
            return;
        }

        this.setLoading(true);

        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: inputText })
            });

            const data = await response.json();

            if (data.success) {
                this.displayResults(data);
            } else {
                this.showAlert(`Error: ${data.error}`, 'danger');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Failed to generate configuration. Please try again.', 'danger');
        } finally {
            this.setLoading(false);
        }
    }

    displayResults(data) {
        // Display configuration output
        this.outputSection.innerHTML = `
            <div class="config-output">${this.escapeHtml(data.output)}</div>
        `;
        
        this.copyBtn.style.display = 'inline-block';

        // Display analysis
        if (data.analysis) {
            this.displayAnalysis(data.analysis);
        }

        this.showAlert('Configuration generated successfully!', 'success');
    }

    displayAnalysis(analysis) {
        const analysisHtml = `
            <div class="analysis-grid">
                <div class="analysis-item">
                    <h6><i class="fas fa-list-ol"></i> Lines</h6>
                    <div class="analysis-value">${Array.isArray(analysis.lines) ? analysis.lines.join(', ') : analysis.lines}</div>
                </div>
                <div class="analysis-item">
                    <h6><i class="fas fa-exchange-alt"></i> Forwarder Type</h6>
                    <div class="analysis-value">${analysis.forwarder_type}</div>
                </div>
                <div class="analysis-item">
                    <h6><i class="fas fa-tag"></i> User VLANs</h6>
                    <div class="analysis-value">${Array.isArray(analysis.user_vlans) && analysis.user_vlans.length > 0 ? analysis.user_vlans.join(', ') : 'Auto-generated'}</div>
                </div>
                <div class="analysis-item">
                    <h6><i class="fas fa-network-wired"></i> Network VLANs</h6>
                    <div class="analysis-value">${Array.isArray(analysis.network_vlans) && analysis.network_vlans.length > 0 ? analysis.network_vlans.join(', ') : 'Auto-generated'}</div>
                </div>
                <div class="analysis-item">
                    <h6><i class="fas fa-sitemap"></i> Multi-line</h6>
                    <div class="analysis-value">${analysis.is_multi_line ? 'Yes' : 'No'}</div>
                </div>
                <div class="analysis-item">
                    <h6><i class="fas fa-unlink"></i> Untagged</h6>
                    <div class="analysis-value">${analysis.is_untagged ? 'Yes' : 'No'}</div>
                </div>
                <div class="analysis-item">
                    <h6><i class="fas fa-globe"></i> Protocols</h6>
                    <div class="analysis-value">${Array.isArray(analysis.protocols) && analysis.protocols.length > 0 ? analysis.protocols.join(', ') : 'Standard Ethernet'}</div>
                </div>
            </div>
        `;
        
        this.analysisContent.innerHTML = analysisHtml;
        this.analysisSection.style.display = 'block';
    }

    async loadExamples() {
        try {
            const response = await fetch('/api/examples');
            const data = await response.json();

            if (data.success && data.examples) {
                this.renderExamples(data.examples);
            }
        } catch (error) {
            console.error('Error loading examples:', error);
            this.examplesList.innerHTML = '<p class="text-muted">Error loading examples</p>';
        }
    }

    renderExamples(examples) {
        this.examplesList.innerHTML = examples.map(example => `
            <div class="example-item" onclick="app.useExample('${this.escapeForJs(example)}')">
                ${example.length > 80 ? example.substring(0, 80) + '...' : example}
            </div>
        `).join('');
    }

    useExample(example) {
        this.inputText.value = example;
        this.inputText.focus();
    }

    clearAll() {
        this.inputText.value = '';
        this.outputSection.innerHTML = `
            <div class="text-muted text-center py-5">
                <i class="fas fa-arrow-left fa-2x mb-3"></i>
                <p>Enter a test procedure and click "Generate Configuration" to see the results here.</p>
            </div>
        `;
        this.copyBtn.style.display = 'none';
        this.analysisSection.style.display = 'none';
        this.inputText.focus();
    }

    copyOutput() {
        const configText = this.outputSection.querySelector('.config-output').textContent;
        navigator.clipboard.writeText(configText).then(() => {
            const originalText = this.copyBtn.innerHTML;
            this.copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
            this.copyBtn.classList.remove('btn-outline-primary');
            this.copyBtn.classList.add('btn-success');
            
            setTimeout(() => {
                this.copyBtn.innerHTML = originalText;
                this.copyBtn.classList.remove('btn-success');
                this.copyBtn.classList.add('btn-outline-primary');
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy:', err);
            this.showAlert('Failed to copy to clipboard', 'warning');
        });
    }

    setLoading(loading) {
        if (loading) {
            this.generateBtn.disabled = true;
            this.generateBtn.innerHTML = '<span class="loading-spinner"></span> Generating...';
            this.outputSection.innerHTML = `
                <div class="text-center py-5">
                    <div class="loading-spinner mb-3" style="width: 2rem; height: 2rem;"></div>
                    <p class="text-muted">Analyzing test procedure and generating configuration...</p>
                </div>
            `;
        } else {
            this.generateBtn.disabled = false;
            this.generateBtn.innerHTML = '<i class="fas fa-cogs"></i> Generate Configuration';
        }
    }

    showAlert(message, type) {
        // Remove existing alerts
        const existingAlerts = document.querySelectorAll('.alert-custom');
        existingAlerts.forEach(alert => alert.remove());

        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-custom alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Insert after the header
        const header = document.querySelector('header');
        header.parentNode.insertBefore(alert, header.nextSibling);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }        }, 5000);
    }

    showStaticMessage() {
        // Show static deployment message
        this.outputSection.style.display = 'block';
        
        const outputDiv = document.getElementById('output');
        if (outputDiv) {
            outputDiv.innerHTML = `
                <div class="alert alert-info">
                    <h4>🌐 GitHub Pages Static Demo</h4>
                    <p>This is a static demonstration of the Network Configuration Generator. To use the full functionality with live processing:</p>
                    <ol>
                        <li>Clone the repository: <code>git clone https://github.com/harshitsharma-dev/testIT.git</code></li>
                        <li>Install dependencies: <code>pip install -r requirements.txt</code></li>
                        <li>Run the Flask app: <code>python app.py</code></li>
                        <li>Open <code>http://localhost:5000</code> in your browser</li>
                    </ol>
                    <p><strong>Repository:</strong> <a href="https://github.com/harshitsharma-dev/testIT" target="_blank">https://github.com/harshitsharma-dev/testIT</a></p>
                </div>
                <div class="config-output">
                    <h3>Sample Output Preview:</h3>
                    <pre class="code-block">
=== Network Configuration Generator ===
Input: "${this.escapeForJs(this.inputText.value)}"

[Analysis would show here]
- User VLANs: Auto-detected
- Network VLANs: Auto-detected  
- Lines: Auto-detected
- Forwarder Type: Auto-detected

[VSI Configuration would be generated here]
[Traffic Configuration would be generated here]

To see actual generated configurations, run locally!
                    </pre>
                </div>
            `;
        }
        
        // Show copy button
        this.copyBtn.style.display = 'inline-block';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    escapeForJs(text) {
        return text.replace(/'/g, "\\'").replace(/"/g, '\\"').replace(/\n/g, '\\n').replace(/\r/g, '\\r');
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new NetworkConfigApp();
});
