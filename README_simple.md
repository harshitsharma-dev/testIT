# Network Configuration Generator

A Flask web application that automatically generates network configuration and traffic test procedures from natural language descriptions.

## 🚀 Features

- **Intelligent Text Parsing**: Extracts network entities (VLANs, lines, forwarders, protocols) from natural language
- **Multi-Forwarder Support**: Handles 1:1, N:1, and mixed forwarder configurations
- **Protocol Detection**: Supports IPv6, PPPoE, and standard Ethernet protocols
- **Traffic Generation**: Creates comprehensive upstream and downstream traffic configurations
- **Web Interface**: Clean, responsive web UI for easy interaction
- **RESTful API**: JSON API endpoints for programmatic access

## 📋 Requirements

- Python 3.9+
- Flask 2.3.3
- pandas 2.0.3
- numpy 1.24.3

## 🛠️ Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/network-config-generator.git
   cd network-config-generator
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open your browser**
   ```
   http://localhost:5000
   ```

## 📁 Project Structure

```
network-config-generator/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── network_config.py     # Core configuration generation logic
├── requirements.txt      # Python dependencies
├── .env                 # Environment variables (optional)
├── .gitignore          # Git ignore rules
├── templates/
│   └── index.html      # Main web interface
└── static/
    ├── css/
    │   └── style.css   # Styling
    └── js/
        └── app.js      # Frontend JavaScript
```

## 🌐 Usage

### Web Interface
1. Enter your test procedure in the text area
2. Click "Generate Config" to process
3. View the generated VSI and traffic configurations
4. Use example procedures to get started

### API Endpoints

- `POST /api/generate` - Generate configuration from text
- `GET /api/examples` - Get example procedures
- `GET /health` - Health check

### Example Input
```
Configure DUT for a Service with 1:1 Forwarder and Ensure that bi-directional Traffic is fine for all 16 lines
```

### Example Output
```
Entity1 = DUT
Entity1 Keywords =
UserVSI-1 = VLAN=101, PBIT=0
UserVSI-1 Parent = Line1
...
NetworkVSI-1 = VLAN=101, PBIT=0
NetworkVSI-1 Parent = Uplink1
Forwarder-1 1:1
```

## 🚀 Deployment

### GitHub
1. Create a new repository on GitHub
2. Push your code:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/network-config-generator.git
   git push -u origin main
   ```

### Heroku (Optional)
1. Install Heroku CLI
2. Login and create app:
   ```bash
   heroku login
   heroku create your-app-name
   git push heroku main
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔧 Configuration

The application can be configured via environment variables:
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 5000)
- `DEBUG`: Debug mode (default: False)
