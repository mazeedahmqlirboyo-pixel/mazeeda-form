from PIL import Image

# Open the original logo
img = Image.open('src/512 Logo.png').convert("RGBA")

# Create a new 512x512 white background image
new_img = Image.new('RGBA', (512, 512), (255, 255, 255, 255))

# Scale to 85% (not too small, not too big)
target_size = int(512 * 0.85)
img_resized = img.resize((target_size, target_size), Image.Resampling.LANCZOS)

# Paste the resized logo in the center
offset = ((512 - target_size) // 2, (512 - target_size) // 2)
new_img.paste(img_resized, offset, img_resized)

# Save as icon-512.png and icon-192.png
new_img.save('static/icon-512.png')

new_img_192 = new_img.resize((192, 192), Image.Resampling.LANCZOS)
new_img_192.save('static/icon-192.png')
