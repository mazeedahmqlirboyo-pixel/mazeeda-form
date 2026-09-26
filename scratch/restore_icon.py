from PIL import Image

# Open the original logo
img = Image.open('src/512 Logo.png').convert("RGBA")

# Save directly to 512
img.save('static/icon-512.png')

# Resize to 192x192 full frame
img_192 = img.resize((192, 192), Image.Resampling.LANCZOS)
img_192.save('static/icon-192.png')
