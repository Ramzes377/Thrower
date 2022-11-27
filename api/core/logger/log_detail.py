import datetime
import sqlite3

connection = sqlite3.connect('logger-details.db')
cursor = connection.cursor()

create_tables_query = [
    """CREATE TABLE IF NOT EXISTS DetailedLog
        (
            message_id bigint NOT NULL,
            channel_id bigint NOT NULL,
            PRIMARY KEY (message_id)
        )
    """,
    """
    CREATE TABLE IF NOT EXISTS Leadership
        (
            message_id bigint NOT NULL,
            user_id bigint NOT NULL,
            begin timestamp without time zone NOT NULL,
            end timestamp without time zone DEFAULT NULL,
            FOREIGN KEY (message_id) REFERENCES DetailedLog(message_id) ON DELETE CASCADE
        )
    """,
    """
        CREATE TABLE IF NOT EXISTS Activities
        (
            message_id bigint NOT NULL,
            member_id bigint,
            activity_id bigint NOT NULL,
            begin timestamp without time zone NOT NULL,
            end timestamp without time zone DEFAULT NULL,
            PRIMARY KEY (message_id, activity_id, begin),
            FOREIGN KEY (message_id) REFERENCES DetailedLog(message_id) ON DELETE CASCADE
        )
    """,
    """
         CREATE TABLE IF NOT EXISTS MemberPresence
         (
             message_id bigint NOT NULL,
             member_id bigint NOT NULL,
             begin timestamp without time zone NOT NULL,
             end timestamp without time zone DEFAULT NULL,
             FOREIGN KEY (message_id) REFERENCES DetailedLog(message_id) ON DELETE CASCADE
         )
     """
]

for query in create_tables_query:
    cursor.execute(query)
connection.commit()


def reg_log(message_id: int, channel_id: int) -> None:
    cursor.execute(
        f"""INSERT INTO DetailedLog (message_id, channel_id) VALUES ({message_id}, {channel_id}) ON CONFLICT DO NOTHING""")
    connection.commit()


def unreg_log(message_id: int) -> None:
    cursor.execute(
        f"""DELETE FROM DetailedLog WHERE message_id = {message_id}""")
    connection.commit()


def log_activity_begin(message_id: int, activity_id: int, member_id: int, begin: datetime.datetime):
    try:
        cursor.execute(f"""INSERT INTO Activities (message_id, activity_id, member_id, begin, end) 
                                VALUES ({message_id}, {activity_id}, {member_id}, '{begin.strftime('%Y-%m-%d %H:%M:%S')}', NULL)""")
    except sqlite3.IntegrityError:
        pass
    connection.commit()


def log_activity_end(message_id: int, activity_id: int, member_id: int, begin: datetime.datetime,
                     end: datetime.datetime):
    cursor.execute(
        f"""UPDATE Activities SET end = '{end.strftime('%Y-%m-%d %H:%M:%S')}'
                WHERE message_id = {message_id} and activity_id = {activity_id} and member_id = {member_id}
                and begin ='{begin.strftime('%Y-%m-%d %H:%M:%S')}'""")
    connection.commit()


def leadership_begin(message_id: int, leader_id: int, begin: datetime.datetime):
    cursor.execute(f"""INSERT INTO Leadership (message_id, user_id, begin, end) 
                            VALUES ({message_id}, {leader_id}, '{begin.strftime('%Y-%m-%d %H:%M:%S')}', NULL)""")
    connection.commit()


def leadership_end(message_id: int, leader_id: int, _time: datetime.datetime):
    cursor.execute(f"""UPDATE Leadership SET end = '{_time.strftime('%Y-%m-%d %H:%M:%S')}'
                            WHERE message_id = {message_id} and user_id = {leader_id}""")
    connection.commit()


def member_join(message_id: int, member_id: int, begin: datetime.datetime):
    cursor.execute(f"""INSERT INTO MemberPresence (message_id, member_id, begin, end) 
                            VALUES ({message_id}, {member_id}, '{begin.strftime('%Y-%m-%d %H:%M:%S')}', NULL)""")
    connection.commit()


def member_leave(message_id: int, member_id: int, end: datetime.datetime):
    cursor.execute(f"""UPDATE MemberPresence SET end = '{end.strftime('%Y-%m-%d %H:%M:%S')}'
                            WHERE message_id = {message_id} and member_id = {member_id} and end is NULL""")
    connection.commit()


def message_from_channel(channel_id: int) -> int | None:
    cursor.execute(f"""SELECT message_id FROM DetailedLog WHERE channel_id = {channel_id}""")
    try:
        return cursor.fetchone()[0]
    except TypeError:
        return None


def get_detailed_msgs():
    cursor.execute(f"""SELECT message_id from DetailedLog""")
    return cursor.fetchall()


def get_leaders_list(message_id: int) -> list[tuple[int, datetime.datetime, datetime.datetime]]:
    cursor.execute(f"""SELECT user_id, begin, end FROM Leadership WHERE message_id = {message_id} ORDER BY begin""")
    return cursor.fetchall()


def get_prescence_list(message_id: int) -> list[tuple[int, datetime.datetime, datetime.datetime]]:
    cursor.execute(
        f"""SELECT member_id, begin, end FROM MemberPresence WHERE message_id = {message_id} ORDER BY end""")
    return cursor.fetchall()


def get_activities_list(message_id: int) -> list[tuple[int, int, datetime.datetime, datetime.datetime]]:
    cursor.execute(
        f"""SELECT activity_id, member_id, begin, end FROM Activities WHERE message_id = {message_id} ORDER BY end""")
    return cursor.fetchall()
