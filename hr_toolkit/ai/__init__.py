"""Cloud AI assistant support for HR Toolkit.

The package keeps a strict Python 3.8 standard-library footprint for the
network layer so the Windows 7 SP1 compatibility stack can use it unchanged.
Business modules import :mod:`hr_toolkit.ai.client`, :mod:`hr_toolkit.ai.config`
and :mod:`hr_toolkit.ai.excel_context` lazily; nothing in this package is
imported from the GUI startup path.
"""
