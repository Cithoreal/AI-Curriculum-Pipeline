from lxml import etree
import json

tree = etree.parse('./sample-article/sample-article.xml')
root = tree.getroot()

LEARNING_TAGS = {
    'definition', 'example', 'exercise', 'problem', 'exploration',
    'project', 'openproblem', 'remark', 'conjecture', 'theorem',
    'lemma', 'corollary', 'axiom', 'fact', 'principle', 'computation',
    'proof', 'note', 'observation', 'insight'
}

VISUAL_TAGS = {'figure'}
INTERACTIVE_TAGS = {'interactive', 'activity', 'worksheet', 'exploration'}

TEXT_TAGS = {'p'}  # plain paragraph content
STRUCTURE_TAGS = {'chapter', 'section', 'subsection', 'subsubsection'}


extracted_content = []

def traverse_node(node, hierarchy):
        tag = node.tag

        if tag in STRUCTURE_TAGS:
            hierarchy[tag] = node.findtext('title')

        elif tag in LEARNING_TAGS.union(TEXT_TAGS):
            content = extract_text(node)
            record = build_record(hierarchy.copy(), tag, content, node.get('xml:id'))
            extracted_content.append(record)

        elif tag in VISUAL_TAGS:
            caption = extract_text(node.find('caption')) if node.find('caption') is not None else ''
            image_node = node.find('image')
            image_src = image_node.get('src') if image_node is not None else None
            content = f"Figure: {caption}"
            record = build_record(hierarchy.copy(), tag, content, node.get('xml:id'), image_src)
            extracted_content.append(record)

        elif tag in INTERACTIVE_TAGS:
            content = extract_text(node)
            record = build_record(hierarchy.copy(), 'interactive', content, node.get('xml:id'))
            extracted_content.append(record)

        for child in node:
            traverse_node(child, hierarchy.copy())
        
def extract_text(node):
    return ''.join(node.itertext()) if node is not None else ''

def build_record(hierarchy, element_type, content, xml_id, image_src=None):
    return {
        'section': hierarchy.get('section',None),
        'subsection': hierarchy.get('subsection', None),
        'subsubsection': hierarchy.get('subsubsection', None),
        'element_type': element_type,
        'content': content,
        'id': xml_id,
        'image_src': image_src
    }
    
traverse_node(root, hierarchy={})

output_path = 'parsed_pretext.json'
with open (output_path, 'w') as f:
    json.dump(extracted_content, f)