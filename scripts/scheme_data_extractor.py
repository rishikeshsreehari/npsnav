# scripts/scheme_data_extractor.py
import requests
import json
import re
import os
from datetime import datetime
from bs4 import BeautifulSoup
import pdfplumber
import pandas as pd
import PyPDF2

class NPSSchemeDataExtractor:
    def __init__(self):
        self.base_url = "https://npstrust.org.in"
        self.scheme_list_url = "https://npstrust.org.in/weekly-snapshot-nps-schemes"
        self.output_file = "data/scheme_data.json"
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        
        # Fund mapping for consistent naming
        self.fund_mapping = {
            'SBIPF': 'SBI PENSION FUNDS PRIVATE LIMITED',
            'SBI': 'SBI PENSION FUNDS PRIVATE LIMITED',
            'LICPF': 'LIC PENSION FUND LIMITED',
            'LIC': 'LIC PENSION FUND LIMITED',
            'UTIPF': 'UTI PENSION FUND LIMITED',
            'UTI': 'UTI PENSION FUND LIMITED',
            'ICICI': 'ICICI PRUDENTIAL PENSION FUNDS MANAGEMENT COMPANY LIMITED',
            'KOTAK': 'KOTAK MAHINDRA PENSION FUND LIMITED',
            'HDFC': 'HDFC PENSION FUND MANAGEMENT LIMITED',
            'Aditya Birla': 'ADITYA BIRLA SUNLIFE PENSION FUND MANAGEMENT LIMITED',
            'ADITYA': 'ADITYA BIRLA SUNLIFE PENSION FUND MANAGEMENT LIMITED',
            'TATA': 'TATA PENSION FUND MANAGEMENT PRIVATE LIMITED',
            'AXIS': 'AXIS PENSION FUND MANAGEMENT LIMITED',
            'DSP': 'DSP PENSION FUND MANAGERS PRIVATE LIMITED',
            'MAX': 'MAX LIFE PENSION FUND MANAGEMENT LIMITED'
        }

    def extract_scheme_links(self):
        """Extract all PDF links from the NPS schemes page"""
        try:
            print("Fetching scheme links...")
            response = requests.get(self.scheme_list_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            scheme_links = []
            
            # Find all PDF links
            pdf_links = soup.find_all('a', href=re.compile(r'scheme_retuen_pdf.*\.pdf'))
            
            for link in pdf_links:
                href = link.get('href')
                title = link.get('title', link.text.strip())
                
                if href and title:
                    full_url = href if href.startswith('http') else self.base_url + href
                    scheme_links.append({
                        'name': title.replace('Scheme - ', ''),
                        'url': full_url,
                        'type': self._categorize_scheme(title)
                    })
            
            print(f"Found {len(scheme_links)} scheme PDFs")
            return scheme_links
            
        except Exception as e:
            print(f"Error extracting scheme links: {e}")
            return []

    def _categorize_scheme(self, title):
        """Categorize scheme based on title"""
        title_lower = title.lower()
        if 'tier i' in title_lower and 'tier ii' not in title_lower:
            return 'Tier-I'
        elif 'tier ii' in title_lower:
            return 'Tier-II' 
        elif 'central government' in title_lower:
            return 'Central-Government'
        elif 'state government' in title_lower:
            return 'State-Government'
        elif 'corporate' in title_lower:
            return 'Corporate'
        elif 'nps lite' in title_lower:
            return 'NPS-Lite'
        elif 'apy' in title_lower or 'atal pension' in title_lower:
            return 'APY'
        elif 'tax saver' in title_lower:
            return 'Tax-Saver'
        elif 'ups' in title_lower:
            return 'UPS'
        elif 'composite' in title_lower:
            return 'Composite'
        else:
            return 'Other'

    def download_and_extract_pdf(self, pdf_url):
        """Download PDF and extract structured data"""
        try:
            print(f"Downloading: {pdf_url}")
            
            # Download PDF
            response = requests.get(pdf_url, timeout=60)
            response.raise_for_status()
            
            # Save temporary PDF file
            temp_pdf = "temp_scheme.pdf"
            with open(temp_pdf, 'wb') as f:
                f.write(response.content)
            
            print("Extracting data from PDF...")
            # Extract data using available methods
            extracted_data = self._extract_pdf_data(temp_pdf)
            
            # Clean up
            if os.path.exists(temp_pdf):
                os.remove(temp_pdf)
                
            return extracted_data
            
        except Exception as e:
            print(f"Error processing PDF {pdf_url}: {e}")
            return None

    def _extract_pdf_data(self, pdf_path):
        """Extract data from PDF using available methods"""
        data = {
            'funds': {},
            'nav_data': {},
            'assets_crores': {},
            'returns': {},
            'holdings': {},
            'top_holdings_weightage': {},
            'sectors': {},
            'metadata': {}
        }
        
        try:
            # Method 1: Try pdfplumber (most reliable for tables)
            print("Trying pdfplumber extraction...")
            pdfplumber_data = self._extract_with_pdfplumber(pdf_path)
            if pdfplumber_data and pdfplumber_data.get('funds'):
                print("✓ PDFPlumber extraction successful")
                data.update(pdfplumber_data)
                return data
            
            # Method 2: Try PyPDF2 as fallback
            print("Trying PyPDF2 extraction...")
            pypdf2_data = self._extract_with_pypdf2(pdf_path)
            if pypdf2_data and pypdf2_data.get('funds'):
                print("✓ PyPDF2 extraction successful")
                data.update(pypdf2_data)
                return data
                
        except Exception as e:
            print(f"Error in PDF extraction: {e}")
            
        return data

    def _extract_with_pdfplumber(self, pdf_path):
        """Extract data using pdfplumber"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                all_text = ""
                tables = []
                
                for page in pdf.pages:
                    # Extract text
                    page_text = page.extract_text()
                    if page_text:
                        all_text += page_text + "\n"
                    
                    # Extract tables
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
                
                if all_text.strip():
                    return self._parse_extracted_content(all_text, tables)
                
        except Exception as e:
            print(f"PDFPlumber extraction failed: {e}")
            
        return None

    def _extract_with_pypdf2(self, pdf_path):
        """Extract data using PyPDF2 as fallback"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                all_text = ""
                
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        all_text += text + "\n"
                
                if all_text.strip():
                    return self._parse_extracted_content(all_text, [])
                
        except Exception as e:
            print(f"PyPDF2 extraction failed: {e}")
            
        return None

    def _parse_extracted_content(self, text, tables):
        """Parse the extracted content and structure the data"""
        print("Parsing extracted content...")
        
        data = {
            'funds': {},
            'nav_data': {},
            'assets_crores': {},
            'returns': {},
            'holdings': {},
            'top_holdings_weightage': {},
            'sectors': {},
            'metadata': {}
        }
        
        try:
            # Find fund names with improved logic
            fund_names = self._extract_fund_names_improved(text, tables)
            
            if not fund_names:
                print("No fund names found")
                return data
            
            print(f"Found funds: {fund_names}")
            
            # Extract all data
            nav_data = self._extract_nav_data_improved(tables, fund_names, text)
            assets_data = self._extract_assets_data_improved(tables, fund_names, text)
            returns_data = self._extract_returns_data_improved(tables, fund_names, text)
            holdings_data, top_weightage = self._extract_holdings_data_improved(text, tables, fund_names)
            sectors_data = self._extract_sectors_data_improved(text, tables)
            
            # Build the data structure
            data['funds'] = {name: self.fund_mapping.get(name, name) for name in fund_names}
            data['nav_data'] = nav_data
            data['assets_crores'] = assets_data
            data['returns'] = returns_data
            data['holdings'] = holdings_data
            data['top_holdings_weightage'] = top_weightage
            data['sectors'] = sectors_data
            data['metadata'] = {
                'extracted_at': datetime.now().isoformat(),
                'total_funds': len(fund_names),
                'fund_names': fund_names
            }
            
            print(f"Extracted data for {len(fund_names)} funds")
            
        except Exception as e:
            print(f"Error parsing content: {e}")
            import traceback
            traceback.print_exc()
            
        return data

    def _extract_fund_names_improved(self, text, tables):
        """Improved fund name extraction"""
        fund_names = []
        
        # All possible fund patterns
        fund_patterns = [
            'SBIPF', 'SBI PF', 'SBI',
            'LICPF', 'LIC PF', 'LIC',
            'UTIPF', 'UTI PF', 'UTI',
            'ICICI PF', 'ICICI',
            'KOTAK PF', 'KOTAK',
            'HDFC PF', 'HDFC',
            'Aditya Birla PF', 'Aditya Birla', 'ADITYA',
            'TATA PF', 'TATA',
            'AXIS PF', 'AXIS',
            'DSP PF', 'DSP',
            'MAX PF', 'MAX'
        ]
        
        # Standardize fund names
        fund_standardizer = {
            'SBIPF': 'SBI', 'SBI PF': 'SBI',
            'LICPF': 'LIC', 'LIC PF': 'LIC',
            'UTIPF': 'UTI', 'UTI PF': 'UTI',
            'ICICI PF': 'ICICI',
            'KOTAK PF': 'KOTAK',
            'HDFC PF': 'HDFC',
            'Aditya Birla PF': 'Aditya Birla', 'ADITYA': 'Aditya Birla',
            'TATA PF': 'TATA',
            'AXIS PF': 'AXIS',
            'DSP PF': 'DSP',
            'MAX PF': 'MAX'
        }
        
        # Method 1: Extract from tables
        for table in tables:
            if not table:
                continue
                
            for row in table:
                if not row:
                    continue
                    
                row_text = ' '.join(str(cell) for cell in row if cell and str(cell).strip())
                found_funds = []
                
                for pattern in fund_patterns:
                    if pattern.upper() in row_text.upper():
                        standardized = fund_standardizer.get(pattern, pattern)
                        if standardized not in found_funds:
                            found_funds.append(standardized)
                
                if len(found_funds) >= 3:  # Found multiple funds
                    fund_names = found_funds[:10]  # Limit to 10 funds
                    break
                        
            if fund_names:
                break
        
        # Method 2: Extract from text lines
        if not fund_names:
            lines = text.split('\n')
            for line in lines:
                found_funds = []
                
                for pattern in fund_patterns:
                    if pattern.upper() in line.upper():
                        standardized = fund_standardizer.get(pattern, pattern)
                        if standardized not in found_funds:
                            found_funds.append(standardized)
                
                if len(found_funds) >= 3:
                    fund_names = found_funds[:10]
                    break
        
        # Method 3: Look for specific patterns in text
        if not fund_names:
            # Look for scheme names that contain fund info
            scheme_patterns = [
                r'(SBI|LIC|UTI|ICICI|KOTAK|HDFC|Aditya|TATA|AXIS|DSP|MAX)[\s\w]*PENSION',
                r'PENSION[\s\w]*(SBI|LIC|UTI|ICICI|KOTAK|HDFC|Aditya|TATA|AXIS|DSP|MAX)'
            ]
            
            text_upper = text.upper()
            found_funds = []
            
            for pattern in scheme_patterns:
                matches = re.findall(pattern, text_upper)
                for match in matches:
                    if match not in found_funds:
                        found_funds.append(match)
            
            if found_funds:
                fund_names = found_funds[:5]  # Limit for scheme-based extraction
        
        return fund_names

    def _extract_nav_data_improved(self, tables, fund_names, text):
        """Improved NAV extraction"""
        nav_data = {}
        
        # Look for NAV in text
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if 'NAV' in line.upper() and len(line.strip()) < 50:  # NAV header line
                # Look in next few lines for values
                for j in range(i + 1, min(i + 4, len(lines))):
                    if j >= len(lines):
                        break
                        
                    check_line = lines[j].strip()
                    # Find decimal numbers that could be NAV
                    nav_values = re.findall(r'\b\d{1,3}\.\d{2,4}\b', check_line)
                    
                    valid_navs = []
                    for nav in nav_values:
                        val = float(nav)
                        if 5.0 <= val <= 500.0:  # Reasonable NAV range
                            valid_navs.append(val)
                    
                    if len(valid_navs) >= len(fund_names):
                        for k, fund in enumerate(fund_names):
                            if k < len(valid_navs):
                                nav_data[fund] = valid_navs[k]
                        return nav_data
        
        return nav_data

    def _extract_assets_data_improved(self, tables, fund_names, text):
        """Improved assets extraction"""
        assets_data = {}
        
        # Look for assets in text
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if 'assets' in line_lower and ('crore' in line_lower or 'rs' in line_lower):
                # Look in next few lines
                for j in range(i + 1, min(i + 4, len(lines))):
                    if j >= len(lines):
                        break
                        
                    check_line = lines[j].strip()
                    asset_values = re.findall(r'\b\d+\.\d+\b', check_line)
                    
                    valid_assets = []
                    for asset in asset_values:
                        val = float(asset)
                        if 0.1 <= val <= 50000:  # Assets range in crores
                            valid_assets.append(val)
                    
                    if len(valid_assets) >= len(fund_names):
                        for k, fund in enumerate(fund_names):
                            if k < len(valid_assets):
                                assets_data[fund] = valid_assets[k]
                        return assets_data
        
        return assets_data

    def _extract_returns_data_improved(self, tables, fund_names, text):
        """Improved returns extraction"""
        returns_data = {}
        
        return_periods = [
            '3 Months', '6 Months', '1 Year', '2 Years', '3 Years', 
            '5 Years', '7 Years', 'Since Inception'
        ]
        
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            for period in return_periods:
                if period.lower() in line_clean.lower():
                    # Look for percentages in next lines
                    for j in range(i + 1, min(i + 3, len(lines))):
                        if j >= len(lines):
                            break
                            
                        check_line = lines[j].strip()
                        # Find percentage values
                        percentages = re.findall(r'(\d+\.\d+)%?', check_line)
                        
                        valid_returns = []
                        for pct in percentages:
                            val = float(pct)
                            if -50 <= val <= 200:  # Reasonable return range
                                valid_returns.append(val)
                        
                        if len(valid_returns) >= len(fund_names):
                            if period not in returns_data:
                                returns_data[period] = {}
                            
                            for k, fund in enumerate(fund_names):
                                if k < len(valid_returns):
                                    returns_data[period][fund] = valid_returns[k]
                            break
                    break
        
        return returns_data

    def _extract_holdings_data_improved(self, text, tables, fund_names):
        """Improved holdings extraction"""
        holdings_data = {fund: {} for fund in fund_names}
        weightage_data = {fund: 0.0 for fund in fund_names}
        
        lines = text.split('\n')
        
        # Look for weightage line
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if 'weightage' in line_lower and 'top' in line_lower and 'holdings' in line_lower:
                # Look in next line for percentages
                for j in range(i + 1, min(i + 3, len(lines))):
                    if j >= len(lines):
                        break
                        
                    check_line = lines[j].strip()
                    percentages = re.findall(r'(\d+\.\d+)', check_line)
                    
                    valid_weightages = []
                    for pct in percentages:
                        val = float(pct)
                        if 5 <= val <= 100:  # Reasonable weightage range
                            valid_weightages.append(val)
                    
                    if len(valid_weightages) >= len(fund_names):
                        for k, fund in enumerate(fund_names):
                            if k < len(valid_weightages):
                                weightage_data[fund] = valid_weightages[k]
                        break
                break
        
        # Look for holdings section (simplified)
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if 'top' in line_lower and 'holdings' in line_lower and 'weightage' not in line_lower:
                # Process next few lines for holdings
                for j in range(i + 1, min(i + 10, len(lines))):
                    if j >= len(lines):
                        break
                    
                    holdings_line = lines[j]
                    if ';' in holdings_line and len(holdings_line) > 50:  # Line with multiple holdings
                        holdings_parts = holdings_line.split(';')
                        
                        for k, holdings_part in enumerate(holdings_parts):
                            if k < len(fund_names):
                                fund = fund_names[k]
                                holdings_part = holdings_part.strip()
                                
                                if holdings_part and len(holdings_part) > 10:
                                    # Extract percentage if present
                                    pct_match = re.search(r'(\d+\.\d+)%', holdings_part)
                                    if pct_match:
                                        percentage = float(pct_match.group(1))
                                        holding_name = re.sub(r'\d+\.\d+%', '', holdings_part).strip()
                                        if holding_name:
                                            holdings_data[fund][holding_name] = percentage
                                    else:
                                        holdings_data[fund][holdings_part] = None
                break
        
        return holdings_data, weightage_data

    def _extract_sectors_data_improved(self, text, tables):
        """Improved sector extraction"""
        sectors_data = {}
        
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            if (('sector' in line_lower or 
                'transmission' in line_lower or 
                'intermediation' in line_lower or
                'real estate' in line_lower) and len(line) > 50):
                
                # Split by semicolon for different fund sectors
                sectors = line.split(';')
                for sector in sectors:
                    sector = sector.strip()
                    if sector and len(sector) > 20:  # Meaningful sector names
                        sector_clean = re.sub(r'\d+\.\d+%?', '', sector).strip()
                        if sector_clean and len(sector_clean) > 15:
                            sectors_data[sector_clean] = sectors_data.get(sector_clean, 0) + 1
                break
        
        return sectors_data

    def process_all_schemes(self):
        """Process all scheme PDFs and generate scheme_data.json"""
        print("Starting NPS scheme data extraction...")
        
        scheme_links = self.extract_scheme_links()
        
        if not scheme_links:
            print("No scheme links found!")
            return
        
        all_scheme_data = {}
        successful_count = 0
        
        for i, scheme in enumerate(scheme_links, 1):
            print(f"\n[{i}/{len(scheme_links)}] Processing: {scheme['name']} ({scheme['type']})")
            
            pdf_data = self.download_and_extract_pdf(scheme['url'])
            
            if pdf_data and pdf_data.get('funds'):
                all_scheme_data[scheme['name']] = {
                    'type': scheme['type'],
                    'url': scheme['url'],
                    'data': pdf_data,
                    'last_updated': datetime.now().isoformat()
                }
                successful_count += 1
                print(f"✓ Successfully processed {scheme['name']}")
            else:
                print(f"✗ Failed to process {scheme['name']}")
        
        # Save results
        output_data = {
            'schemes': all_scheme_data,
            'metadata': {
                'total_schemes': len(all_scheme_data),
                'extraction_date': datetime.now().isoformat(),
                'source_url': self.scheme_list_url,
                'total_schemes_found': len(scheme_links),
                'successful_extractions': successful_count,
                'success_rate': f"{successful_count/len(scheme_links)*100:.1f}%"
            }
        }
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Generated {self.output_file}")
        print(f"✓ Successfully processed: {successful_count}/{len(scheme_links)} schemes")
        print(f"✓ Success rate: {successful_count/len(scheme_links)*100:.1f}%")
        
        return output_data

if __name__ == "__main__":
    extractor = NPSSchemeDataExtractor()
    result = extractor.process_all_schemes()