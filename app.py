'''import streamlit as st
import pandas as pd
from difflib import SequenceMatcher  # For basic similarity calculations

# Load your existing DataFrame
try:
    df = pd.read_csv('your_similarity_scores.csv')  # Replace with actual CSV file path
except FileNotFoundError:
    st.error("CSV file not found. Please check the file path.")
    df = None

# Function to calculate similarity using SequenceMatcher
def calculate_similarity(input_code, existing_code):
    matcher = SequenceMatcher(None, input_code, existing_code)
    return matcher.ratio()  # Returns a score between 0 and 1

# Function to check plagiarism and find the closest match
def check_plagiarism(input_code):
    if df is None or 'original_src' not in df.columns:  # Ensure the correct column exists
        st.error("Dataset does not contain the required 'original_src' column.")
        return None, None
    
    results = []
    for _, row in df.iterrows():
        similarity = calculate_similarity(input_code, row['original_src'])
        results.append({
            "problem_id": row['problem_id'],
            "token_similarity": similarity,  # Replace with token-level similarity if available
            "syntax_similarity": row.get('syntax_similarity', 0),  # Fallback if column is absent
            "semantic_similarity": row.get('semantic_similarity', 0),  # Fallback if column is absent
            "final_similarity": similarity,  # Example: Average of similarities or just this one
        })
    
    # Find the entry with the highest similarity
    if results:
        best_match = max(results, key=lambda x: x['final_similarity'])
        plagiarism_status = "Plagiarized" if best_match["final_similarity"] > 0.8 else "Not Plagiarized"  # Example threshold
        return best_match, plagiarism_status
    return None, None

# Streamlit UI
st.title("Code Similarity and Plagiarism Checker")

# Input field for source code
input_code = st.text_area("Paste the source code you want to check for plagiarism:")

if st.button("Check Similarity"):
    if input_code.strip():
        best_match, plagiarism_status = check_plagiarism(input_code)
        if best_match:
            # Display results
            st.write(f"Problem ID: {best_match['problem_id']}")
            st.write(f"Token Similarity: {best_match['token_similarity']:.2f}")
            st.write(f"Syntactic Similarity: {best_match['syntax_similarity']:.2f}")
            st.write(f"Semantic Similarity: {best_match['semantic_similarity']:.2f}")
            st.write(f"Final Similarity Score: {best_match['final_similarity']:.2f}")
            st.write(f"Plagiarism Status: **{plagiarism_status}**")
        else:
            st.write("No similar entries found in the dataset.")
    else:
        st.error("Please enter some source code.")'''
import streamlit as st
from sentence_transformers import SentenceTransformer, util
from io import StringIO
import pandas as pd

# Load pre-trained model
@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

model = load_model()

# Function to calculate similarity
def calculate_similarity(reference_content, other_content):
    ref_embedding = model.encode(reference_content, convert_to_tensor=True)
    other_embedding = model.encode(other_content, convert_to_tensor=True)
    similarity = util.pytorch_cos_sim(ref_embedding, other_embedding).item()
    return similarity

# Streamlit App UI
st.title("Code Similarity Checker")
st.write("Upload a reference file and up to 10 other files to compare for similarity.")

# Upload Reference File
reference_file = st.file_uploader("Upload Reference File", type=['py', 'txt'])
if reference_file:
    reference_content = StringIO(reference_file.getvalue().decode("utf-8")).read()
    st.success(f"Reference file '{reference_file.name}' uploaded successfully!")

# Upload Other Files
uploaded_files = st.file_uploader(
    "Upload up to 10 Files for Comparison", type=['py', 'txt'], accept_multiple_files=True
)

if reference_file and uploaded_files:
    if len(uploaded_files) > 10:
        st.warning("Please upload a maximum of 10 files.")
    else:
        results = []
        for uploaded_file in uploaded_files:
            other_content = StringIO(uploaded_file.getvalue().decode("utf-8")).read()
            similarity_score = calculate_similarity(reference_content, other_content)
            results.append({
                "File Name": uploaded_file.name,
                "Similarity Score": similarity_score
            })
        
        # Convert results to DataFrame
        results_df = pd.DataFrame(results)
        
        # Highlight files with similarity score above threshold
        threshold = st.slider("Set Similarity Threshold", min_value=0.0, max_value=1.0, value=0.85)
        def highlight_high_similarity(row):
            return ['background-color: red' if row['Similarity Score'] >= threshold else '' for _ in row]
        
        st.write("Similarity Results:")
        styled_results = results_df.style.apply(highlight_high_similarity, axis=1)
        st.dataframe(styled_results, use_container_width=True)

        # Download Results
        st.download_button(
            label="Download Results as CSV",
            data=results_df.to_csv(index=False).encode('utf-8'),
            file_name="similarity_results.csv",
            mime="text/csv"
        )
