"""
Testes unitários para o módulo map.py
"""

import unittest
import sys
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from map import gerar_mapa
import folium


class TestGerarMapa(unittest.TestCase):
    """Testes para gerar_mapa"""
    
    def test_gera_mapa_com_regioes(self):
        """Testa geração de mapa com regiões"""
        regioes = [
            (-3.7319, -38.5267, "Aldeota"),
            (-3.7419, -38.5167, "Meireles"),
            (-3.7519, -38.5067, "Varjota")
        ]
        
        mapa = gerar_mapa(regioes)
        
        self.assertIsInstance(mapa, folium.Map)
    
    def test_mapa_vazio(self):
        """Testa geração de mapa sem regiões"""
        mapa = gerar_mapa([])
        
        self.assertIsInstance(mapa, folium.Map)
        # Verifica que usa centro de Fortaleza
        self.assertEqual(mapa.location, [-3.7319, -38.5267])
    
    def test_mapa_com_uma_regiao(self):
        """Testa mapa com apenas uma região"""
        regioes = [(-3.7319, -38.5267, "Aldeota")]
        
        mapa = gerar_mapa(regioes)
        
        self.assertIsInstance(mapa, folium.Map)
    
    def test_coordenadas_calculadas(self):
        """Testa que o centro é calculado corretamente"""
        regioes = [
            (-3.0, -38.0, "Regiao 1"),
            (-4.0, -39.0, "Regiao 2")
        ]
        
        mapa = gerar_mapa(regioes)
        
        # Centro deve ser aproximadamente (-3.5, -38.5)
        self.assertAlmostEqual(mapa.location[0], -3.5, places=1)
        self.assertAlmostEqual(mapa.location[1], -38.5, places=1)
    
    def test_tipos_coordenadas(self):
        """Testa que aceita diferentes tipos de coordenadas"""
        regioes = [
            (-3.7319, -38.5267, "Float"),
            (-3, -38, "Int"),
        ]
        
        mapa = gerar_mapa(regioes)
        
        self.assertIsInstance(mapa, folium.Map)


if __name__ == "__main__":
    unittest.main()
