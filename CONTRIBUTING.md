# 🤝 Contributing to ShortlyBot

Thank you for your interest in contributing to ShortlyBot! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Issue Guidelines](#issue-guidelines)
- [Pull Request Guidelines](#pull-request-guidelines)

## 📜 Code of Conduct

This project follows a code of conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/shortlyBot.git
   cd shortlyBot
   ```
3. **Add the upstream repository**:
   ```bash
   git remote add upstream https://github.com/dmitryvoronkov/shortlyBot.git
   ```

## 🛠️ Development Setup

### Prerequisites

- Python 3.13+
- Docker and Docker Compose
- Git

### Local Development

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp env.example .env
   # Edit .env and add your TELEGRAM_BOT_TOKEN
   ```

4. **Start RabbitMQ for development**:
   ```bash
   ./scripts/dev.sh
   # or
   docker-compose -f docker-compose.dev.yml up -d
   ```

5. **Run the bot locally**:
   ```bash
   python main.py
   ```

### Docker Development

1. **Build and run with Docker**:
   ```bash
   docker-compose up -d --build
   ```

2. **View logs**:
   ```bash
   docker-compose logs -f bot
   ```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=providers --cov=analytics --cov=handlers --cov=commands --cov=localization --cov-report=term-missing

# Run specific test file
python -m pytest tests/test_providers.py -v

# Run specific test
python -m pytest tests/test_providers.py::TestInstagramProvider::test_valid_urls -v
```

### Test Coverage

We maintain high test coverage. Before submitting a PR, ensure:
- All tests pass
- New code is covered by tests
- Coverage doesn't decrease significantly

### Writing Tests

- Follow the existing test patterns
- Use descriptive test names
- Mock external dependencies
- Test both success and failure cases

## 📝 Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-vimeo-support`
- `fix/instagram-download-issue`
- `docs/update-readme`
- `refactor/cleanup-providers`

### Commit Messages

Follow conventional commits:
- `feat: add Vimeo platform support`
- `fix: resolve Instagram download timeout`
- `docs: update installation instructions`
- `test: add tests for new provider`
- `refactor: simplify provider interface`

### Code Style

- Follow PEP 8
- Use type hints where appropriate
- Add docstrings for functions and classes
- Keep functions small and focused
- Use meaningful variable names

## 🔄 Submitting Changes

### Pull Request Process

1. **Create a feature branch** from `main`:
   ```bash
   git checkout main
   git pull upstream main
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and commit them:
   ```bash
   git add .
   git commit -m "feat: add your feature"
   ```

3. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create a Pull Request** on GitHub

### Pull Request Guidelines

- Use the provided PR template
- Link related issues
- Ensure all CI checks pass
- Request review from maintainers
- Keep PRs focused and small when possible

## 🐛 Issue Guidelines

### Bug Reports

Use the bug report template and include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Relevant logs

### Feature Requests

Use the feature request template and include:
- Clear description of the feature
- Use case and motivation
- Proposed implementation (if any)
- Platform support requirements

### Platform Support Requests

Use the platform support template and include:
- Platform information
- Example URLs
- Technical details
- yt-dlp support status

## 🏗️ Architecture

### Project Structure

```
shortlyBot/
├── providers/          # Video platform providers
├── handlers/           # Request handlers
├── commands/           # Bot commands
├── analytics/          # Statistics and analytics
├── localization/       # Multi-language support
├── tests/              # Test suite
├── scripts/            # Utility scripts
└── docs/               # Documentation
```

### Key Components

- **Providers**: Handle different video platforms
- **Handlers**: Process user requests
- **Analytics**: Collect usage statistics
- **Localization**: Multi-language support

## 🔧 Adding New Platforms

1. **Create a new provider** in `providers/`
2. **Implement required methods**:
   - `is_valid_url()`
   - `extract_id()`
   - `_build_url()`
   - `download_video()`
3. **Add to downloader** in `handlers/downloader.py`
4. **Update documentation**
5. **Add tests**
6. **Update localization**

## 🌍 Localization

### Adding Translations

1. **Add new keys** to `localization/translations.py`
2. **Provide translations** for both Russian and English
3. **Use in code** with `t('key', user=user)`
4. **Test with different languages**

### Language Mapping

- Slavic languages → Russian
- Other languages → English
- Unknown languages → English (default)

## 📊 Analytics

### Adding New Metrics

1. **Define event types** in `analytics/stats_collector.py`
2. **Send events** using the collector
3. **Update RabbitMQ queues** if needed
4. **Document the new metrics**

## 🐳 Docker

### Updating Docker Configuration

1. **Modify Dockerfile** if needed
2. **Update docker-compose.yml**
3. **Test locally** with Docker
4. **Update documentation**

## 📚 Documentation

### Updating Documentation

- Keep README.md up to date
- Update API documentation
- Add examples for new features
- Update deployment instructions

## 🚨 Security

### Security Guidelines

- Never commit secrets or tokens
- Use environment variables for sensitive data
- Validate all user inputs
- Follow security best practices
- Report security issues privately

## 🎯 Release Process

1. **Update version** in relevant files
2. **Update CHANGELOG.md**
3. **Create release tag**
4. **GitHub Actions** will handle the rest

## ❓ Getting Help

- Check existing issues and PRs
- Join discussions in issues
- Contact maintainers for questions
- Read the documentation

## 🏆 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- GitHub contributors page

Thank you for contributing to ShortlyBot! 🎉
