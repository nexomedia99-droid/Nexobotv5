# NexoBot - Comprehensive Telegram Bot for NexoBuzz Community

## Overview

NexoBot is a comprehensive Telegram bot designed for the NexoBuzz community platform, facilitating job applications for buzzers and influencers. The bot provides multi-step user registration, job management, gamification through points and badges, AI assistance, social media promotion features, and administrative tools. It serves as a central hub for community members to discover work opportunities, interact with AI, and participate in a point-based reward system.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Language & Framework**: Python-based Telegram bot using python-telegram-bot library
- **Database**: SQLite with context manager pattern for connection handling
- **Architecture Pattern**: Modular design with separate files for different functional areas (admin, AI, jobs, registration, etc.)
- **State Management**: Conversation handlers for multi-step user interactions
- **Error Handling**: Centralized error handling with logging and user-friendly error messages

### Database Design
- **Users Table**: Stores user profiles with referral system, points, and payment information
- **Jobs Table**: Manages job postings with status tracking
- **Applicants Table**: Links users to job applications
- **Achievements Table**: Badge system for gamification
- **Promotions Table**: Social media boost tracking
- **Group Messages**: AI conversation context storage

### Authentication & Authorization
- **Role-based Access**: Decorator-based admin authentication using OWNER_ID
- **User Registration**: Multi-step registration process with data validation
- **Rate Limiting**: Basic rate limiting to prevent spam

### AI Integration
- **Google Gemini 2.5 Flash**: AI chatbot with context preservation
- **Interactive Chat**: Private chat mode with session management
- **Group Monitoring**: Message tracking for summaries and activity rewards

### Job Management System
- **Job Lifecycle**: Creation, application tracking, status updates, and deletion
- **Multi-topic Posting**: Separate channels for buzzer and influencer jobs
- **Application Tracking**: User application history and status monitoring

### Gamification System
- **Points System**: Activity-based point rewards (job applications, referrals, group activity)
- **Badge System**: Achievement badges with automatic awarding
- **Leaderboard**: Ranking system for community engagement
- **Referral Program**: Multi-level referral rewards with validation

### Social Media Promotion
- **Boost System**: Two-tier promotion system (standard and premium)
- **Auto-deletion**: Time-based promotion cleanup
- **Analytics**: Click tracking and engagement monitoring

## External Dependencies

### Third-party Services
- **Telegram Bot API**: Core bot functionality and messaging
- **Google Gemini AI**: AI assistant and conversation handling
- **SQLite**: Local database storage

### Python Libraries
- **python-telegram-bot**: Telegram bot framework
- **google-generativeai**: Google Gemini AI integration
- **Flask**: Web dashboard and API endpoints
- **sqlite3**: Database operations

### External Integrations
- **Telegram Groups**: Multi-topic message posting for different job types
- **Web Dashboard**: Real-time monitoring and analytics interface
- **UptimeRobot**: Health check endpoints for monitoring
- **Social Media Platforms**: URL validation for promotion features

### Environment Configuration
- **BOT_TOKEN**: Telegram bot authentication
- **GEMINI_API_KEY**: Google AI service authentication
- **OWNER_ID**: Admin user identification
- **GROUP_ID**: Target Telegram group for posting
- **Topic IDs**: Message threading for different content types