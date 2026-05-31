import pandas as pd

df = pd.read_csv('data/cleaned_merged_data.csv')

# Show rows that DO have images - what's in see_all_photos for them
has_img = df[df['image_src'].str.startswith('http', na=False)]
print(f"Rows WITH images: {len(has_img)}")
print("\nSample of rows with images:")
for _, row in has_img.head(5).iterrows():
    print(f"  location_id={row['location_id']}, photo_count={row['photo_count']}")
    print(f"  image_src={row['image_src']}")
    print(f"  see_all_photos={row['see_all_photos']}")
    print()
