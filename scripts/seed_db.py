"""
Seed database with test data for development.
"""
import sys
sys.path.insert(0, ".")

from src.db.session import create_tables, SessionLocal
from src.db.crud import create_user
from src.db.models import UserRole


def seed():
    create_tables()
    db = SessionLocal()

    try:
        # Create test faculty
        create_user(db, "Dr. Sharma", "sharma@vnit.ac.in", "faculty123",
                   UserRole.FACULTY)
        print("✅ Faculty: Dr. Sharma (sharma@vnit.ac.in / faculty123)")

        # Create test admin
        create_user(db, "Admin User", "admin@vnit.ac.in", "admin123",
                   UserRole.ADMIN)
        print("✅ Admin: Admin User (admin@vnit.ac.in / admin123)")

        # Create test students
        test_students = [
            ("Samyak Jain", "samyak@vnit.ac.in", "student123", "BT23CSE001"),
            ("Priya Patel", "priya@vnit.ac.in", "student123", "BT23CSE002"),
            ("Rahul Kumar", "rahul@vnit.ac.in", "student123", "BT23CSE003"),
            ("Ananya Singh", "ananya@vnit.ac.in", "student123", "BT23CSE004"),
            ("Vikram Reddy", "vikram@vnit.ac.in", "student123", "BT23CSE005"),
        ]

        for name, email, pwd, roll in test_students:
            create_user(db, name, email, pwd, UserRole.STUDENT, roll)
            print(f"✅ Student: {name} ({email} / {pwd}) [{roll}]")

        print(f"\n🎉 Seeded {2 + len(test_students)} users successfully!")

    except Exception as e:
        print(f"⚠️ Seed error (may already exist): {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
