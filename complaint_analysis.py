import pandas as pd
import sys
from pathlib import Path

def load_and_validate(file_path):
    required_cols = [
        'complaint_id', 'customer_id', 'category', 
        'status', 'date_opened', 'date_closed'
    ]
    
    if not Path(file_path).exists():
        print(f"Error: Required file '{file_path}' not found.", file=sys.stderr)
        sys.exit(1)
        
    df = pd.read_csv(file_path)
    
    # Validate columns
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"Error: Missing required columns: {missing_cols}", file=sys.stderr)
        sys.exit(1)
        
    return df

def analyze_complaints(df):
    # Missing value counts
    missing_counts = df.isnull().sum().to_dict()
    print("Missing-value counts:", missing_counts)
    
    # Status and Category counts
    status_counts = df['status'].value_counts()
    category_counts = df['category'].value_counts()
    
    total_records = len(df)
    category_pct = (category_counts / total_records) * 100
    
    # Closed-case resolution duration calculation
    df['date_opened'] = pd.to_datetime(df['date_opened'])
    df['date_closed'] = pd.to_datetime(df['date_closed'])
    
    closed_mask = df['status'].isin(['Closed', 'RESOLVED'])
    df.loc[closed_mask, 'resolution_days'] = (
        df.loc[closed_mask, 'date_closed'] - df.loc[closed_mask, 'date_opened']
    ).dt.days
    
    resolution_summary = df[closed_mask].groupby('category').agg(
        closed_cases=('complaint_id', 'count'),
        avg_resolution_days=('resolution_days', 'mean')
    ).reset_index()
    
    return category_counts, category_pct, resolution_summary

def main():
    file_name = "complaints.csv"
    df = load_and_validate(file_name)
    cat_counts, cat_pct, res_summary = analyze_complaints(df)
    
    # Export CSV summary
    output_df = pd.DataFrame({
        'Category': cat_counts.index,
        'Total_Count': cat_counts.values,
        'Percentage': cat_pct.values
    })
    output_df.to_csv("complaint_analysis_output.csv", index=False)
    print("Analysis complete. Output exported to complaint_analysis_output.csv")

if __name__ == "__main__":
    main()