# Contributing to RevenueShield

Thank you for your interest in contributing to **RevenueShield**! We welcome community contributions, bug reports, and enhancements.

## Code of Conduct
Please review and adhere to our [Code of Conduct](CODE_OF_CONDUCT.md) in all community interactions.

## Development Workflow

1. **Fork the Repository** on GitHub.
2. **Clone your fork locally**:
   ```bash
   git clone https://github.com/roxxerdk/RevenueShield.git
   cd RevenueShield
   ```
3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Or `.\venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   ```
4. **Create a feature branch**:
   ```bash
   git checkout -b feat/your-feature-name
   ```
5. **Follow Conventional Commits**:
   - `feat: add new recovery heuristic`
   - `fix: correct expected value edge case`
   - `docs: update deployment guidelines`
   - `test: add webhook signature edge case tests`
6. **Run the Test Suite**:
   ```bash
   pytest tests/ -v
   ```
7. **Submit a Pull Request** against the `main` branch with a clear description of your changes.
