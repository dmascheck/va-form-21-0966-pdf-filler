#!/usr/bin/env python3
"""
Complete VA Form 21-0966 PDF Filler
Uses discovered field patterns and values to fill the form programmatically
"""

import sys
import os
import json
from datetime import datetime
from pdfrw import PdfReader, PdfWriter

class VAForm21_0966Filler:
    def __init__(self, blank_pdf_path):
        self.blank_pdf_path = blank_pdf_path
        self.pdf_reader = None
        self.pdf_writer = None
        
    def load_blank_form(self):
        """Load the blank PDF form"""
        try:
            self.pdf_reader = PdfReader(self.blank_pdf_path)
            print(f"✅ Loaded blank form: {self.blank_pdf_path}")
            return True
        except Exception as e:
            print(f"❌ Error loading blank form: {e}")
            return False
    
    def validate_json_input(self, data):
        """Validate the JSON input structure"""
        required_fields = ['veteran_info']
        
        for field in required_fields:
            if field not in data:
                print(f"❌ Missing required field: {field}")
                return False
        
        # Check veteran info
        veteran_info = data['veteran_info']
        required_veteran_fields = ['first_name', 'last_name', 'date_of_birth']
        
        for field in required_veteran_fields:
            if field not in veteran_info:
                print(f"❌ Missing required veteran field: {field}")
                return False
                
        print("✅ JSON input validation passed")
        return True
    
    def handle_email_overflow(self, email):
        """
        Handle email overflow using the REVERSED pattern discovered:
        EMAIL_ADDRESS[1] gets first 20 chars
        EMAIL_ADDRESS[0] gets remaining chars
        """
        if not email:
            return "", ""
            
        if len(email) <= 20:
            # Short email goes in field [1], field [0] stays empty
            return "", email
        else:
            # Split: first 20 chars in [1], remainder in [0] 
            email_part_1 = email[:20]  # First 20 chars
            email_part_0 = email[20:]  # Remaining chars
            return email_part_0, email_part_1
    
    def split_ssn(self, ssn):
        """Split SSN into three parts (XXX-XX-XXXX)"""
        # Remove any existing dashes
        clean_ssn = ssn.replace('-', '').replace(' ', '')
        
        if len(clean_ssn) != 9:
            print(f"⚠️ Warning: SSN should be 9 digits, got {len(clean_ssn)}")
            return clean_ssn[:3], clean_ssn[3:5], clean_ssn[5:9]
        
        return clean_ssn[:3], clean_ssn[3:5], clean_ssn[5:9]
    
    def split_phone(self, phone):
        """Split phone into three parts (XXX-XXX-XXXX)"""
        # Remove any formatting
        clean_phone = ''.join(filter(str.isdigit, phone))
        
        if len(clean_phone) != 10:
            print(f"⚠️ Warning: Phone should be 10 digits, got {len(clean_phone)}")
            # Pad or truncate as needed
            clean_phone = clean_phone.ljust(10, '0')[:10]
        
        return clean_phone[:3], clean_phone[3:6], clean_phone[6:10]
    
    def split_date(self, date_str):
        """Split date into MM, DD, YYYY components"""
        try:
            # Handle various date formats
            if '/' in date_str:
                parts = date_str.split('/')
            elif '-' in date_str:
                parts = date_str.split('-')
            else:
                print(f"⚠️ Warning: Unrecognized date format: {date_str}")
                return "01", "01", "1970"
            
            if len(parts) == 3:
                month, day, year = parts
                # Ensure 2-digit month and day, 4-digit year
                month = month.zfill(2)
                day = day.zfill(2)
                if len(year) == 2:
                    year = "19" + year if int(year) > 50 else "20" + year
                
                return month, day, year
            else:
                print(f"⚠️ Warning: Invalid date format: {date_str}")
                return "01", "01", "1970"
                
        except Exception as e:
            print(f"⚠️ Error parsing date {date_str}: {e}")
            return "01", "01", "1970"
    
    def split_zip(self, zip_code):
        """Split ZIP code into 5+4 format"""
        clean_zip = ''.join(filter(str.isdigit, zip_code))
        
        if len(clean_zip) >= 5:
            zip_5 = clean_zip[:5]
            zip_4 = clean_zip[5:9] if len(clean_zip) > 5 else ""
            return zip_5, zip_4
        else:
            print(f"⚠️ Warning: ZIP code too short: {zip_code}")
            return clean_zip.ljust(5, '0'), ""
    
    def create_field_mapping(self, data):
        """Create the complete field mapping from JSON data"""
        
        veteran_info = data['veteran_info']
        benefit_election = data.get('benefit_election', {})
        signature_info = data.get('signature_info', {})
        
        # Handle email overflow
        email = veteran_info.get('email', '')
        email_0, email_1 = self.handle_email_overflow(email)
        
        # Handle SSN split
        ssn = veteran_info.get('ssn', '')
        if ssn:
            ssn_1, ssn_2, ssn_3 = self.split_ssn(ssn)
        else:
            ssn_1, ssn_2, ssn_3 = "", "", ""
        
        # Handle phone split  
        phone = veteran_info.get('phone', '')
        if phone:
            phone_1, phone_2, phone_3 = self.split_phone(phone)
        else:
            phone_1, phone_2, phone_3 = "", "", ""
        
        # Handle date of birth
        dob = veteran_info.get('date_of_birth', '')
        if dob:
            dob_month, dob_day, dob_year = self.split_date(dob)
        else:
            dob_month, dob_day, dob_year = "", "", ""
        
        # Handle signature date
        sig_date = signature_info.get('date_signed', '')
        if sig_date:
            sig_month, sig_day, sig_year = self.split_date(sig_date)
        else:
            # Use today's date if not provided
            today = datetime.now()
            sig_month, sig_day, sig_year = f"{today.month:02d}", f"{today.day:02d}", str(today.year)
        
        # Handle address
        address = veteran_info.get('address', {})
        
        # Handle ZIP code split
        zip_code = address.get('zip_code', '')
        if zip_code:
            zip_5, zip_4 = self.split_zip(zip_code)
        else:
            zip_5, zip_4 = "", ""
        
        # Create complete field mapping using discovered field names
        field_mapping = {
            # Veteran Name Fields
            "F[0].Page_1[0].Veterans_First_Name[0]": veteran_info.get('first_name', ''),
            "F[0].Page_1[0].Veterans_Middle_Initial1[0]": veteran_info.get('middle_initial', ''),
            "F[0].Page_1[0].Veterans_Last_Name[0]": veteran_info.get('last_name', ''),
            
            # SSN Fields (split into 3 parts)
            "F[0].Page_1[0].Veterans_Social_SecurityNumber_FirstThreeNumbers[0]": ssn_1,
            "F[0].Page_1[0].Veterans_Social_SecurityNumber_SecondTwoNumbers[0]": ssn_2,
            "F[0].Page_1[0].VeteransSocialSecurityNumber_LastFourNumbers[0]": ssn_3,
            
            # Date of Birth Fields
            "F[0].Page_1[0].DOB_Month[0]": dob_month,
            "F[0].Page_1[0].DOB_Day[0]": dob_day,
            "F[0].Page_1[0].DOB_Year[0]": dob_year,
            
            # Contact Fields - REVERSED EMAIL PATTERN!
            "F[0].Page_1[0].EMAIL_ADDRESS[0]": email_0,  # Remaining chars
            "F[0].Page_1[0].EMAIL_ADDRESS[1]": email_1,  # First 20 chars
            
            # Phone Fields (split into 3 parts)
            "F[0].Page_1[0].Telephone_Number_FirstThreeNumbers[0]": phone_1,
            "F[0].Page_1[0].Telephone_Number_SecondThreeNumbers[0]": phone_2,
            "F[0].Page_1[0].Telephone_Number_LastFourNumbers[0]": phone_3,
            
            # Address Fields
            "F[0].Page_1[0].Mailing_Address_NumberAndStreet[0]": address.get('street', ''),
            "F[0].Page_1[0].Mailing_Address_ApartmentOrUnitNumber[0]": address.get('apt_unit', ''),
            "F[0].Page_1[0].MailingAddress_City[0]": address.get('city', ''),
            "F[0].Page_1[0].MailingAddress_StateOrProvince[0]": address.get('state', ''),
            "F[0].Page_1[0].MailingAddress_Country[0]": address.get('country', ''),
            "F[0].Page_1[0].MailingAddress_ZIPOrPostalCode_FirstFiveNumbers[0]": zip_5,
            "F[0].Page_1[0].MailingAddress_ZIPOrPostalCode_LastFourNumbers[0]": zip_4,
            
            # VA File Number (if provided)
            "F[0].Page_1[0].VA_File_Number[0]": veteran_info.get('va_file_number', ''),
            
            # Service Number (if provided)
            "F[0].Page_1[0].Veterans_Service_Number[0]": veteran_info.get('service_number', ''),
            
            # Signature Date Fields
            "F[0].#subform[1].Date_Signed_Month[0]": sig_month,
            "F[0].#subform[1].Date_Signed_Day[0]": sig_day,
            "F[0].#subform[1].Date_Signed_Year[0]": sig_year,
            
            # Attorney/VSO Field (if provided)
            "F[0].#subform[1].Name_Of_Attorney_Agent_Or_Veterans_Service_Organization_VS[0]": signature_info.get('attorney_agent_vso_name', ''),
        }
        
        # CHECKBOX STRATEGY: ONLY ADD TRUE CHECKBOXES TO MAPPING
        # This way we don't touch unchecked boxes at all
        
        if benefit_election.get('compensation', False):
            field_mapping["F[0].#subform[1].COMPENSATION[0]"] = "/1"
            
        if benefit_election.get('pension', False):
            field_mapping["F[0].#subform[1].PENSION[0]"] = "/1"
            
        if benefit_election.get('survivors_pension_dic', False):
            field_mapping["F[0].#subform[1].SURVIVORS_PENSION_AND_OR_DEPENDENCY_AND_INDEMNITY_COMPENSATION_DIC[0]"] = "/1"
        
        # NOTE: We deliberately DO NOT add "/Off" values for unchecked boxes
        # This should leave them in their default unchecked state
        
        return field_mapping
    
    def fill_form(self, field_mapping):
        """Fill the PDF form with the mapped values using correct pdfrw syntax"""
        try:
            # Fill form fields using pdfrw method
            filled_count = 0
            failed_count = 0
            
            print("\n🔧 Filling form fields...")
            
            # Get the form object
            if self.pdf_reader.Root.AcroForm is None:
                print("❌ No AcroForm found in PDF")
                return False
                
            # Fill fields using pdfrw's method
            for field_name, field_value in field_mapping.items():
                if field_value:  # Only fill non-empty values
                    try:
                        # Find the field in the form
                        field_found = self.find_and_fill_field(self.pdf_reader.Root.AcroForm.Fields, field_name, field_value)
                        if field_found:
                            print(f"✅ {field_name}: '{field_value}'")
                            filled_count += 1
                        else:
                            print(f"⚠️ Field not found: {field_name}")
                            failed_count += 1
                    except Exception as e:
                        print(f"❌ Failed to fill {field_name}: {e}")
                        failed_count += 1
            
            print(f"\n📊 Form filling summary:")
            print(f"✅ Successfully filled: {filled_count} fields")
            print(f"❌ Failed to fill: {failed_count} fields")
            
            return True
            
        except Exception as e:
            print(f"❌ Error filling form: {e}")
            return False
    
    def find_and_fill_field(self, fields, target_field_name, value, parent_path=""):
        """Recursively find and fill the target field - FIXED VERSION"""
        from pdfrw import PdfName
        
        for field in fields:
            try:
                # Decode field name
                if field.T:
                    field_name = self.decode_unicode_field_name(field.T)
                else:
                    continue
                
                # Build full path
                if parent_path:
                    full_path = f"{parent_path}.{field_name}"
                else:
                    full_path = field_name
                
                # Check if this is our target field
                if full_path == target_field_name:
                    # Set the field value - FIXED FORMATTING
                    if field.FT == PdfName.Btn:  # Button/Checkbox field
                        # For checkboxes, use the discovered working values
                        field.V = PdfName(value.replace('/', ''))  # Remove leading slash
                        field.AS = PdfName(value.replace('/', ''))
                    else:  # Text field - REMOVE PARENTHESES!
                        field.V = value  # No more f"({value})"!
                    return True
                
                # Recursively search children
                if field.Kids:
                    found = self.find_and_fill_field(field.Kids, target_field_name, value, full_path)
                    if found:
                        return True
                        
            except Exception as e:
                continue
                
        return False
    
    def decode_unicode_field_name(self, field_name_obj):
        """Decode Unicode field names"""
        field_str = str(field_name_obj)
        
        if field_str.startswith('<FEFF') and field_str.endswith('>'):
            hex_content = field_str[5:-1]
            try:
                decoded = ""
                for i in range(0, len(hex_content), 4):
                    hex_char = hex_content[i:i+4]
                    char_code = int(hex_char, 16)
                    decoded += chr(char_code)
                return decoded
            except:
                return field_str
        
        if field_str.startswith('(') and field_str.endswith(')'):
            return field_str[1:-1]
        
        return field_str
    
    def save_filled_form(self, output_path):
        """Save the filled form to specified path using pdfrw"""
        try:
            # Use PdfWriter to save the modified form
            self.pdf_writer = PdfWriter()
            
            # Add all pages from the modified reader
            for page in self.pdf_reader.pages:
                self.pdf_writer.addPage(page)
            
            # Write to file
            with open(output_path, 'wb') as output_file:
                self.pdf_writer.write(output_file)
                
            print(f"💾 Filled form saved to: {output_path}")
            return True
        except Exception as e:
            print(f"❌ Error saving form: {e}")
            return False
    
    def generate_output_filename(self, data):
        """Generate output filename based on veteran's name"""
        veteran_info = data.get('veteran_info', {})
        first_name = veteran_info.get('first_name', 'Unknown')
        last_name = veteran_info.get('last_name', 'Veteran')
        
        # Clean names for filename
        clean_first = ''.join(c for c in first_name if c.isalnum())
        clean_last = ''.join(c for c in last_name if c.isalnum())
        
        return f"VA_Form_21-0966_{clean_first}{clean_last}.pdf"

def load_json_input(json_path):
    """Load and parse JSON input file"""
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        print(f"✅ Loaded JSON input: {json_path}")
        return data
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")
        return None

def main():
    """Main function"""
    if len(sys.argv) < 3:
        print("Usage: python va_form_filler_complete.py <blank_pdf> <json_input>")
        print("Example: python va_form_filler_complete.py data/VA_Form_21-0966_blank.pdf data/test_data.json")
        return
    
    blank_pdf_path = sys.argv[1]
    json_input_path = sys.argv[2]
    
    # Verify files exist
    if not os.path.exists(blank_pdf_path):
        print(f"❌ Blank PDF not found: {blank_pdf_path}")
        return
        
    if not os.path.exists(json_input_path):
        print(f"❌ JSON input not found: {json_input_path}")
        return
    
    print("🚀 Starting VA Form 21-0966 Fill Process...")
    print("=" * 50)
    
    # Load JSON input
    data = load_json_input(json_input_path)
    if not data:
        return
    
    # Initialize form filler
    filler = VAForm21_0966Filler(blank_pdf_path)
    
    # Load blank form
    if not filler.load_blank_form():
        return
    
    # Validate input
    if not filler.validate_json_input(data):
        return
    
    # Create field mapping
    field_mapping = filler.create_field_mapping(data)
    
    # Fill form
    if not filler.fill_form(field_mapping):
        return
    
    # Generate output filename
    output_filename = filler.generate_output_filename(data)
    output_path = f"output/{output_filename}"
    
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    
    # Save filled form
    if filler.save_filled_form(output_path):
        print("\n🎉 SUCCESS!")
        print(f"📄 Filled form created: {output_path}")
        print("\n🎯 Ready for production use!")
    else:
        print("\n❌ Failed to save filled form")

if __name__ == "__main__":
    main()