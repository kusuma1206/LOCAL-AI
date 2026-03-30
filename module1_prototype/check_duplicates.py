from processing.storage import supabase
import pandas as pd

# Check for duplicate chunks
res = supabase.table("document_chunks").select("chunk_id, content, section_id").execute()
df = pd.DataFrame(res.data)

print(f"Total chunks: {len(df)}")
duplicates = df[df.duplicated(subset=['content', 'section_id'], keep=False)]
print(f"Number of chunks with duplicate content within same section: {len(duplicates)}")

if len(duplicates) > 0:
    print("\nDuplicate snippets (first 5):")
    print(duplicates.head(5)['content'].values)

# Group by content and section_id and count
dupes_count = df.groupby(['content', 'section_id']).size().reset_index(name='count')
top_dupes = dupes_count[dupes_count['count'] > 1].sort_values('count', ascending=False)
print("\nTop duplicate chunks:")
print(top_dupes.head(10))
