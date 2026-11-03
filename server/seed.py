from faker import Faker

from app import app
from config import db
from models import Note, User

fake = Faker()
CATEGORIES = ["work", "personal", "ideas", "todo"]

with app.app_context():
    print("Clearing old data...")
    Note.query.delete()
    User.query.delete()

    print("Creating users and notes...")
    for name in ["alice", "bob", "carol"]:
        user = User(username=name)
        user.password = "password123"
        db.session.add(user)
        db.session.flush()

        for _ in range(8):
            db.session.add(
                Note(
                    title=fake.sentence(nb_words=4).rstrip("."),
                    content=fake.paragraph(nb_sentences=3),
                    category=fake.random_element(CATEGORIES),
                    user_id=user.id,
                )
            )

    db.session.commit()
    print("Done seeding! Log in with alice / password123")