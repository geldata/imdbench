#!/usr/bin/env python3
#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##

import argparse
import json
import sys

import gel
from .models import default

from datetime import datetime, timedelta

import contextlib


@contextlib.contextmanager
def timeit(msg):
    import time

    st = time.monotonic()
    try:
        yield
    finally:
        print(f"{msg}: {time.monotonic() - st:.4f} secs")


DEBUG_SAVE = False
SAVE_AT_ONCE = True
INSERT_LINK_PROPS = True
PROFILE = True


@contextlib.contextmanager
def profile():
    if not PROFILE:
        yield
        return

    import cProfile
    import pstats
    import io

    pr = cProfile.Profile()
    pr.enable()

    try:
        yield
    finally:
        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
        ps.print_stats()
        profile_stats = s.getvalue()
        print("\n\n", profile_stats, "\n\n")


def main():
    parser = argparse.ArgumentParser(description="Load Gel ORM dataset.")
    parser.add_argument("filename", type=str, help="The JSON dataset file")
    args = parser.parse_args()

    print(f">>> {DEBUG_SAVE=} {SAVE_AT_ONCE=} {INSERT_LINK_PROPS=} {PROFILE=} <<<")

    with open(args.filename, "rt") as f:
        data = json.load(f)

    # Create Gel ORM client
    db = gel.create_client().with_config(
        session_idle_transaction_timeout=timedelta(minutes=5)
    )

    # LOAD PEOPLE

    with timeit("Instantiating people"):
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
        print()

    if not SAVE_AT_ONCE:
        with timeit("Saving people"):
            db.save(*people_objs)

    # LOAD USERS
    with timeit("Instantiating users"):
        user_map = {}
        user_objs = []
        for i, u in enumerate(data["user"]):
            user = default.User(name=u["name"], image=u["image"])
            user_map[u["id"]] = user
            user_objs.append(user)
            print(f"\rUser {i}/{len(data['user'])}", end="", flush=True)
        print()

    if not SAVE_AT_ONCE:
        with timeit("Saving users"):
            db.save(*user_objs)

    # LOAD MOVIES
    with (
        timeit(f"Instantiating movies {'with linkprops' if INSERT_LINK_PROPS else ''}"),
        profile(),
    ):
        movie_map = {}
        movie_objs = []
        for i, m in enumerate(data["movie"]):
            if INSERT_LINK_PROPS:
                directors = [
                    default.Movie.directors.link(people_map[pid], list_order=i)
                    for i, pid in enumerate(m["directors"])
                ]
                cast = [
                    default.Movie.cast.link(people_map[pid], list_order=i)
                    for i, pid in enumerate(m["cast"])
                ]
            else:
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
        print()

    sys.exit()

    if not SAVE_AT_ONCE:
        with timeit("Saving movies"):
            db.save(*movie_objs)

    # LOAD REVIEWS
    with timeit("Instantiating reviews"):
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
            print(f"\rReview {i}/{len(data['review'])}", end="", flush=True)
        print()

    if not SAVE_AT_ONCE:
        with timeit("Saving reviews"):
            db.save(*review_objs)
    elif DEBUG_SAVE:
        with timeit("Saving everything (debug)"):  # , profile():
            debug = db.__debug_save__(
                *people_objs,
                *user_objs,
                *movie_objs,
                *review_objs,
            )

        for i, q in enumerate(debug.queries):
            print(
                f"++ {i} {q.total_execs=} {q.total_exec_time:.2f} {q.max_args_number=}"
            )
            print(q.query, "\n\n")

            # with open(f"{i}.json", "wt") as f:
            #     f.write(qdebug.args_analyze)

            # with open(f"{i}.py", "wt") as f:
            #     f.write(f"query = {qdebug.args_query!r}\n")
            #     f.write(f"args = {qdebug.analyze_args!r}")
    else:
        with timeit("Saving everything"):
            db.save(
                *people_objs,
                *user_objs,
                *movie_objs,
                *review_objs,
            )


if __name__ == "__main__":
    with timeit("total time"):
        main()
