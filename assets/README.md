# PrecipGen Assets

This directory contains assets for the PrecipGen Desktop application.

## Application Icon

Place the application icon file here:
- **File name**: `precipgen.ico`
- **Format**: Windows ICO format
- **Recommended sizes**: 16x16, 32x32, 48x48, 256x256 pixels
- **Purpose**: Used for the executable icon and window title bar

### Creating an Icon

You can create an icon using:
1. Online converters (e.g., convertio.co, icoconvert.com)
2. GIMP (export as .ico with multiple sizes)
3. ImageMagick: `convert logo.png -define icon:auto-resize=256,128,64,48,32,16 precipgen.ico`

### Placeholder Icon

If no icon is provided, PyInstaller will use the default Python icon.
The application will still function normally without a custom icon.

## Other Assets

Additional assets can be placed here and will be included in the executable:
- Images for the UI
- Configuration templates
- Documentation files
- Any other static resources needed by the application
