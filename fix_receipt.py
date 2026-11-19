#!/usr/bin/env python
import re

with open('accounts/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the receipt number generation in rider_mark_delivered
old_code = '''                # Generate unique receipt number
                import random
                import time
                max_attempts = 100
                for _ in range(max_attempts):
                    last_sale = Sale.objects.order_by('-id').first()
                    if last_sale:
                        try:
                            receipt_num = int(last_sale.receipt_number.split('-')[1]) + 1
                        except (ValueError, IndexError):
                            receipt_num = 1000
                    else:
                        receipt_num = 1000
                    
                    receipt_number = f"RCP-{receipt_num}"
                    if not Sale.objects.filter(receipt_number=receipt_number).exists():
                        break
                    # If exists, add random suffix + timestamp to ensure uniqueness
                    receipt_num = random.randint(1000, 99999) + int(time.time()) % 1000
                
                # Convert payment method'''

new_code = '''                # Generate unique receipt number
                import random
                import time
                receipt_number = None
                max_attempts = 100
                
                for attempt in range(max_attempts):
                    last_sale = Sale.objects.order_by('-id').first()
                    if last_sale and attempt == 0:
                        # First try: sequential number
                        try:
                            receipt_num = int(last_sale.receipt_number.split('-')[1]) + 1
                        except (ValueError, IndexError):
                            receipt_num = 1000
                    else:
                        # Use random + timestamp for uniqueness
                        receipt_num = random.randint(1000, 999999) + int(time.time()) % 10000
                    
                    candidate = f"RCP-{receipt_num}"
                    if not Sale.objects.filter(receipt_number=candidate).exists():
                        receipt_number = candidate
                        break
                
                # Fallback if no unique number found in loop
                if not receipt_number:
                    receipt_number = f"RCP-{int(time.time())}-{random.randint(1000, 9999)}"
                
                # Convert payment method'''

if old_code in content:
    content = content.replace(old_code, new_code, 1)
    with open('accounts/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Fixed rider_mark_delivered receipt number generation')
else:
    print('Pattern not found - checking file...')
    # Find the line numbers
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'Generate unique receipt number' in line and i > 800:
            print(f'Found at line {i+1}')
            for j in range(max(0, i), min(len(lines), i+22)):
                print(f'{j+1}: {repr(lines[j])}')
            break
