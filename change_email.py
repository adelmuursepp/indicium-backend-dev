from firebase_admin import auth
import firebase_admin
from dotenv import load_dotenv


def change_email(uid, email):
    user = auth.update_user(uid, email=email)
    print("User:", user)


if __name__ == "__main__":
    load_dotenv()
    firebase_admin.initialize_app()

    change_email(uid="vmRkbwhG99NOmD3vKLHDNq27ZON2", email="Cole.Patterson@gmail.com")
