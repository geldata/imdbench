#!/usr/bin/env python3
#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##

import argparse
import json
import gel
from .models import default
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description="Load Gel ORM dataset.")
    parser.add_argument("filename", type=str, help="The JSON dataset file")
    args = parser.parse_args()

    with open(args.filename, "rt") as f:
        data = json.load(f)

    # Create Gel ORM client
    db = gel.create_client()

    # LOAD PEOPLE
    people_map = {}
    people_objs = []
    for i, p in enumerate(data["person"]):
        person = default.Person(
            first_name=p["first_name"],
            middle_name=p["middle_name"],
            last_name=p["last_name"],
            image=p["image"],
            bio=p["bio"],
        )
        people_map[p["id"]] = person
        people_objs.append(person)
        print(f"\rPerson {i}/{len(data['person'])}", end="", flush=True)
    db.save(*people_objs)
    print()

    # LOAD USERS
    user_map = {}
    user_objs = []
    for i, u in enumerate(data["user"]):
        user = default.User(name=u["name"], image=u["image"])
        user_map[u["id"]] = user
        user_objs.append(user)
        print(f"\rUser {i}/{len(data['user'])}", end="", flush=True)
    db.save(*user_objs)
    print()

    # LOAD MOVIES
    movie_map = {}
    movie_objs = []
    for i, m in enumerate(data["movie"]):
        directors = [people_map[pid] for pid in m["directors"]]
        cast = [people_map[pid] for pid in m["cast"]]
        movie = default.Movie(
            title=m["title"],
            description=m["description"],
            year=m["year"],
            image=m["image"],
            directors=directors,
            cast=cast,
        )
        movie_map[m["id"]] = movie
        movie_objs.append(movie)
        print(f"\rMovie {i}/{len(data['movie'])}", end="", flush=True)
    db.save(*movie_objs)
    print()

    # LOAD REVIEWS
    review_objs = []
    for i, r in enumerate(data["review"]):
        creation_time = datetime.fromisoformat(r["creation_time"][:-6])
        review = default.Review(
            body=r["body"],
            rating=r["rating"],
            author=user_map[r["author"]],
            movie=movie_map[r["movie"]],
            creation_time=creation_time,
        )
        review_objs.append(review)
        print(f"\rReview {i}/{len(data['movie'])}", end="", flush=True)
    db.save(*review_objs)
    print()


if __name__ == "__main__":
    main()
