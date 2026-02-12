# Installing Streamlit for PrecipGen

## Quick Installation

### Option 1: Install Just Streamlit
```bash
pip install streamlit
```

### Option 2: Install All Requirements (Recommended)
```bash
pip install -r requirements.txt
```

This will install:
- streamlit (web interface)
- All existing PrecipGen dependencies

## Verify Installation

After installation, verify Streamlit is installed:

```bash
streamlit --version
```

You should see something like: `Streamlit, version 1.28.0`

## First Run

### Windows
Double-click `run_streamlit.bat` or run:
```cmd
streamlit run streamlit_app.py
```

### Mac/Linux
```bash
chmod +x run_streamlit.sh
./run_streamlit.sh
```

Or:
```bash
streamlit run streamlit_app.py
```

## What Happens on First Run

1. Streamlit starts a local web server
2. Your default browser opens automatically
3. The PrecipGen interface loads at `http://localhost:8501`
4. You'll see the home page with navigation in the sidebar

## Troubleshooting

### "Module not found: streamlit"
**Solution:** Install streamlit
```bash
pip install streamlit
```

### "Port 8501 is already in use"
**Solution:** Either close the existing Streamlit instance or use a different port:
```bash
streamlit run streamlit_app.py --server.port 8502
```

### Browser doesn't open automatically
**Solution:** Manually open your browser and go to:
```
http://localhost:8501
```

### "Command not found: streamlit"
**Solution:** Make sure pip installed to the correct Python environment:
```bash
python -m pip install streamlit
python -m streamlit run streamlit_app.py
```

### Import errors for other modules
**Solution:** Install all requirements:
```bash
pip install -r requirements.txt
```

## System Requirements

- **Python**: 3.8 or higher
- **RAM**: 2GB minimum (4GB recommended)
- **Browser**: Chrome, Firefox, Safari, or Edge
- **Internet**: Required for initial inventory download

## Optional: Create Virtual Environment

For a clean installation:

### Windows
```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Mac/Linux
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Next Steps

Once installed:
1. Run `streamlit run streamlit_app.py`
2. Read `STREAMLIT_GUIDE.md` for usage instructions
3. Start with "Find Stations" in the sidebar
4. Follow the workflow from the home page

## Uninstalling

If you want to remove Streamlit:
```bash
pip uninstall streamlit
```

## Getting Help

- Streamlit docs: https://docs.streamlit.io
- PrecipGen docs: See README.md and GETTING_STARTED.md
- Issues: Check the terminal output for error messages
