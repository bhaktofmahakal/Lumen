# PWA Icons

This directory should contain the following icon sizes for the PWA manifest:

- icon-72x72.png
- icon-96x96.png
- icon-128x128.png
- icon-144x144.png
- icon-152x152.png
- icon-192x192.png
- icon-384x384.png
- icon-512x512.png

These icons are used for:
- App installation on mobile devices
- Home screen shortcuts
- Splash screens
- App switcher

## Generating Icons

You can generate these icons from a single high-resolution source image (at least 512x512px) using tools like:
- https://realfavicongenerator.net/
- https://www.pwabuilder.com/imageGenerator
- ImageMagick: `convert icon.png -resize 192x192 icon-192x192.png`

## Design Guidelines

- Use a simple, recognizable design
- Ensure good contrast for visibility
- Test on both light and dark backgrounds
- Include padding to prevent clipping on rounded corners
