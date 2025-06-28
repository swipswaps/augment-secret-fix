"""
🛠️ AUGMENT SECRET FIX PACKAGE
Comprehensive solution for Augment secrets, CPU contention, version management, and VSCode updates
"""

__version__ = "0.2.1"
__author__ = "swipswaps"
__description__ = "Comprehensive solution for Augment extension issues"

# Import main classes for easy access
from .detector import AugmentSecretDetector
from .version_manager import AugmentVersionManager
from .updater import VSCodeUpdater

__all__ = [
    "AugmentSecretDetector",
    "AugmentVersionManager",
    "VSCodeUpdater",
    "__version__",
]
