import requests

BASE_URL = 'https://jsonplaceholder.typicode.com'

def get_users():
    response = requests.get(f'{BASE_URL}/users')
    if response.status_code == 200:
        users = response.json()
        print("Dummy User Dashboard:")
        print("-" * 40)
        for user in users[:5]:  # Show first 5
            print(f"Name: {user['name']} | Email: {user['email']} | City: {user['address']['city']}")
        print(f"\nTotal users fetched: {len(users)}")
    else:
        print(f"Oof: {response.status_code}")

if __name__ == "__main__":
    get_users()