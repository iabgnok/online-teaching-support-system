import pytest
from app import app
from models import db, Users, generate_next_id, Friendship, FriendRequest, Conversation, ConversationMember, MessageReaction
from api.v1.auth import generate_token

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        # Teardown
        with app.app_context():
            db.session.remove()
            # Note: Don't drop all tables in dev DB


def create_user(username, real_name, user_id=None, role='student'):
    if user_id is None:
        user_id = generate_next_id(Users, 'user_id')
    u = Users(user_id=user_id, username=username, real_name=real_name, role=role)
    u.set_password('password')
    db.session.add(u)
    db.session.commit()
    return u


def test_friend_request_and_accept_flow(client):
    with app.app_context():
        # create two users
        a = create_user('alice', 'Alice')
        b = create_user('bob', 'Bob')

        token_a = generate_token(a)
        token_b = generate_token(b)

        # send friend request from A to B
        rv = client.post('/api/v1/contacts/requests', json={'target_id': b.user_id}, headers={'Authorization': f'Bearer {token_a}'})
        assert rv.status_code == 201
        data = rv.get_json()
        req_id = data['request_id']

        # B gets requests
        rv = client.get('/api/v1/contacts/requests', headers={'Authorization': f'Bearer {token_b}'})
        assert rv.status_code == 200
        j = rv.get_json()
        assert len(j['incoming']) == 1

        # B accepts
        rv = client.post(f'/api/v1/contacts/requests/{req_id}/accept', headers={'Authorization': f'Bearer {token_b}'})
        assert rv.status_code == 200
        j = rv.get_json()
        assert 'conversation_id' in j

        # Verify Friendship entries
        f_ab = Friendship.query.filter_by(user_id=a.user_id, friend_id=b.user_id).first()
        f_ba = Friendship.query.filter_by(user_id=b.user_id, friend_id=a.user_id).first()
        assert f_ab is not None and f_ba is not None

        # Verify Conversation members
        conv_id = j['conversation_id']
        conv = Conversation.query.get(conv_id)
        assert conv is not None
        members = [m.user_id for m in conv.members]
        assert set(members) == set([a.user_id, b.user_id])
