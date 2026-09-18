# Build Tools (Maven, Python, C, NodeJS) Cheat Sheet

> Essential compilation, dependency packaging, linting, and artifact building commands across Maven, Python, C/Make, and Node.js.

| Command | Description & AI Explanation | Category / Tags |
| :--- | :--- | :--- |
| `mvn clean package -DskipTests=true` | Cleans target output directory and compiles Java sources into JAR/WAR package while skipping unit test execution to accelerate builds. | Maven, Java |
| `mvn dependency:tree -Dverbose` | Outputs a complete visual tree of project dependencies and transitive resolutions, vital for diagnosing dependency version conflicts (JAR hell). | Maven, Troubleshooting |
| `mvn versions:display-dependency-updates` | Scans pom.xml dependencies against remote Maven Central / Nexus to identify available newer releases and security updates. | Maven, Security |
| `mvn verify sonar:sonar -Dsonar.host.url=http://sonar:9000` | Executes verification phase and uploads code coverage reports and static analysis metrics to SonarQube quality gate server. | Maven, CI/CD, SonarQube |
| `pip install --no-cache-dir -r requirements.txt` | Installs Python packages from requirements file while disabling pip's wheel cache, optimizing Docker container layer sizes. | Python, Pip |
| `pip-audit -r requirements.txt` | Audits installed Python dependencies against the PyPI Advisory Database and Open Source Vulnerabilities (OSV) database for known CVEs. | Python, Security |
| `python -m venv .venv && source .venv/bin/activate` | Creates and activates an isolated virtual environment to prevent package pollution across host OS and system Python installations. | Python, Virtualenv |
| `pytest -v --cov=app --cov-report=xml` | Runs pytest suite with verbose test name output and generates an XML code coverage report suitable for CI/CD pipeline integration. | Python, Testing |
| `flake8 app/ --max-line-length=120 --statistics` | Lints Python code against PEP 8 style guidelines, reporting error counts categorized by rule code. | Python, Code Quality |
| `gcc -Wall -Wextra -O2 -g main.c -o myapp` | Compiles C program with all standard warnings enabled (-Wall -Wextra), level 2 optimization (-O2), and debug symbols (-g) for gdb diagnostics. | C, Compilation |
| `make -j$(nproc)` | Runs Makefile targets utilizing all available CPU cores in parallel to dramatically shorten compilation times on large C/C++ codebases. | C, Make, Performance |
| `valgrind --leak-check=full --show-leak-kinds=all ./myapp` | Executes compiled C binary under Valgrind's memory instrumentation engine to pinpoint memory leaks, buffer overruns, and uninitialized reads. | C, Memory Diagnostics |
| `npm ci --prefer-offline` | Installs dependencies strictly matching package-lock.json without modifying it. Faster and deterministic for CI/CD pipelines compared to 'npm install'. | Node.js, NPM |
| `npm audit fix --production` | Scans Node.js dependencies for security vulnerabilities and automatically patches non-breaking security updates for production packages. | Node.js, Security |
| `npm run build` | Compiles, bundles, and minifies frontend React, Vue, or Angular applications into static HTML/CSS/JS assets inside /dist or /build. | Node.js, Bundling |
| `yarn build --frozen-lockfile` | Runs production build ensuring yarn.lock is strictly respected and throws an error if any lockfile discrepancies exist. | Node.js, Yarn |
| `npx depcheck` | Analyzes Node.js project to identify unused dependencies declared in package.json and missing dependencies imported in source files. | Node.js, Optimization |
| `tsc --noEmit --strict` | Runs TypeScript type-checker across the entire codebase without emitting JavaScript output files, catching type mismatches during CI gates. | Node.js, TypeScript |
