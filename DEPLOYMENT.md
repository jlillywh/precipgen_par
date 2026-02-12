# Deploying PrecipGen to Streamlit Cloud

## Prerequisites

- ✅ Streamlit Cloud account (you have this!)
- ✅ GitHub account
- ✅ Your PrecipGen code in a GitHub repository

## Quick Deployment Steps

### 1. Push to GitHub

If you haven't already, push your code to GitHub:

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - PrecipGen with Streamlit interface"

# Add remote (replace with your repo URL)
git remote add origin https://github.com/yourusername/precipgen_par.git

# Push
git push -u origin main
```

### 2. Deploy on Streamlit Cloud

1. Go to https://share.streamlit.io/
2. Click "New app"
3. Select your GitHub repository
4. Set these values:
   - **Repository:** `yourusername/precipgen_par`
   - **Branch:** `main`
   - **Main file path:** `streamlit_app.py`
5. Click "Deploy!"

### 3. Wait for Deployment

- First deployment takes 2-5 minutes
- Streamlit Cloud will:
  - Clone your repository
  - Install dependencies from `requirements.txt`
  - Start your app
  - Give you a public URL

### 4. Your App is Live! 🎉

You'll get a URL like:
```
https://yourusername-precipgen-par-streamlit-app-abc123.streamlit.app
```

## Important Considerations

### Data Storage

⚠️ **Important:** Streamlit Cloud apps are ephemeral - data doesn't persist between sessions!

**What this means:**
- Downloaded data files are temporary
- Files disappear when app restarts
- Each user gets their own temporary storage

**Solutions:**

#### Option 1: For Demo/Testing
- Accept temporary storage
- Users download results before leaving
- Good for showcasing the tool

#### Option 2: Add Cloud Storage
- Use AWS S3, Google Cloud Storage, or similar
- Store user data in cloud
- Requires additional setup

#### Option 3: Local Installation Only
- Keep Streamlit Cloud for demos
- Users install locally for real work
- Best for data-intensive workflows

### Recommended Approach

**Use Streamlit Cloud for:**
- ✅ Demonstrations
- ✅ Quick analyses
- ✅ Showcasing features
- ✅ Testing workflows

**Use Local Installation for:**
- ✅ Large datasets
- ✅ Long-term projects
- ✅ Batch processing
- ✅ Data persistence

## Configuration Files

### requirements.txt ✅
Already configured with all dependencies:
```
requests>=2.28.0
pandas>=1.5.0
numpy>=1.21.0
scipy>=1.9.0
matplotlib>=3.5.0
tqdm>=4.64.0
streamlit>=1.28.0
```

### .streamlit/config.toml ✅
Theme and server settings configured

### packages.txt ✅
System dependencies (if needed)

### .gitignore ✅
Excludes data files and cache

## Customization

### Custom Domain (Optional)

Streamlit Cloud allows custom domains:
1. Go to app settings
2. Add custom domain
3. Update DNS records
4. SSL certificate auto-generated

### Environment Variables

For API keys or secrets:
1. Go to app settings
2. Click "Secrets"
3. Add key-value pairs
4. Access in code: `st.secrets["key"]`

### Resource Limits

Streamlit Cloud free tier:
- **CPU:** 1 core
- **RAM:** 1 GB
- **Storage:** Temporary only
- **Bandwidth:** Unlimited

For more resources, upgrade to paid plan.

## Updating Your App

### Automatic Updates

Streamlit Cloud auto-deploys when you push to GitHub:

```bash
# Make changes
git add .
git commit -m "Update feature"
git push

# App automatically redeploys!
```

### Manual Reboot

From Streamlit Cloud dashboard:
1. Click on your app
2. Click "⋮" menu
3. Select "Reboot app"

## Monitoring

### View Logs

In Streamlit Cloud dashboard:
1. Click on your app
2. Click "Manage app"
3. View logs in real-time

### Analytics

Streamlit Cloud provides:
- Viewer count
- Session duration
- Error rates
- Resource usage

## Sharing

### Public App

Your app is public by default:
- Anyone with URL can access
- No authentication required
- Good for demos

### Private App (Paid)

Upgrade for:
- Password protection
- User authentication
- Access control
- Team collaboration

## Best Practices

### 1. Add a Landing Page

Update home page with:
- Clear instructions
- Demo video/GIF
- Example workflow
- Contact info

### 2. Add Usage Limits

For public apps, consider:
- Limiting file sizes
- Restricting download counts
- Adding rate limiting
- Showing warnings for large datasets

### 3. Documentation

Include in your app:
- Help section
- FAQ
- Tutorial
- Contact/support info

### 4. Error Handling

Ensure graceful failures:
- Catch exceptions
- Show user-friendly messages
- Provide fallback options
- Log errors for debugging

## Example Deployment Workflow

### Initial Setup

```bash
# 1. Create GitHub repo
# 2. Push code
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/precipgen_par.git
git push -u origin main

# 3. Deploy on Streamlit Cloud
# - Go to share.streamlit.io
# - Connect GitHub
# - Select repo
# - Deploy!
```

### Making Updates

```bash
# 1. Make changes locally
# 2. Test locally
streamlit run streamlit_app.py

# 3. Commit and push
git add .
git commit -m "Add new feature"
git push

# 4. Streamlit Cloud auto-deploys!
```

## Troubleshooting

### "Module not found"

**Problem:** Missing dependency  
**Solution:** Add to `requirements.txt` and push

### "App won't start"

**Problem:** Error in code  
**Solution:** Check logs in Streamlit Cloud dashboard

### "Out of memory"

**Problem:** Processing too much data  
**Solution:** 
- Reduce data size limits
- Optimize code
- Upgrade to paid plan

### "Slow performance"

**Problem:** Heavy computation  
**Solution:**
- Add caching with `@st.cache_data`
- Optimize algorithms
- Consider local installation for heavy work

## Adding Features for Cloud

### 1. Session State Management

```python
# Persist data across reruns
if 'data' not in st.session_state:
    st.session_state.data = None
```

### 2. File Upload

```python
# Allow users to upload their own data
uploaded_file = st.file_uploader("Upload CSV", type="csv")
if uploaded_file:
    df = pd.read_csv(uploaded_file)
```

### 3. Download Results

```python
# Let users download results
csv = df.to_csv(index=False)
st.download_button(
    "Download Results",
    csv,
    "results.csv",
    "text/csv"
)
```

### 4. Caching

```python
# Cache expensive operations
@st.cache_data
def load_inventory():
    # Expensive operation
    return data
```

## Security Considerations

### Public Deployment

⚠️ **Remember:**
- Code is visible on GitHub
- Anyone can access the app
- Don't include API keys in code
- Use Streamlit secrets for sensitive data

### Data Privacy

- User data is temporary
- No persistent storage
- Each session is isolated
- Data deleted on app restart

## Cost

### Free Tier

- ✅ Unlimited public apps
- ✅ 1 GB RAM per app
- ✅ Community support
- ✅ Auto-deployment

### Paid Plans

Starting at $20/month:
- More resources
- Private apps
- Custom domains
- Priority support
- Team features

## Next Steps

1. **Push to GitHub** ✅
2. **Deploy to Streamlit Cloud** ✅
3. **Test the deployed app** ✅
4. **Share the URL** ✅
5. **Monitor usage** ✅
6. **Iterate and improve** ✅

## Example README for GitHub

Add this to your README.md:

```markdown
## 🌐 Live Demo

Try PrecipGen online: [https://your-app-url.streamlit.app](https://your-app-url.streamlit.app)

## 🚀 Quick Start

### Online (Streamlit Cloud)
1. Visit the live demo
2. No installation required!
3. Note: Data is temporary

### Local Installation
1. Clone this repo
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `streamlit run streamlit_app.py`
4. Data persists locally
```

## Support

- **Streamlit Docs:** https://docs.streamlit.io/
- **Streamlit Cloud:** https://share.streamlit.io/
- **Community Forum:** https://discuss.streamlit.io/

Happy deploying! 🎉
