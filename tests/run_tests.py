"""
Script para executar todos os testes do projeto
"""

import unittest
import sys
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def run_all_tests():
    """Executa todos os testes do projeto"""
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=Path(__file__).parent, pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Retorna código de saída apropriado
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
