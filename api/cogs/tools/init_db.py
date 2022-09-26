
async def create_tables(cur):
    commands = '''
        CREATE TABLE IF NOT EXISTS CreatedSessions
        (
            channel_id bigint PRIMARY KEY,
            user_id bigint UNIQUE
        );
        CREATE TABLE IF NOT EXISTS LoggerSessions
        (
            channel_id bigint PRIMARY KEY,
            creator_id bigint, 
            start_day bigint, 
            sess_repr text, 
            message_id bigint, 
            FOREIGN KEY (channel_id) REFERENCES CreatedSessions(channel_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS SessionCounters
        (
            current_day serial PRIMARY KEY, 
            past_sessions_counter bigint, 
            current_sessions_counter bigint
        );
        CREATE TABLE IF NOT EXISTS SessionMembers
        (
            channel_id bigint NOT NULL,
            member_id bigint NOT NULL,
            PRIMARY KEY (channel_id, member_id),
            FOREIGN KEY (channel_id) REFERENCES CreatedSessions(channel_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS SessionActivities
        (
            channel_id bigint NOT NULL,
            associate_role bigint NOT NULL,
            PRIMARY KEY (channel_id, associate_role)
        );
        CREATE TABLE IF NOT EXISTS ActivitiesINFO
        (
            app_id bigint PRIMARY KEY,  
            app_name text,
            icon_url text
        );
        CREATE TABLE IF NOT EXISTS CreatedRoles
        (
            role_id bigint PRIMARY KEY, 
            app_id bigint UNIQUE
        );
        CREATE TABLE IF NOT EXISTS CreatedEmoji
        (
            role_id bigint PRIMARY KEY, 
            emoji_id bigint,
            FOREIGN KEY (role_id) REFERENCES CreatedRoles(role_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS UserActivities
        (
            role_id bigint PRIMARY KEY,
            user_id bigint, 
            seconds bigint,
            FOREIGN KEY (role_id) REFERENCES CreatedRoles(role_id) ON DELETE CASCADE
        );
    '''
    await cur.execute(commands)
    await cur.execute('SELECT COUNT(*) FROM SessionCounters')
    count = await cur.fetchone()
    if not count[0]:
        commands = '\n'.join([
            f'INSERT INTO SessionCounters (current_day, past_sessions_counter, current_sessions_counter) VALUES ({x}, 0, 0);'
            for x in range(1, 367)
        ])
        await cur.execute(commands)