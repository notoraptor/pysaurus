import sqlite3


def sqlite_supports_fts5(con):
    cur = con.cursor()
    cur.execute("pragma compile_options;")
    available_pragmas = cur.fetchall()
    return ("ENABLE_FTS5",) in available_pragmas


def main():
    con = sqlite3.connect(":memory:")
    has_fts5 = sqlite_supports_fts5(con)
    con.close()

    if has_fts5:
        print("YES")
    else:
        print("NO")


if __name__ == "__main__":
    main()
