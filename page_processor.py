from bs4 import BeautifulSoup
import bs4
import requests

def get_text_between_tags(start_tag, end_tag):
    """
    Returns a string of all text between two tags (e.g., two headers).
    """
    texts = []
    curr_element = start_tag.next_element
    
    while curr_element and curr_element != end_tag:
        if type(curr_element) == bs4.element.NavigableString:
            texts.append(curr_element.strip())
        curr_element = curr_element.next_element

    return ' '.join(texts)

def find_tags_between_elements(start_element, end_element, tag):
    """
    Finds all instances of a tag that are after start_element but before end_element.
    """
    
    matches = []
    curr_element = start_element.next_element

    while curr_element and curr_element != end_element:
        if curr_element.name == tag:
            matches.append(curr_element)
        curr_element = curr_element.next_element
    
    return(matches)

def add_infobox_data(div, docs_list, metadata_list, page_name):
    """
    Appends text and metadata for all infobox sections in given div.
    """
    sections = div.find_all('section', class_='pi-item pi-group pi-border-color')
    doc = ""
    
    for section in sections:
        data_divs = section.find_all('div', class_='pi-item pi-data pi-item-spacing pi-border-color')

        entries = []
        for div in data_divs:
            h3_text = None
            if div.find('h3'):
                h3_text = div.find('h3').text.strip()

            # Process contents
            value_div = div.find('div', class_='pi-data-value pi-font')
            items = []
            for child in value_div.children:
                if child.name == 'a':
                    items.append(child.text.strip())
                elif child.name == 'small':
                    items[-1] = items[-1] + " (" + child.text.strip() + ")"
                elif isinstance(child, str): 
                    items.append(child.strip())

            entry = h3_text + ": " + ', '.join(items) 
            entries.append(entry)
        
        doc += ". ".join(entries) + ". "
    
    docs_list.append(doc.strip())
    metadata_list.append({'Page': page_name, 'Section': 'Information'})

def add_overview_data(div, docs_list, metadata_list, page_name):
    """
    Appends text and metadata for top quote & overview.
    """
    texts = []
    for child in div.children:
        if child.name == 'p':
            if child.find('aside'):
                continue
            texts.append(child.text.strip())
        elif child.name == 'dl':
            dl_text = get_text_between_tags(child, child.find_next_sibling())
            texts.append(dl_text)
        elif child.name == 'h2':
            break
    
    docs_list.append('. '.join(texts))
    metadata_list.append({'Page': page_name, 'Section': 'Overview'})

def add_body_data(div, docs_list, metadata_list, page_name):
    """
    Appends text and metadata for article body, split by section/subsection.
    """
    for child in div.children:
        # skip if not section header
        if child.name != 'h2':
            continue
        section_title = child.text.strip()
        if section_title in ["References", "Notes", "Gallery"]:
            continue

        # find next section header if available
        curr = child.next_sibling
        next_h2 = None
        while curr:
            if curr.name == 'h2':
                next_h2 = curr
                break
            curr = curr.next_sibling
        
        if next_h2:
            subsection_headers = find_tags_between_elements(child, next_h2, 'h3')
            if subsection_headers:
                # split text by subsections
                for i in range(len(subsection_headers)):
                    curr_h3 = subsection_headers[i]
                    if i < len(subsection_headers) - 1:
                        next = subsection_headers[i + 1]
                    else:
                        next = next_h2
                    text = get_text_between_tags(curr_h3, next)
                    subsection_title = curr_h3.text.strip()
                    docs_list.append(text)
                    metadata_list.append({'Page': page_name, 'Section': section_title, 'Subsection': subsection_title})
            else:
                # if no subsections, get section text
                text = get_text_between_tags(child, next_h2)
                docs_list.append(text)
                metadata_list.append({'Page': page_name, 'Section': section_title})
        else:
            # if last section on page, get section text
            element_after_div = div.next_sibling
            text = get_text_between_tags(child, element_after_div)
            docs_list.append(text)
            metadata_list.append({'Page': page_name, 'Section': section_title})

def add_page_data(link, all_docs, all_metadata):
    """
    Updates lists of all docs and metadata with data from link.
    """
    response = requests.get(link)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')

    page_name = link
    title_span = soup.find('span', class_= 'mw-page-title-main')
    if title_span:
        page_name = title_span.text.strip()
    main_div = soup.find('div', class_= 'mw-parser-output')

    add_infobox_data(main_div, all_docs, all_metadata, page_name)
    add_overview_data(main_div, all_docs, all_metadata, page_name)
    add_body_data(main_div, all_docs, all_metadata, page_name)
