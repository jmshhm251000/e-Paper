from PIL import Image, ImageEnhance, ImageDraw, ImageFont, ImageFilter
import subprocess
import shutil
import psutil

EPD_WIDTH = 800
EPD_HEIGHT = 480

palette_colors = [
    (0, 0, 0),        # Black
    (255, 255, 255),  # White
    (255, 0, 0),      # Red
    (255, 255, 0),    # Yellow
    (255, 165, 0),    # Orange
    (0, 255, 0),      # Green
    (0, 0, 255),      # Blue
]

def get_system_info():
    try:
        temp = subprocess.check_output(["vcgencmd", "measure_temp"]).decode().strip().split('=')[1]
    except:
        temp = "N/A"
    ram = psutil.virtual_memory()
    disk = shutil.disk_usage("/")
    return f"CPU: {temp} | RAM: {ram.percent}% | DISK: {disk.used // (1024**2)}MB / {disk.total // (1024**2)}MB"

def quantize_with_palette(img: Image.Image) -> Image.Image:
    img = ImageEnhance.Contrast(img).enhance(1.3)
    img = ImageEnhance.Sharpness(img).enhance(1.5)
    img_rgb = img.convert("RGB").resize((EPD_WIDTH, EPD_HEIGHT), Image.LANCZOS)
    img_rgb = img_rgb.filter(ImageFilter.GaussianBlur(radius=0.5))

    # Create palette
    palette_img = Image.new("P", (1, 1))
    flat_palette = sum(palette_colors, ()) + (0,) * (768 - len(palette_colors) * 3)
    palette_img.putpalette(flat_palette)

    img_quantized = img_rgb.quantize(palette=palette_img)
    img_rgb_overlay = img_quantized.convert("RGB")

    draw = ImageDraw.Draw(img_rgb_overlay)
    try:
        font = ImageFont.truetype("/home/minseok/myepaper/Font.ttc", 16)
    except:
        font = ImageFont.load_default()

    sysinfo = get_system_info()
    bbox = draw.textbbox((0, 0), sysinfo, font=font)
    x = EPD_WIDTH - (bbox[2] - bbox[0]) - 10
    y = EPD_HEIGHT - (bbox[3] - bbox[1]) - 10
    draw.text((x, y), sysinfo, font=font, fill=(0, 0, 0))

    return img_rgb_overlay
