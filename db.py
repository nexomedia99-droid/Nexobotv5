import sqlite3
import logging
from datetime import datetime
from contextlib import contextmanager
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_FILE = "database.db"

@contextmanager
def get_conn():
    """Context manager for database connections"""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE, timeout=30.0)
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def init_db():
    """Initialize database with all required tables"""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            
            # Users table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                whatsapp TEXT NOT NULL,
                telegram TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                payment_number TEXT NOT NULL,
                owner_name TEXT NOT NULL,
                referrer TEXT,
                points INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Jobs table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                fee TEXT NOT NULL,
                desc TEXT NOT NULL,
                status TEXT DEFAULT 'aktif',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Applicants table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS applicants (
                job_id INTEGER,
                user_id TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (job_id, user_id),
                FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            )
            """)
            
            # Achievements table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                badge_name TEXT NOT NULL,
                awarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            )
            """)
            
            # Activity logs table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                action_type TEXT NOT NULL,
                user_id TEXT,
                description TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE SET NULL
            )
            """)
            
            # Group messages table for AI summary
            cur.execute("""
            CREATE TABLE IF NOT EXISTS group_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                user_id TEXT,
                username TEXT,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS promotions (
                promo_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                link TEXT NOT NULL,
                type TEXT NOT NULL,
                followers TEXT NOT NULL,
                description TEXT DEFAULT 'follow',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Indexes for better performance
            cur.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_users_points ON users(points)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_applicants_job_id ON applicants(job_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_applicants_user_id ON applicants(user_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_achievements_user_id ON achievements(user_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON activity_logs(user_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_activity_logs_timestamp ON activity_logs(timestamp)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_promotions_user_id ON promotions(user_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_promotions_created_at ON promotions(created_at)")
            
            conn.commit()
            logger.info("✅ Database berhasil di inisialisasi")
            
    except Exception as e:
        logger.error(f"Gagal menginisialisasi database: {e}")
        raise

# ==== USER FUNCTIONS ====

def add_user(user_id, data):
    """Add or update user in database"""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO users 
                (user_id, username, whatsapp, telegram, payment_method, payment_number, owner_name, referrer, points, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                user_id,
                data['username'],
                data['whatsapp'],
                data['telegram'],
                data['payment_method'],
                data['payment_number'],
                data['owner_name'],
                data.get('referrer', None),
                data.get('points', 0)
            ))
            conn.commit()
            logger.info(f"User {user_id} added/updated successfully")
    except Exception as e:
        logger.error(f"Failed to add user {user_id}: {e}")
        raise

def get_user_by_id(user_id):
    """Get user by ID"""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT user_id, username, whatsapp, telegram, payment_method, 
                       payment_number, owner_name, referrer, points, created_at
                FROM users WHERE user_id = ?
            """, (user_id,))
            row = cur.fetchone()
            if row:
                keys = ["user_id", "username", "whatsapp", "telegram", "payment_method", 
                       "payment_number", "owner_name", "referrer", "points", "created_at"]
                return dict(zip(keys, row))
        return None
    except Exception as e:
        logger.error(f"Failed to get user {user_id}: {e}")
        return None

def get_user_by_username(username):
    """Get user by username"""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT user_id, username, whatsapp, telegram, payment_method, 
                       payment_number, owner_name, referrer, points, created_at
                FROM users WHERE username = ?
            """, (username,))
            row = cur.fetchone()
            if row:
                keys = ["user_id", "username", "whatsapp", "telegram", "payment_method", 
                       "payment_number", "owner_name", "referrer", "points", "created_at"]
                return dict(zip(keys, row))
        return None
    except Exception as e:
        logger.error(f"Failed to get user by username {username}: {e}")
        return None

def get_all_users():
    """Get all users"""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT user_id, username, whatsapp, telegram, payment_method, 
                       payment_number, owner_name, referrer, points, created_at
                FROM users ORDER BY created_at DESC
            """)
            rows = cur.fetchall()
            keys = ["user_id", "username", "whatsapp", "telegram", "payment_method", 
                   "payment_number", "owner_name", "referrer", "points", "created_at"]
            return [dict(zip(keys, row)) for row in rows]
    except Exception as e:
        logger.error(f"Failed to get all users: {e}")
        return []

def get_referrals_by_username(referrer_username):
    """Get all users referred by a specific username"""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT user_id, username, whatsapp, telegram, payment_method, 
                       payment_number, owner_name, referrer, points, created_at
                FROM users WHERE referrer = ?
            """, (referrer_username,))
            rows = cur.fetchall()
            keys = ["user_id", "username", "whatsapp", "telegram", "payment_method", 
                   "payment_number", "owner_name", "referrer", "points", "created_at"]
            return [dict(zip(keys, row)) for row in rows]
    except Exception as e:
        logger.error(f"Failed to get referrals for {referrer_username}: {e}")
        return []

def add_points_to_user(user_id, points_to_add):
    """Add points to user"""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE users SET points = points + ?, updated_at = CURRENT_TIMESTAMP 
                WHERE user_id = ?
            """, (points_to_add, user_id))
            conn.commit()
            logger.info(f"Added {points_to_add} points to user {user_id}")
    except Exception as e:
        logger.error(f"Failed to add points to user {user_id}: {e}")
        raise

def deduct_points(user_id, points):
    """Mengurangi poin dari saldo pengguna."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET points = points - ? WHERE user_id=?", (points, user_id))
        conn.commit()

def delete_user_by_id(user_id):
    """Delete user and all related data"""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            # Delete user (cascading will handle related data)
            cur.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            conn.commit()
            logger.info(f"User {user_id} deleted successfully")
    except Exception as e:
        logger.error(f"Failed to delete user {user_id}: {e}")
        raise

# ==== JOB FUNCTIONS ====

def add_job(title, fee, desc, status="aktif"):
    """Add new job"""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO jobs (title, fee, desc, status) VALUES (?, ?, ?, ?)
            """, (title, fee, desc, status))
            conn.commit()
            job_id = cur.lastrowid
            logger.info(f"Job {job_id} created successfully")
            return job_id
    except Exception as e:
        logger.error(f"Failed to add job: {e}")
        raise

def get_job_by_id(job_id):
    """Get job by ID"""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, title, fee, desc, status, created_at 
                FROM jobs WHERE id = ?
            """, (job_id,))
            row = cur.fetchone()
            if row:
                keys = ["id", "title", "fee", "desc", "status", "created_at"]
                return dict(zip(keys, row))
        return None
    except Exception as e:
        logger.error(f"Failed to get job {job_id}: {e}")
        return None

def get_all_jobs():
    """Get all jobs"""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, title, fee, desc, status, created_at 
                FROM jobs ORDER BY created_at DESC
            """)
            rows = cur.fetchall()
            keys = ["id", "title", "fee", "desc", "status", "created_at"]
            return [dict(zip(keys, row)) for row in rows]
    except Exception as e:
        logger.error(f"Failed to get all jobs: {e}")
        return []

# ==== APPLICANTS FUNCTIONS ====

def add_applicant(job_id, user_id):
    """Add job applicant"""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT OR IGNORE INTO applicants (job_id, user_id) VALUES (?, ?)
            """, (job_id, user_id))
            conn.commit()
            logger.info(f"User {user_id} applied to job {job_id}")
    except Exception as e:
        logger.error(f"Failed to add applicant {user_id} to job {job_id}: {e}")
        raise

def get_applicants_by_job(job_id):
    """Get all applicants for a job"""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT user_id FROM applicants WHERE job_id = ? ORDER BY applied_at
            """, (job_id,))
            return [row[0] for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Failed to get applicants for job {job_id}: {e}")
        return []

def get_total_applies(user_id):
    """Get total number of jobs applied by user"""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM applicants WHERE user_id = ?", (user_id,))
            return cur.fetchone()[0]
    except Exception as e:
        logger.error(f"Failed to get total applies for user {user_id}: {e}")
        return 0

# ==== ACHIEVEMENT FUNCTIONS ====

def has_badge(user_id, badge_name):
    """Check if user has specific badge"""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT 1 FROM achievements WHERE user_id = ? AND badge_name = ?
            """, (user_id, badge_name))
            return cur.fetchone() is not None
    except Exception as e:
        logger.error(f"Failed to check badge for user {user_id}: {e}")
        return False

def add_badge_to_user(user_id, badge_name):
    """Add badge to user if not already exists"""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT OR IGNORE INTO achievements (user_id, badge_name) VALUES (?, ?)
            """, (user_id, badge_name))
            conn.commit()
            logger.info(f"Badge '{badge_name}' added to user {user_id}")
    except Exception as e:
        logger.error(f"Failed to add badge to user {user_id}: {e}")
        raise

def get_badges(user_id):
    """Get all badges for user"""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT badge_name FROM achievements WHERE user_id = ? ORDER BY awarded_at
            """, (user_id,))
            return [row[0] for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Failed to get badges for user {user_id}: {e}")
        return []

# ==== GROUP MESSAGES FUNCTIONS ====

def save_group_message(chat_id, user_id, username, message):
    """Save group message for AI summary"""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO group_messages (chat_id, user_id, username, message)
                VALUES (?, ?, ?, ?)
            """, (chat_id, user_id, username, message))
            
            # Keep only last 100 messages per chat
            cur.execute("""
                DELETE FROM group_messages 
                WHERE chat_id = ? AND id NOT IN (
                    SELECT id FROM group_messages 
                    WHERE chat_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 100
                )
            """, (chat_id, chat_id))
            
            conn.commit()
    except Exception as e:
        logger.error(f"Failed to save group message: {e}")

def get_recent_group_messages(chat_id, limit=50):
    """Get recent group messages for summary"""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT username, message, timestamp 
                FROM group_messages 
                WHERE chat_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (chat_id, limit))
            return cur.fetchall()
    except Exception as e:
        logger.error(f"Failed to get recent messages: {e}")
        return []

#=======BOOST FUNCTIONS=======
def save_promotion(boost_data):
    """Menyimpan data boost baru ke database."""
    with get_conn() as conn:
        cur = conn.cursor()
        boosters_json = json.dumps(boost_data['boosters'])
        cur.execute("""
            INSERT INTO promotions (promo_id, user_id, link, type, followers, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (boost_data['promo_id'], boost_data['user_id'], boost_data['link'], boost_data['type'], boosters_json, boost_data['description'], datetime.now()))
        conn.commit()

def get_promotion(promo_id):
    """Mengambil data boost dari database."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM promotions WHERE promo_id=?", (promo_id,))
        boost = cur.fetchone()
        if boost:
            boosters_list = json.loads(boost[4])
            description = boost[6] if len(boost) > 6 else 'follow'  # Backward compatibility
            return {
                'promo_id': boost[0], 
                'user_id': boost[1], 
                'link': boost[2], 
                'type': boost[3], 
                'boosters': boosters_list,
                'description': description
            }
    return None

def add_booster(promo_id, booster_user_id):
    """Menambahkan ID pengguna yang mengklik ke daftar booster sebuah boost."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT followers FROM promotions WHERE promo_id=?", (promo_id,))
        current_boosters_json = cur.fetchone()[0]

        current_boosters = json.loads(current_boosters_json)
        current_boosters.append(booster_user_id)

        updated_boosters_json = json.dumps(current_boosters)

        cur.execute("UPDATE promotions SET followers=? WHERE promo_id=?", (updated_boosters_json, promo_id))
        conn.commit()