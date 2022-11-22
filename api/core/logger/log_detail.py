import datetime
import sqlite3

connection = sqlite3.connect('logger-details.db')
cursor = connection.cursor()

create_tables_query = [
    """CREATE TABLE IF NOT EXISTS DetailedLog
                            (
                                message_id bigint NOT NULL,
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


def register_detailed_log(message_id: int):
    cursor.execute(f"""INSERT INTO DetailedLog (message_id) VALUES ({message_id}) ON CONFLICT DO NOTHING""")
    connection.commit()


def get_detailed_msgs():
    cursor.execute(f"""SELECT message_id from DetailedLog""")
    return cursor.fetchall()


def detailed_log_activity(message_id: int, activity_id: int, begin: datetime.datetime = datetime.datetime.now(),
                          end: datetime.datetime = None):
    if end is None:
        try:
            cursor.execute(f"""INSERT INTO Activities (message_id, activity_id, begin, end) 
                                    VALUES ({message_id}, {activity_id}, '{begin.strftime('%Y-%m-%d %H:%M:%S')}', null)""")
        except sqlite3.IntegrityError:
            pass
    else:
        try:
            cursor.execute(
                f"""UPDATE Activities SET activity_id = {activity_id}, end = '{end.strftime('%Y-%m-%d %H:%M:%S')}'
                                    WHERE message_id = {message_id} and activity_id = {activity_id} and end is NULL""")
        except sqlite3.IntegrityError:
            pass
    connection.commit()


def leadership_begin(message_id: int, leader_id: int, begin: datetime.datetime = datetime.datetime.now()):
    cursor.execute(f"""INSERT INTO Leadership (message_id, user_id, begin, end) 
                            VALUES ({message_id}, {leader_id}, '{begin.strftime('%Y-%m-%d %H:%M:%S')}', null)""")
    connection.commit()


def leadership_end(message_id: int, leader_id: int, _time: datetime.datetime, new_leader_id: int = None):
    cursor.execute(f"""UPDATE Leadership SET end = '{_time.strftime('%Y-%m-%d %H:%M:%S')}'
                            WHERE message_id = {message_id} and user_id = {leader_id}""")
    if new_leader_id is not None:
        leadership_begin(message_id, new_leader_id, _time)
    connection.commit()


def member_join(message_id: int, member_id: int, begin: datetime.datetime):
    cursor.execute(f"""INSERT INTO MemberPresence (message_id, member_id, begin, end) 
                            VALUES ({message_id}, {member_id}, '{begin.strftime('%Y-%m-%d %H:%M:%S')}', null)""")
    connection.commit()


def member_leave(message_id: int, member_id: int, end: datetime.datetime):
    cursor.execute(f"""UPDATE MemberPresence SET end = '{end.strftime('%Y-%m-%d %H:%M:%S')}'
                            WHERE message_id = {message_id} and member_id = {member_id} and end is NULL""")
    connection.commit()


def get_leaders_list(message_id: int) -> list[tuple[int, datetime.datetime, datetime.datetime]]:
    cursor.execute(f"""SELECT user_id, begin, end FROM Leadership WHERE message_id = {message_id} ORDER BY begin""")
    return cursor.fetchall()


def get_prescence_list(message_id: int) -> list[tuple[int, datetime.datetime, datetime.datetime]]:
    cursor.execute(
        f"""SELECT member_id, begin, end FROM MemberPresence WHERE message_id = {message_id} ORDER BY end""")
    return cursor.fetchall()


def get_activities_list(message_id: int) -> list[tuple[int, datetime.datetime, datetime.datetime]]:
    cursor.execute(
        f"""SELECT activity_id, begin, end FROM Activities WHERE message_id = {message_id} ORDER BY end""")
    return cursor.fetchall()
