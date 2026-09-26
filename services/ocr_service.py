import sys
import os
import re
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import logging
from datetime import datetime
from mrz.checker.td3 import TD3CodeChecker
from mrz.checker.td2 import TD2CodeChecker
from mrz.checker.td1 import TD1CodeChecker

logger = logging.getLogger(__name__)

class OcrServiceError(Exception):
    pass

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class OcrService:
    def __init__(self):
        # Try default installation path first
        default_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.exists(default_path):
            tesseract_path = default_path
        else:
            # Fallback to bundled path
            tesseract_path = resource_path(os.path.join("Tesseract-OCR", "tesseract.exe"))
        
        # Explicitly set the PyTesseract command path
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
    def check_tesseract_installed(self) -> bool:
        """Verifies if Tesseract OCR is available on the system."""
        if not os.path.exists(pytesseract.pytesseract.tesseract_cmd):
            logger.error(f"Tesseract executable not found at: {pytesseract.pytesseract.tesseract_cmd}")
            return False
            
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def extract_mrz_data(self, image_path: str) -> dict:
        """
        Takes an image file path, processes it with Pillow, 
        and extracts passport MRZ and visual zone data.
        Returns a dictionary with parsed information.
        """
        if not self.check_tesseract_installed():
            raise OcrServiceError("Tesseract-OCR is not installed or not in PATH. Please install Tesseract to use the Passport Scanner.")
            
        best_fallback = None
        last_error = None
            
        try:
            with Image.open(image_path) as img:
                
                # Auto-rotation and cropping loop: 
                # Try all orientations if the user uploaded it sideways/upside down
                # Also try cropping to the bottom 60% in case the user uploaded a photo of the entire 2-page passport book
                for angle in (0, -90, -180, -270):
                    rotated_img = img.rotate(angle, expand=True) if angle != 0 else img
                    
                    # Get full image text for visual labels (Father Name, etc) which might be cut off by cropping
                    full_gray = rotated_img.convert('L')
                    full_raw_text = pytesseract.image_to_string(full_gray)
                    
                    angle_had_mrz = False
                    
                    for crop_bottom in (False, True):
                        if crop_bottom:
                            w, h = rotated_img.size
                            processing_img = rotated_img.crop((0, int(h * 0.4), w, h))
                        else:
                            processing_img = rotated_img
                            
                        # Convert to grayscale
                        gray_img = processing_img.convert('L')
                        
                        # Optionally enhance contrast to help OCR
                        enhancer = ImageEnhance.Contrast(gray_img)
                        enhanced_img = enhancer.enhance(2.0)
                        
                        # 1st Pass: Raw text for visual zone (Regex fallback)
                        raw_text = pytesseract.image_to_string(gray_img)
                        
                        # 2nd Pass: MRZ text with strict whitelist on BOTH images to overcome contrast distortion
                        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<'
                        mrz_enhanced = pytesseract.image_to_string(enhanced_img, config=custom_config)
                        mrz_gray = pytesseract.image_to_string(gray_img, config=custom_config)
                        
                        # Clean up MRZ text
                        lines = [line.strip() for line in (mrz_enhanced + "\n" + mrz_gray).split('\n') if len(line.strip()) > 10]
                        mrz_text = "\n".join(lines)
                        
                        try:
                            # Attempt to parse using dual-layer pipeline
                            combined_raw = full_raw_text + "\n" + raw_text
                            parsed = self._parse_passport_data(mrz_text, combined_raw)
                            
                            if parsed.get('father_husband_name'):
                                return parsed
                            else:
                                best_fallback = parsed
                                angle_had_mrz = True
                                continue
                        except OcrServiceError as e:
                            last_error = e
                            continue # Try the next variation!
                            
                    # If we found a valid MRZ on this angle but just missed the father name, 
                    # we don't need to try 90-degree rotations. We already have the right orientation.
                    if angle_had_mrz:
                        return best_fallback
                        
                # If we exhausted all 4 angles and none worked, return fallback if exists or raise last error
                if best_fallback:
                    return best_fallback
                if last_error:
                    raise last_error

        except Exception as e:
            logger.exception("Error extracting passport data")
            raise OcrServiceError(f"Failed to extract data: {str(e)}")
            
    def _parse_passport_data(self, mrz_text: str, raw_text: str) -> dict:
        """Parses the MRZ and uses regex on raw_text for fallbacks (Father Name, CNIC, etc.)."""
        # --- 1. MRZ Parsing ---
        # Combine both mrz_text and raw_text. The enhanced image sometimes ruins the MRZ,
        # but the raw_text without contrast enhancement captures it perfectly.
        lines = mrz_text.split('\n') + raw_text.split('\n')
        
        # Keep only valid MRZ characters
        valid_lines = []
        for line in lines:
            cleaned = ''.join(c for c in line if c.isalnum() or c == '<')
            if len(cleaned) >= 30:
                valid_lines.append(cleaned)
                
        parsed_data = {
            "first_name": "",
            "last_name": "",
            "father_husband_name": "",
            "passport_number": "",
            "cnic": "",
            "dob": "",
            "expiry_date": "",
            "nationality": ""
        }
        
        if len(valid_lines) >= 2:
            try:
                # Intelligently select L1 and L2 (Tesseract often misreads P< as PE or P5)
                l1_cand = next((l for l in valid_lines if l.startswith('P') and '<' in l and len(l) >= 30), None)
                l2_cand = next((l for l in valid_lines if not l.startswith('P') and len(l) >= 38 and sum(c.isdigit() for c in l) >= 10), None)
                
                if not l1_cand or not l2_cand:
                    raise OcrServiceError("Could not find valid L1 or L2 MRZ lines in candidate text.")
                    
                l1 = l1_cand.ljust(44, '<')[:44]
                l2 = l2_cand.ljust(44, '<')[:44]
                
                # Full Name Logic (Always manual parsing from MRZ string to avoid mrz package bugs)
                if "<<" in l1[5:]:
                    parts = l1[5:].split("<<", 1)
                    surname = parts[0].replace('<', ' ').strip()
                    given_name = parts[1].replace('<', ' ').strip()
                    
                    # If the passport has no surname, the MRZ starts with << (e.g. P<PAK<<FARHAN)
                    if not surname and given_name:
                        parsed_data['first_name'] = given_name
                        parsed_data['last_name'] = ""
                        parsed_data['_surname_blank'] = True
                    else:
                        parsed_data['last_name'] = surname
                        parsed_data['first_name'] = given_name
                else:
                    parsed_data['last_name'] = l1[5:].replace('<', ' ').strip()
                    
                # Clean up trailing garbage (K, E, S, X) from first_name caused by OCR misreading '<'
                if parsed_data.get('first_name'):
                    words = parsed_data['first_name'].split()
                    clean_words = []
                    for i, w in enumerate(words):
                        # Keep the first word always. For subsequent words, discard if it's just garbage characters
                        if i == 0 or not all(c in 'KEXS' for c in w):
                            clean_words.append(w)
                    parsed_data['first_name'] = ' '.join(clean_words)
                
                try:
                    mrz_string = f"{l1}\n{l2}"
                    checker = TD3CodeChecker(mrz_string)
                    fields = checker.fields()
                    parsed_data['passport_number'] = fields.document_number.replace('<', '')
                    parsed_data['dob'] = self._parse_mrz_date(fields.birth_date)
                    parsed_data['expiry_date'] = self._parse_mrz_date(fields.expiry_date)
                    parsed_data['nationality'] = fields.nationality
                    
                    # CNIC from MRZ optional data (Pakistani format)
                    opt_data = fields.optional_data.replace('<', '')
                    if len(opt_data) >= 13 and opt_data[:13].isdigit():
                        parsed_data['cnic'] = f"{opt_data[:5]}-{opt_data[5:12]}-{opt_data[12]}"
                except Exception as e:
                    logger.warning(f"Strict TD3 Parsing failed ({e}), falling back to manual slicing...")
                    # Manual slicing fallback if checksums fail
                    parsed_data['passport_number'] = l2[0:9].replace('<', '').replace('O', '0')
                    parsed_data['nationality'] = l2[10:13].replace('<', '')
                    parsed_data['dob'] = self._parse_mrz_date(l2[13:19].replace('O', '0'))
                    parsed_data['expiry_date'] = self._parse_mrz_date(l2[21:27].replace('O', '0'))
                    
                    opt_data = l2[28:42].replace('<', '').replace('O', '0')
                    if len(opt_data) >= 13:
                        parsed_data['cnic'] = f"{opt_data[:5]}-{opt_data[5:12]}-{opt_data[12]}"

            except Exception as e:
                logger.warning(f"MRZ manual parsing failed: {e}")
                
        # --- 2. Regex Fallbacks (Visual Zone) ---
        
        # Surname Fallback (Visual Zone is usually more accurate than MRZ which misreads < as K)
        # Visual Zone Fallbacks (if MRZ failed or produced bad data)
        surname_match = re.search(r'(?:Surname)[\s\n:]+([^\n]+)', raw_text, re.IGNORECASE)
        if surname_match and '<' not in surname_match.group(1) and not parsed_data.get('_surname_blank'):
            clean_surname = re.sub(r'[^A-Z\s]', '', surname_match.group(1).upper()).strip()
            if clean_surname:
                parsed_data['last_name'] = clean_surname
        
        # Given Name / Full Name Fallback
        name_match = re.search(r'(?:Full Name|Given Name|Given Names)[\s\n:]+([^\n]+)', raw_text, re.IGNORECASE)
        if name_match:
            clean_name = re.sub(r'[^A-Z\s]', '', name_match.group(1).upper()).strip()
            if clean_name:
                parsed_data['first_name'] = clean_name
                    
        # CNIC Fallback
        if not parsed_data['cnic']:
            cnic_match = re.search(r'\b(\d{5})[\s-]*(\d{7})[\s-]*(\d{1})\b', raw_text)
            if cnic_match:
                parsed_data['cnic'] = f"{cnic_match.group(1)}-{cnic_match.group(2)}-{cnic_match.group(3)}"
                
        # Father / Husband Name Extraction
        father_match = re.search(r'(?:Father|Husband).*?Name[\s\n:]+([^\n]+)', raw_text, re.IGNORECASE)
        if father_match:
            # Clean up potential OCR artifacts like underscores or tildes
            parsed_data['father_husband_name'] = re.sub(r'[^A-Z\s]', '', father_match.group(1).upper()).strip()
            
        # Fallback 2: Look for the line before 'ISLAM' or 'Religion' if label is missing
        if not parsed_data.get('father_husband_name'):
            lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
            for i, line in enumerate(lines):
                if re.search(r'\b(ISLAM|istAM|1SLAM|Religion)\b', line, re.IGNORECASE):
                    # Look at the previous 3 lines and pick the longest uppercase string
                    candidates = lines[max(0, i-3):i]
                    best_cand = ""
                    for cand in candidates:
                        clean = re.sub(r'[^A-Z\s]', '', cand.upper()).strip()
                        if len(clean) > len(best_cand) and not clean.endswith('PAK'):
                            best_cand = clean
                    if len(best_cand) > 3:
                        parsed_data['father_husband_name'] = best_cand
                    break
                    
        # Clean up temporary flags
        parsed_data.pop('_surname_blank', None)
            
        logger.info(f"=== OCR RAW TEXT ==\n{raw_text}\n===================")
        logger.info(f"=== MRZ TEXT ==\n{mrz_text}\n===================")
        logger.info(f"=== PARSED DATA ==\n{parsed_data}\n===================")
        
        try:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop", "ocr_debug.txt")
            with open(desktop, "w", encoding="utf-8") as f:
                f.write(f"=== PARSED DATA ===\n{parsed_data}\n\n")
                f.write(f"=== MRZ TEXT ===\n{mrz_text}\n\n")
                f.write(f"=== RAW TEXT ===\n{raw_text}\n")
        except Exception:
            pass
            
        if not parsed_data['first_name'] and not parsed_data['passport_number']:
            raise OcrServiceError("Failed to parse MRZ or extract valid data. Ensure the passport is clearly visible.")
            
        return parsed_data

    def _parse_mrz_date(self, date_str: str) -> str:
        """Converts MRZ date YYMMDD into YYYY-MM-DD."""
        if not date_str or len(date_str) != 6:
            return ""
        
        # Handle common OCR confusion
        date_str = date_str.replace('O', '0').replace('I', '1').replace('l', '1')
        
        try:
            year = int(date_str[:2])
            month = int(date_str[2:4])
            day = int(date_str[4:6])
            
            # MRZ doesn't specify century. 
            # If year > 50, assume 1900s, else 2000s
            # (In 2026, a DOB could be 1950 (50) or 2010 (10))
            current_year = datetime.now().year % 100
            
            if year > current_year + 10: # arbitrary cutoff for expiry vs dob
                full_year = 1900 + year
            else:
                full_year = 2000 + year
                
            return f"{full_year:04d}-{month:02d}-{day:02d}"
        except ValueError:
            return ""
