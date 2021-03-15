from requests_html import HTMLSession
import requests
import os
import sys

URL_HOST = "https://www.dbooks.org"
SAVE_AT = "./dbooks"
README = "./DBOOKS_README.md"
CHUNK_SIZE = 1024
PROGRESS_LEN = 50


class dbooks():
    def __init__(self):
        self.books = set()
        self.clear_urls()
        os.makedirs(SAVE_AT, exist_ok=True)

    def clear_urls(self):
        with open(README, "w") as f:
            f.write("# Open Books of dbooks.org\n\n")

    def add_to_urls(self, filename, link):
        print("book added: %s" % filename)
        with open(README, "a") as f:
            f.write("1. [%s](%s)\n" % (filename, link))

    def save_at(self, filename):
        return os.path.join(SAVE_AT, filename) + ".pdf"

    def download_book(self, filename, link):
        filepath = self.save_at(filename)
        ok = False
        if not os.path.exists(filepath):
            response = requests.get(link, stream=True)
            total = response.headers.get("content-length")
            if total is not None:
                with open(filepath, "wb") as f:
                    downloaded = 0
                    total = int(total)
                    for data in response.iter_content(chunk_size=CHUNK_SIZE):
                        downloaded += len(data)
                        f.write(data)
                        done = int(PROGRESS_LEN * downloaded / total)
                        params = ("=" * done, " " * (PROGRESS_LEN - done))
                        sys.stdout.write("\r[%s%s]" % params)
                        sys.stdout.flush()
                    print("\n%s downloaded." % filename)
                    ok = True
        if not ok:
            print("failed: %s -> %s" % (filename, link))
            os.remove(filepath)

    def fetch_book_full_link(self, link):
        return URL_HOST + link

    def fetch_book_download_link(self, link):
        response = HTMLSession().get(link)
        links = response.html.find(".box1 a")
        titles = response.html.find(".col100 h1")
        if len(titles) > 0:
            filename = titles[0].text
        for link in links:
            title = link.attrs["title"]
            if title == "Download PDF":
                raw = link.attrs["href"]
                print("book found: %s" % filename)
                return filename, self.fetch_book_full_link(raw), response.html
        return None, None, response.html

    def search_in_page(self, html):
        links = html.find(".pad a")
        for link in links:
            raw = link.attrs["href"]
            raw = self.fetch_book_full_link(raw)
            filename, link, content = self.fetch_book_download_link(raw)
            if filename not in self.books:
                """
                open comments below if you want to download books at the meanwhile
                """
                # self.download_book(filename, link)
                self.books.add(filename)
                self.add_to_urls(filename, link)
                if content is not None:
                    self.search_in_page(content)

    def fetch_from_start_page(self):
        response = HTMLSession().get(URL_HOST)
        self.search_in_page(response.html)


if __name__ == "__main__":
    dbooks().fetch_from_start_page()
