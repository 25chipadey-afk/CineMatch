import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Page settings
st.set_page_config(
    page_title="CineMatch | Movie Finder",
    page_icon="🎬",
    layout="wide"
)

# Load datasets
@st.cache_data
def load_data():
    movies = pd.read_csv("data/movies.csv")
    ratings = pd.read_csv("data/ratings.csv")

    stats = ratings.groupby("movieId").agg(
        average_rating=("rating", "mean"),
        total_ratings=("rating", "count")
    ).reset_index()

    data = movies.merge(stats, on="movieId", how="left")
    data["average_rating"] = data["average_rating"].fillna(0)
    data["total_ratings"] = data["total_ratings"].fillna(0)
    data["genres"] = data["genres"].fillna("")

    return data

movie_data = load_data()

# Website styling
st.markdown("""
<style>
.stApp { background-color: #101014; color: white; }
h1, h2, h3, p, label { color: white; }
.hero {
    background: linear-gradient(120deg, #451515, #191923, #101014);
    padding: 35px; border-radius: 18px; margin-bottom: 25px;
}
.hero h1 { font-size: 42px; margin-bottom: 8px; }
.hero p { color: #dddddd; font-size: 17px; }
.movie-card {
    background: #202027; border: 1px solid #34343e;
    border-radius: 12px; padding: 16px;
    min-height: 180px; margin-bottom: 15px;
}
.poster {
    background: linear-gradient(145deg, #682525, #292943);
    border-radius: 9px; height: 95px;
    display: flex; align-items: center; justify-content: center;
    font-size: 38px; margin-bottom: 12px;
}
.movie-title { font-size: 15px; font-weight: bold; margin-bottom: 8px; }
.movie-info { color: #c5c5cf; font-size: 13px; }
div.stButton > button {
    background: #e50914; color: white; border: none; border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# Navigation
st.markdown("## 🎬 CineMatch")
st.caption("DISCOVER • EXPLORE • FIND YOUR NEXT FAVORITE")

# Hero section
st.markdown("""
<div class="hero">
    <h1>Find Your Next Favorite</h1>
    <p>Explore movies and discover your next movie night pick.</p>
</div>
""", unsafe_allow_html=True)

# ---------- Helper functions ----------
def show_movies(data):
    if data.empty:
        st.warning("No movies found. Try another search or genre.")
        return

    rows = [data.iloc[i:i+4] for i in range(0, len(data), 4)]

    for row_data in rows:
        cols = st.columns(4)
        for col, (_, movie) in zip(cols, row_data.iterrows()):
            with col:
                genres_text = str(movie["genres"]).replace("|", ", ")
                st.markdown(f"""
                <div class="movie-card">
                    <div class="poster">🎞️</div>
                    <div class="movie-title">{movie['title']}</div>
                    <div class="movie-info">
                        ⭐ {movie['average_rating']:.1f}/5
                        <br><br>
                        🎭 {genres_text}
                        <br><br>
                        👥 {int(movie['total_ratings'])} ratings
                    </div>
                </div>
                """, unsafe_allow_html=True)


def recommend_movies(genre, movie_name=""):
    recommendations = movie_data.copy()

    if genre != "All Genres":
        recommendations = recommendations[
            recommendations["genres"].str.contains(
                genre, case=False, na=False, regex=False
            )
        ]

    recommendations = recommendations[recommendations["total_ratings"] >= 10]

    if movie_name.strip():
        matched = movie_data[
            movie_data["title"].str.contains(
                movie_name, case=False, na=False, regex=False
            )
        ]

        if not matched.empty:
            selected_genres = [
                g for g in matched.iloc[0]["genres"].split("|")
                if g and g != "(no genres listed)"
            ]

            recommendations = recommendations[
                recommendations["genres"].apply(
                    lambda genres: any(
                        g in str(genres).split("|") for g in selected_genres
                    )
                )
            ]

            recommendations = recommendations[
                recommendations["movieId"] != matched.iloc[0]["movieId"]
            ]

    recommendations = recommendations.sort_values(
        by=["average_rating", "total_ratings"],
        ascending=[False, False]
    )

    return recommendations.head(10)

# ---------- Search and filters ----------
st.subheader("🔎 Explore Movies")

col1, col2 = st.columns([2, 1])

with col1:
    search = st.text_input("Search movies", placeholder="Enter a movie name...")

with col2:
    all_genres = sorted(set(
        genre
        for genres in movie_data["genres"]
        for genre in genres.split("|")
        if genre and genre != "(no genres listed)"
    ))
    selected_genre = st.selectbox("Choose a genre", ["All Genres"] + all_genres)

# Filter movies
filtered = movie_data.copy()

if search:
    filtered = filtered[
        filtered["title"].str.contains(search, case=False, na=False, regex=False)
    ]

if selected_genre != "All Genres":
    filtered = filtered[
        filtered["genres"].str.contains(
            selected_genre, case=False, na=False, regex=False
        )
    ]

# ---------- Top rated ----------
st.subheader("⭐ Top Rated Movies")
st.caption("Movies with at least 10 ratings")

top_movies = (
    movie_data[movie_data["total_ratings"] >= 10]
    .sort_values(by="average_rating", ascending=False)
    .head(10)
)
show_movies(top_movies)

st.divider()

# ---------- Browse ----------
st.subheader("🍿 Browse Movies")
st.write(f"Movies found: {len(filtered)}")

show_movies(
    filtered.sort_values(by="average_rating", ascending=False).head(40)
)

st.divider()

# ---------- Recommendations ----------
st.subheader("🎯 Recommend Similar Movies")

rec_name = st.text_input(
    "Enter a movie you like",
    placeholder="e.g. Toy Story",
    key="rec_name"
)

if st.button("Get Recommendations"):
    recs = recommend_movies(selected_genre, rec_name)
    show_movies(recs)

st.divider()

# ---------- Rating analysis chart ----------
st.subheader("📊 Movie Rating Analysis")

chart_data = (
    movie_data[movie_data["total_ratings"] >= 10]
    .nlargest(10, "average_rating")
    .sort_values("average_rating")
)

fig, ax = plt.subplots(figsize=(10, 5))
ax.barh(chart_data["title"], chart_data["average_rating"])
ax.set_xlabel("Average Rating")
ax.set_ylabel("Movie")
ax.set_title("Top 10 Movies by Average Rating")
ax.set_xlim(0, 5)
fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

# ---------- Footer ----------
st.divider()
st.caption("CineMatch | A Python, Pandas & NumPy Movie Recommendation Project")