import requests

def verify_captcha(captcha_token):
    """
    Verify the captcha token with the cap server
    Returns True if verification succeeds, False otherwise
    """
    import os
    client_id = 'bd4f205aa0ab'
    client_secret = os.environ.get('CAPTCHA_CLIENT_SECRET', '')
    verify_url = f'https://cap.ozeliurs.com/{client_id}/siteverify'
    
    try:
        response = requests.post(verify_url, json={
            'secret': client_secret,
            'response': captcha_token
        })
        response.raise_for_status()
        result = response.json()
        return result.get('success', False)
    except Exception as e:
        print(f"Error verifying captcha: {e}")
        return False
