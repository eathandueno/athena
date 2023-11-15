import mwparserfromhell
import lxml.etree as etree

def extract_and_clean_xml(file_path, output_path):
    # Counter for articles processed
    total_articles = 0

    # Open the output file
    with open(output_path, 'w', encoding='utf-8', errors='replace') as output_file:
        for event, elem in etree.iterparse(file_path, events=('end',), tag='{http://www.mediawiki.org/xml/export-0.10/}page'):
                ns = elem.find('{http://www.mediawiki.org/xml/export-0.10/}revision/{http://www.mediawiki.org/xml/export-0.10/}text').text
                if ns:
                    wikicode = mwparserfromhell.parse(ns)
                    text = wikicode.strip_code().strip()
                    try:
                        output_file.write(text + '\n\n')
                    except UnicodeEncodeError as e:
                        # Replace or ignore problematic characters
                        safe_text = text.encode('utf-8', 'replace').decode('utf-8')
                        output_file.write(safe_text + '\n\n')
                        # Optionally log the error without printing the text
                        print(f"UnicodeEncodeError encountered and handled at article number {total_articles}")
                    

                elem.clear()
                total_articles += 1

    print(f"Total articles processed: {total_articles}")

# Usage example:
extract_and_clean_xml('./texts/wiki-dump/enwiki.xml', 'wiki-dump.txt')
