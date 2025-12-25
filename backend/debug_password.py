from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def test_hashing():
    pwd = "password123"
    print(f"Hashing '{pwd}'...")
    try:
        hashed = pwd_context.hash(pwd)
        print(f"Hash: {hashed}")
        
        print("Verifying...")
        is_valid = pwd_context.verify(pwd, hashed)
        print(f"Verify result: {is_valid}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_hashing()
