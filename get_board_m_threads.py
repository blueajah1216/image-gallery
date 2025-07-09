import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_folder_name_from_url(url):
    path = urlparse(url).path
    return os.path.basename(path.rstrip('/'))

def download_largest_image(url, output_dir):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"❌ Failed to fetch {url}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        img_tags = soup.find_all('img')

        largest_image = None
        largest_size = 0
        largest_data = None

        for img in img_tags:
            src = img.get("src")
            if not src:
                continue
            img_url = urljoin(url, src)
            try:
                img_resp = requests.get(img_url, headers=headers, timeout=10)
                img_resp.raise_for_status()
                size = len(img_resp.content)
                if size > largest_size:
                    largest_size = size
                    largest_image = img_url
                    largest_data = img_resp.content
            except requests.RequestException:
                continue

        if largest_image:
            filename = os.path.basename(largest_image.split("?")[0])
            save_path = os.path.join(output_dir, filename)
            with open(save_path, "wb") as f:
                f.write(largest_data)
            print(f"✓ Saved: {save_path} ({largest_size} bytes)")
        else:
            print(f"⚠️ No image found on {url}")
    except Exception as e:
        print(f"💥 Error on {url}: {e}")

def create_unique_folder(base_name):
    folder = base_name
    counter = 1
    while os.path.exists(folder):
        folder = f"{base_name}_{counter}"
        counter += 1
    os.makedirs(folder)
    return folder

def download_gallery_images_multithreaded(gallery_url, domain_filter='example.com', max_threads=8):
    headers = {"User-Agent": "Mozilla/5.0"}
    print(f"\n📂 Scanning gallery page: {gallery_url}")
    resp = requests.get(gallery_url, headers=headers)
    if resp.status_code != 200:
        print(f"❌ Failed to load gallery: {resp.status_code}")
        return

    soup = BeautifulSoup(resp.text, 'html.parser')
    all_links = soup.find_all('a', href=True)

    pin_links = set()
    for link in all_links:
        href = link['href']
        full_url = urljoin(gallery_url, href)
        parsed = urlparse(full_url)
        if domain_filter in parsed.netloc and '/pin/' in parsed.path:
            pin_links.add(full_url)

    print(f"🔗 Found {len(pin_links)} pin pages.")

    # Make the output folder
    # Grab the *true* board name from the URL path
    parsed = urlparse(gallery_url)
    path_parts = parsed.path.strip("/").split("/")
    board_name = path_parts[-1] if path_parts else "gallery"

    folder_name = create_unique_folder(board_name)
    print(f"📁 Saving images to folder: {folder_name}")

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(download_largest_image, pin_url, folder_name) for pin_url in pin_links]
        for i, future in enumerate(as_completed(futures), 1):
            try:
                future.result()
            except Exception as e:
                print(f"❌ Thread {i} raised an error: {e}")

def download_all_user_boards(user_url, domain_filter="example.com", max_threads=8):
    headers = {"User-Agent": "Mozilla/5.0"}
    print(f"\n👤 Scanning user page: {user_url}")
    resp = requests.get(user_url, headers=headers)
    if resp.status_code != 200:
        print(f"❌ Failed to load user page: {resp.status_code}")
        return

    soup = BeautifulSoup(resp.text, 'html.parser')
    all_links = soup.find_all('a', href=True)

    parsed_user_url = urlparse(user_url)
    user_path_parts = parsed_user_url.path.strip('/').split('/')
    username = user_path_parts[1] if len(user_path_parts) >= 2 else None
    if not username:
        print("❌ Could not extract username from URL.")
        return

    board_links = set()
    for link in all_links:
        href = link['href']
        full_url = urljoin(user_url, href)
        parsed = urlparse(full_url)
        path_parts = parsed.path.strip('/').split('/')

        # Match /user/<username>/<boardname> only
        if (len(path_parts) == 3 and
            path_parts[0] == 'user' and
            path_parts[1] == username and
            domain_filter in parsed.netloc):
            board_links.add(full_url)

    print(f"📋 Found {len(board_links)} board(s) for user '{username}'.")

    for i, board_url in enumerate(sorted(board_links), 1):
        print(f"\n🧭 [{i}/{len(board_links)}] Scraping board: {board_url}")
        download_gallery_images_multithreaded(board_url, domain_filter=domain_filter, max_threads=max_threads)

# ==== Example usage ====
download_gallery_images_multithreaded("", domain_filter="", max_threads=10)
# Example: crawl all boards for a user
#download_all_user_boards("https://www.example.com/user/reddaddy/", domain_filter="example.com", max_threads=8)