import pandas as pd
import os
from pathlib import Path
import warnings

def smart_file_merger(folder_path, output_filename="merged_data.csv", backup_originals=True):
    """
    Merge all data files in a folder into one DataFrame
    Supports CSV, Excel (.xlsx, .xls), and JSON files
    
    Parameters:
    - folder_path: Path to folder containing data files
    - output_filename: Name for the merged output file
    - backup_originals: Whether to create backups before processing
    """
    folder = Path(folder_path)
    
    # Validate folder exists
    if not folder.exists():
        print(f"Error: Folder '{folder_path}' does not exist!")
        return None
    
    all_dataframes = []
    processed_files = []
    file_info = []
    
    # Supported file extensions
    supported_formats = {'.csv', '.xlsx', '.xls', '.json'}
    
    print("Scanning for data files...")
    
    # Get all compatible files first
    compatible_files = [f for f in folder.iterdir() 
                       if f.suffix.lower() in supported_formats and f.is_file()]
    
    if not compatible_files:
        print("No compatible data files found!")
        return None
    
    print(f"Found {len(compatible_files)} compatible files")
    
    # Optional: Create backup folder
    if backup_originals:
        backup_folder = folder / "originals_backup"
        backup_folder.mkdir(exist_ok=True)
        print(f"Backup folder created: {backup_folder}")
    
    for file_path in compatible_files:
        print(f"Processing: {file_path.name}")
        
        try:
            # Read based on file extension with error handling
            if file_path.suffix.lower() == '.csv':
                # Try different encodings for CSV files
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(file_path, encoding='latin-1')
                        print(f"  └ Used latin-1 encoding for {file_path.name}")
                    except UnicodeDecodeError:
                        df = pd.read_csv(file_path, encoding='cp1252')
                        print(f"  └ Used cp1252 encoding for {file_path.name}")
                        
            elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                # Handle Excel files - read all sheets if multiple exist
                excel_file = pd.ExcelFile(file_path)
                if len(excel_file.sheet_names) > 1:
                    print(f"  └ Found {len(excel_file.sheet_names)} sheets, using first sheet")
                df = pd.read_excel(file_path, sheet_name=0)
                
            elif file_path.suffix.lower() == '.json':
                # Handle different JSON structures
                try:
                    df = pd.read_json(file_path)
                except ValueError:
                    # Try reading as records format
                    df = pd.read_json(file_path, lines=True)
                    print(f"  └ Used line-delimited JSON format for {file_path.name}")
            
            # Validate DataFrame
            if df.empty:
                print(f"  └ Warning: {file_path.name} is empty, skipping")
                continue
            
            # Add metadata
            df['source_file'] = file_path.name
            df['file_processed_order'] = len(all_dataframes) + 1
            
            # Store file information
            file_info.append({
                'filename': file_path.name,
                'rows': len(df),
                'columns': len(df.columns),
                'size_mb': file_path.stat().st_size / (1024*1024)
            })
            
            all_dataframes.append(df)
            processed_files.append(file_path.name)
            
            print(f"  └ ✓ {len(df)} rows, {len(df.columns)} columns")
            
        except Exception as e:
            print(f"  └ ✗ Error reading {file_path.name}: {str(e)}")
            continue
    
    if not all_dataframes:
        print("No valid data files could be processed!")
        return None
    
    # Show summary before merging
    print(f"\n{'='*50}")
    print("FILE SUMMARY:")
    total_rows = sum(info['rows'] for info in file_info)
    total_size = sum(info['size_mb'] for info in file_info)
    
    for info in file_info:
        print(f"  {info['filename']}: {info['rows']:,} rows, {info['columns']} cols, {info['size_mb']:.2f}MB")
    
    print(f"\nTOTAL: {total_rows:,} rows across {len(file_info)} files ({total_size:.2f}MB)")
    print(f"{'='*50}")
    
    # Merge all dataframes with progress indication
    print(f"Merging {len(all_dataframes)} files...")
    
    # Check for column consistency
    all_columns = set()
    for df in all_dataframes:
        all_columns.update(df.columns)
    
    unique_columns_per_file = [set(df.columns) for df in all_dataframes]
    common_columns = set.intersection(*unique_columns_per_file) if unique_columns_per_file else set()
    
    if len(common_columns) < len(all_columns):
        print(f"  └ Note: Files have different column structures")
        print(f"     Common columns: {len(common_columns)}")
        print(f"     Total unique columns: {len(all_columns)}")
    
    # Perform merge
    merged_df = pd.concat(all_dataframes, ignore_index=True, sort=False)
    
    # Save merged file with error handling
    output_path = folder / output_filename
    
    # Check if file already exists
    if output_path.exists():
        backup_name = output_filename.replace('.csv', '_backup.csv')
        backup_path = folder / backup_name
        print(f"  └ Backing up existing file to: {backup_name}")
        output_path.rename(backup_path)
    
    try:
        merged_df.to_csv(output_path, index=False)
        print(f"\n✓ SUCCESS!")
        print(f"✓ Merged {len(processed_files)} files")
        print(f"✓ Final dataset: {len(merged_df):,} rows × {len(merged_df.columns)} columns")
        print(f"✓ Output saved: {output_path}")
        print(f"✓ File size: {output_path.stat().st_size / (1024*1024):.2f}MB")
        
        # Show data quality summary
        print(f"\nDATA QUALITY CHECK:")
        print(f"  Missing values: {merged_df.isnull().sum().sum():,}")
        print(f"  Duplicate rows: {merged_df.duplicated().sum():,}")
        
        return merged_df
        
    except Exception as e:
        print(f"✗ Error saving merged file: {str(e)}")
        return merged_df  # Return the DataFrame even if saving failed

# Enhanced usage with error handling
def run_merger_safely(folder_path, output_filename="merged_data.csv"):
    """Wrapper function with comprehensive error handling"""
    try:
        result = smart_file_merger(folder_path, output_filename)
        if result is not None:
            print("\n🎉 File merger completed successfully!")
            return result
        else:
            print("\n❌ File merger failed - no data was processed")
            return None
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        return None

# Usage examples:
# Basic usage:
# merged_data = smart_file_merger('/path/to/your/data/folder')

# Safe usage with error handling:
# merged_data = run_merger_safely('/path/to/your/data/folder', 'my_merged_data.csv')

# Example with specific parameters:
# merged_data = smart_file_merger(
#     folder_path='/path/to/data', 
#     output_filename='combined_dataset.csv',
#     backup_originals=True
# )
