#!/usr/bin/env python3
"""
Field Value Inspector - Shows ACTUAL VALUES in filled PDF fields
This will reveal the email overflow pattern and checkbox values
"""

import sys
import os
from pdfrw import PdfReader
import json

def decode_unicode_field_name(field_name_obj):
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

def extract_field_values(pdf_path):
    """Extract field names AND their current values"""
    print("🔍 EXTRACTING FIELD VALUES FROM FILLED PDF...")
    print(f"📄 Analyzing: {pdf_path}")
    
    try:
        pdf = PdfReader(pdf_path)
        print(f"✅ PDF loaded successfully - {len(pdf.pages)} pages")
        
        field_values = {}
        
        if pdf.Root.AcroForm is None:
            print("❌ No form fields found")
            return None
            
        form = pdf.Root.AcroForm
        if form.Fields is None:
            print("❌ No Fields found in AcroForm")
            return None
            
        print(f"📋 Found {len(form.Fields)} top-level fields")
        
        # Extract all field values recursively
        extract_values_recursive(form.Fields, field_values, "")
        
        return field_values
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def extract_values_recursive(fields, field_values, parent_path):
    """Recursively extract field names and values"""
    
    for field in fields:
        try:
            # Get field name
            if field.T:
                field_name = decode_unicode_field_name(field.T)
            else:
                field_name = f"unnamed_{len(field_values)}"
            
            # Build full path
            if parent_path:
                full_path = f"{parent_path}.{field_name}"
            else:
                full_path = field_name
            
            # Get field value
            field_value = ""
            if field.V:
                field_value = str(field.V)
                # Clean up value format
                if field_value.startswith('(') and field_value.endswith(')'):
                    field_value = field_value[1:-1]
            
            # Get field type
            field_type = str(field.FT) if field.FT else "Unknown"
            
            # Store field info
            field_info = {
                "full_path": full_path,
                "field_type": field_type,
                "current_value": field_value,
                "has_value": bool(field_value),
                "max_length": str(field.MaxLen) if field.MaxLen else "No limit"
            }
            
            field_values[full_path] = field_info
            
            # Process children if they exist
            if field.Kids:
                extract_values_recursive(field.Kids, field_values, full_path)
                
        except Exception as e:
            print(f"⚠️ Error processing field: {e}")

def analyze_field_values(field_values):
    """Analyze the extracted field values for patterns"""
    print("\n" + "="*80)
    print("📊 FIELD VALUE ANALYSIS - FILLED PDF")
    print("="*80)
    
    # Separate fields with values vs empty
    filled_fields = {k: v for k, v in field_values.items() if v["has_value"]}
    empty_fields = {k: v for k, v in field_values.items() if not v["has_value"]}
    
    print(f"\n📈 Total Fields: {len(field_values)}")
    print(f"✅ Fields with Values: {len(filled_fields)}")
    print(f"⚪ Empty Fields: {len(empty_fields)}")
    
    # Show all filled fields
    print(f"\n🔍 FIELDS WITH ACTUAL VALUES:")
    print("-" * 60)
    
    for field_path, info in sorted(filled_fields.items()):
        field_type = info["field_type"]
        value = info["current_value"]
        max_len = info["max_length"]
        
        print(f"📍 {field_path}")
        print(f"   Type: {field_type}")
        print(f"   Value: '{value}'")
        print(f"   Max Length: {max_len}")
        print()
    
    # Analyze specific patterns
    print("🎯 CRITICAL PATTERN ANALYSIS:")
    print("-" * 40)
    
    # Email fields analysis
    email_fields = {k: v for k, v in filled_fields.items() if "EMAIL_ADDRESS" in k}
    if email_fields:
        print("\n📧 EMAIL FIELD VALUES:")
        for field_path, info in sorted(email_fields.items()):
            print(f"   {field_path}: '{info['current_value']}'")
    
    # Checkbox analysis
    checkbox_fields = {k: v for k, v in filled_fields.items() if 
                      "COMPENSATION" in k or "PENSION" in k or "SURVIVORS" in k}
    if checkbox_fields:
        print("\n☑️ CHECKBOX FIELD VALUES:")
        for field_path, info in sorted(checkbox_fields.items()):
            print(f"   {field_path}: '{info['current_value']}'")
    
    # Button/Radio analysis
    button_fields = {k: v for k, v in filled_fields.items() if info["field_type"] == "/Btn"}
    if button_fields:
        print("\n🔘 BUTTON FIELD VALUES:")
        for field_path, info in sorted(button_fields.items()):
            print(f"   {field_path}: '{info['current_value']}'")
    
    return filled_fields

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python field_value_inspector.py <path_to_filled_pdf>")
        return
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return
    
    # Extract field values
    field_values = extract_field_values(pdf_path)
    
    if field_values:
        # Analyze the values
        filled_fields = analyze_field_values(field_values)
        
        # Save to JSON for reference
        output_path = "data/filled_field_values.json"
        with open(output_path, 'w') as f:
            json.dump(field_values, f, indent=2)
        print(f"\n💾 Field values saved to: {output_path}")
        
        print(f"\n🎯 KEY INSIGHTS:")
        print("✅ Email overflow pattern revealed")
        print("✅ Checkbox 'checked' values identified") 
        print("✅ Ready to create form filling script with exact values")
        
    else:
        print("❌ Failed to extract field values")

if __name__ == "__main__":
    main()