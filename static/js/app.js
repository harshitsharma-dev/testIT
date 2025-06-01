// Network Configuration Generator JavaScript
class NetworkConfigApp {
    constructor() {
        this.initializeElements();
        this.loadExamples();
        this.bindEvents();
    }    initializeElements() {
        this.form = document.getElementById('configForm');
        this.inputText = document.getElementById('inputText');
        this.generateBtn = document.getElementById('generateBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.copyBtn = document.getElementById('copyBtn');
        this.outputSection = document.getElementById('outputSection');
        this.analysisSection = document.getElementById('analysisSection');
        this.analysisContent = document.getElementById('analysisContent');
        this.examplesList = document.getElementById('examplesList');
    }bindEvents() {
        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }
        if (this.clearBtn) {
            this.clearBtn.addEventListener('click', () => this.clearAll());
        }
        if (this.copyBtn) {
            this.copyBtn.addEventListener('click', () => this.copyOutput());
        }
    }    async handleSubmit(e) {
        e.preventDefault();
        
        const inputText = this.inputText.value.trim();
        if (!inputText) {
            this.showAlert('Please enter a test procedure.', 'warning');
            return;
        }

        this.setLoading(true);        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ input_text: inputText })
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
    }    displayResults(data) {
        // Display configuration output
        this.outputSection.innerHTML = `
            <div class="config-output">${this.escapeHtml(data.configuration)}</div>
        `;
        
        this.copyBtn.style.display = 'inline-block';

        // Display analysis/entities
        if (data.entities) {
            this.displayAnalysis(data.entities);
        }

        this.showAlert('Configuration generated successfully!', 'success');
    }    displayAnalysis(entities) {
        const analysisHtml = `
            <div class="analysis-grid">
                <div class="analysis-item">
                    <h6><i class="fas fa-list-ol"></i> Lines</h6>
                    <div class="analysis-value">${Array.isArray(entities.lines) && entities.lines.length > 0 ? entities.lines.join(', ') : 'Not specified'}</div>
                </div>
                <div class="analysis-item">
                    <h6><i class="fas fa-exchange-alt"></i> Forwarder Type</h6>
                    <div class="analysis-value">${entities.forwarder_type || 'N:1'}</div>
                </div>
                <div class="analysis-item">
                    <h6><i class="fas fa-tag"></i> User VLANs</h6>
                    <div class="analysis-value">${Array.isArray(entities.user_vlans) && entities.user_vlans.length > 0 ? entities.user_vlans.join(', ') : 'Auto-generated'}</div>
                </div>
                <div class="analysis-item">
                    <h6><i class="fas fa-network-wired"></i> Network VLANs</h6>
                    <div class="analysis-value">${Array.isArray(entities.network_vlans) && entities.network_vlans.length > 0 ? entities.network_vlans.join(', ') : 'Auto-generated'}</div>
                </div>
                <div class="analysis-item">
                    <h6><i class="fas fa-sitemap"></i> Multi-line</h6>
                    <div class="analysis-value">${entities.is_multi_line ? 'Yes' : 'No'}</div>
                </div>
                <div class="analysis-item">
                    <h6><i class="fas fa-unlink"></i> Untagged</h6>
                    <div class="analysis-value">${entities.is_untagged ? 'Yes' : 'No'}</div>
                </div>
                <div class="analysis-item">
                    <h6><i class="fas fa-globe"></i> Protocols</h6>
                    <div class="analysis-value">${Array.isArray(entities.protocols) && entities.protocols.length > 0 ? entities.protocols.join(', ') : 'Standard Ethernet'}</div>
                </div>
                <div class="analysis-item">
                    <h6><i class="fas fa-cogs"></i> Services</h6>
                    <div class="analysis-value">${entities.is_multi_service ? `Multi-service (${entities.service_count || 'Auto'})` : 'Single service'}</div>
                </div>
            </div>
        `;
        
        this.analysisContent.innerHTML = analysisHtml;
        this.analysisSection.style.display = 'block';
    }    async loadExamples() {
        try {
            // Hardcoded examples since the server doesn't have an examples endpoint
            const examples = [
                "Configure DUT for a Service with 1:1 Forwarder and Ensure that bi-directional Traffic is fine.",
                "1. Configure DUT with User Side VSI with VLAN 100 on Line1\n2. Configure DUT with Network Side VSI with VLAN 200 on Uplink1\n3. Send Upstream Traffic with VLAN100 and PBIT 5",
                "Configure 2 Services per line2, 3 lines with N:1 forwarder. Send bidirectional traffic with VLAN 4000 and PBIT 0 to 7.",
                "Configure DUT with User Side VSI with untagged on Line1 and Network Side VSI with VLAN 200 on Uplink1.",
                "Test multi-service scenario: 3 services per line on Line1, Line2, Line3 with different VLANs and PBITs."
            ];
            
            this.renderExamples(examples);
        } catch (error) {
            console.error('Error loading examples:', error);
            if (this.examplesList) {
                this.examplesList.innerHTML = '<p class="text-muted">Error loading examples</p>';
            }
        }
    }renderExamples(examples) {
        if (!this.examplesList) return;
        
        this.examplesList.innerHTML = examples.map(example => `
            <div class="example-item" onclick="app.useExample('${this.escapeForJs(example)}')">
                ${example.length > 80 ? example.substring(0, 80) + '...' : example}
            </div>
        `).join('');
    }

    useExample(example) {
        if (this.inputText) {
            this.inputText.value = example;
            this.inputText.focus();
        }
    }clearAll() {
        if (this.inputText) {
            this.inputText.value = '';
            this.inputText.focus();
        }
        if (this.outputSection) {
            this.outputSection.innerHTML = `
                <div class="text-muted text-center py-5">
                    <i class="fas fa-arrow-left fa-2x mb-3"></i>
                    <p>Enter a test procedure and click "Generate Configuration" to see the results here.</p>
                </div>
            `;
        }
        if (this.copyBtn) {
            this.copyBtn.style.display = 'none';
        }
        if (this.analysisSection) {
            this.analysisSection.style.display = 'none';
        }
    }

    copyOutput() {
        if (!this.outputSection) return;
        
        const configOutput = this.outputSection.querySelector('.config-output');
        if (!configOutput) return;
        
        const configText = configOutput.textContent;
        navigator.clipboard.writeText(configText).then(() => {
            if (this.copyBtn) {
                const originalText = this.copyBtn.innerHTML;
                this.copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                this.copyBtn.classList.remove('btn-outline-primary');
                this.copyBtn.classList.add('btn-success');
                
                setTimeout(() => {
                    this.copyBtn.innerHTML = originalText;
                    this.copyBtn.classList.remove('btn-success');
                    this.copyBtn.classList.add('btn-outline-primary');
                }, 2000);
            }
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
    }    escapeHtml(text) {
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
