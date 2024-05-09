from urllib.parse import urlparse


def normalize_domain(url):
  if url.startswith('http://') or url.startswith('https://'):
    return urlparse(url).netloc
  return url


def get_favicon_filename(url):
  return f"{normalize_domain(url)}.favicon.ico"
