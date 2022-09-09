from .pruner import pruner
from .compressor import compress
from .analyzer.analyzer import analyze
from .significant_bits import analyze_file_significant_bits
from .evaluator import evaluate
from .cli import main as cli

__version__ = "v0.1.0"
