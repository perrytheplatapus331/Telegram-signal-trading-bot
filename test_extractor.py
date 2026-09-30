from extractor import extract_signal

with open("card_tp2.jpeg", "rb") as f:
    image_bytes = f.read()

caption = "Tp2\nSet stoploss at entry and book 50%"

print(extract_signal(caption, image_bytes))