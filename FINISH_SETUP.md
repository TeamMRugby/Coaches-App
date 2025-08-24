

**Password hashing**
Install passlib locally and generate hashes:
```bash
pip install passlib[bcrypt]
python -c "from passlib.hash import bcrypt; print(bcrypt.hash('YourStrongPassword!'))"
```
Paste the hash string(s) into `.streamlit/auth.yaml` in place of the `REPLACE_WITH_BCRYPT_HASH_*` placeholders.
