# 🚀 Vercel Deployment Guide

Deploy your Network Configuration Generator Flask app to Vercel with a live backend.

## Prerequisites

1. **GitHub Repository**: Your code must be pushed to GitHub
2. **Vercel Account**: Sign up at [vercel.com](https://vercel.com) (free)

## Deployment Steps

### 1. Connect GitHub to Vercel

1. Go to [vercel.com](https://vercel.com) and sign up/login
2. Click "New Project"
3. Import your GitHub repository: `harshitsharma-dev/testIT`

### 2. Configure Project Settings

Vercel will automatically detect it's a Python project. The deployment configuration is already set up in `vercel.json`.

### 3. Deploy

1. Click "Deploy" 
2. Wait for deployment to complete (~2-3 minutes)
3. Your app will be live at: `https://your-project-name.vercel.app`

## ✅ What's Included

- ✅ **Live Flask Backend**: Full API functionality with `/api/generate` and `/api/examples`
- ✅ **Static Assets**: CSS, JavaScript, and images served efficiently
- ✅ **Automatic HTTPS**: Secure connection included
- ✅ **Custom Domain**: Add your own domain if needed
- ✅ **Automatic Updates**: Redeploys on every git push

## 🔧 Configuration Files

The deployment uses these files (already configured):

- `vercel.json` - Vercel deployment configuration
- `requirements.txt` - Python dependencies  
- `app.py` - Flask application (Vercel-ready)

## 🌐 Live Backend Features

Once deployed on Vercel, your app will have:

- **Full Flask API**: Real-time network configuration generation
- **Working Examples**: Dynamic example loading from backend
- **Interactive UI**: Complete functionality with live processing
- **Fast Performance**: Serverless functions with quick cold starts

## 📝 Environment Variables (Optional)

If you need custom configuration, add these in Vercel dashboard:

- `FLASK_ENV=production`
- `DEBUG=False`

## 🎯 Testing Your Deployment

1. Visit your Vercel URL
2. Try entering a test procedure like: "Configure DUT for a Service with 1:1 Forwarder"
3. Click "Generate Configuration" 
4. Verify that examples load properly
5. Test the copy functionality

## 🔄 Updates

Any changes pushed to your GitHub repository will automatically trigger a new deployment.

## 🆘 Troubleshooting

- **Build Fails**: Check build logs in Vercel dashboard
- **Import Errors**: Verify all dependencies are in `requirements.txt`
- **Function Timeout**: Vercel functions have a 10-second timeout on free tier

---

**🎉 That's it! Your Network Configuration Generator is now live with a fully functional Flask backend on Vercel.**
