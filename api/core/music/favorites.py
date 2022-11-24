import sqlite3

connection = sqlite3.connect('favorites.db')
cursor = connection.cursor()

create_table_query = """
    CREATE TABLE IF NOT EXISTS MusicMemberQueries
        (
            title str,
            user_id bigint NOT NULL,
            query text NOT NULL,
            counter int DEFAULT 1,
            PRIMARY KEY (user_id, query)
        )
    """
cursor.execute(create_table_query)
connection.commit()


def write_music_query(title: str, user_id: int, uri: str) -> None:
    query = f"""INSERT INTO MusicMemberQueries (title, user_id, query)
                    VALUES ('{title}', {user_id}, '{uri}')
                        ON CONFLICT (user_id, query) 
                            DO UPDATE SET counter = MusicMemberQueries.counter + 1"""
    cursor.execute(query)
    connection.commit()


def mru_queries(user_id: int, limit: int = 20) -> list[tuple[str, str, int]]:
    query = f"""SELECT title, query, counter FROM MusicMemberQueries 
                    WHERE user_id = {user_id}
                ORDER BY counter desc
                LIMIT {limit}"""
    cursor.execute(query)
    return cursor.fetchall()


if __name__ == '__main__':
    print(mru_queries(242349833245949953))
    # write_music_query('', 242349833245949953, 'https://youtu.be/OvCQrgJTmxo')
    # write_music_query('', 242349833245949953, 'https://youtu.be/oDsiqiYCp1A')
    # write_music_query('', 242349833245949953, 'https://youtu.be/Iv3edUPFalg')





