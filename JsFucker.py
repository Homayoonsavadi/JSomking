import os
import time
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from colorama import Fore, Style

def download_core_js_files(url, output_folder="downloaded_js", visited_urls=None, downloaded_files=None, base_domain=None, keywords=None):
    if visited_urls is None:
        visited_urls = set()

    if downloaded_files is None:
        downloaded_files = set()

    if base_domain is None:
        base_domain = urlparse(url).netloc

    # Prevent visiting the same URL multiple times
    if url in visited_urls:
        return
    visited_urls.add(url)

    try:
        # Create the output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)

        # Fetch the page content
        print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Fetching URL: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Step 1: Download JavaScript files from the main page
        script_tags = soup.find_all('script', src=True)
        for script in script_tags:
            js_url = script['src']
            full_url = urljoin(url, js_url)

            # Only include JS files from the same domain
            if urlparse(full_url).netloc != base_domain:
                continue

            # Exclude unnecessary files
            if any(keyword in js_url.lower() for keyword in ['webpack', 'vendor', 'bootstrap', 'jquery', 'analytics', 'bundle', 'theme', 'framework']):
                continue

            # Avoid re-downloading files
            if full_url in downloaded_files:
                continue

            downloaded_files.add(full_url)
            
            parsed_url = urlparse(full_url)
            file_name = os.path.basename(parsed_url.path) or "index.js"  # Default to "index.js" if no file name
            file_path = os.path.join(output_folder, file_name)

            try:
                print(f"{Fore.GREEN}[DOWNLOAD]{Style.RESET_ALL} Downloading JavaScript: {full_url}")
                js_response = requests.get(full_url, timeout=10)
                js_response.raise_for_status()

                with open(file_path, 'wb') as f:
                    f.write(js_response.content)
            except Exception as e:
                print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Error downloading {full_url}: {e}")

            time.sleep(1)  # Prevent overwhelming the server

        # Step 2: Extract links and recursively fetch JS files
        links = soup.find_all('a', href=True)
        for link in links:
            href_url = urljoin(url, link['href'])

            # Skip links outside the base domain
            if urlparse(href_url).netloc != base_domain:
                continue

            # Recursively process the URL for more JS files
            download_core_js_files(href_url, output_folder, visited_urls, downloaded_files, base_domain, keywords)

    except Exception as e:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} An error occurred while processing {url}: {e}")

import time

def search_keywords_in_files(folder, keywords):
    """
    Open each JS file in the folder and search for the provided keywords, displaying lines and counts.

    :param folder: Folder where JS files are stored.
    :param keywords: List of keywords to search for.
    """
    print(f"{Fore.MAGENTA}[SEARCH]{Style.RESET_ALL} Searching for keywords in JavaScript files...\n")
    file_count = 0
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.path.isfile(file_path) and filename.endswith(".js"):
            file_count += 1
            keyword_hits = {}  # Dictionary to track keyword hits with line numbers
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                    lines = file.readlines()

                    # Iterate through lines to find keywords
                    for line_number, line in enumerate(lines, start=1):
                        for keyword in keywords:
                            if keyword.lower() in line.lower():
                                if keyword not in keyword_hits:
                                    keyword_hits[keyword] = []
                                keyword_hits[keyword].append(line_number)

                # Display results for this file
                if keyword_hits:
                    print(f"{Fore.GREEN}[FILE]{Style.RESET_ALL} {file_count}. {file_path}")
                    for keyword, line_numbers in keyword_hits.items():
                        line_info = ", ".join(map(str, line_numbers))
                        print(f"  {Fore.YELLOW}[FOUND]{Style.RESET_ALL} '{keyword}' ({len(line_numbers)} times) in lines: {line_info}")

            except Exception as e:
                print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Could not read {file_path}: {e}")
            
            print("\n" + "-" * 40 + "\n")  # Add spacing between file results
            time.sleep(0.5)  # Add a short delay for each file to control speed

    print(f"\n{Fore.MAGENTA}[DONE]{Style.RESET_ALL} Completed searching {file_count} files.")

def load_keywords_from_file(keyword_file):
    """
    Load keywords from a wordlist file.

    :param keyword_file: Path to the file containing keywords (one per line).
    :return: List of keywords.
    """
    keywords = []
    try:
        with open(keyword_file, 'r') as file:
            for line in file:
                keyword = line.strip()
                if keyword:  # Avoid adding empty lines
                    keywords.append(keyword)
    except Exception as e:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Error reading keyword file: {e}")
    return keywords

def detect_architecture(folder):
    """
    Detect if the site architecture is GraphQL, REST API, or other based on JS files.

    :param folder: Folder containing downloaded JS files.
    """
    print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Detecting site architecture...\n")
    graph_keywords = ['graphql', 'mutation', 'query', 'subscription', '/graphql', 'graphql-schema']
    rest_keywords = ['api/v1', 'api/v2', '/auth', '/users', '/login', '/logout', 'GET', 'POST', 'PUT', 'DELETE']

    graph_detected = False
    rest_detected = False

    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.path.isfile(file_path) and filename.endswith(".js"):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                    content = file.read().lower()

                    # Check for GraphQL keywords
                    if any(keyword in content for keyword in graph_keywords):
                        graph_detected = True
                    
                    # Check for REST API keywords
                    if any(keyword in content for keyword in rest_keywords):
                        rest_detected = True

            except Exception as e:
                print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Could not read {file_path}: {e}")

    print(f"{Fore.GREEN}[RESULT]{Style.RESET_ALL} Architecture Detection Results:")
    if graph_detected and rest_detected:
        print(f"  - Detected both {Fore.YELLOW}GraphQL{Style.RESET_ALL} and {Fore.YELLOW}REST API{Style.RESET_ALL} patterns.")
    elif graph_detected:
        print(f"  - Detected {Fore.YELLOW}GraphQL{Style.RESET_ALL} architecture.")
    elif rest_detected:
        print(f"  - Detected {Fore.YELLOW}REST API{Style.RESET_ALL} architecture.")
    else:
        print(f"  - No specific architecture detected.\n")

    print(f"\n{Fore.MAGENTA}[DONE]{Style.RESET_ALL} Architecture detection completed.\n")


if __name__ == "__main__":
    import sys

    print(f"{Fore.GREEN}{Style.BRIGHT}*** 0xpwn ***{Style.RESET_ALL}")

    if len(sys.argv) != 4:
        print(f"{Fore.RED}[USAGE]{Style.RESET_ALL} python JsFucker.py <URL> <OUTPUT_FOLDER> <KEYWORD_FILE>")
        sys.exit(1)

    start_url = sys.argv[1]
    output_directory = sys.argv[2]
    keyword_file = sys.argv[3]

    keywords = load_keywords_from_file(keyword_file)
    download_core_js_files(start_url, output_directory, keywords=keywords)
    search_keywords_in_files(output_directory, keywords)
    detect_architecture(output_directory)
