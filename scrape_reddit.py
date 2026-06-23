import urllib.request
import xml.etree.ElementTree as ET
import html
import re
import time
import json
import os

def clean_html(raw_html):
    """
    Remove HTML tags and clean up text.
    Reddit RSS feed bodies are wrapped in HTML tables with links, user info, etc.
    We try to extract the main text content.
    """
    if not raw_html:
        return ""
    
    # Unescape HTML entities first
    unescaped = html.unescape(raw_html)
    
    # We want to remove standard boilerplates like "submitted by /u/username to /r/CryptoCurrency"
    # and "[link] [comments]"
    clean = re.sub(r'submitted by .*? to r/CryptoCurrency', '', unescaped)
    clean = re.sub(r'\[link\].*?\[comments\]', '', clean)
    
    # Remove all HTML tags
    clean = re.sub(r'<[^<]+?>', ' ', clean)
    
    # Replace multiple spaces/newlines with a single space/newline
    clean = re.sub(r'\s+', ' ', clean)
    return clean.strip()

def fetch_feed(url):
    """
    Fetch RSS feed from Reddit with a custom User-Agent.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            return response.read()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def main():
    search_queries = [
        "bitcoin", "ethereum", "solana", "crypto", "market", 
        "regulation", "sec", "ETF", "price", "DCA", 
        "exchange", "bull", "bear", "analysis", "opinion", 
        "advice", "news", "halving", "fed", "inflation", 
        "tax", "wallet", "hack", "scam", "hold"
    ]
    
    urls = [
        "https://www.reddit.com/r/CryptoCurrency/.rss",
        "https://www.reddit.com/r/CryptoCurrency/new/.rss",
        "https://www.reddit.com/r/CryptoCurrency/hot/.rss",
        "https://www.reddit.com/r/CryptoCurrency/top/.rss"
    ]
    
    for q in search_queries:
        urls.append(f"https://www.reddit.com/r/CryptoCurrency/search.rss?q={q}&restrict_sr=on&sort=new")
        urls.append(f"https://www.reddit.com/r/CryptoCurrency/search.rss?q={q}&restrict_sr=on&sort=relevance")

    # Load existing scraped file if it exists to avoid losing data
    output_path = "/Users/leminhhieu/.gemini/antigravity/scratch/scraped_posts.json"
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                all_posts = json.load(f)
            print(f"Loaded {len(all_posts)} existing scraped posts from cache.")
        except Exception:
            all_posts = {}
    else:
        all_posts = {}

    namespaces = {'atom': 'http://www.w3.org/2005/Atom'}
    
    # We will fetch and deduplicate
    for idx, url in enumerate(urls):
        print(f"[{idx+1}/{len(urls)}] Fetching: {url}")
        content = fetch_feed(url)
        if content:
            try:
                root = ET.fromstring(content)
                entries = root.findall('atom:entry', namespaces)
                new_in_feed = 0
                for entry in entries:
                    link_el = entry.find('atom:link', namespaces)
                    link = link_el.attrib.get('href') if link_el is not None else None
                    if not link:
                        continue
                    
                    # Deduplicate using post link
                    if link in all_posts:
                        continue
                        
                    title = entry.find('atom:title', namespaces).text or ""
                    content_el = entry.find('atom:content', namespaces)
                    raw_content = content_el.text if content_el is not None else ""
                    
                    cleaned_body = clean_html(raw_content)
                    
                    all_posts[link] = {
                        "title": title,
                        "body": cleaned_body,
                        "link": link
                    }
                    new_in_feed += 1
                
                print(f"  Added {new_in_feed} new unique posts. Total cached: {len(all_posts)}")
            except Exception as parse_err:
                print(f"  Error parsing XML: {parse_err}")
        
        # Sleep to avoid rate limiting (429)
        time.sleep(3.5)

    # Save all scraped posts
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_posts, f, indent=2, ensure_ascii=False)
        
    print(f"Finished scraping! Total unique posts stored: {len(all_posts)}")

if __name__ == "__main__":
    main()
