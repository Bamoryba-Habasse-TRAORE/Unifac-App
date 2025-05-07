import qrcode

# Remplace cette URL par ton domaine de production
url = "https://calc-diff.onrender.com"

# Génère le QR
img = qrcode.make(url)
# Sauvegarde dans static/images
img.save("website/static/images/qr_code.png")
