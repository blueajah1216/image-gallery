import requests
from bs4 import BeautifulSoup
import os

def download_thumbnail_from_pin_container(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    print(f"Fetching page from: {url}")
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch page. Status code: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    # Look inside the pin_container div
    pin_container = soup.find('div', class_='pin_container')
    if not pin_container:
        print("Couldn't find .pin_container div.")
        return

    meta_tag = pin_container.find('meta', itemprop='thumbnailUrl')
    if not meta_tag or 'content' not in meta_tag.attrs:
        print("thumbnailUrl <meta> tag not found inside .pin_container.")
        return

    image_url = meta_tag['content'].replace('&amp;', '&')
    print(f"Found thumbnail URL: {image_url}")

    # Download the image
    img_response = requests.get(image_url, headers=headers)
    if img_response.status_code == 200:
        filename = os.path.basename(image_url.split('?')[0])  # Strip query params
        with open(filename, 'wb') as f:
            f.write(img_response.content)
        print(f"Image saved as '{filename}'")
    else:
        print(f"Failed to download image. Status code: {img_response.status_code}")

# Example usage:
download_thumbnail_from_pin_container("https://www.example.com/")