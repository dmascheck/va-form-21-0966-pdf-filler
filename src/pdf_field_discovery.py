#!/usr/bin/env python3
"""
VA Form 21-0966 PDF Field Discovery Script
Extracts internal field names, types, and properties from the blank PDF
"""

import sys
import os
from pdfrw import PdfReader
import json

def discover_pdf_fields(pdf_path):
    """
    Discover all form fields in the PDF and their properties
    """
    print("🔍 Starting PDF Field Discovery...")
    print(f"📄 Analyzing: {pdf_path}")
    
    try:
        # Read the PDF
        pdf = PdfReader(pdf_path)
        print(f"✅ PDF loaded successfully - {len(pdf.pages)} pages")
        
        # Extract form fields
        fields_info = []
        
        if pdf.Root.AcroForm is None:
            print("❌ No form fields found in PDF")
            return None
            
        form = pdf.Root.AcroForm
        if form.Fields is None:
            print("❌ AcroForm exists but no Fields found")
            return None
            
        print(f"📋 Found {len(form.Fields)} form fields")
        
        # Analyze each field
        for i, field in enumerate(form.Fields):
            field_info = analyze_field(field, i)
            if field_info:
                fields_info.append(field_info)
                
        return fields_info
        
    except Exception as e:
        print(f"❌ Error reading PDF: {e}")
        return None

def analyze_field(field, index):
    """
    Extract detailed information about a single field
    """
    try:
        field_info = {
            "index": index,
            "internal_name": str(field.T) if field.T else f"field_{index}",
            "field_type": str(field.FT) if field.FT else "Unknown",
            "field_flags": str(field.Ff) if field.Ff else "None",
            "default_value": str(field.DV) if field.DV else "",
            "current_value": str(field.V) if field.V else "",
            "max_length": str(field.MaxLen) if field.MaxLen else "No limit",
            "rect": str(field.Rect) if field.Rect else "No position",
            "page": "TBD"  # Will determine page later
        }
        
        # Special handling for checkboxes and radio buttons
        if field.FT == '/Btn':  # Button field (checkbox/radio)
            if field.Kids:  # Has children (radio button group)
                field_info["button_type"] = "Radio Button Group"
                field_info["options"] = []
                for kid in field.Kids:
                    if kid.AS:
                        field_info["options"].append(str(kid.AS))
            else:
                field_info["button_type"] = "Checkbox"
                
        # Special handling for choice fields (dropdowns, lists)
        elif field.FT == '/Ch':  # Choice field
            field_info["field_type"] = "Choice Field"
            if field.Opt:
                field_info["options"] = [str(opt) for opt in field.Opt]
                
        return field_info
        
    except Exception as e:
        print(f"⚠️ Error analyzing field {index}: {e}")
        return None

def save_field_mapping(fields_info, output_path):
    """
    Save field information to JSON file for future reference
    """
    try:
        with open(output_path, 'w') as f:
            json.dump(fields_info, f, indent=2)
        print(f"💾 Field mapping saved to: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Error saving field mapping: {e}")
        return False

def print_field_summary(fields_info):
    """
    Print a human-readable summary of discovered fields
    """
    print("\n" + "="*60)
    print("📊 PDF FIELD DISCOVERY SUMMARY")
    print("="*60)
    
    # Group fields by type
    field_types = {}
    for field in fields_info:
        ftype = field['field_type']
        if ftype not in field_types:
            field_types[ftype] = []
        field_types[ftype].append(field)
    
    # Print summary by type
    for ftype, fields in field_types.items():
        print(f"\n🔸 {ftype} Fields ({len(fields)}):")
        for field in fields:
            print(f"   • {field['internal_name']}")
            if field.get('button_type'):
                print(f"     Type: {field['button_type']}")
            if field.get('max_length') != 'No limit':
                print(f"     Max Length: {field['max_length']}")
    
    print(f"\n📈 Total Fields Discovered: {len(fields_info)}")
    
    # Look for email-related fields
    email_fields = [f for f in fields_info if 'email' in f['internal_name'].lower() or 'mail' in f['internal_name'].lower()]
    if email_fields:
        print(f"\n📧 Email Fields Found ({len(email_fields)}):")
        for field in email_fields:
            print(f"   • {field['internal_name']} (Max: {field['max_length']})")
    
    # Look for checkbox fields
    checkbox_fields = [f for f in fields_info if f.get('button_type') == 'Checkbox']
    if checkbox_fields:
        print(f"\n☑️ Checkbox Fields Found ({len(checkbox_fields)}):")
        for field in checkbox_fields:
            print(f"   • {field['internal_name']}")

def main():
    """
    Main function to run field discovery
    """
    # Check for PDF file argument
    if len(sys.argv) < 2:
        print("Usage: python pdf_field_discovery.py <path_to_blank_pdf>")
        print("Example: python pdf_field_discovery.py data/VA_Form_21-0966_blank.pdf")
        return
    
    pdf_path = sys.argv[1]
    
    # Verify file exists
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return
    
    # Discover fields
    fields_info = discover_pdf_fields(pdf_path)
    
    if fields_info:
        # Print summary
        print_field_summary(fields_info)
        
        # Save to JSON
        output_path = "data/field_mapping.json"
        save_field_mapping(fields_info, output_path)
        
        print(f"\n🎯 Next Steps:")
        print(f"1. Review the field mapping in {output_path}")
        print(f"2. Look for email fields to solve overflow issue")
        print(f"3. Identify checkbox fields for value testing")
        print(f"4. Create form filling script using discovered field names")
        
    else:
        print("❌ Field discovery failed. Please check the PDF file.")

if __name__ == "__main__":
    main()