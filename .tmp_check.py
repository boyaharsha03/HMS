import routes.auth as ra
from app import app
ra.send_otp_email = lambda recipient, name, code: print('FAKE_EMAIL', recipient, code)
client = app.test_client()
resp = client.post('/register', data={'name':'Test User','email':'testuser@example.com','phone':'9876543210','password':'Test1234','confirm_password':'Test1234'}, follow_redirects=False)
print('register_status', resp.status_code, resp.headers.get('Location'))
with client.session_transaction() as session:
    print('pending_registration', bool(session.get('pending_registration')))
    if session.get('pending_registration'):
        print('email', session['pending_registration']['email'])
        print('otp_exists', bool(session.get('otp')))
