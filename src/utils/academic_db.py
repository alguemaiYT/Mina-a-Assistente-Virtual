import sqlite3
import os
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "academic.db")

def init_db():
    """Initialize the SQLite academic database tables."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Table for Professors
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS professors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            room TEXT NOT NULL,
            email TEXT,
            department TEXT
        )
    """)
    
    # 2. Table for Class Schedules
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            weekday INTEGER NOT NULL, -- 0=Monday, ..., 6=Sunday
            start_time TEXT NOT NULL,  -- HH:MM
            end_time TEXT NOT NULL,    -- HH:MM
            room TEXT NOT NULL,
            teacher_name TEXT
        )
    """)
    
    # 3. Table for Events and News
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            link TEXT,
            pub_date TEXT,
            category TEXT,
            is_event BOOLEAN DEFAULT 0
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info("Academic database initialized at %s", DB_PATH)

def save_professor(name: str, room: str, email: str = None, department: str = None):
    """Save or update a professor's info."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO professors (name, room, email, department)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            room = excluded.room,
            email = excluded.email,
            department = excluded.department
    """, (name, room, email, department))
    conn.commit()
    conn.close()

def save_schedule(subject: str, weekday: int, start_time: str, end_time: str, room: str, teacher_name: str = None):
    """Save a class schedule slot."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Check if slot exists to prevent duplicates
    cursor.execute("""
        SELECT id FROM schedules 
        WHERE subject = ? AND weekday = ? AND start_time = ? AND room = ?
    """, (subject, weekday, start_time, room))
    row = cursor.fetchone()
    if not row:
        cursor.execute("""
            INSERT INTO schedules (subject, weekday, start_time, end_time, room, teacher_name)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (subject, weekday, start_time, end_time, room, teacher_name))
        conn.commit()
    conn.close()

def save_news_event(title: str, link: str, pub_date: str, category: str, is_event: bool = False):
    """Save a news or event item."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Check if item exists by title
    cursor.execute("SELECT id FROM news_events WHERE title = ?", (title,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("""
            INSERT INTO news_events (title, link, pub_date, category, is_event)
            VALUES (?, ?, ?, ?, ?)
        """, (title, link, pub_date, category, 1 if is_event else 0))
        conn.commit()
    conn.close()

def clear_schedules():
    """Clear all schedules to reload them."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM schedules")
    conn.commit()
    conn.close()

def get_professors() -> List[Dict[str, Any]]:
    """Retrieve list of all professors."""
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, room, email, department FROM professors ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [{"name": r[0], "room": r[1], "email": r[2], "department": r[3]} for r in rows]

def get_recent_news_events(limit: int = 5) -> List[Dict[str, Any]]:
    """Retrieve recent news or events."""
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT title, link, pub_date, category, is_event FROM news_events ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [{"title": r[0], "link": r[1], "pub_date": r[2], "category": r[3], "is_event": bool(r[4])} for r in rows]

def get_active_classes() -> List[Dict[str, Any]]:
    """Retrieve classes currently active based on current Brazil time."""
    if not os.path.exists(DB_PATH):
        return []
    
    # Brazil Time (UTC-3)
    tz_br = timezone(timedelta(hours=-3))
    now_br = datetime.now(timezone.utc).astimezone(tz_br)
    weekday = now_br.weekday()
    time_str = now_br.strftime("%H:%M")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT subject, start_time, end_time, room, teacher_name 
        FROM schedules 
        WHERE weekday = ? AND start_time <= ? AND end_time > ?
    """, (weekday, time_str, time_str))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [{"subject": r[0], "start_time": r[1], "end_time": r[2], "room": r[3], "teacher_name": r[4]} for r in rows]

def get_upcoming_classes_today() -> List[Dict[str, Any]]:
    """Retrieve upcoming classes today based on current Brazil time."""
    if not os.path.exists(DB_PATH):
        return []
    
    tz_br = timezone(timedelta(hours=-3))
    now_br = datetime.now(timezone.utc).astimezone(tz_br)
    weekday = now_br.weekday()
    time_str = now_br.strftime("%H:%M")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT subject, start_time, end_time, room, teacher_name 
        FROM schedules 
        WHERE weekday = ? AND start_time > ?
        ORDER BY start_time ASC
        LIMIT 5
    """, (weekday, time_str))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [{"subject": r[0], "start_time": r[1], "end_time": r[2], "room": r[3], "teacher_name": r[4]} for r in rows]

def get_academic_context() -> str:
    """Format all SQLite database tables into a prompt-friendly context text block."""
    if not os.path.exists(DB_PATH):
        return "Nenhum dado acadêmico da UNESP disponível no momento."
        
    tz_br = timezone(timedelta(hours=-3))
    now_br = datetime.now(timezone.utc).astimezone(tz_br)
    
    parts = []
    parts.append("=== CONTEXTO ACADÊMICO ATUAL DA UNESP SOROCABA (Mina Local DB) ===")
    parts.append(f"Data/Hora do Sistema: {now_br.strftime('%d/%m/%Y %H:%M')} (Horário de Brasília)")
    
    # 1. Active Classes Right Now
    active = get_active_classes()
    if active:
        parts.append("\n[Aulas em Andamento Agora]:")
        for a in active:
            parts.append(f"- Matéria: {a['subject']} | Horário: {a['start_time']} às {a['end_time']} | Sala: {a['room']} | Prof: {a['teacher_name']}")
    else:
        parts.append("\n[Aulas em Andamento Agora]: Nenhuma aula ocorrendo neste momento.")
        
    # 2. Upcoming Classes Today
    upcoming = get_upcoming_classes_today()
    if upcoming:
        parts.append("\n[Próximas Aulas de Hoje]:")
        for u in upcoming:
            parts.append(f"- Matéria: {u['subject']} | Início: {u['start_time']} | Sala: {u['room']} | Prof: {u['teacher_name']}")
            
    # 3. Professors Rooms list
    profs = get_professors()
    if profs:
        parts.append("\n[Localização de Professores e Salas]:")
        for p in profs:
            parts.append(f"- {p['name']}: {p['room']} (E-mail: {p['email'] or 'Não informado'})")
            
    # 4. News & Events
    news = get_recent_news_events(5)
    if news:
        parts.append("\n[Mural e Notícias do Jornal da Unesp]:")
        for n in news:
            type_str = "Evento" if n['is_event'] else "Notícia"
            parts.append(f"- [{type_str}] {n['title']} (Categoria: {n['category'] or 'Geral'})")
            
    return "\n".join(parts)
