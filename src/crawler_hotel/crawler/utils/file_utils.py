# utils/file_utils.py
import os

def load_urls_from_province(province_path):
    all_urls = []
    for txt_file in os.listdir(province_path):
        if not txt_file.lower().endswith('.txt'):
            continue
        file_path = os.path.join(province_path, txt_file)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                urls = [line.strip() for line in f if line.strip().startswith('http')]
                all_urls.extend(urls)
        except Exception as e:
            print(f"Cannot read {file_path}: {e}")
    return all_urls

def chunk_urls(urls, n_chunks):
    chunk_size = (len(urls) + n_chunks - 1) // n_chunks
    chunks = [urls[i:i + chunk_size] for i in range(0, len(urls), chunk_size)]
    while len(chunks) < n_chunks:
        chunks.append([])
    return chunks