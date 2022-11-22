import pytest

from api.tools.utils import query_identifiers


@pytest.mark.parametrize('query, expected',
                         [
                             ('select a from foo;', False),
                             ('select a, b from foo;', True),
                             ('select * from foo;', True),
                             ('select a from foo; select b from bar;', False),
                             ('select a from foo; select b, c from bar;', True),
                             ('select a, b from foo; select c from bar;', True),
                             ('select * from foo; select b from bar;', True),
                             ('select a from foo; select * from bar;', True),
                             ("""SELECT emoji_id FROM 
                                                    CreatedRoles JOIN CreatedEmoji 
                                                        on CreatedRoles.role_id = CreatedEmoji.role_id
                                                    WHERE CreatedRoles.role_id = {role_id}""", False)
                         ])
def test_query_identifiers(query: str, expected: bool):
    assert query_identifiers(query) == expected
