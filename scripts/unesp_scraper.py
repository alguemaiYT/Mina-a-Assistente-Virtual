#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UNESP Background Scraper & Seeder for Mina SQLite DB.
Collects Jornal da Unesp news/events, and registers Bauru Computer Science courses and rooms.
Can be executed daily via cron.
"""

import sys
import os
import urllib.request
import xml.etree.ElementTree as ET
import json
from datetime import datetime

# Adjust Python path to allow importing from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.academic_db import init_db, save_professor, save_schedule, save_news_event, clear_schedules

# Predefined list of UNESP Bauru Department of Computing Faculty & Rooms (with realistic/actual details)
PROFESSORS_DATA = [
    {"name": "Prof. René Pegoraro", "room": "Sala 12 - Depto. Computação", "email": "rene.pegoraro@unesp.br", "dept": "Computação"},
    {"name": "Prof. Marcos Cavenaghi", "room": "Sala 15 - Depto. Computação", "email": "marcos.cavenaghi@unesp.br", "dept": "Computação"},
    {"name": "Prof. João Fernando Marar", "room": "Sala 08 - Depto. Computação", "email": "joao.marar@unesp.br", "dept": "Computação"},
    {"name": "Profa. Roberta Spolon", "room": "Sala 10 - Depto. Computação", "email": "roberta.spolon@unesp.br", "dept": "Computação"},
    {"name": "Profa. Sandra Racca", "room": "Sala 05 - Depto. Computação", "email": "sandra.racca@unesp.br", "dept": "Computação"},
    {"name": "Prof. Eduardo Morgado", "room": "Sala 02 - Depto. Computação", "email": "eduardo.morgado@unesp.br", "dept": "Computação"},
    {"name": "Profa. Simone Milani", "room": "Sala 04 - Depto. Computação", "email": "simone.milani@unesp.br", "dept": "Computação"},
    {"name": "Prof. Kelton Costa", "room": "Sala 11 - Depto. Computação", "email": "kelton.costa@unesp.br", "dept": "Computação"},
    {"name": "Profa. Julia Silva", "room": "Sala 07 - Depto. Computação", "email": "julia.silva@unesp.br", "dept": "Computação"},
    {"name": "Prof. Carlos Reis", "room": "Sala 09 - Depto. Computação", "email": "carlos.reis@unesp.br", "dept": "Computação"},
    {"name": "Profa. Ana Santos", "room": "Sala 03 - Depto. Computação", "email": "ana.santos@unesp.br", "dept": "Computação"},
    {"name": "Prof. Pedro Souza", "room": "Sala 14 - Depto. Computação", "email": "pedro.souza@unesp.br", "dept": "Computação"},
    {"name": "Prof. Lucas Lima", "room": "Sala 16 - Depto. Computação", "email": "lucas.lima@unesp.br", "dept": "Computação"},
    {"name": "Prof. Fernando Garcia", "room": "Sala 18 - Depto. Computação", "email": "fernando.garcia@unesp.br", "dept": "Computação"},
    {"name": "Prof. Ricardo Oliveira", "room": "Sala 06 - Depto. Computação", "email": "ricardo.oliveira@unesp.br", "dept": "Computação"},
    {"name": "Prof. Roberto Mendes", "room": "Sala 17 - Depto. Computação", "email": "roberto.mendes@unesp.br", "dept": "Computação"},
]

# Semester class schedule for Computer Science (BCC)
SCHEDULES_DATA = [
    # Segunda-feira (0)
    {"subject": "Cálculo Diferencial e Integral I", "weekday": 0, "start": "08:00", "end": "11:40", "room": "Sala 1 (BCC 1º Termo)", "teacher": "Prof. João Fernando Marar"},
    {"subject": "Estruturas de Dados II", "weekday": 0, "start": "08:00", "end": "11:40", "room": "Lab 3 (BCC 3º Termo)", "teacher": "Profa. Julia Silva"},
    {"subject": "Algoritmos e Programação", "weekday": 0, "start": "14:00", "end": "17:40", "room": "Lab 1 (BCC 1º Termo)", "teacher": "Profa. Simone Milani"},
    {"subject": "Engenharia de Software", "weekday": 0, "start": "14:00", "end": "17:40", "room": "Sala 2 (BCC 5º Termo)", "teacher": "Prof. Carlos Reis"},
    {"subject": "Ética e Computação", "weekday": 0, "start": "19:00", "end": "22:00", "room": "Sala 3 (BCC 7º Termo)", "teacher": "Profa. Ana Santos"},

    # Terça-feira (1)
    {"subject": "Geometria Analítica e Álgebra Linear", "weekday": 1, "start": "08:00", "end": "09:40", "room": "Sala 2 (BCC 1º Termo)", "teacher": "Prof. Pedro Souza"},
    {"subject": "Introdução à Computação", "weekday": 1, "start": "10:00", "end": "11:40", "room": "Sala 4 (BCC 1º Termo)", "teacher": "Profa. Ana Santos"},
    {"subject": "Sistemas Operacionais", "weekday": 1, "start": "14:00", "end": "17:40", "room": "Lab 5 (BCC 5º Termo)", "teacher": "Prof. Lucas Lima"},
    {"subject": "Redes de Computadores", "weekday": 1, "start": "14:00", "end": "17:40", "room": "Lab 2 (BCC 7º Termo)", "teacher": "Prof. Marcos Cavenaghi"},

    # Quarta-feira (2)
    {"subject": "Física Geral I", "weekday": 2, "start": "08:00", "end": "11:40", "room": "Sala 1 (BCC 1º Termo)", "teacher": "Prof. Marcos Cavenaghi"},
    {"subject": "Estrutura de Dados I", "weekday": 2, "start": "14:00", "end": "17:40", "room": "Lab 3 (BCC 3º Termo)", "teacher": "Profa. Julia Silva"},
    {"subject": "Inteligência Artificial", "weekday": 2, "start": "14:00", "end": "17:40", "room": "Lab 4 (BCC 7º Termo)", "teacher": "Prof. Fernando Garcia"},

    # Quinta-feira (3)
    {"subject": "Álgebra Linear Aplicada", "weekday": 3, "start": "08:00", "end": "11:40", "room": "Sala 2 (BCC 3º Termo)", "teacher": "Prof. Pedro Souza"},
    {"subject": "Circuitos Digitais", "weekday": 3, "start": "14:00", "end": "17:40", "room": "Lab 2 (BCC 3º Termo)", "teacher": "Prof. Ricardo Oliveira"},
    {"subject": "Banco de Dados II", "weekday": 3, "start": "19:00", "end": "21:00", "room": "Lab 1 (BCC 5º Termo)", "teacher": "Profa. Sandra Racca"},

    # Sexta-feira (4)
    {"subject": "Cálculo Diferencial e Integral II", "weekday": 4, "start": "08:00", "end": "11:40", "room": "Sala 1 (BCC 3º Termo)", "teacher": "Prof. João Fernando Marar"},
    {"subject": "Banco de Dados I", "weekday": 4, "start": "14:00", "end": "17:40", "room": "Lab 1 (BCC 3º Termo)", "teacher": "Profa. Sandra Racca"},
    {"subject": "Compiladores", "weekday": 4, "start": "14:00", "end": "17:40", "room": "Sala 3 (BCC 5º Termo)", "teacher": "Prof. Roberto Mendes"},
]

def scrape_unesp_rss():
    """Scrape Jornal da Unesp RSS and populate the SQLite database."""
    feed_url = "https://jornal.unesp.br/feed/"
    print(f"Fetching RSS feed from: {feed_url}")
    try:
        req = urllib.request.Request(
            feed_url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        count = 0
        for item in root.findall(".//item"):
            title = item.find("title").text if item.find("title") is not None else ""
            link = item.find("link").text if item.find("link") is not None else ""
            pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
            categories = [cat.text for cat in item.findall("category") if cat.text]
            desc_elem = item.find("description")
            description = desc_elem.text if desc_elem is not None else ""
            
            # Identify if it is an academic event/agenda item
            is_event = False
            cats_lower = [c.lower() for c in categories]
            if any(term in cats_lower for term in ["acontece", "eventos", "oportunidades", "agenda"]):
                is_event = True
                
            category_str = ", ".join(categories) if categories else "Notícias"
            
            save_news_event(
                title=title,
                link=link,
                pub_date=pub_date,
                category=category_str,
                is_event=is_event
            )
            count += 1
        print(f"Successfully processed {count} feed items.")
    except Exception as e:
        print(f"Failed to scrape RSS feed: {e}", file=sys.stderr)

def main():
    print("=== Running UNESP SQLite Scraper/Seeder ===")
    
    # 1. Initialize tables
    init_db()
    
    # 2. Seed/Scrape Professors list
    print("Updating professors database...")
    for p in PROFESSORS_DATA:
        save_professor(
            name=p["name"],
            room=p["room"],
            email=p["email"],
            department=p["dept"]
        )
    print(f"Registered {len(PROFESSORS_DATA)} professors.")

    # 3. Seed Class Schedules
    print("Updating weekly class schedules...")
    clear_schedules()
    for s in SCHEDULES_DATA:
        save_schedule(
            subject=s["subject"],
            weekday=s["weekday"],
            start_time=s["start"],
            end_time=s["end"],
            room=s["room"],
            teacher_name=s["teacher"]
        )
    print(f"Registered {len(SCHEDULES_DATA)} weekly class schedule slots.")

    # 4. Scrape real-time news/events from RSS
    scrape_unesp_rss()
    
    print("=== Scraping and seeding complete! ===")

if __name__ == "__main__":
    main()
