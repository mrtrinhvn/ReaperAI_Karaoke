#!/usr/bin/env python3
"""
TokenJuice - Nén Token Siêu Việt cho ag-kit
Lấy cảm hứng từ OpenHuman, nén HTML/JSON/Logs thành dạng siêu nhỏ để tiết kiệm token cho LLM.
"""

import sys
import re
import json
import argparse

from html.parser import HTMLParser

class HTMLToMarkdownParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.markdown = []
        self.in_script_or_style = False
        self.current_href = ""
    
    def handle_starttag(self, tag, attrs):
        if tag in ['script', 'style']:
            self.in_script_or_style = True
        elif tag == 'a':
            for attr in attrs:
                if attr[0] == 'href':
                    self.current_href = attr[1]
            self.markdown.append("[")
        elif tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            level = int(tag[1])
            self.markdown.append("\n" + "#" * level + " ")
        elif tag in ['br', 'p', 'div']:
            self.markdown.append("\n")
        elif tag == 'li':
            self.markdown.append("\n- ")

    def handle_endtag(self, tag):
        if tag in ['script', 'style']:
            self.in_script_or_style = False
        elif tag == 'a':
            if self.current_href:
                self.markdown.append(f"]({self.current_href})")
                self.current_href = ""
            else:
                self.markdown.append("]")
        elif tag in ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            self.markdown.append("\n")

    def handle_data(self, data):
        if not self.in_script_or_style:
            self.markdown.append(data)

def compress_html(text):
    parser = HTMLToMarkdownParser()
    try:
        parser.feed(text)
        return "".join(parser.markdown)
    except Exception:
        # Fallback to simple regex if parser fails
        text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style.*?>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        return re.sub(r'<[^>]+>', ' ', text)

def compress_urls(text):
    # Truncate long URLs to just domain or short path
    def url_repl(match):
        url = match.group(0)
        if len(url) > 50:
            return url[:47] + "..."
        return url
    
    # Simple regex for http/https URLs
    return re.sub(r'https?://[^\s<>"]+|www\.[^\s<>"]+', url_repl, text)

def compress_json(text):
    try:
        data = json.loads(text)
        # Convert to compact JSON string
        return json.dumps(data, separators=(',', ':'))
    except json.JSONDecodeError:
        return text

def juice_text(text, input_type='auto'):
    if input_type == 'auto':
        if text.strip().startswith(('{', '[')):
            input_type = 'json'
        elif '<html' in text.lower() or '<body' in text.lower() or '</' in text:
            input_type = 'html'
        else:
            input_type = 'text'

    if input_type == 'html':
        text = compress_html(text)
    elif input_type == 'json':
        text = compress_json(text)
    
    # Universal compressions
    text = compress_urls(text)
    
    # Remove multiple spaces and newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    
    return text.strip()

def main():
    parser = argparse.ArgumentParser(description="TokenJuice - Nén Token cho LLM")
    parser.add_argument("file", nargs="?", type=argparse.FileType("r"), default=sys.stdin, help="File input (mặc định là stdin)")
    parser.add_argument("-t", "--type", choices=["auto", "html", "json", "text"], default="auto", help="Loại dữ liệu")
    
    args = parser.parse_args()
    
    content = args.file.read()
    compressed = juice_text(content, args.type)
    
    print(compressed)

if __name__ == "__main__":
    main()
