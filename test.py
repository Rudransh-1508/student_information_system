from passlib.hash import bcrypt

hashed = bcrypt.hash("test123")
print("Hashed password:", hashed)

assert bcrypt.verify("test123", hashed)
print("Password verified ✔️")
