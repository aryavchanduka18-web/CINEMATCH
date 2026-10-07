"""Movie catalogue: movies, genres, people, keywords, awards."""
from datetime import date

from sqlalchemy import (
    CHAR, CheckConstraint, Computed, Date, ForeignKey, Index, Integer, Numeric, REAL,
    SmallInteger, String, Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

# Full-text search: titles weigh most, then tagline, then overview.
# The "simple" config (no stemming) is used because titles span many languages.
SEARCH_VECTOR_SQL = (
    "setweight(to_tsvector('simple'::regconfig, coalesce(title, '')), 'A') || "
    "setweight(to_tsvector('simple'::regconfig, coalesce(original_title, '')), 'A') || "
    "setweight(to_tsvector('simple'::regconfig, coalesce(tagline, '')), 'B') || "
    "setweight(to_tsvector('simple'::regconfig, coalesce(overview, '')), 'C')"
)


class Movie(Base):
    __tablename__ = "movies"
    __table_args__ = (
        CheckConstraint("catalog_part IN ('A','B','C')", name="ck_movies_catalog_part"),
        Index("ix_movies_search_vector", "search_vector", postgresql_using="gin"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tmdb_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    ml_movie_id: Mapped[int | None] = mapped_column(Integer, unique=True)
    imdb_id: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    original_title: Mapped[str | None] = mapped_column(Text)
    overview: Mapped[str | None] = mapped_column(Text)
    release_date: Mapped[date | None] = mapped_column(Date)
    year: Mapped[int | None] = mapped_column(SmallInteger)
    runtime_min: Mapped[int | None] = mapped_column(SmallInteger)
    original_language: Mapped[str | None] = mapped_column(String(3))
    spoken_languages: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    countries: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    certification: Mapped[str | None] = mapped_column(Text)
    poster_path: Mapped[str | None] = mapped_column(Text)
    backdrop_path: Mapped[str | None] = mapped_column(Text)
    dominant_color: Mapped[str | None] = mapped_column(CHAR(7))
    tagline: Mapped[str | None] = mapped_column(Text)
    studios: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    logo_path: Mapped[str | None] = mapped_column(Text)
    catalog_part: Mapped[str | None] = mapped_column(CHAR(1))
    ml_rating_count: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    ml_rating_mean: Mapped[float | None] = mapped_column(Numeric(4, 2))
    # 10 buckets: count of ratings at 1, 2, ..., 10
    rating_hist: Mapped[list[int] | None] = mapped_column(ARRAY(Integer))
    popularity_score: Mapped[float | None] = mapped_column(REAL)
    tmdb_vote_count: Mapped[int | None] = mapped_column(Integer)
    search_vector = mapped_column(TSVECTOR, Computed(SEARCH_VECTOR_SQL, persisted=True))


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)


class MovieGenre(Base):
    __tablename__ = "movie_genres"

    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True)
    genre_id: Mapped[int] = mapped_column(
        ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True, index=True
    )


class Person(Base):
    __tablename__ = "people"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tmdb_person_id: Mapped[int | None] = mapped_column(Integer, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    profile_path: Mapped[str | None] = mapped_column(Text)


class MovieCredit(Base):
    __tablename__ = "movie_credits"
    __table_args__ = (
        CheckConstraint("role IN ('cast','director','writer')", name="ck_movie_credits_role"),
    )

    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True)
    person_id: Mapped[int] = mapped_column(
        ForeignKey("people.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    role: Mapped[str] = mapped_column(Text, primary_key=True)
    character: Mapped[str | None] = mapped_column(Text)
    credit_order: Mapped[int | None] = mapped_column(SmallInteger)


class Keyword(Base):
    __tablename__ = "keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)


class MovieKeyword(Base):
    __tablename__ = "movie_keywords"

    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True)
    keyword_id: Mapped[int] = mapped_column(
        ForeignKey("keywords.id", ondelete="CASCADE"), primary_key=True, index=True
    )


class MovieAward(Base):
    __tablename__ = "movie_awards"
    __table_args__ = (
        CheckConstraint("result IN ('won','nominated')", name="ck_movie_awards_result"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    award: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(Text)
    year: Mapped[int | None] = mapped_column(SmallInteger)
    result: Mapped[str] = mapped_column(Text, nullable=False)
    wikidata_id: Mapped[str | None] = mapped_column(Text)
