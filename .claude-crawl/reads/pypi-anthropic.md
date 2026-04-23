[Skip to main content](https://pypi.org/project/anthropic/#content) Switch to mobile version

Join us in Long Beach, CA starting May 13, 2026. Grab your ticket and discounted hotel today before they’re gone!
[REGISTER FOR PYCON US!](https://us.pycon.org/2026/attend/information/)

Search PyPISearch

# anthropic 0.96.0

pip install anthropicCopy PIP instructions

[Latest version](https://pypi.org/project/anthropic/)

Released: Apr 16, 2026

The official Python library for the anthropic API

### Navigation

### Verified details

_These details have been [verified by PyPI](https://docs.pypi.org/project_metadata/#verified-details)_

###### Owner

- [Anthropic, PBC.](https://pypi.org/org/Anthropic/)

### Unverified details

_These details have **not** been verified by PyPI_

###### Project links

- [Homepage](https://github.com/anthropics/anthropic-sdk-python)
- [Repository](https://github.com/anthropics/anthropic-sdk-python)

###### Meta

- **License:** MIT License (MIT)

- **Author:** [Anthropic](mailto:support@anthropic.com)
- **Requires:** Python >=3.9

- **Provides-Extra:**`aiohttp`
, `aws`
, `bedrock`
, `mcp`
, `vertex`

###### Classifiers

- **Intended Audience**  - [Developers](https://pypi.org/search/?c=Intended+Audience+%3A%3A+Developers)
- **License**  - [OSI Approved :: MIT License](https://pypi.org/search/?c=License+%3A%3A+OSI+Approved+%3A%3A+MIT+License)
- **Operating System**  - [MacOS](https://pypi.org/search/?c=Operating+System+%3A%3A+MacOS)
  - [Microsoft :: Windows](https://pypi.org/search/?c=Operating+System+%3A%3A+Microsoft+%3A%3A+Windows)
  - [OS Independent](https://pypi.org/search/?c=Operating+System+%3A%3A+OS+Independent)
  - [POSIX](https://pypi.org/search/?c=Operating+System+%3A%3A+POSIX)
  - [POSIX :: Linux](https://pypi.org/search/?c=Operating+System+%3A%3A+POSIX+%3A%3A+Linux)
- **Programming Language**  - [Python :: 3.9](https://pypi.org/search/?c=Programming+Language+%3A%3A+Python+%3A%3A+3.9)
  - [Python :: 3.10](https://pypi.org/search/?c=Programming+Language+%3A%3A+Python+%3A%3A+3.10)
  - [Python :: 3.11](https://pypi.org/search/?c=Programming+Language+%3A%3A+Python+%3A%3A+3.11)
  - [Python :: 3.12](https://pypi.org/search/?c=Programming+Language+%3A%3A+Python+%3A%3A+3.12)
  - [Python :: 3.13](https://pypi.org/search/?c=Programming+Language+%3A%3A+Python+%3A%3A+3.13)
  - [Python :: 3.14](https://pypi.org/search/?c=Programming+Language+%3A%3A+Python+%3A%3A+3.14)
- **Topic**  - [Software Development :: Libraries :: Python Modules](https://pypi.org/search/?c=Topic+%3A%3A+Software+Development+%3A%3A+Libraries+%3A%3A+Python+Modules)
- **Typing**  - [Typed](https://pypi.org/search/?c=Typing+%3A%3A+Typed)

[Report project as malware](https://pypi.org/project/anthropic/submit-malware-report/)

## Project description

# Claude SDK for Python

[![PyPI version](https://pypi-camo.freetls.fastly.net/c879c304919b56da97463a4f482eb1b7aa69e588/68747470733a2f2f696d672e736869656c64732e696f2f707970692f762f616e7468726f7069632e737667)](https://pypi.org/project/anthropic/)

The Claude SDK for Python provides access to the [Claude API](https://docs.anthropic.com/en/api/) from Python applications.

## Documentation

Full documentation is available at **[platform.claude.com/docs/en/api/sdks/python](https://platform.claude.com/docs/en/api/sdks/python)**.

## Installation

```
pip install anthropic
```

## Getting started

```
import os
from anthropic import Anthropic

client = Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),  # This is the default and can be omitted
)

message = client.messages.create(
    max_tokens=1024,
    messages=[\
        {\
            "role": "user",\
            "content": "Hello, Claude",\
        }\
    ],
    model="claude-opus-4-6",
)
print(message.content)
```

## Requirements

Python 3.9+

## Contributing

See [CONTRIBUTING.md](https://github.com/anthropics/anthropic-sdk-python/tree/main/CONTRIBUTING.md).

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/anthropics/anthropic-sdk-python/tree/main/LICENSE) file for details.

## Project details

### Verified details

_These details have been [verified by PyPI](https://docs.pypi.org/project_metadata/#verified-details)_

###### Owner

- [Anthropic, PBC.](https://pypi.org/org/Anthropic/)

### Unverified details

_These details have **not** been verified by PyPI_

###### Project links

- [Homepage](https://github.com/anthropics/anthropic-sdk-python)
- [Repository](https://github.com/anthropics/anthropic-sdk-python)

###### Meta

- **License:** MIT License (MIT)

- **Author:** [Anthropic](mailto:support@anthropic.com)
- **Requires:** Python >=3.9

- **Provides-Extra:**`aiohttp`
, `aws`
, `bedrock`
, `mcp`
, `vertex`

###### Classifiers

- **Intended Audience**  - [Developers](https://pypi.org/search/?c=Intended+Audience+%3A%3A+Developers)
- **License**  - [OSI Approved :: MIT License](https://pypi.org/search/?c=License+%3A%3A+OSI+Approved+%3A%3A+MIT+License)
- **Operating System**  - [MacOS](https://pypi.org/search/?c=Operating+System+%3A%3A+MacOS)
  - [Microsoft :: Windows](https://pypi.org/search/?c=Operating+System+%3A%3A+Microsoft+%3A%3A+Windows)
  - [OS Independent](https://pypi.org/search/?c=Operating+System+%3A%3A+OS+Independent)
  - [POSIX](https://pypi.org/search/?c=Operating+System+%3A%3A+POSIX)
  - [POSIX :: Linux](https://pypi.org/search/?c=Operating+System+%3A%3A+POSIX+%3A%3A+Linux)
- **Programming Language**  - [Python :: 3.9](https://pypi.org/search/?c=Programming+Language+%3A%3A+Python+%3A%3A+3.9)
  - [Python :: 3.10](https://pypi.org/search/?c=Programming+Language+%3A%3A+Python+%3A%3A+3.10)
  - [Python :: 3.11](https://pypi.org/search/?c=Programming+Language+%3A%3A+Python+%3A%3A+3.11)
  - [Python :: 3.12](https://pypi.org/search/?c=Programming+Language+%3A%3A+Python+%3A%3A+3.12)
  - [Python :: 3.13](https://pypi.org/search/?c=Programming+Language+%3A%3A+Python+%3A%3A+3.13)
  - [Python :: 3.14](https://pypi.org/search/?c=Programming+Language+%3A%3A+Python+%3A%3A+3.14)
- **Topic**  - [Software Development :: Libraries :: Python Modules](https://pypi.org/search/?c=Topic+%3A%3A+Software+Development+%3A%3A+Libraries+%3A%3A+Python+Modules)
- **Typing**  - [Typed](https://pypi.org/search/?c=Typing+%3A%3A+Typed)

## Release history[Release notifications](https://pypi.org/help/\#project-release-notifications) \|  [RSS feed](https://pypi.org/rss/project/anthropic/releases.xml)

This version

![](https://pypi.org/static/images/blue-cube.572a5bfb.svg)

[0.96.0\\
\\
\\
Apr 16, 2026](https://pypi.org/project/anthropic/0.96.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.95.0\\
\\
\\
Apr 14, 2026](https://pypi.org/project/anthropic/0.95.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.94.1\\
\\
\\
Apr 13, 2026](https://pypi.org/project/anthropic/0.94.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.94.0\\
\\
\\
Apr 10, 2026](https://pypi.org/project/anthropic/0.94.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.93.0\\
\\
\\
Apr 9, 2026](https://pypi.org/project/anthropic/0.93.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.92.0\\
\\
\\
Apr 8, 2026](https://pypi.org/project/anthropic/0.92.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.91.0\\
\\
\\
Apr 7, 2026](https://pypi.org/project/anthropic/0.91.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.90.0\\
\\
\\
Apr 7, 2026](https://pypi.org/project/anthropic/0.90.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.89.0\\
\\
\\
Apr 3, 2026](https://pypi.org/project/anthropic/0.89.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.88.0\\
\\
\\
Apr 1, 2026](https://pypi.org/project/anthropic/0.88.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.87.0\\
\\
\\
Mar 31, 2026](https://pypi.org/project/anthropic/0.87.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.86.0\\
\\
\\
Mar 18, 2026](https://pypi.org/project/anthropic/0.86.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.85.0\\
\\
\\
Mar 16, 2026](https://pypi.org/project/anthropic/0.85.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.84.0\\
\\
\\
Feb 25, 2026](https://pypi.org/project/anthropic/0.84.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.83.0\\
\\
\\
Feb 19, 2026](https://pypi.org/project/anthropic/0.83.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.82.0\\
\\
\\
Feb 18, 2026](https://pypi.org/project/anthropic/0.82.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.81.0\\
\\
\\
Feb 17, 2026](https://pypi.org/project/anthropic/0.81.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.80.0\\
\\
\\
Feb 17, 2026](https://pypi.org/project/anthropic/0.80.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.79.0\\
\\
\\
Feb 7, 2026](https://pypi.org/project/anthropic/0.79.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.78.0\\
\\
\\
Feb 5, 2026](https://pypi.org/project/anthropic/0.78.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.77.1\\
\\
\\
Feb 3, 2026](https://pypi.org/project/anthropic/0.77.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.77.0\\
\\
\\
Jan 29, 2026](https://pypi.org/project/anthropic/0.77.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.76.0\\
\\
\\
Jan 13, 2026](https://pypi.org/project/anthropic/0.76.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.75.0\\
\\
\\
Nov 24, 2025](https://pypi.org/project/anthropic/0.75.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.74.1\\
\\
\\
Nov 19, 2025](https://pypi.org/project/anthropic/0.74.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.74.0\\
\\
\\
Nov 18, 2025](https://pypi.org/project/anthropic/0.74.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.73.0\\
\\
\\
Nov 14, 2025](https://pypi.org/project/anthropic/0.73.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.72.1\\
\\
\\
Nov 11, 2025](https://pypi.org/project/anthropic/0.72.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.72.0\\
\\
\\
Oct 28, 2025](https://pypi.org/project/anthropic/0.72.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.71.1\\
\\
\\
Oct 28, 2025](https://pypi.org/project/anthropic/0.71.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.71.0\\
\\
\\
Oct 16, 2025](https://pypi.org/project/anthropic/0.71.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.70.0\\
\\
\\
Oct 15, 2025](https://pypi.org/project/anthropic/0.70.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.69.0\\
\\
\\
Sep 29, 2025](https://pypi.org/project/anthropic/0.69.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.68.2\\
\\
\\
Sep 29, 2025](https://pypi.org/project/anthropic/0.68.2/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.68.1\\
\\
\\
Sep 26, 2025](https://pypi.org/project/anthropic/0.68.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.68.0\\
\\
\\
Sep 17, 2025](https://pypi.org/project/anthropic/0.68.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.67.0\\
\\
\\
Sep 10, 2025](https://pypi.org/project/anthropic/0.67.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.66.0\\
\\
\\
Sep 3, 2025](https://pypi.org/project/anthropic/0.66.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.65.0\\
\\
\\
Sep 2, 2025](https://pypi.org/project/anthropic/0.65.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.64.0\\
\\
\\
Aug 13, 2025](https://pypi.org/project/anthropic/0.64.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.63.0\\
\\
\\
Aug 12, 2025](https://pypi.org/project/anthropic/0.63.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.62.0\\
\\
\\
Aug 8, 2025](https://pypi.org/project/anthropic/0.62.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.61.0\\
\\
\\
Aug 5, 2025](https://pypi.org/project/anthropic/0.61.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.60.0\\
\\
\\
Jul 28, 2025](https://pypi.org/project/anthropic/0.60.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.59.0\\
\\
\\
Jul 23, 2025](https://pypi.org/project/anthropic/0.59.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.58.2\\
\\
\\
Jul 18, 2025](https://pypi.org/project/anthropic/0.58.2/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.58.1\\
\\
\\
Jul 18, 2025](https://pypi.org/project/anthropic/0.58.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.58.0\\
\\
\\
Jul 18, 2025](https://pypi.org/project/anthropic/0.58.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.57.1\\
\\
\\
Jul 3, 2025](https://pypi.org/project/anthropic/0.57.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.57.0\\
\\
\\
Jul 3, 2025](https://pypi.org/project/anthropic/0.57.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.56.0\\
\\
\\
Jul 1, 2025](https://pypi.org/project/anthropic/0.56.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.55.0\\
\\
\\
Jun 23, 2025](https://pypi.org/project/anthropic/0.55.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.54.0\\
\\
\\
Jun 10, 2025](https://pypi.org/project/anthropic/0.54.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.53.0\\
\\
\\
Jun 9, 2025](https://pypi.org/project/anthropic/0.53.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.52.2\\
\\
\\
Jun 2, 2025](https://pypi.org/project/anthropic/0.52.2/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.52.1\\
\\
\\
May 28, 2025](https://pypi.org/project/anthropic/0.52.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.52.0\\
\\
\\
May 22, 2025](https://pypi.org/project/anthropic/0.52.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.51.0\\
\\
\\
May 7, 2025](https://pypi.org/project/anthropic/0.51.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.50.0\\
\\
\\
Apr 22, 2025](https://pypi.org/project/anthropic/0.50.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.49.0\\
\\
\\
Feb 28, 2025](https://pypi.org/project/anthropic/0.49.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.48.0\\
\\
\\
Feb 27, 2025](https://pypi.org/project/anthropic/0.48.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.47.2\\
\\
\\
Feb 25, 2025](https://pypi.org/project/anthropic/0.47.2/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.47.1\\
\\
\\
Feb 24, 2025](https://pypi.org/project/anthropic/0.47.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.47.0\\
\\
\\
Feb 24, 2025](https://pypi.org/project/anthropic/0.47.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.46.0\\
\\
\\
Feb 18, 2025](https://pypi.org/project/anthropic/0.46.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.45.2\\
\\
\\
Jan 27, 2025](https://pypi.org/project/anthropic/0.45.2/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.45.1\\
\\
\\
Jan 27, 2025](https://pypi.org/project/anthropic/0.45.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.45.0\\
\\
\\
Jan 23, 2025](https://pypi.org/project/anthropic/0.45.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.44.0\\
\\
\\
Jan 21, 2025](https://pypi.org/project/anthropic/0.44.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.43.1\\
\\
\\
Jan 17, 2025](https://pypi.org/project/anthropic/0.43.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.43.0\\
\\
\\
Jan 14, 2025](https://pypi.org/project/anthropic/0.43.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.42.0\\
\\
\\
Dec 17, 2024](https://pypi.org/project/anthropic/0.42.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.41.0\\
\\
\\
Dec 17, 2024](https://pypi.org/project/anthropic/0.41.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.40.0\\
\\
\\
Nov 28, 2024](https://pypi.org/project/anthropic/0.40.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.39.0\\
\\
\\
Nov 4, 2024](https://pypi.org/project/anthropic/0.39.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.38.0\\
\\
\\
Nov 1, 2024](https://pypi.org/project/anthropic/0.38.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.37.1\\
\\
\\
Oct 22, 2024](https://pypi.org/project/anthropic/0.37.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.37.0\\
\\
\\
Oct 22, 2024](https://pypi.org/project/anthropic/0.37.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.36.2\\
\\
\\
Oct 17, 2024](https://pypi.org/project/anthropic/0.36.2/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.36.1\\
\\
\\
Oct 15, 2024](https://pypi.org/project/anthropic/0.36.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.36.0\\
\\
\\
Oct 8, 2024](https://pypi.org/project/anthropic/0.36.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.35.0\\
\\
\\
Oct 4, 2024](https://pypi.org/project/anthropic/0.35.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.34.2\\
\\
\\
Sep 4, 2024](https://pypi.org/project/anthropic/0.34.2/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.34.1\\
\\
\\
Aug 19, 2024](https://pypi.org/project/anthropic/0.34.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.34.0\\
\\
\\
Aug 14, 2024](https://pypi.org/project/anthropic/0.34.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.33.1\\
\\
\\
Aug 12, 2024](https://pypi.org/project/anthropic/0.33.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.33.0\\
\\
\\
Aug 9, 2024](https://pypi.org/project/anthropic/0.33.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.32.0\\
\\
\\
Jul 29, 2024](https://pypi.org/project/anthropic/0.32.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.31.2\\
\\
\\
Jul 17, 2024](https://pypi.org/project/anthropic/0.31.2/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.31.1\\
\\
\\
Jul 15, 2024](https://pypi.org/project/anthropic/0.31.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.31.0\\
\\
\\
Jul 10, 2024](https://pypi.org/project/anthropic/0.31.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.30.1\\
\\
\\
Jul 1, 2024](https://pypi.org/project/anthropic/0.30.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.30.0\\
\\
\\
Jun 26, 2024](https://pypi.org/project/anthropic/0.30.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.29.2\\
\\
\\
Jun 26, 2024](https://pypi.org/project/anthropic/0.29.2/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.29.0\\
\\
\\
Jun 20, 2024](https://pypi.org/project/anthropic/0.29.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.28.1\\
\\
\\
Jun 14, 2024](https://pypi.org/project/anthropic/0.28.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.28.0\\
\\
\\
May 30, 2024](https://pypi.org/project/anthropic/0.28.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.27.0\\
\\
\\
May 30, 2024](https://pypi.org/project/anthropic/0.27.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.26.1\\
\\
\\
May 21, 2024](https://pypi.org/project/anthropic/0.26.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.26.0\\
\\
\\
May 16, 2024](https://pypi.org/project/anthropic/0.26.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.25.9\\
\\
\\
May 14, 2024](https://pypi.org/project/anthropic/0.25.9/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.25.8\\
\\
\\
May 7, 2024](https://pypi.org/project/anthropic/0.25.8/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.25.7\\
\\
\\
Apr 29, 2024](https://pypi.org/project/anthropic/0.25.7/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.25.6\\
\\
\\
Apr 18, 2024](https://pypi.org/project/anthropic/0.25.6/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.25.5\\
\\
\\
Apr 17, 2024](https://pypi.org/project/anthropic/0.25.5/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.25.4\\
\\
\\
Apr 17, 2024](https://pypi.org/project/anthropic/0.25.4/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.25.3\\
\\
\\
Apr 17, 2024](https://pypi.org/project/anthropic/0.25.3/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.25.2\\
\\
\\
Apr 15, 2024](https://pypi.org/project/anthropic/0.25.2/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.25.1\\
\\
\\
Apr 11, 2024](https://pypi.org/project/anthropic/0.25.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.25.0\\
\\
\\
Apr 9, 2024](https://pypi.org/project/anthropic/0.25.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.24.0\\
\\
\\
Apr 9, 2024](https://pypi.org/project/anthropic/0.24.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.23.1\\
\\
\\
Apr 4, 2024](https://pypi.org/project/anthropic/0.23.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.23.0\\
\\
\\
Apr 4, 2024](https://pypi.org/project/anthropic/0.23.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.22.1\\
\\
\\
Apr 4, 2024](https://pypi.org/project/anthropic/0.22.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.22.0\\
\\
\\
Apr 4, 2024](https://pypi.org/project/anthropic/0.22.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.21.3\\
\\
\\
Mar 21, 2024](https://pypi.org/project/anthropic/0.21.3/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.21.2\\
\\
\\
Mar 21, 2024](https://pypi.org/project/anthropic/0.21.2/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.21.1\\
\\
\\
Mar 20, 2024](https://pypi.org/project/anthropic/0.21.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.21.0\\
\\
\\
Mar 19, 2024](https://pypi.org/project/anthropic/0.21.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.20.0\\
\\
\\
Mar 13, 2024](https://pypi.org/project/anthropic/0.20.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.19.2\\
\\
\\
Mar 11, 2024](https://pypi.org/project/anthropic/0.19.2/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.19.1\\
\\
\\
Mar 6, 2024](https://pypi.org/project/anthropic/0.19.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.19.0\\
\\
\\
Mar 6, 2024](https://pypi.org/project/anthropic/0.19.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.18.1\\
\\
\\
Mar 4, 2024](https://pypi.org/project/anthropic/0.18.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.18.0\\
\\
\\
Mar 4, 2024](https://pypi.org/project/anthropic/0.18.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.17.0\\
\\
\\
Mar 4, 2024](https://pypi.org/project/anthropic/0.17.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.16.0\\
\\
\\
Feb 13, 2024](https://pypi.org/project/anthropic/0.16.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.15.1\\
\\
\\
Feb 7, 2024](https://pypi.org/project/anthropic/0.15.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.15.0\\
\\
\\
Feb 2, 2024](https://pypi.org/project/anthropic/0.15.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.14.1\\
\\
\\
Feb 2, 2024](https://pypi.org/project/anthropic/0.14.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.14.0\\
\\
\\
Jan 31, 2024](https://pypi.org/project/anthropic/0.14.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.13.0\\
\\
\\
Jan 30, 2024](https://pypi.org/project/anthropic/0.13.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.12.0\\
\\
\\
Jan 25, 2024](https://pypi.org/project/anthropic/0.12.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.11.0\\
\\
\\
Jan 23, 2024](https://pypi.org/project/anthropic/0.11.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.10.0\\
\\
\\
Jan 18, 2024](https://pypi.org/project/anthropic/0.10.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.9.0\\
\\
\\
Jan 8, 2024](https://pypi.org/project/anthropic/0.9.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.8.1\\
\\
\\
Dec 22, 2023](https://pypi.org/project/anthropic/0.8.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.8.0\\
\\
\\
Dec 19, 2023](https://pypi.org/project/anthropic/0.8.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.7.8\\
\\
\\
Dec 13, 2023](https://pypi.org/project/anthropic/0.7.8/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.7.7\\
\\
\\
Nov 29, 2023](https://pypi.org/project/anthropic/0.7.7/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.7.6\\
\\
\\
Nov 28, 2023](https://pypi.org/project/anthropic/0.7.6/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.7.5\\
\\
\\
Nov 27, 2023](https://pypi.org/project/anthropic/0.7.5/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.7.4\\
\\
\\
Nov 23, 2023](https://pypi.org/project/anthropic/0.7.4/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.7.3\\
\\
\\
Nov 21, 2023](https://pypi.org/project/anthropic/0.7.3/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.7.2\\
\\
\\
Nov 17, 2023](https://pypi.org/project/anthropic/0.7.2/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.7.1\\
\\
\\
Nov 17, 2023](https://pypi.org/project/anthropic/0.7.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.7.0\\
\\
\\
Nov 15, 2023](https://pypi.org/project/anthropic/0.7.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.6.0\\
\\
\\
Nov 9, 2023](https://pypi.org/project/anthropic/0.6.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.5.0\\
\\
\\
Oct 18, 2023](https://pypi.org/project/anthropic/0.5.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.4.1\\
\\
\\
Oct 16, 2023](https://pypi.org/project/anthropic/0.4.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.3.11\\
\\
\\
Aug 28, 2023](https://pypi.org/project/anthropic/0.3.11/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.3.10\\
\\
\\
Aug 16, 2023](https://pypi.org/project/anthropic/0.3.10/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.3.9\\
\\
\\
Aug 11, 2023](https://pypi.org/project/anthropic/0.3.9/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.3.8\\
\\
\\
Aug 2, 2023](https://pypi.org/project/anthropic/0.3.8/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.3.7\\
\\
\\
Jul 31, 2023](https://pypi.org/project/anthropic/0.3.7/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.3.6\\
\\
\\
Jul 21, 2023](https://pypi.org/project/anthropic/0.3.6/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.3.5\\
\\
\\
Jul 19, 2023](https://pypi.org/project/anthropic/0.3.5/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.3.4\\
\\
\\
Jul 11, 2023](https://pypi.org/project/anthropic/0.3.4/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.3.3\\
\\
\\
Jul 10, 2023](https://pypi.org/project/anthropic/0.3.3/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.3.2\\
\\
\\
Jun 30, 2023](https://pypi.org/project/anthropic/0.3.2/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.3.1\\
\\
\\
Jun 29, 2023](https://pypi.org/project/anthropic/0.3.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.3.0\\
\\
\\
Jun 28, 2023](https://pypi.org/project/anthropic/0.3.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.2.10\\
\\
\\
Jun 2, 2023](https://pypi.org/project/anthropic/0.2.10/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.2.9\\
\\
\\
May 15, 2023](https://pypi.org/project/anthropic/0.2.9/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.2.8\\
\\
\\
May 8, 2023](https://pypi.org/project/anthropic/0.2.8/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.2.7\\
\\
\\
Apr 14, 2023](https://pypi.org/project/anthropic/0.2.7/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.2.6\\
\\
\\
Apr 3, 2023](https://pypi.org/project/anthropic/0.2.6/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.2.5\\
\\
\\
Mar 29, 2023](https://pypi.org/project/anthropic/0.2.5/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.2.4\\
\\
\\
Mar 28, 2023](https://pypi.org/project/anthropic/0.2.4/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.2.3\\
\\
\\
Mar 20, 2023](https://pypi.org/project/anthropic/0.2.3/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.2.2\\
\\
\\
Feb 9, 2023](https://pypi.org/project/anthropic/0.2.2/)

## Download files

Download the file for your platform. If you're not sure which to choose, learn more about [installing packages](https://packaging.python.org/tutorials/installing-packages/ "External link").

### Source Distribution

[anthropic-0.96.0.tar.gz](https://files.pythonhosted.org/packages/b9/7e/672f533dee813028d2c699bfd2a7f52c9118d7353680d9aa44b9e23f717f/anthropic-0.96.0.tar.gz)
(658.2 kB
[view details](https://pypi.org/project/anthropic/#anthropic-0.96.0.tar.gz))


Uploaded Apr 16, 2026`Source`

### Built Distribution

Filter files by name, interpreter, ABI, and platform.

If you're not sure about the file name format, learn more about [wheel file names](https://packaging.python.org/en/latest/specifications/binary-distribution-format/ "External link").

Copy a direct link to the current filters [https://pypi.org/project/anthropic/#files](https://pypi.org/project/anthropic/#files)
Copy

Showing 1 of 1 file.

File name

InterpreterInterpreterpy3

ABIABInone

PlatformPlatformany

[anthropic-0.96.0-py3-none-any.whl](https://files.pythonhosted.org/packages/48/5a/72f33204064b6e87601a71a6baf8d855769f8a0c1eaae8d06a1094872371/anthropic-0.96.0-py3-none-any.whl)
(635.9 kB
[view details](https://pypi.org/project/anthropic/#anthropic-0.96.0-py3-none-any.whl))


Uploaded Apr 16, 2026`Python 3`

## File details

Details for the file `anthropic-0.96.0.tar.gz`.


### File metadata

- Download URL: [anthropic-0.96.0.tar.gz](https://files.pythonhosted.org/packages/b9/7e/672f533dee813028d2c699bfd2a7f52c9118d7353680d9aa44b9e23f717f/anthropic-0.96.0.tar.gz)
- Upload date: Apr 16, 2026
- Size: 658.2 kB
- Tags: Source
- Uploaded using Trusted Publishing? No
- Uploaded via: uv/0.9.13 {"installer":{"name":"uv","version":"0.9.13"},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl\_version":null,"setuptools\_version":null,"rustc\_version":null,"ci":true}

### File hashes

| Algorithm | Hash digest |  |
| --- | --- | --- |
| SHA256 | `9de947b737f39452f68aa520f1c2239d44119c9b73b0fb6d4e6ca80f00279ee6` | Copy |
| MD5 | `679132b40bd90241ad3163d5a2c7ae89` | Copy |
| BLAKE2b-256 | `b97e672f533dee813028d2c699bfd2a7f52c9118d7353680d9aa44b9e23f717f` | Copy |

Hashes for anthropic-0.96.0.tar.gz

[See more details on using hashes here.](https://pip.pypa.io/en/stable/topics/secure-installs/#hash-checking-mode "External link")

## File details

Details for the file `anthropic-0.96.0-py3-none-any.whl`.


### File metadata

- Download URL: [anthropic-0.96.0-py3-none-any.whl](https://files.pythonhosted.org/packages/48/5a/72f33204064b6e87601a71a6baf8d855769f8a0c1eaae8d06a1094872371/anthropic-0.96.0-py3-none-any.whl)
- Upload date: Apr 16, 2026
- Size: 635.9 kB
- Tags: Python 3
- Uploaded using Trusted Publishing? No
- Uploaded via: uv/0.9.13 {"installer":{"name":"uv","version":"0.9.13"},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl\_version":null,"setuptools\_version":null,"rustc\_version":null,"ci":true}

### File hashes

| Algorithm | Hash digest |  |
| --- | --- | --- |
| SHA256 | `9a6e335a354602a521cd9e777e92bfd46ba6e115bf9bbfe6135311e8fb2015b2` | Copy |
| MD5 | `8170ee4a16d6a28883303cfeeecdb3fd` | Copy |
| BLAKE2b-256 | `485a72f33204064b6e87601a71a6baf8d855769f8a0c1eaae8d06a1094872371` | Copy |

Hashes for anthropic-0.96.0-py3-none-any.whl

[See more details on using hashes here.](https://pip.pypa.io/en/stable/topics/secure-installs/#hash-checking-mode "External link")

- English
- español
- français
- 日本語
- português (Brasil)
- українська
- Ελληνικά
- Deutsch
- 中文 (简体)
- 中文 (繁體)
- русский
- עברית
- Esperanto
- 한국어

Supported by

[![](https://pypi-camo.freetls.fastly.net/ed7074cadad1a06f56bc520ad9bd3e00d0704c5b/68747470733a2f2f73746f726167652e676f6f676c65617069732e636f6d2f707970692d6173736574732f73706f6e736f726c6f676f732f6177732d77686974652d6c6f676f2d7443615473387a432e706e67)AWS\\
Cloud computing and Security Sponsor](https://aws.amazon.com/) [![](https://pypi-camo.freetls.fastly.net/8855f7c063a3bdb5b0ce8d91bfc50cf851cc5c51/68747470733a2f2f73746f726167652e676f6f676c65617069732e636f6d2f707970692d6173736574732f73706f6e736f726c6f676f732f64617461646f672d77686974652d6c6f676f2d6668644c4e666c6f2e706e67)Datadog\\
Monitoring](https://www.datadoghq.com/) [![](https://pypi-camo.freetls.fastly.net/60f709d24f3e4d469f9adc77c65e2f5291a3d165/68747470733a2f2f73746f726167652e676f6f676c65617069732e636f6d2f707970692d6173736574732f73706f6e736f726c6f676f732f6465706f742d77686974652d6c6f676f2d7038506f476831302e706e67)Depot\\
Continuous Integration](https://depot.dev/) [![](https://pypi-camo.freetls.fastly.net/df6fe8829cbff2d7f668d98571df1fd011f36192/68747470733a2f2f73746f726167652e676f6f676c65617069732e636f6d2f707970692d6173736574732f73706f6e736f726c6f676f732f666173746c792d77686974652d6c6f676f2d65684d3077735f6f2e706e67)Fastly\\
CDN](https://www.fastly.com/) [![](https://pypi-camo.freetls.fastly.net/420cc8cf360bac879e24c923b2f50ba7d1314fb0/68747470733a2f2f73746f726167652e676f6f676c65617069732e636f6d2f707970692d6173736574732f73706f6e736f726c6f676f732f676f6f676c652d77686974652d6c6f676f2d616734424e3774332e706e67)Google\\
Download Analytics](https://careers.google.com/) [![](https://pypi-camo.freetls.fastly.net/d01053c02f3a626b73ffcb06b96367fdbbf9e230/68747470733a2f2f73746f726167652e676f6f676c65617069732e636f6d2f707970692d6173736574732f73706f6e736f726c6f676f732f70696e67646f6d2d77686974652d6c6f676f2d67355831547546362e706e67)Pingdom\\
Monitoring](https://www.pingdom.com/) [![](https://pypi-camo.freetls.fastly.net/67af7117035e2345bacb5a82e9aa8b5b3e70701d/68747470733a2f2f73746f726167652e676f6f676c65617069732e636f6d2f707970692d6173736574732f73706f6e736f726c6f676f732f73656e7472792d77686974652d6c6f676f2d4a2d6b64742d706e2e706e67)Sentry\\
Error logging](https://sentry.io/for/python/?utm_source=pypi&utm_medium=paid-community&utm_campaign=python-na-evergreen&utm_content=static-ad-pypi-sponsor-learnmore) [![](https://pypi-camo.freetls.fastly.net/b611884ff90435a0575dbab7d9b0d3e60f136466/68747470733a2f2f73746f726167652e676f6f676c65617069732e636f6d2f707970692d6173736574732f73706f6e736f726c6f676f732f737461747573706167652d77686974652d6c6f676f2d5467476c6a4a2d502e706e67)StatusPage\\
Status page](https://statuspage.io/)
