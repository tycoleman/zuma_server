import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import time


from geopy.distance import geodesic
from datetime import datetime


# Use a service account.
cred = credentials.Certificate('zuma-credentials.json')

app2 = firebase_admin.initialize_app(cred)

db = firestore.client()


def get_matching_score(user1, user2):
    # Calculate age for both users
    user1_age = calculate_age(user1['birthday'])
    user2_age = calculate_age(user2['birthday'])

    # Calculate age difference
    age_difference = abs(user1_age - user2_age)

    # Calculate geographical distance
    location1 = (user1['lat'], user1['lng'])
    location2 = (user2['lat'], user2['lng'])
    geo_distance = geodesic(location1, location2).miles

    # Count matching interests
    matching_interests = len(set(user1['interests']).intersection(set(user2['interests'])))

    # Score computation - customize the weights as needed
    score = -age_difference - geo_distance + (10 * matching_interests)
    print(user1['id'], user2['id'], score)
    return score
    
    
    

def find_matches():
    # Initialize Firestore client
    db = firestore.client()
    users_ref = db.collection('users')
    users = [{'id': doc.id, **doc.to_dict()} for doc in users_ref.stream()]

    potential_matches = []

    for i, user1 in enumerate(users):
        for j, user2 in enumerate(users):
            if i >= j:  # Avoid duplicate pairs and matching with oneself
                continue
            if is_match_by_gender(user1['gender'], user2['gender'], user1['interestedIn'], user2['interestedIn']):
                score = get_matching_score(user1, user2)
                potential_matches.append((score, user1, user2))

    # Sort by matching score
    potential_matches.sort(key=lambda x: x[0], reverse=True)

    matched_users = set()
    final_matches = []

    for match in potential_matches:
        _, user1, user2 = match
        if user1['id'] not in matched_users and user2['id'] not in matched_users:
            final_matches.append((user1, user2))
            matched_users.add(user1['id'])
            matched_users.add(user2['id'])
    
    print(final_matches)
    return final_matches



def store_matches_in_firestore(matches):
    # Initialize Firestore client
    db = firestore.client()
    matches_ref = db.collection('matches')

    current_epoch_seconds = int(time.time())

    for match in matches:
        user1, user2 = match
        match_data = {
            "date": current_epoch_seconds,
            "isActive": True,
            "members": [user1['id'], user2['id']]
        }
        # Add the match data to the matches collection
        matches_ref.add(match_data)


def calculate_age(birthday_str):
    birth_date = datetime.strptime(birthday_str, "%d/%m/%Y")
    today = datetime.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age
    
    
def is_match_by_gender(user1_gender, user2_gender, user1_pref, user2_pref):
    # Gender to preference mapping
    gender_to_pref = {
        "Man": "Men",
        "Woman": "Women",
        "Non-Binary": "Other"
    }

    return gender_to_pref[user1_gender] == user2_pref and gender_to_pref[user2_gender] == user1_pref

    
matches = find_matches()
store_matches_in_firestore(matches)
