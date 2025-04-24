import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import ast

# Load and preprocess dataset
@st.cache_data
def load_data():
    df = pd.read_csv("data/tmdb_2000_credits.csv")

    def extract_names(field, key, limit=None):
        try:
            items = ast.literal_eval(field)
            names = [item[key] for item in items if key in item]
            return ' '.join(names[:limit]) if limit else ' '.join(names)
        except:
            return ''

    df['cast_clean'] = df['cast'].apply(lambda x: extract_names(x, 'name', limit=5))  # top 5 actors
    df['director'] = df['crew'].apply(lambda x: next((d['name'] for d in ast.literal_eval(x) if d.get('job') == 'Director'), ''))

    df['combined_features'] = df['cast_clean'] + ' ' + df['director']
    return df[['title', 'combined_features']]

# Build similarity matrix
@st.cache_resource
def create_similarity(data):
    cv = CountVectorizer(max_features=5000, stop_words='english')
    vectors = cv.fit_transform(data['combined_features']).toarray()
    similarity = cosine_similarity(vectors)
    return similarity

# Recommend movies
def recommend(movie, data, similarity):
    movie = movie.lower()
    if movie not in data['title'].str.lower().values:
        return ["Movie not found. Try another."]
    idx = data[data['title'].str.lower() == movie].index[0]
    distances = list(enumerate(similarity[idx]))
    movies = sorted(distances, key=lambda x: x[1], reverse=True)[1:6]
    return data.iloc[[i[0] for i in movies]]['title'].tolist()

# Streamlit app UI
st.title("🎬 Movie Recommender (TMDB 2000)")

data = load_data()
similarity = create_similarity(data)

movie_list = data['title'].values
selected_movie = st.selectbox("Choose a movie", movie_list)

if st.button("Recommend"):
    recommendations = recommend(selected_movie, data, similarity)
    st.write("### You might also like:")
    for m in recommendations:
        st.write(f"- {m}")
