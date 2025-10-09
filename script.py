import sqlite3

USER_DB = "users.db"

def upgrade_user_to_premium(user_id):
    conn = sqlite3.connect(USER_DB)
    cursor = conn.cursor()

    # Check if the user exists
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        print(f"❌ User with ID {user_id} not found.")
        conn.close()
        return

    # Update subscription tier
    cursor.execute("""
        UPDATE users
        SET subscription_tier = 'premium'
        WHERE id = ?
    """, (user_id,))
    conn.commit()
    conn.close()

    print(f"✅ User {user_id} upgraded to Premium successfully!")

if __name__ == "__main__":
    upgrade_user_to_premium(1)
