from django import forms
from .models import Post, get_price
import csv
import io

# Form for uploading Quick Sales Report file - CSV only for now
class SalesReportUploadForm(forms.Form):
    # File field for CSV
    report_file = forms.FileField(label='Upload Sales Report (CSV only)')

    # Validate file
    def clean_report_file(self):
        file = self.cleaned_data['report_file']
        # Check size max 5MB
        if file.size > 5 * 1024 * 1024:
            raise forms.ValidationError("File too large. Max 5MB")
        # Check if CSV
        if not file.name.endswith('.csv'):
            raise forms.ValidationError("Only CSV allowed for now")
        return file

    # Calculate totals from CSV
    def calculate_totals(self):
        file = self.cleaned_data['report_file']
        try:
            # Read file content as text
            data = file.read().decode('utf-8')
            # Use StringIO to read as CSV
            reader = csv.DictReader(io.StringIO(data))
            
            total_sales = 0  # Start sales at 0
            total_expense = 0  # Start expense at 0
            count = 0  # Row count
            
            # Convert headers to lowercase for easy check
            if reader.fieldnames:
                reader.fieldnames = [f.lower().strip() for f in reader.fieldnames]
            
            # Loop through each row
            for row in reader:
                count += 1  # Increase count
                # If row has sales and expense columns
                if 'sales' in row and 'expense' in row:
                    try:
                        total_sales += float(row['sales'] or 0)  # Add sales
                        total_expense += float(row['expense'] or 0)  # Add expense
                    except:
                        pass  # Skip invalid numbers
                # If row has amount and type columns
                elif 'amount' in row and 'type' in row:
                    try:
                        amt = float(row['amount'] or 0)
                        if 'sales' in row['type'].lower():
                            total_sales += amt  # Add to sales
                        elif 'expense' in row['type'].lower():
                            total_expense += amt  # Add to expense
                    except:
                        pass
                else:
                    # If only numbers, take first number as sales
                    for v in row.values():
                        try:
                            total_sales += float(v)
                            break  # Only first number per row
                        except:
                            continue
            
            # Calculate profit
            profit = total_sales - total_expense
            # Calculate margin
            margin = (profit / total_sales * 100) if total_sales > 0 else 0
            # Get price based on count
            price = get_price(count)
            
            # Return results
            return {
                'total_sales': total_sales,
                'total_expense': total_expense,
                'profit': profit,
                'margin': margin,
                'count': count,
                'price': price,
            }
        except Exception as e:
            # Raise error if file can't be read
            raise forms.ValidationError(f"Could not read file: {str(e)}")

# Form for market post
class MarketPostForm(forms.ModelForm):
    class Meta:
        # Use Post model
        model = Post
        # Fields to show
        fields = ['caption', 'image', 'location']
        widgets = {
            # Caption text area
            'caption': forms.Textarea(attrs={
                'placeholder': "What's happening in your market today?",
                'rows': 3,
                'class': 'form-control'
            })
        }
