import pandas as pd

df = pd.read_csv('backend/data/cleaned_merged_data.csv', low_memory=False)
mask = (df['image_src'] == 'Not available') & (df['location_id'].notna()) & (df['location_id'] != 'Not available') & (pd.to_numeric(df['photo_count'], errors='coerce').fillna(0) > 0)
print(f'Rows needing images: {mask.sum()}')
print(f'Total rows: {len(df)}')
