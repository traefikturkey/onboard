import logging
import os
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from models.utils import pwd

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def normalize_domain(url):
    if url.startswith("http://") or url.startswith("https://"):
        return urlparse(url).netloc
    return url


def base(url):
    try:
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        return base_url
    except Exception as ex:
        logger.error(f"Error in base({url}): {ex}")
        return url


def favicon_filename(url):
    return f"{normalize_domain(url)}.favicon.ico"


def favicon_failed_filename(url):
    return f"{normalize_domain(url)}.failed"


def make_request(url):
    request_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    return requests.get(url, headers=request_headers, allow_redirects=True, timeout=5)


def favicon_path(icon_path, favicon_filename):
    return os.path.join(icon_path, favicon_filename)


def find_favicon_from(url):
    try:
        response = make_request(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            icon_link = soup.find("link", rel=["icon", "shortcut icon"])
            if icon_link and hasattr(icon_link, "get"):
                icon_url = icon_link.get("href")
                icon_url_str = str(icon_url)
                if not icon_url_str.startswith("http"):
                    icon_url_str = urljoin(url, icon_url_str)
                return icon_url_str
    except Exception as ex:
        logger.debug(f"Error: find_favicon_url({url}): {ex}")
        return None


def download_favicon(url, icon_dir):
    icon_url = find_favicon_from(url)
    if icon_url:
        _download(url, icon_dir, icon_url)
    else:
        _download(
            url,
            icon_dir,
            f"http://www.google.com/s2/favicons?domain={normalize_domain(url)}",
        )


def _download(url, icon_dir, icon_url):
    try:
        response = make_request(icon_url)
        if response.status_code == 200 and response.headers.get(
            "content-type", ""
        ).lower().startswith("image/"):
            filename = pwd.joinpath(icon_dir, favicon_filename(url))
            with open(filename, "wb") as file:
                file.write(response.content)
            logger.debug(f"saving {url} as {filename}")
        else:
            filename = pwd.joinpath(icon_dir, favicon_failed_filename(url))
            print(
                f'response_code: {response.status_code} content-type: {response.headers.get("content-type", "")}',
                file=open(filename, "w"),
            )
            logger.debug(f"Marking {url} as failed with {filename}")
    except Exception as ex:
        filename = pwd.joinpath(icon_dir, favicon_failed_filename(url))
        print(f"Error: {ex}", file=open(filename, "w"))
        logger.debug(f"Marking {url} as failed with {filename}")

    logger.debug(f"_download({icon_url}) completed")
