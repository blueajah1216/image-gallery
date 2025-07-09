import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os

def download_largest_image(url):
    headers = {"User-Agent": "Mozilla/5.0"}

    print(f"Fetching HTML from {url}...")
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch page. Status code: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    img_tags = soup.find_all('img')

    if not img_tags:
        print("No images found.")
        return

    print(f"Found {len(img_tags)} image(s). Checking sizes...")

    largest_image = None
    largest_size = 0
    largest_data = None

    for img in img_tags:
        img_src = img.get("src")
        if not img_src:
            continue

        # Resolve relative URLs
        img_url = urljoin(url, img_src)
        try:
            img_response = requests.get(img_url, headers=headers, timeout=10)
            img_response.raise_for_status()
            size = len(img_response.content)

            print(f"→ {img_url} : {size} bytes")

            if size > largest_size:
                largest_size = size
                largest_image = img_url
                largest_data = img_response.content

        except requests.RequestException as e:
            print(f"⚠️ Error fetching {img_url}: {e}")

    if largest_image:
        filename = os.path.basename(largest_image.split('?')[0])
        with open(filename, 'wb') as f:
            f.write(largest_data)
        print(f"\n🎯 Largest image saved as '{filename}' ({largest_size} bytes)")
    else:
        print("❌ No images could be downloaded.")

def download_gallery_images(gallery_url, domain_filter='example.com'):
    headers = {"User-Agent": "Mozilla/5.0"}
    print(f"\n📂 Scanning gallery page: {gallery_url}")
    resp = requests.get(gallery_url, headers=headers)
    if resp.status_code != 200:
        print(f"Failed to load gallery: {resp.status_code}")
        return

    soup = BeautifulSoup(resp.text, 'html.parser')
    all_links = soup.find_all('a', href=True)

    # Filter for /pin/... links
    pin_links = set()
    for link in all_links:
        href = link['href']
        full_url = urljoin(gallery_url, href)
        parsed = urlparse(full_url)
        if domain_filter in parsed.netloc and '/pin/' in parsed.path:
            pin_links.add(full_url)

    print(f"🔗 Found {len(pin_links)} pin pages to download.")

    for i, pin_url in enumerate(sorted(pin_links), 1):
        print(f"\n➡️ [{i}/{len(pin_links)}] Fetching: {pin_url}")
        download_largest_image(pin_url)


# ==== Example usage ====
download_gallery_images("https://www.example.com/", domain_filter="sex.com")