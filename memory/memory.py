import sqlite3
from pathlib import Path


class Memory:

    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.database = self.base_dir / "nova_memory.db"

        self.connection = sqlite3.connect(
            self.database,
            check_same_thread=False
        )

        self.connection.row_factory = sqlite3.Row

        self._create_tables()
        self._create_indexes()

    def _create_tables(self):
        cursor = self.connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                importance INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.connection.commit()

        columns = {
            row["name"]
            for row in cursor.execute(
                "PRAGMA table_info(memories)"
            ).fetchall()
        }

        if "category" not in columns:
            cursor.execute("""
                ALTER TABLE memories
                ADD COLUMN category TEXT DEFAULT 'general'
            """)

        if "importance" not in columns:
            cursor.execute("""
                ALTER TABLE memories
                ADD COLUMN importance INTEGER DEFAULT 1
            """)

        if "created_at" not in columns:
            cursor.execute("""
                ALTER TABLE memories
                ADD COLUMN created_at TIMESTAMP
            """)

            cursor.execute("""
                UPDATE memories
                SET created_at = CURRENT_TIMESTAMP
                WHERE created_at IS NULL
            """)

        if "updated_at" not in columns:
            cursor.execute("""
                ALTER TABLE memories
                ADD COLUMN updated_at TIMESTAMP
            """)

            cursor.execute("""
                UPDATE memories
                SET updated_at = CURRENT_TIMESTAMP
                WHERE updated_at IS NULL
            """)

        conversation_columns = {
            row["name"]
            for row in cursor.execute(
                "PRAGMA table_info(conversation)"
            ).fetchall()
        }

        if "created_at" not in conversation_columns:
            cursor.execute("""
                ALTER TABLE conversation
                ADD COLUMN created_at TIMESTAMP
            """)

            cursor.execute("""
                UPDATE conversation
                SET created_at = CURRENT_TIMESTAMP
                WHERE created_at IS NULL
            """)

        self.connection.commit()

    def _create_indexes(self):
        cursor = self.connection.cursor()

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_key
            ON memories(key)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_category
            ON memories(category)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_importance
            ON memories(importance)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversation_created_at
            ON conversation(created_at)
        """)

        self.connection.commit()

    def remember(
        self,
        key,
        value,
        category="general",
        importance=1
    ):
        key = str(key).strip()
        value = str(value).strip()
        category = str(category).strip() or "general"

        try:
            importance = int(importance)
        except (TypeError, ValueError):
            importance = 1

        importance = max(1, min(10, importance))

        if not key or not value:
            return False

        cursor = self.connection.cursor()

        cursor.execute("""
            INSERT INTO memories (
                key,
                value,
                category,
                importance,
                created_at,
                updated_at
            )
            VALUES (
                ?, ?, ?, ?,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            ON CONFLICT(key)
            DO UPDATE SET
                value = excluded.value,
                category = excluded.category,
                importance = excluded.importance,
                updated_at = CURRENT_TIMESTAMP
        """, (
            key,
            value,
            category,
            importance
        ))

        self.connection.commit()

        return True

    def recall(self, key):
        if not key:
            return None

        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT
                id,
                key,
                value,
                category,
                importance,
                created_at,
                updated_at
            FROM memories
            WHERE key = ?
        """, (str(key).strip(),))

        row = cursor.fetchone()

        if not row:
            return None

        return row["value"]

    def get_memory(self, key):
        if not key:
            return None

        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT
                id,
                key,
                value,
                category,
                importance,
                created_at,
                updated_at
            FROM memories
            WHERE key = ?
        """, (str(key).strip(),))

        row = cursor.fetchone()

        if not row:
            return None

        return dict(row)

    def search(self, query, limit=10):
        if not query:
            return []

        query = str(query).strip()

        if not query:
            return []

        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 10

        limit = max(1, min(100, limit))

        pattern = f"%{query}%"

        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT
                id,
                key,
                value,
                category,
                importance,
                created_at,
                updated_at
            FROM memories
            WHERE
                key LIKE ?
                OR value LIKE ?
                OR category LIKE ?
            ORDER BY
                importance DESC,
                updated_at DESC
            LIMIT ?
        """, (
            pattern,
            pattern,
            pattern,
            limit
        ))

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    def search_by_category(self, category, limit=50):
        if not category:
            return []

        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 50

        limit = max(1, min(100, limit))

        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT
                id,
                key,
                value,
                category,
                importance,
                created_at,
                updated_at
            FROM memories
            WHERE category = ?
            ORDER BY
                importance DESC,
                updated_at DESC
            LIMIT ?
        """, (
            str(category).strip(),
            limit
        ))

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    def forget(self, key):
        if not key:
            return False

        cursor = self.connection.cursor()

        cursor.execute("""
            DELETE FROM memories
            WHERE key = ?
        """, (str(key).strip(),))

        deleted = cursor.rowcount > 0

        self.connection.commit()

        return deleted

    def forget_all(self):
        cursor = self.connection.cursor()

        cursor.execute("""
            DELETE FROM memories
        """)

        deleted = cursor.rowcount

        self.connection.commit()

        return deleted

    def get_all(self):
        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT
                id,
                key,
                value,
                category,
                importance,
                created_at,
                updated_at
            FROM memories
            ORDER BY
                importance DESC,
                updated_at DESC
        """)

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    def count(self):
        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT COUNT(*) AS count
            FROM memories
        """)

        row = cursor.fetchone()

        return row["count"]

    def save_message(self, role, content):
        if not role or not content:
            return False

        cursor = self.connection.cursor()

        cursor.execute("""
            INSERT INTO conversation (
                role,
                content,
                created_at
            )
            VALUES (
                ?, ?,
                CURRENT_TIMESTAMP
            )
        """, (
            str(role).strip(),
            str(content).strip()
        ))

        self.connection.commit()

        return True

    def get_recent_messages(self, limit=10):
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 10

        limit = max(1, min(100, limit))

        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT
                role,
                content,
                created_at
            FROM conversation
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        rows.reverse()

        return [
            {
                "role": row["role"],
                "content": row["content"],
                "created_at": row["created_at"]
            }
            for row in rows
        ]

    def get_conversation_count(self):
        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT COUNT(*) AS count
            FROM conversation
        """)

        row = cursor.fetchone()

        return row["count"]

    def clear_conversation(self):
        cursor = self.connection.cursor()

        cursor.execute("""
            DELETE FROM conversation
        """)

        deleted = cursor.rowcount

        self.connection.commit()

        return deleted

    def delete_old_messages(self, keep=1000):
        try:
            keep = int(keep)
        except (TypeError, ValueError):
            keep = 1000

        keep = max(0, keep)

        cursor = self.connection.cursor()

        cursor.execute("""
            DELETE FROM conversation
            WHERE id NOT IN (
                SELECT id
                FROM conversation
                ORDER BY id DESC
                LIMIT ?
            )
        """, (keep,))

        deleted = cursor.rowcount

        self.connection.commit()

        return deleted

    def get_memory_context(self, query=None, limit=10):
        if query:
            memories = self.search(
                query,
                limit=limit
            )
        else:
            memories = self.get_all()[:limit]

        if not memories:
            return ""

        lines = []

        for memory in memories:
            lines.append(
                f"- {memory['key']}: {memory['value']}"
            )

        return "\n".join(lines)

    def get_context(
        self,
        query=None,
        memory_limit=10,
        message_limit=10
    ):
        memories = self.get_memory_context(
            query=query,
            limit=memory_limit
        )

        messages = self.get_recent_messages(
            limit=message_limit
        )

        return {
            "memories": memories,
            "messages": messages
        }

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None