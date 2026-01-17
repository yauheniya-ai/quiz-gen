#!/usr/bin/env python3
"""
EUR-Lex Regulation HTML Parser - Simplified version
Builds TOC and chunks only recitals and articles (level 3 elements)
"""

import re
import requests
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict
from enum import Enum
import json


class SectionType(Enum):
    """Types of regulation sections"""
    # Level 1 - Major sections
    PREAMBLE = "preamble"
    ENACTING_TERMS = "enacting_terms"
    CONCLUDING_FORMULAS = "concluding_formulas"
    ANNEX = "annex"
    APPENDIX = "appendix"
    
    # Level 2 - Preamble elements
    CITATION = "citation"
    RECITAL = "recital"  # CHUNK THIS
    
    # Level 2/3 - Structural
    CHAPTER = "chapter"
    SECTION = "section"
    
    # Level 3 - Content
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


class EURLexParser:
    """Parse EUR-Lex HTML and build TOC + chunk recitals/articles"""
    
    def __init__(self, url: str = None, html_content: str = None):
        self.url = url
        self.html_content = html_content
        self.soup = None
        self.chunks: List[RegulationChunk] = []
        self.toc: Dict = {'title': 'Regulation', 'sections': []}
        self.current_hierarchy: List[str] = []
        
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
        self._parse_preamble()
        self._parse_enacting_terms()
        self._parse_annexes()
        
        print(f"\n✓ TOC built with {len(self.toc['sections'])} major sections and 3 levels")
        print(f"✓ Created {len(self.chunks)} chunks (recitals + articles)")
        
        return self.chunks, self.toc
    
    def _parse_preamble(self):
        """Parse preamble: add citations and recitals to TOC, chunk recitals"""
        preamble_section = {'type': 'preamble', 'title': 'Preamble', 'children': []}
        
        # Parse citations
        citations = self.soup.find_all('div', class_='eli-subdivision', id=re.compile(r'^cit_\d+'))
        for cit in citations:
            num = cit.get('id', '').replace('cit_', '')
            para = cit.find('p', class_='oj-normal')
            if para:
                text = self._clean_text(para.get_text())
                preamble_section['children'].append({
                    'type': 'citation',
                    'number': num,
                    'title': f"Citation {num}"
                })
        
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
                            chunk = RegulationChunk(
                                section_type=SectionType.RECITAL,
                                number=num,
                                title=f"Recital {num}",
                                content=content,
                                hierarchy_path=["Preamble", f"Recital {num}"],
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
        
        for chapter_div in chapters:
            # Get chapter number and title
            chapter_p = chapter_div.find('p', class_='oj-ti-section-1')
            if not chapter_p:
                continue
                
            chapter_text = self._clean_text(chapter_p.get_text())
            chapter_match = re.match(r'CHAPTER\s+([IVXLCDM]+|\d+)', chapter_text, re.I)
            
            if chapter_match:
                chapter_num = chapter_match.group(1)
                
                # Get subtitle
                subtitle_p = chapter_div.find('p', class_='oj-ti-section-2')
                chapter_title = self._clean_text(subtitle_p.get_text()) if subtitle_p else ''
                
                full_title = f"CHAPTER {chapter_num}" + (f" - {chapter_title}" if chapter_title else "")
                
                chapter_toc = {
                    'type': 'chapter',
                    'number': chapter_num,
                    'title': full_title,
                    'children': []
                }
                
                # Update hierarchy
                self.current_hierarchy = [full_title]
                
                # Find articles within this chapter
                articles = chapter_div.find_all('div', class_='eli-subdivision', id=re.compile(r'^art_\d+'))
                
                for art_div in articles:
                    art_p = art_div.find('p', class_='oj-ti-art')
                    if not art_p:
                        continue
                        
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
                        content_divs = art_div.find_all('div', id=re.compile(r'^\d+\.\d+'))
                        for content_div in content_divs:
                            paras = content_div.find_all('p', class_='oj-normal')
                            for para in paras:
                                text = self._clean_text(para.get_text())
                                if text:
                                    content_parts.append(text)
                        
                        full_content = '\n\n'.join(content_parts)
                        
                        # Add to TOC
                        chapter_toc['children'].append({
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
                            hierarchy_path=self.current_hierarchy + [art_full_title],
                            metadata={'id': art_div.get('id', ''), 'subtitle': art_subtitle}
                        )
                        self.chunks.append(chunk)
                
                enacting_section['children'].append(chapter_toc)
        
        self.toc['sections'].append(enacting_section)
        print(f"Parsed enacting terms: {len(chapters)} chapters")
    
    def _parse_annexes(self):
        """Parse annexes"""
        # TODO: Implement if needed
        pass
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean and normalize text"""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
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
        """Print formatted TOC showing 3-level hierarchy"""
        print("\n" + "="*70)
        print("TABLE OF CONTENTS (3 LEVELS)")
        print("="*70)
        
        for section in self.toc['sections']:
            # Level 1: Major sections
            print(f"\n{section['title'].upper()}")
            
            for child in section.get('children', []):
                if child['type'] in ['citation', 'recital']:
                    # Level 2: Citations and Recitals
                    print(f"  {child['title']}")
                elif child['type'] == 'chapter':
                    # Level 2: Chapters
                    print(f"  {child['title']}")
                    # Level 3: Articles within chapters
                    for art in child.get('children', []):
                        print(f"    {art['title']}")


def main():
    """Test the parser"""
    url = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32018R1139"
    
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
