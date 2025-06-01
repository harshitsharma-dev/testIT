# Network Configuration Generator

A Flask web application that automatically generates network configuration and traffic test procedures from natural language descriptions.

🚀 **Deploy to Vercel:** [One-click deployment with live backend](VERCEL_DEPLOYMENT.md)

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

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/harshitsharma-dev/testIT.git
   cd testIT
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

### ☁️ Deploy to Vercel (Recommended)

For a live deployment with full backend functionality:

1. **Fork this repository** to your GitHub account
2. **Sign up at [Vercel](https://vercel.com)** (free)
3. **Import your repository** in Vercel dashboard
4. **Deploy** - Your app will be live in minutes!

📖 **Detailed Guide:** [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md)

## 📁 Project Structure

```
network-config-generator/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── network_config.py     # Core configuration generation logic
├── requirements.txt      # Python dependencies
├── .env                 # Environment variables (optional)
├── .gitignore          # Git ignore rules
├── .github/
│   └── workflows/      # GitHub Actions for deployment
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

### Vercel (Recommended)
Deploy your Flask app to Vercel for a live backend with serverless functions:

1. **Fork this repository** to your GitHub account
2. **Sign up at [Vercel](https://vercel.com)** (free account)
3. **Import your repository** in Vercel dashboard
4. **Click Deploy** - Your app will be live in minutes!

✅ **Full functionality**: Working Flask backend, API endpoints, and database processing  
✅ **Automatic HTTPS**: Secure connection included  
✅ **Custom domains**: Add your own domain if needed  
✅ **Auto-deployment**: Updates on every git push  

📖 **Detailed Guide**: [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md)

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