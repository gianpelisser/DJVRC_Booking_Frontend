# DJ VRC Booking — FRONTEND

Plataforma para contratação de DJs virtuais para eventos no VRChat e metaverso.

## Stack

| Camada | Tecnologia |
|---|---|
| API | Python 3.12 + Flask |
| ORM | SQLAlchemy + Flask-Migrate |
| Auth | JWT (access + refresh) + Discord OAuth |
| Banco | MySQL 8 |
| Cache / Filas | Redis + Celery |
| Servidor | Gunicorn + Nginx |
| Container | Docker + Docker Compose |

---

## Estrutura

```
DJVRC_Booking_Frontend/
├── app/
│   ├── __pycache__/
│   │   └── __init__.cpython-312.pyc
│   ├── admin/
│   │   ├── __pycache__/
│   │   │   ├── __init__.cpython-312.pyc
│   │   │   └── routes.cpython-312.pyc
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── auth/
│   │   ├── __pycache__/
│   │   │   ├── __init__.cpython-312.pyc
│   │   │   └── routes.cpython-312.pyc
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── bookings/
│   │   ├── __pycache__/
│   │   │   ├── __init__.cpython-312.pyc
│   │   │   └── routes.cpython-312.pyc
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── core/
│   │   ├── __pycache__/
│   │   │   ├── __init__.cpython-312.pyc
│   │   │   ├── api.cpython-312.pyc
│   │   │   ├── config.cpython-312.pyc
│   │   │   ├── context.cpython-312.pyc
│   │   │   └── decorators.cpython-312.pyc
│   │   ├── __init__.py
│   │   ├── api.py
│   │   ├── config.py
│   │   ├── context.py
│   │   └── decorators.py
│   ├── djs/
│   │   ├── __pycache__/
│   │   │   ├── __init__.cpython-312.pyc
│   │   │   └── routes.cpython-312.pyc
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── events/
│   │   ├── __pycache__/
│   │   │   ├── __init__.cpython-312.pyc
│   │   │   └── routes.cpython-312.pyc
│   │   ├── __init__.py
│   │   └── routes.py
│   └── __init__.py
├── static/
│   ├── css/
│   │   └── main.css
│   ├── js/
│       └── main.js
├── templates/
│   ├── admin/
│   │   ├── audit_logs.html
│   │   ├── dashboard.html
│   │   ├── djs.html
│   │   └── users.html
│   ├── auth/
│   │   ├── forgot_password.html
│   │   ├── login.html
│   │   ├── register.html
│   │   └── reset_password.html
│   ├── bookings/
│   │   ├── detail.html
│   │   ├── list.html
│   │   └── new.html
│   ├── djs/
│   │   ├── availability.html
│   │   ├── edit_profile.html
│   │   ├── list.html
│   │   └── profile.html
│   ├── errors/
│   │   ├── 403.html
│   │   ├── 404.html
│   │   └── 500.html
│   ├── events/
│   │   ├── detail.html
│   │   └── list.html
│   ├── partials/
│   │   └── dj_card.html
│   ├── base.html
│   └── index.html
├── Dockerfile
├── README.md
├── requirements.txt
└── run.py
```

---
