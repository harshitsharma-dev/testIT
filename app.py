from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from config import Config
from network_config import IntelligentConfigGenerator
import traceback

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialize the configuration generator
config_generator = IntelligentConfigGenerator()

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate_config():
    """API endpoint to generate network configuration"""
    try:
        # Get the input text from request
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'success': False,
                'error': 'No input text provided'
            }), 400
        
        input_text = data['text'].strip()
        
        if not input_text:
            return jsonify({
                'success': False,
                'error': 'Input text cannot be empty'
            }), 400
        
        # Generate configuration
        config_output = config_generator.generate_configuration(input_text)
        
        # Extract entities for analysis (optional)
        entities = config_generator.entity_extractor.extract_comprehensive_entities(input_text)
        
        # Return the result
        return jsonify({
            'success': True,
            'input': input_text,
            'output': config_output,
            'analysis': {
                'user_vlans': entities['user_vlans'],
                'network_vlans': entities['network_vlans'],
                'lines': entities['lines'],
                'forwarder_type': entities['forwarder_type'],
                'is_multi_line': entities['is_multi_line'],
                'is_untagged': entities['is_untagged'],
                'protocols': entities['protocols']
            }
        })
        
    except Exception as e:
        # Log the error for debugging
        print(f"Error generating configuration: {str(e)}")
        print(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

@app.route('/api/examples')
def get_examples():
    """Get example test procedures"""
    examples = [
        "Configure DUT for a Service with 1:1 Forwarder and Ensure that bi-directional Traffic is fine.",
        "Configure DUT for a Service with N:1 Forwarder and Ensure that bi-directional Traffic is fine for all Lines",
        "1. Configure DUT with User Side VSI with VLAN 100 on Line1\n2. Configure DUT with Network Side VSI with VLAN 200 on Uplink1\n3. Send Upstream Traffic with VLAN100 and PBIT 5\n4. Send Downstream Traffic with VLAN200 and PBIT 7",
        "Configure DUT for a service with 1:1 Forwarder for first 8 lines and N:1 Forwarder for remaining 8 lines",
        "1. Configure DUT with User Side VSI with VLAN Identifier 110 for line 10\n2. Configure DUT with Network Side VSI with VLAN 401 on Uplink1\n3. Validate bi-directional Ipv6 Traffic",
        "Configure DUT for a service with N:1 forwarder for the line 1 with Untagged VLAN ID."
    ]
    
    return jsonify({
        'success': True,
        'examples': examples
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Network Configuration Generator'
    })

if __name__ == '__main__':
    # Handle cloud deployment ports
    import os
    port = int(os.environ.get('PORT', app.config['PORT']))
    host = os.environ.get('HOST', app.config['HOST'])
    
    app.run(
        host=host,
        port=port,
        debug=app.config['DEBUG']
    )
