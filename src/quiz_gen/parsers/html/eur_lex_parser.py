

import re
import requests
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict
from enum import Enum
import json


class SectionType(Enum):
    """Types of regulation sections"""
    # Level 0 - Document title
    TITLE = "title"  # CHUNK THIS
    
    # Level 1 - Major sections
    PREAMBLE = "preamble"
    ENACTING_TERMS = "enacting_terms"
    CONCLUDING_FORMULAS = "concluding_formulas"
    ANNEX = "annex"
    APPENDIX = "appendix"
    
    # Level 2 - Preamble elements
    CITATION = "citation" # CHUNK THIS
    RECITAL = "recital"  # CHUNK THIS
    
    # Level 2/3 - Structural
    CHAPTER = "chapter"
    SECTION = "section"
    
    # Level 3/4 - Content
    ARTICLE = "article"  # CHUNK THIS


@dataclass
class RegulationChunk:
    """Represents a parsed chunk (recital or article only)"""
    section_type: SectionType
    number: Optional[str]
    title: Optional[str]
    content: str
    hierarchy_path: Optional[List[str]] = None
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.hierarchy_path is None:
            self.hierarchy_path = []
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['section_type'] = self.section_type.value
        return data


    def _extract_annex_content(self, element, prefix=""):
        """Recursively extract all visible text from an element, preserving structure and markers."""
        parts = []
        if element is None:
            return parts
        # If it's a NavigableString, just return the text
        from bs4 import NavigableString, Tag
        if isinstance(element, NavigableString):
            text = str(element).strip()
            if text:
                parts.append(prefix + text)
            return parts
        # If it's a <p> or <span>, get its text
        if element.name in ["p", "span"]:
            text = self._clean_text(element.get_text())
            if text:
                parts.append(prefix + text)
        # If it's a <table>, process each row
        elif element.name == "table":
            for row in element.find_all("tr", recursive=False):
                cells = row.find_all(["td", "th"], recursive=False)
                if len(cells) == 2:
                    left = self._extract_annex_content(cells[0])
                    right = self._extract_annex_content(cells[1])
                    # Combine marker and content
                    if left and right:
                        for l in left:
                            for r in right:
                                parts.append(f"{l} {r}")
                    elif right:
                        parts.extend(right)
                elif len(cells) == 1:
                    parts.extend(self._extract_annex_content(cells[0]))
        # If it's a <ul> or <ol>, process each <li>
        elif element.name in ["ul", "ol"]:
            for li in element.find_all("li", recursive=False):
                parts.extend(self._extract_annex_content(li, prefix=prefix+"- "))
        # Otherwise, process children
        else:
            for child in element.children:
                parts.extend(self._extract_annex_content(child, prefix=prefix))
        return parts


class EURLexParser:
    """Parse EUR-Lex HTML and build TOC + chunk recitals/articles"""
    
    def __init__(self, url: str = None, html_content: str = None):
        self.url = url
        self.html_content = html_content
        self.soup = None
        self.chunks: List[RegulationChunk] = []
        self.toc: Dict = {'title': '', 'sections': []}
        self.current_hierarchy: List[str] = []
        self.regulation_title: str = ''
        
    def fetch(self) -> str:
        """Fetch HTML content from URL"""
        if not self.url:
            raise ValueError("No URL provided")
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(self.url, headers=headers, timeout=30)
        response.raise_for_status()
        self.html_content = response.text
        return self.html_content
    
    def parse(self) -> tuple[List[RegulationChunk], Dict]:
        """Parse and return (chunks, toc)"""
        if not self.html_content:
            if self.url:
                self.fetch()
            else:
                raise ValueError("No HTML content or URL provided")
        
        self.soup = BeautifulSoup(self.html_content, 'lxml-xml')
        
        # Parse document structure
        self._parse_title()
        self._parse_preamble()
        self._parse_enacting_terms()
        self._parse_concluding_formulas()
        self._parse_annexes()
        
        print(f"\n✓ TOC built with {len(self.toc['sections'])} major sections (flexible 2-4 levels)")
        print(f"✓ Created {len(self.chunks)} chunks (recitals + articles)")
        
        return self.chunks, self.toc
    
    def _parse_title(self):
        """Parse main title and create a chunk for it"""
        title_div = self.soup.find('div', class_='eli-main-title')
        if title_div:
            # Get all paragraphs from the title
            title_paragraphs = title_div.find_all('p', class_='oj-doc-ti')
            title_parts = [self._clean_text(p.get_text()) for p in title_paragraphs if p]
            
            # First paragraph is typically the main title
            if title_parts:
                main_title = title_parts[0]
                full_content = '\n\n'.join(title_parts)
                
                # Store for use in hierarchy
                self.regulation_title = main_title
                self.toc['title'] = main_title
                
                # CHUNK IT
                chunk = RegulationChunk(
                    section_type=SectionType.TITLE,
                    number=None,
                    title=main_title,
                    content=full_content,
                    hierarchy_path=[main_title],
                    metadata={'id': title_div.get('id', '')}
                )
                self.chunks.append(chunk)
                
                print(f"Parsed title: {main_title[:80]}...")
    
    def _parse_preamble(self):
        """Parse preamble: extract preamble content, citations, and recitals"""
        preamble_section = {'type': 'preamble', 'title': 'Preamble', 'children': []}

        # --- Extract preamble content before first citation ---
        preamble_div = self.soup.find('div', class_='eli-subdivision', id=re.compile(r'^pbl_\d+'))
        if preamble_div:
            # Find the first citation div inside preamble
            preamble_content_parts = []
            for child in preamble_div.children:
                # Stop at first citation div
                child_id = getattr(child, 'get', lambda x, y=None: None)('id', '')
                if isinstance(child_id, str) and child_id.startswith('cit_'):
                    break
                # Collect text from <p class="oj-normal">
                if getattr(child, 'name', None) == 'p' and 'oj-normal' in child.get('class', []):
                    text = self._clean_text(child.get_text())
                    if text:
                        preamble_content_parts.append(text)
            if preamble_content_parts:
                # Only chunk, do not add a separate TOC entry
                hierarchy = [self.regulation_title, "Preamble"] if self.regulation_title else ["Preamble"]
                chunk = RegulationChunk(
                    section_type=SectionType.PREAMBLE,
                    number=None,
                    title="Preamble",
                    content='\n\n'.join(preamble_content_parts),
                    hierarchy_path=hierarchy,
                    metadata={'id': preamble_div.get('id', '')}
                )
                self.chunks.append(chunk)

        # Parse citations - combine all into one chunk
        citations = self.soup.find_all('div', class_='eli-subdivision', id=re.compile(r'^cit_\d+'))
        if citations:
            # Collect all citation text
            citation_parts = []
            citation_ids = []
            for cit in citations:
                para = cit.find('p', class_='oj-normal')
                if para:
                    text = self._clean_text(para.get_text())
                    if text:
                        citation_parts.append(text)
                        citation_ids.append(cit.get('id', ''))
            if citation_parts:
                preamble_section['children'].append({
                    'type': 'citation',
                    'title': 'Citation'
                })
                hierarchy = [self.regulation_title, "Preamble", "Citation"] if self.regulation_title else ["Preamble", "Citation"]
                chunk = RegulationChunk(
                    section_type=SectionType.CITATION,
                    number=None,
                    title="Citation",
                    content='\n\n'.join(citation_parts),
                    hierarchy_path=hierarchy,
                    metadata={'id': citation_ids[0] if citation_ids else 'cit_1', 'citation_ids': citation_ids}
                )
                self.chunks.append(chunk)

        # Parse recitals
        recitals = self.soup.find_all('div', class_='eli-subdivision', id=re.compile(r'^rct_\d+'))
        for rct in recitals:
            table = rct.find('table')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) == 2:
                        num_text = self._clean_text(cells[0].get_text())
                        content = self._clean_text(cells[1].get_text())
                        
                        match = re.match(r'^\((\d+)\)$', num_text)
                        if match:
                            num = match.group(1)
                            
                            # Add to TOC
                            preamble_section['children'].append({
                                'type': 'recital',
                                'number': num,
                                'title': f"Recital {num}"
                            })
                            
                            # CHUNK IT
                            hierarchy = [self.regulation_title, "Preamble", f"Recital {num}"] if self.regulation_title else ["Preamble", f"Recital {num}"]
                            chunk = RegulationChunk(
                                section_type=SectionType.RECITAL,
                                number=num,
                                title=f"Recital {num}",
                                content=content,
                                hierarchy_path=hierarchy,
                                metadata={'id': rct.get('id', '')}
                            )
                            self.chunks.append(chunk)
        
        self.toc['sections'].append(preamble_section)
        print(f"Parsed preamble: {len(citations)} citations, {len(recitals)} recitals")
    
    def _parse_enacting_terms(self):
        """Parse chapters/sections/articles: all to TOC, chunk articles only"""
        enacting_section = {'type': 'enacting_terms', 'title': 'Enacting Terms', 'children': []}
        
        # Find all chapters
        chapters = self.soup.find_all('div', id=re.compile(r'^cpt_'))
        
        # Check if there are chapters
        if not chapters:
            # No chapters found - articles might be directly under enacting terms
            # Look for articles at the top level
            articles = self.soup.find_all('div', class_='eli-subdivision', id=re.compile(r'^art_\d+'))
            
            if articles:
                # Articles without chapters - parse them directly
                hierarchy = [self.regulation_title, "Enacting Terms"] if self.regulation_title else ["Enacting Terms"]
                for art_div in articles:
                    self._parse_article(art_div, enacting_section, hierarchy)
                
                self.toc['sections'].append(enacting_section)
                print(f"Parsed enacting terms: {len(articles)} articles (no chapters)")
                return
        
        for chapter_div in chapters:
            # Get chapter number and title
            chapter_p = chapter_div.find('p', class_='oj-ti-section-1')
            if not chapter_p:
                continue
                
            chapter_text = self._clean_text(chapter_p.get_text())
            chapter_match = re.match(r'CHAPTER\s+([IVXLCDM]+|\d+)', chapter_text, re.I)
            
            if chapter_match:
                chapter_num = chapter_match.group(1)
                
                # Get subtitle (might be in oj-ti-section-2 or in eli-title)
                subtitle_p = chapter_div.find('p', class_='oj-ti-section-2')
                if not subtitle_p:
                    # Try to find title in eli-title container
                    title_div = chapter_div.find('div', class_='eli-title')
                    if title_div:
                        subtitle_p = title_div.find('p', class_='oj-ti-section-2')
                
                chapter_title = self._clean_text(subtitle_p.get_text()) if subtitle_p else ''
                
                full_title = f"CHAPTER {chapter_num}" + (f" - {chapter_title}" if chapter_title else "")
                
                chapter_toc = {
                    'type': 'chapter',
                    'number': chapter_num,
                    'title': full_title,
                    'children': []
                }
                
                # Update hierarchy
                self.current_hierarchy = [self.regulation_title, full_title] if self.regulation_title else [full_title]
                
                # Check if this chapter has sections
                sections = chapter_div.find_all('div', id=re.compile(r'^cpt_[^.]+\.sct_'), recursive=False)
                
                if sections:
                    # Chapter has sections - parse them
                    for section_div in sections:
                        section_id = section_div.get('id', '')
                        
                        # Get section title - look for SECTION I, SECTION II, etc.
                        section_title_p = section_div.find('p', class_='oj-ti-section-1')
                        if section_title_p:
                            section_text = self._clean_text(section_title_p.get_text())
                            section_match = re.match(r'SECTION\s+([IVXLCDM]+|\d+)', section_text, re.I)
                            
                            if section_match:
                                section_num = section_match.group(1)
                                
                                # Get section subtitle
                                section_subtitle_p = section_div.find('p', class_='oj-ti-section-2')
                                if not section_subtitle_p:
                                    # Try in eli-title
                                    title_div = section_div.find('div', class_='eli-title')
                                    if title_div:
                                        section_subtitle_p = title_div.find('p', class_='oj-ti-section-2')
                                
                                section_title = self._clean_text(section_subtitle_p.get_text()) if section_subtitle_p else ''
                                
                                section_full_title = f"SECTION {section_num}" + (f" - {section_title}" if section_title else "")
                                
                                section_toc = {
                                    'type': 'section',
                                    'number': section_num,
                                    'title': section_full_title,
                                    'children': []
                                }
                                
                                # Update hierarchy to include section
                                section_hierarchy = self.current_hierarchy + [section_full_title]
                                
                                # Find articles within this section
                                articles = section_div.find_all('div', class_='eli-subdivision', id=re.compile(r'^art_\d+'))
                                
                                for art_div in articles:
                                    self._parse_article(art_div, section_toc, section_hierarchy)
                                
                                chapter_toc['children'].append(section_toc)
                else:
                    # No sections - articles directly under chapter
                    articles = chapter_div.find_all('div', class_='eli-subdivision', id=re.compile(r'^art_\d+'))
                    
                    for art_div in articles:
                        self._parse_article(art_div, chapter_toc, self.current_hierarchy)
                
                enacting_section['children'].append(chapter_toc)
        
        self.toc['sections'].append(enacting_section)
        print(f"Parsed enacting terms: {len(chapters)} chapters")
    
    def _parse_article(self, art_div, parent_toc, hierarchy_path):
        """Parse a single article and add to TOC and chunks"""
        art_p = art_div.find('p', class_='oj-ti-art')
        if not art_p:
            return
            
        art_text = self._clean_text(art_p.get_text())
        art_match = re.search(r'Article\s+(\d+[a-z]*)', art_text, re.I)
        
        if art_match:
            art_num = art_match.group(1)
            
            # Get article subtitle
            art_subtitle_p = art_div.find('p', class_='oj-sti-art')
            art_subtitle = self._clean_text(art_subtitle_p.get_text()) if art_subtitle_p else ''
            
            art_full_title = f"Article {art_num}" + (f" - {art_subtitle}" if art_subtitle else "")
            
            # Collect article content
            content_parts = []
            
            # Method 1: Look for content divs (numbered paragraphs like 1.1, 1.2)
            content_divs = art_div.find_all('div', id=re.compile(r'^\d+\.\d+'))
            for content_div in content_divs:
                paras = content_div.find_all('p', class_='oj-normal')
                for para in paras:
                    text = self._clean_text(para.get_text())
                    if text:
                        content_parts.append(text)
            
            # Method 2: Look for direct paragraphs (intro text before tables)
            direct_paras = art_div.find_all('p', class_='oj-normal', recursive=False)
            for para in direct_paras:
                text = self._clean_text(para.get_text())
                if text:
                    content_parts.append(text)
            
            # Method 3: Look for tables (list items like (a), (b), (c))
            tables = art_div.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) == 2:
                        # First cell is typically the list marker (a), (b), etc.
                        marker = self._clean_text(cells[0].get_text())
                        text = self._clean_text(cells[1].get_text())
                        if text:
                            # Combine marker and text
                            content_parts.append(f"{marker} {text}")
            
            full_content = '\n\n'.join(content_parts)
            # Apply cleaning to the combined content to fix list formatting
            full_content = self._clean_combined_text(full_content)
            
            # Add to TOC
            parent_toc['children'].append({
                'type': 'article',
                'number': art_num,
                'title': art_full_title
            })
            
            # CHUNK IT
            chunk = RegulationChunk(
                section_type=SectionType.ARTICLE,
                number=art_num,
                title=art_full_title,
                content=full_content or art_subtitle,
                hierarchy_path=hierarchy_path + [art_full_title],
                metadata={'id': art_div.get('id', ''), 'subtitle': art_subtitle}
            )
            self.chunks.append(chunk)
    
    def _parse_concluding_formulas(self):
        """Parse concluding formulas and create a chunk"""
        concluding_div = self.soup.find('div', class_='eli-subdivision', id=re.compile(r'^fnp_\d+'))
        if concluding_div:
            # Get all content from the concluding formulas
            final_div = concluding_div.find('div', class_='oj-final')
            if final_div:
                content_parts = []
                paras = final_div.find_all('p', class_='oj-normal')
                for para in paras:
                    text = self._clean_text(para.get_text())
                    if text:
                        content_parts.append(text)
                
                # Get signatory information
                signatories = final_div.find_all('div', class_='oj-signatory')
                for sig in signatories:
                    sig_paras = sig.find_all('p', class_='oj-signatory')
                    sig_parts = [self._clean_text(p.get_text()) for p in sig_paras if p]
                    if sig_parts:
                        content_parts.append('\n'.join(sig_parts))
                
                full_content = '\n\n'.join(content_parts)
                
                if full_content:
                    # Add to TOC
                    concluding_section = {
                        'type': 'concluding_formulas',
                        'title': 'Concluding formulas'
                    }
                    self.toc['sections'].append(concluding_section)
                    
                    # CHUNK IT
                    hierarchy = [self.regulation_title, "Concluding formulas"] if self.regulation_title else ["Concluding formulas"]
                    chunk = RegulationChunk(
                        section_type=SectionType.CONCLUDING_FORMULAS,
                        number=None,
                        title="Concluding formulas",
                        content=full_content,
                        hierarchy_path=hierarchy,
                        metadata={'id': concluding_div.get('id', '')}
                    )
                    self.chunks.append(chunk)
                    print(f"Parsed concluding formulas")
    
    def _parse_annexes(self):
        """Parse annexes and appendices and create chunks for each"""
        import re  # Ensure re is always the module, not a local variable
        # Find all annexes and appendices
        annexes = self.soup.find_all('div', class_='eli-container', id=re.compile(r'^anx_'))
        
        if not annexes:
            return
        
        for annex_div in annexes:
            # Get annex/appendix ID
            annex_id = annex_div.get('id', '')
            
            # Check if this is an appendix (contains .app_)
            is_appendix = '.app_' in annex_id
            
            if is_appendix:
                # Parse as appendix: anx_1.app_1
                app_match = re.match(r'^anx_(\d+)\.app_(\d+)', annex_id)
                if app_match:
                    annex_num = app_match.group(1)
                    app_num = app_match.group(2)
                    section_type = SectionType.APPENDIX
                    identifier = f"{annex_num}.{app_num}"
                else:
                    # Fallback
                    identifier = annex_id.replace('anx_', '').replace('.app_', '.')
                    section_type = SectionType.APPENDIX
            else:
                # Parse as annex: anx_1, anx_I, etc.
                annex_match = re.match(r'^anx_([IVXLCDM]+|\d+[A-Z]?)', annex_id, re.I)
                identifier = annex_match.group(1) if annex_match else annex_id.replace('anx_', '')
                section_type = SectionType.ANNEX
            
            # Get title from first oj-doc-ti paragraph
            title_paragraphs = annex_div.find_all('p', class_='oj-doc-ti')
            if title_paragraphs:
                # Get first paragraph as main title
                title_text = self._clean_text(title_paragraphs[0].get_text())
                # If there are multiple oj-doc-ti paragraphs, combine them as subtitle
                # (but NOT oj-ti-grseq-1 which typically contains PART numbers within the annex)
                if len(title_paragraphs) > 1:
                    subtitle_parts = [self._clean_text(p.get_text()) for p in title_paragraphs[1:]]
                    subtitle = ' '.join(subtitle_parts)
                else:
                    subtitle = ''
            else:
                # Fallback title
                if is_appendix:
                    title_text = f"APPENDIX {identifier}"
                else:
                    title_text = f"ANNEX {identifier}"
                subtitle = ''
            
            full_title = title_text + (f" - {subtitle}" if subtitle else "")
            
            # Create a base title with identifier for use in parts
            # This ensures parts are titled like "ANNEX 1 - PART 1" not just "ANNEX - PART 1"
            if is_appendix:
                base_title_with_id = f"APPENDIX {identifier}"
            else:
                # Check if title_text already contains the identifier
                if identifier and identifier.upper() not in title_text.upper():
                    base_title_with_id = f"ANNEX {identifier}"
                else:
                    base_title_with_id = title_text
            
            # Check if annex contains parts or sections (oj-ti-grseq-1 with PART X or Section X pattern)
            part_headers = annex_div.find_all('p', class_='oj-ti-grseq-1')
            parts_detected = []
            for part_header in part_headers:
                part_text = self._clean_text(part_header.get_text())
                # Match "PART 1", "PART I", "Part 1", etc.
                part_match = re.match(r'^PART\s+([IVXLCDM]+|\d+)', part_text, re.I)
                # Also match "Section A", "Section B", "SECTION 1", etc.
                section_match = re.match(r'^Section\s+([A-Z]|\d+)', part_text, re.I)
                
                if part_match:
                    parts_detected.append({
                        'element': part_header,
                        'number': part_match.group(1),
                        'title': part_text,
                        'type': 'part'
                    })
                elif section_match:
                    parts_detected.append({
                        'element': part_header,
                        'number': section_match.group(1),
                        'title': part_text,
                        'type': 'section'
                    })
            
            # If parts/sections detected, create separate chunks for each
            if parts_detected:
                # Add annex to TOC with parts/sections as children
                toc_entry = {
                    'type': 'appendix' if is_appendix else 'annex',
                    'number': identifier,
                    'title': base_title_with_id,  # Use base_title_with_id to show "ANNEX 1" not "ANNEX"
                    'children': []
                }
                
                hierarchy_base = [self.regulation_title, base_title_with_id] if self.regulation_title else [base_title_with_id]
                
                # Process each part/section
                for i, part_info in enumerate(parts_detected):
                    part_elem = part_info['element']
                    part_num = part_info['number']
                    part_title = part_info['title']
                    part_type = part_info.get('type', 'part')  # 'part' or 'section'
                    
                    # Simple approach: Extract all text between this header and the next one
                    # This preserves natural text flow without duplication
                    
                    # Find the container that has content between parts
                    # We need to find all siblings after this part header until the next part header
                    content_elements = []
                    current_elem = part_elem.find_next_sibling()
                    
                    # Get next part element to know when to stop
                    next_part_elem = parts_detected[i + 1]['element'] if i + 1 < len(parts_detected) else None
                    
                    # Collect all siblings until we hit the next part or run out of siblings
                    while current_elem:
                        # Stop if we hit the next part header
                        if next_part_elem and current_elem == next_part_elem:
                            break
                        
                        content_elements.append(current_elem)
                        current_elem = current_elem.find_next_sibling()
                    
                    # Extract text from collected elements
                    # Handle tables specially to avoid line breaks in numbered lists
                    part_content_parts = []
                    for elem in content_elements:
                        # Check if this element contains tables (common in annex sections)
                        tables = elem.find_all('table') if hasattr(elem, 'find_all') else []
                        
                        if tables:
                            # Extract table rows properly
                            for table in tables:
                                rows = table.find_all('tr')
                                for row in rows:
                                    cells = row.find_all('td')
                                    if len(cells) >= 2:
                                        # First cell is typically the number, second is the content
                                        num_text = self._clean_text(cells[0].get_text())
                                        content_text = self._clean_text(cells[1].get_text())
                                        if num_text and content_text:
                                            # Combine on same line
                                            part_content_parts.append(f"{num_text} {content_text}")
                                    elif len(cells) == 1:
                                        # Single cell, just get text
                                        text = self._clean_text(cells[0].get_text())
                                        if text:
                                            part_content_parts.append(text)
                        else:
                            # For non-table elements, get text normally
                            text = self._clean_text(elem.get_text())
                            if text:
                                part_content_parts.append(text)
                    
                    part_content = '\n\n'.join(part_content_parts)
                    # Use base_title_with_id to include annex/appendix number in part titles
                    part_full_title = f"{base_title_with_id} - {part_title}"
                    
                    # Add to TOC
                    toc_entry['children'].append({
                        'type': part_type,
                        'number': part_num,
                        'title': part_title
                    })
                    
                    # CHUNK IT
                    chunk = RegulationChunk(
                        section_type=section_type,
                        number=f"{identifier}.{part_num}",
                        title=part_full_title,
                        content=part_content,
                        hierarchy_path=hierarchy_base + [part_title],
                        metadata={'id': annex_id, part_type: part_num}
                    )
                    self.chunks.append(chunk)
                
                self.toc['sections'].append(toc_entry)
                
            else:
                # No parts/sections - treat as single chunk (original behavior)
                for p in annex_div.find_all('p', class_='oj-doc-ti'):
                    p.decompose()
                full_content = annex_div.get_text(separator='\n')
                full_content = '\n'.join([line.strip() for line in full_content.splitlines() if line.strip()])
                import re
                full_content = re.sub(r'\n\(([a-zA-Z]+|[ivxlcdmIVXLCDM]+|\d+)\)\n', r'\n(\1) ', full_content)
                full_content = re.sub(r'\n—\n', '\n— ', full_content)
                # Fix: join 'm\n3' (meter-cube) and similar unit splits
                full_content = re.sub(r'm\s*\n\s*3', 'm3', full_content)
                if not full_content and subtitle:
                    full_content = subtitle
                
                if full_content or subtitle:
                    # Add to TOC
                    toc_entry = {
                        'type': 'appendix' if is_appendix else 'annex',
                        'number': identifier,
                        'title': full_title
                    }
                    self.toc['sections'].append(toc_entry)
                    
                    # CHUNK IT
                    hierarchy = [self.regulation_title, full_title] if self.regulation_title else [full_title]
                    chunk = RegulationChunk(
                        section_type=section_type,
                        number=identifier,
                        title=full_title,
                        content=full_content,
                        hierarchy_path=hierarchy,
                        metadata={'id': annex_id, 'subtitle': subtitle}
                    )
                    self.chunks.append(chunk)
        
        # Count annexes vs appendices for reporting
        annex_count = sum(1 for a in annexes if '.app_' not in a.get('id', ''))
        appendix_count = sum(1 for a in annexes if '.app_' in a.get('id', ''))
        if annex_count and appendix_count:
            print(f"Parsed {annex_count} annexes and {appendix_count} appendices")
        elif annex_count:
            print(f"Parsed {annex_count} annexes")
        elif appendix_count:
            print(f"Parsed {appendix_count} appendices")
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean and normalize text for individual paragraphs"""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    @staticmethod
    def _clean_combined_text(text: str) -> str:
        """Clean combined text content, fixing list and paragraph formatting"""
        # Fix list items: (a)\n\n should become (a) with text on same line
        text = re.sub(r'\(([a-z]+|[ivx]+)\)\n\n', r'(\1) ', text)
        
        # Fix numbered list items within content
        text = re.sub(r'\n\n(\d+\.)\n\n', r'\n\n\1 ', text)
        
        return text
    
    def save_chunks(self, filepath: str):
        """Save chunks to JSON"""
        data = [chunk.to_dict() for chunk in self.chunks]
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(data)} chunks to {filepath}")
    
    def save_toc(self, filepath: str):
        """Save TOC to JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.toc, f, indent=2, ensure_ascii=False)
        print(f"Saved TOC to {filepath}")
    
    def print_toc(self):
        """Print formatted TOC showing flexible hierarchy (2-4 levels)"""
        print("\n" + "="*70)
        print("TABLE OF CONTENTS")
        print("="*70)
        
        # Print regulation title
        if self.toc.get('title'):
            print(f"\n{self.toc['title']}")
        
        for section in self.toc['sections']:
            # Level 1: Major sections
            print(f"\n{section['title'].upper()}")
            
            # Handle sections without children (like concluding formulas, annexes)
            if 'children' not in section:
                continue
            
            for child in section.get('children', []):
                if child['type'] in ['citation', 'recital']:
                    # Level 2: Citations and Recitals
                    print(f"  {child['title']}")
                elif child['type'] == 'chapter':
                    # Level 2: Chapters
                    print(f"  {child['title']}")
                    # Level 3: Sections or Articles
                    for item in child.get('children', []):
                        if item['type'] == 'section':
                            # Level 3: Sections
                            print(f"    {item['title']}")
                            # Level 4: Articles within sections
                            for art in item.get('children', []):
                                print(f"      {art['title']}")
                        elif item['type'] == 'article':
                            # Level 3: Articles (when no sections)
                            print(f"    {item['title']}")


def main():
    """Test the parser"""
    url = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32019R0947"
    
    print(f"Parsing: {url}\n")
    
    parser = EURLexParser(url=url)
    chunks, toc = parser.parse()
    
    # Print TOC
    parser.print_toc()
    
    # Print summary
    print("\n" + "="*70)
    print(f"SUMMARY")
    print("="*70)
    print(f"Total chunks: {len(chunks)}")
    by_type = {}
    for chunk in chunks:
        t = chunk.section_type.value
        by_type[t] = by_type.get(t, 0) + 1
    for t, count in sorted(by_type.items()):
        print(f"  {t}: {count}")
    
    # Save
    parser.save_chunks('data/processed/easa_chunks.json')
    parser.save_toc('data/processed/easa_toc.json')
    
    print("\n✓ Done!")


if __name__ == "__main__":
    main()
