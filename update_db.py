import sqlite3
import os

# 数据库文件路径
db_path = '/Users/wangwenfei/Dev/github/F5-TTS/f5_tts_api/data/f5_tts.db'

# 检查数据库文件是否存在
if not os.path.exists(db_path):
    print(f"数据库文件不存在: {db_path}")
    exit(1)

print(f"正在连接数据库: {db_path}")

# 连接到SQLite数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # 检查audio_samples表是否有text字段
    cursor.execute("PRAGMA table_info(audio_samples)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'text' not in columns:
        print("为audio_samples表添加text字段...")
        cursor.execute("ALTER TABLE audio_samples ADD COLUMN text TEXT")
        conn.commit()
        print("text字段添加成功！")
    else:
        print("audio_samples表已经有text字段，不需要更新。")
        
    # 验证更新结果
    cursor.execute("PRAGMA table_info(audio_samples)")
    print("\n更新后的表结构：")
    for col in cursor.fetchall():
        print(f"- {col[1]} ({col[2]})")
        
finally:
    # 关闭连接
    cursor.close()
    conn.close()
    print(f"\n数据库连接已关闭。")