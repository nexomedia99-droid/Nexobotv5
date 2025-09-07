
# NexoBot - Comprehensive Telegram Bot for NexoBuzz Community

![Python](https://img.shields.io/badge/python-v3.11+-blue.svg)
![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-v20.7-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

NexoBot adalah bot Telegram yang komprehensif untuk platform komunitas NexoBuzz. Bot ini memfasilitasi aplikasi pekerjaan untuk buzzer dan influencer, mengelola registrasi pengguna, menyediakan asisten AI, sistem boost social media, dan memelihara leaderboard komunitas dengan fitur gamifikasi.

## 🚀 Fitur Utama

### 👥 Manajemen Pengguna
- **Registrasi Multi-step**: Proses pendaftaran lengkap dengan validasi data
- **Edit Profil**: Pengguna dapat mengubah informasi pribadi mereka
- **Sistem Referral**: Program rujukan dengan reward points
- **Validasi Data**: Validasi nomor telepon dan informasi pembayaran

### 💼 Sistem Job & Aplikasi
- **Posting Job**: Admin dapat memposting lowongan buzzer/influencer
- **Aplikasi Job**: Pengguna dapat melamar pekerjaan yang tersedia
- **Tracking Aplikasi**: Monitoring status aplikasi dan pelamar
- **Management Job**: Update dan reset job oleh admin
- **Notifikasi Private**: Semua notifikasi job dikirim via private chat

### 🎮 Gamifikasi & Points
- **Sistem Points**: Earn points melalui berbagai aktivitas
- **Leaderboard**: Ranking pengguna berdasarkan points
- **Badge System**: Achievement badges untuk milestone tertentu
- **Activity Rewards**: Points untuk partisipasi grup dan interaksi

### 📢 Fitur Boost Social Media
- **Boost Standar**: Post boost sosial media dengan deskripsi action
- **Boost Special**: Post boost premium dengan pin dan deskripsi (biaya lebih tinggi)
- **Auto-delete**: Boost otomatis terhapus setelah 24 jam
- **Tracking Engagement**: Monitor yang mengklik boost

### 🤖 AI Assistant
- **Google Gemini Integration**: AI chatbot dengan Gemini 2.5 Flash
- **Context Preservation**: Menyimpan konteks percakapan
- **Group Summary**: Rangkuman aktivitas grup
- **Interactive Mode**: Mode chat interaktif di private message
- **AI Points**: Earn points dengan menggunakan AI

### 📊 Dashboard & Monitoring
- **Real-time Analytics**: Monitor aktivitas bot secara real-time
- **Health Check**: Endpoint kesehatan untuk monitoring
- **Error Handling**: Penanganan error yang robust
- **Logging**: Comprehensive logging untuk debugging

### 🔐 Security & Admin
- **Role-based Access**: Kontrol akses berbasis peran
- **Admin Commands**: Command khusus untuk admin
- **Input Validation**: Sanitasi input untuk mencegah serangan
- **Security Decorators**: Decorator-based authentication

## 🛠️ Teknologi Yang Digunakan

- **Python 3.11+**: Bahasa pemrograman utama
- **python-telegram-bot 20.7**: Framework Telegram bot
- **Google Gemini AI**: AI chatbot integration
- **SQLite**: Database embedded untuk penyimpanan data
- **Flask**: Framework untuk health check dan monitoring

## 📋 Prasyarat

- Python 3.11 atau lebih tinggi
- Telegram Bot Token (dari @BotFather)
- Google Gemini API Key
- Akses ke grup Telegram untuk deploy

## ⚙️ Instalasi & Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd nexobot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Set environment variables di Replit Secrets:

```
BOT_TOKEN = "your_telegram_bot_token"
GEMINI_API_KEY = "your_gemini_api_key"
OWNER_ID = "your_telegram_user_id"
GROUP_ID = "your_telegram_group_id"
GEMINI_MODEL = "gemini-2.5-flash"
```

### 4. Jalankan Bot
```bash
python main.py
```

Bot akan berjalan dengan health check di port 8080.

## 📖 Dokumentasi Command

### User Commands
- `/start` - Memulai bot dan menampilkan menu utama
- `/register` - Mendaftar sebagai member (private chat only)
- `/myinfo` - Lihat informasi profil pribadi
- `/editinfo` - Edit informasi profil
- `/myreferral` - Lihat daftar referral
- `/points` - Cek saldo points dan cara mendapatkannya
- `/leaderboard` - Lihat ranking komunitas
- `/listjob` - Lihat daftar job tersedia
- `/infojob <id>` - Detail informasi job
- `/boost <deskripsi>` - Boost sosial media dengan deskripsi action
- `/boost_special <deskripsi>` - Boost sosial media premium dengan pin
- `/help` - Bantuan penggunaan bot

### AI Commands
- `/startai` - Aktifkan mode AI interaktif (private only)
- `/stopai` - Nonaktifkan mode AI
- `/ai <text>` - Chat dengan AI (grup)
- `/summary` - Rangkuman aktivitas grup

### Admin Commands
- `/listmember [page]` - Daftar semua member dengan pagination
- `/memberinfo <username>` - Info detail member
- `/paymentinfo <username>` - Info pembayaran member
- `/delete <username>` - Hapus member
- `/addpoint <username> <amount>` - Tambah points
- `/resetpoint <username>` - Reset points ke 0
- `/addbadge <username> <badge>` - Tambah badge
- `/postjob` - Post job baru
- `/updatejob <id> <status>` - Update status job
- `/resetjob <id>` - Reset job
- `/pelamarjob <id>` - Lihat pelamar job

## 🏗️ Struktur Project

```
nexobot/
├── main.py              # Entry point aplikasi
├── db.py                # Database operations
├── utils.py             # Utility functions
├── start.py             # Start command & menu
├── register.py          # User registration system
├── boost.py             # Social media boost system
├── jobs.py              # Job management system
├── ai.py                # AI chatbot integration
├── admin.py             # Admin commands
├── leaderboard.py       # Points & ranking system
├── help.py              # Help system
├── security.py          # Security utilities
├── error_handler.py     # Error handling
├── validators.py        # Input validation
├── decorators.py        # Function decorators
├── requirements.txt     # Python dependencies
├── pyproject.toml       # Project configuration
└── database.db          # SQLite database
```

## 🔧 Konfigurasi

### Database Schema
Bot menggunakan SQLite dengan tabel-tabel:
- `users` - Data pengguna dan profil
- `jobs` - Informasi lowongan pekerjaan
- `applicants` - Aplikasi job dari pengguna
- `badges` - System achievement badges
- `promotions` - Data boost social media
- `ai_sessions` - Session AI chat
- `group_messages` - Pesan grup untuk summary

### Topics & Groups
Bot dikonfigurasi untuk bekerja dengan topic-topic tertentu:
- `BUZZER_TOPIC_ID = 3` - Topic untuk job buzzer
- `INFLUENCER_TOPIC_ID = 4` - Topic untuk job influencer
- `PAYMENT_TOPIC_ID = 5` - Topic untuk konfirmasi payment
- `BOOST_TOPIC_ID = 11` - Topic untuk boost social media

## 🚀 Deployment

### Replit (Recommended)
1. Fork repository ke Replit
2. Set environment variables di Secrets
3. Klik tombol Run
4. Bot akan berjalan dengan health check endpoint

### Manual Deployment
1. Setup server dengan Python 3.11+
2. Install dependencies
3. Set environment variables
4. Jalankan dengan `python main.py`

## 📊 Monitoring & Health Checks

### Health Endpoints
- **Health**: Port 8080 untuk monitoring
- **Bot Status**: Logs tersedia di console

### Points System
- Apply job: +2 poin
- Aktif di grup (chat): +1 poin/hari
- Referral berhasil: +25 poin
- Gunakan AI di grup: +1 poin
- Summary grup: +2 poin
- Boost sosmed: +1 poin

## 🔒 Keamanan

- Input sanitization untuk mencegah injection
- Role-based access control dengan decorators
- Rate limiting untuk AI requests
- Secure environment variable handling
- Private chat only untuk data sensitif
- Admin authentication dengan OWNER_ID

## 🤝 Contributing

1. Fork repository
2. Buat feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push ke branch (`git push origin feature/amazing-feature`)
5. Buat Pull Request

## 📝 License

Project ini menggunakan MIT License.

## 🆘 Support

Untuk bantuan dan support:
- Hubungi admin bot melalui Telegram
- Gunakan command `/help` untuk panduan
- Check logs untuk troubleshooting

## 🔄 Changelog

### v3.0.0
- Added social media boost system
- Enhanced AI integration with Google Gemini
- Improved error handling and security
- Better database schema and validation
- Updated command structure and help system
- Added comprehensive logging and monitoring

---

**NexoBot** - Powering NexoBuzz Community 🚀
