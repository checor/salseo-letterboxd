import requests
import pandas as pd
import bs4
from flask import Flask, render_template, request


app = Flask(__name__)


@app.route("/", methods=["get"])
def index():
    user1 = request.args.get("u1")
    user2 = request.args.get("u2")
    return render_template("index.html", user1=user1, user2=user2)


@app.route("/versus", methods=["post"])
def versus():
    user1 = request.form["user1"]
    user2 = request.form["user2"]
    df = controversy_takes(user1, user2)
    results = df.to_dict("records")
    tweet = f"🍿 {user1} vs {user2} 🍿 en Salseo Letterboxd, mira los resultados en: https://slb.checor.me/?u1={user1}&u2={user2}"
    return render_template(
        "versus.html", results=results, user1=user1, user2=user2, tweet=tweet
    )


def scrap_movies(username):
    """Scrap movies from a Letterboxd user's profile."""
    try:
        df = pd.read_csv(f"/tmp/movies_{username}.csv")
        return df
    except FileNotFoundError:
        pass
    movies = []
    i = 1
    while True:
        url = f"https://letterboxd.com/{username}/films/page/{i}/"
        page = requests.get(url)
        soup = bs4.BeautifulSoup(page.content, "html.parser")
        movies_soup = soup.find_all("li", class_="poster-container")
        for movie in movies_soup:
            if not movie.find("span", class_="rating"):
                continue
            id_ = int(movie.div.attrs["data-film-id"])
            title = movie.img.attrs["alt"]
            link = movie.div.attrs["data-target-link"]
            rating = movie.find("span", class_="rating").string
            rating = rating.count("★") + rating.count("½") * 0.5
            movies.append([id_, title, link, rating])
        if not soup.find("a", class_="next"):
            break
        i += 1
    df = pd.DataFrame(movies, columns=["id", "title", "link", "rating"])
    df.to_csv(f"/tmp/movies_{username}.csv", index=False)
    return df


def controversy_takes(user1, user2, min_diff=1.0):
    """Find the movies with more rating difference between the users"""
    df1 = scrap_movies(user1)
    df2 = scrap_movies(user2)
    df = pd.merge(df1, df2, on="id", suffixes=("_1", "_2"))
    df["diff"] = abs(df["rating_1"] - df["rating_2"])
    df = df.sort_values(by=["diff", "rating_1"], ascending=False)
    return df[df["diff"] >= min_diff]
