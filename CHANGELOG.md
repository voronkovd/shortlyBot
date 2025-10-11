# Changelog

All notable changes to ShortlyBot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions CI/CD pipeline
- Automated dependency updates with Dependabot
- CodeQL security analysis
- Comprehensive test coverage (84 tests)
- Multi-language support (Russian/English)
- Docker containerization
- RabbitMQ analytics system
- Automated release process

### Changed
- Improved error handling and timeouts
- Enhanced logging and monitoring
- Better user experience with localized messages

### Fixed
- Import path issues in providers
- Timeout handling for video downloads
- Message deletion after successful video send

## [1.0.0] - 2024-01-XX

### Added
- Initial release of ShortlyBot
- Support for Instagram (posts, reels, IGTV)
- Support for TikTok videos
- Support for YouTube Shorts
- Support for Likee videos
- Support for Facebook Reels
- Support for RuTube videos and shorts
- Telegram Bot API integration
- yt-dlp integration for video downloading
- Automatic platform detection
- Video processing with timeouts
- Original message deletion after successful download
- Comprehensive error handling
- Docker support with docker-compose
- RabbitMQ integration for analytics
- Statistics collection for users and providers
- Multi-language support with automatic detection
- Extensive test suite with 84 tests
- Complete documentation

### Technical Details
- Python 3.13+ support
- Asynchronous processing with asyncio
- Docker containerization
- Health checks and monitoring
- Automated CI/CD with GitHub Actions
- Security scanning with CodeQL
- Dependency management with Dependabot
- Code coverage reporting
- Multi-platform testing

### Supported Platforms
- Instagram: Posts, Reels, IGTV
- TikTok: Short videos
- YouTube: Shorts only
- Likee: Short videos
- Facebook: Reels
- RuTube: Videos and Shorts

### Features
- Automatic video platform detection
- Fast video downloading with optimized settings
- User-friendly error messages
- Multi-language interface (Russian/English)
- Statistics collection and analytics
- Docker deployment ready
- Comprehensive test coverage
- Security best practices
- Automated dependency updates
