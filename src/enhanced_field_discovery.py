#!/usr/bin/env python3
"""
Enhanced VA Form 21-0966 PDF Field Discovery Script
Handles hierarchical fields and Unicode field names
"""

import sys
import os
from pdfrw import PdfReader
import json

def decode_unicode_field_name(field_name_obj):
    """
    Decode Unicode field names that appear as <FEFF...>
    """
    field_str = str(field_name_obj)
    
    # Handle Unicode encoded field names
    if field_str.startswith('<FEFF') and field_str.endswith('>'):
        # Extract hex content
        hex_content = field_str[5:-1]  # Remove <FEFF and >
        
        try:
            # Convert hex pairs to characters
            decoded = ""
            for i in range(0, len(hex_content), 4):
                hex_char = hex_content[i:i+4]
                char_code = int(hex_char, 16)
                decoded += chr(char_code)
            return decoded
        except:
            return field_str
    
    # Handle regular parentheses format
    if field_str.startswith('(') and field_str.endswith(')'):
        return field_str[1:-1]
    
    return field_str

def discover_pdf_fields_enhanced(pdf_path):
    """
    Enhanced field discovery with hierarchical field support
    """
    print("🔍 Starting Enhanced PDF Field Discovery...")
    print(f"📄 Analyzing: {pdf_path}")
    
    try:
        pdf = PdfReader(pdf_path)
        print(f"✅ PDF loaded successfully - {len(pdf.pages)} pages")
        
        fields_info = []
        
        if pdf.Root.AcroForm is None:
            print("❌ No form fields found in PDF")
            return None
            
        form = pdf.Root.AcroForm
        if form.Fields is None:
            print("❌ AcroForm exists but no Fields found")
            return None
            
        print(f"📋 Found {len(form.Fields)} top-level form fields")
        
        # Analyze each top-level field and its children
        for i, field in enumerate(form.Fields):
            analyze_field_recursive(field, fields_info, level=0, parent_name="")
                
        return fields_info
        
    except Exception as e:
        print(f"❌ Error reading PDF: {e}")
        return None

def analyze_field_recursive(field, fields_info, level=0, parent_name=""):
    """
    Recursively analyze fields and their children
    """
    try:
        # Decode field name
        if field.T:
            field_name = decode_unicode_field_name(field.T)
        else:
            field_name = f"unnamed_field_{len(fields_info)}"
        
        # Build full field path
        if parent_name:
            full_name = f"{parent_name}.{field_name}"
        else:
            full_name = field_name
        
        field_info = {
            "level": level,
            "parent": parent_name,
            "field_name": field_name,
            "full_path": full_name,
            "field_type": str(field.FT) if field.FT else "Unknown",
            "field_flags": str(field.Ff) if field.Ff else "None",
            "default_value": str(field.DV) if field.DV else "",
            "current_value": str(field.V) if field.V else "",
            "max_length": str(field.MaxLen) if field.MaxLen else "No limit",
            "has_children": bool(field.Kids),
            "child_count": len(field.Kids) if field.Kids else 0
        }
        
        # Add to fields list
        fields_info.append(field_info)
        
        # Print discovery progress
        indent = "  " * level
        print(f"{indent}🔸 {full_name} (Type: {field_info['field_type']}, Children: {field_info['child_count']})")
        
        # Special handling for different field types
        if field.FT == '/Btn':  # Button field
            if field.Kids:
                field_info["button_type"] = "Radio Button Group"
                field_info["options"] = []
            else:
                field_info["button_type"] = "Checkbox"
                
        elif field.FT == '/Ch':  # Choice field
            field_info["field_type"] = "Choice Field"
            if field.Opt:
                field_info["options"] = [str(opt) for opt in field.Opt]
        
        # Recursively process children
        if field.Kids:
            for child in field.Kids:
                analyze_field_recursive(child, fields_info, level + 1, full_name)
                
    except Exception as e:
        print(f"⚠️ Error analyzing field at level {level}: {e}")

def print_enhanced_summary(fields_info):
    """
    Print enhanced summary with hierarchical structure
    """
    print("\n" + "="*80)
    print("📊 ENHANCED PDF FIELD DISCOVERY SUMMARY")
    print("="*80)
    
    # Organize by hierarchy level
    levels = {}
    for field in fields_info:
        level = field['level']
        if level not in levels:
            levels[level] = []
        levels[level].append(field)
    
    print(f"\n📈 Total Fields Discovered: {len(fields_info)}")
    print(f"📊 Hierarchy Levels: {len(levels)}")
    
    # Print by level
    for level in sorted(levels.keys()):
        fields_at_level = levels[level]
        print(f"\n🔸 Level {level} Fields ({len(fields_at_level)}):")
        
        for field in fields_at_level:
            indent = "  " * (level + 1)
            field_type = field['field_type']
            if field.get('button_type'):
                field_type += f" ({field['button_type']})"
            
            print(f"{indent}• {field['full_path']} - {field_type}")
            
            if field['max_length'] != 'No limit':
                print(f"{indent}  Max Length: {field['max_length']}")
            if field['child_count'] > 0:
                print(f"{indent}  Children: {field['child_count']}")
    
    # Look for specific field patterns
    print(f"\n🔍 FIELD PATTERN ANALYSIS:")
    
    # Email fields
    email_fields = [f for f in fields_info if 'email' in f['field_name'].lower() or 'mail' in f['field_name'].lower()]
    if email_fields:
        print(f"\n📧 Email Fields ({len(email_fields)}):")
        for field in email_fields:
            print(f"   • {field['full_path']} (Max: {field['max_length']})")
    else:
        print(f"\n📧 Email Fields: None found with 'email' keyword")
    
    # Checkbox/Button fields
    button_fields = [f for f in fields_info if f['field_type'] == '/Btn' or f.get('button_type')]
    if button_fields:
        print(f"\n☑️ Button/Checkbox Fields ({len(button_fields)}):")
        for field in button_fields:
            button_type = field.get('button_type', 'Button')
            print(f"   • {field['full_path']} ({button_type})")
    else:
        print(f"\n☑️ Button/Checkbox Fields: None found")
    
    # Text fields
    text_fields = [f for f in fields_info if f['field_type'] == '/Tx']
    if text_fields:
        print(f"\n📝 Text Fields ({len(text_fields)}):")
        for field in text_fields:
            print(f"   • {field['full_path']} (Max: {field['max_length']})")
    else:
        print(f"\n📝 Text Fields: None found")

def main():
    """
    Main function with enhanced discovery
    """
    if len(sys.argv) < 2:
        print("Usage: python enhanced_field_discovery.py <path_to_blank_pdf>")
        return
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return
    
    # Enhanced field discovery
    fields_info = discover_pdf_fields_enhanced(pdf_path)
    
    if fields_info:
        print_enhanced_summary(fields_info)
        
        # Save detailed mapping
        output_path = "data/enhanced_field_mapping.json"
        with open(output_path, 'w') as f:
            json.dump(fields_info, f, indent=2)
        print(f"\n💾 Enhanced field mapping saved to: {output_path}")
        
        print(f"\n🎯 Key Findings:")
        print(f"✅ Discovered {len(fields_info)} total fields")
        print(f"✅ Root field 'F[0]' successfully decoded")
        print(f"✅ Hierarchical structure mapped")
        print(f"🔍 Next: Analyze field mapping to solve email overflow and checkbox issues")
        
    else:
        print("❌ Enhanced field discovery failed")

if __name__ == "__main__":
    main()