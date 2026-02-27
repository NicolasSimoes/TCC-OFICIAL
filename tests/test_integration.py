"""
Testes de integração do sistema completo
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import importlib.util

# Importa nlp.py
nlp_path = str(Path(__file__).parent.parent / "src" / "nlp.py")
spec_nlp = importlib.util.spec_from_file_location("nlp", nlp_path)
nlp = importlib.util.module_from_spec(spec_nlp)
spec_nlp.loader.exec_module(nlp)

# Importa map.py
map_path = str(Path(__file__).parent.parent / "src" / "map.py")
spec_map = importlib.util.spec_from_file_location("map", map_path)
map_mod = importlib.util.module_from_spec(spec_map)
spec_map.loader.exec_module(map_mod)

analisar_produto_completo = nlp.analisar_produto_completo
gerar_estrategia_comercial = nlp.gerar_estrategia_comercial
gerar_mapa = map_mod.gerar_mapa
import folium


class TestFluxoCompleto(unittest.TestCase):
    """Testes do fluxo completo da aplicação"""
    
    def test_fluxo_analise_completa(self):
        """Testa fluxo completo: análise + estratégia + mapa"""
        # 1. Análise do produto
        produto = "whey protein isolado"
        analise = analisar_produto_completo(produto)
        
        self.assertEqual(analise["nicho"], "Fitness")
        self.assertIsInstance(analise["pois_sugeridos"], list)
        self.assertIsInstance(analise["pesos_classe"], dict)
        
        # 2. Simula regiões identificadas
        regioes = [
            (-3.7319, -38.5267, "Aldeota"),
            (-3.7419, -38.5167, "Meireles")
        ]
        
        # 3. Gera mapa
        mapa = gerar_mapa(regioes)
        self.assertIsInstance(mapa, folium.Map)
        
        # 4. Gera estratégia
        estrategia = gerar_estrategia_comercial(
            produto=produto,
            nicho=analise["nicho"],
            regioes=regioes,
            pesos_classe=analise["pesos_classe"]
        )
        
        self.assertIsInstance(estrategia, str)
        self.assertGreater(len(estrategia), 100)
    
    def test_diferentes_nichos(self):
        """Testa fluxo com diferentes nichos"""
        produtos_nichos = [
            ("fralda pampers", "Infantil"),
            ("caderno universitário", "Escolar"),
            ("ração golden", "Pet"),
            ("shampoo pantene", "Beleza")
        ]
        
        for produto, nicho_esperado in produtos_nichos:
            with self.subTest(produto=produto):
                analise = analisar_produto_completo(produto)
                self.assertEqual(analise["nicho"], nicho_esperado)
                
                # Verifica consistência dos dados
                self.assertGreater(len(analise["pois_sugeridos"]), 0)
                self.assertGreater(len(analise["pesos_classe"]), 0)
    
    def test_fluxo_com_filtros(self):
        """Testa fluxo com filtros aplicados"""
        produto = "suplemento fitness"
        filtros = {
            "classe": ["A", "B"],
            "tipo": "ACADEMIA",
            "bairro": ["Aldeota", "Meireles"]
        }
        
        analise = analisar_produto_completo(produto)
        regioes = [(-3.7319, -38.5267, "Aldeota")]
        
        estrategia = gerar_estrategia_comercial(
            produto=produto,
            nicho=analise["nicho"],
            regioes=regioes,
            pesos_classe=analise["pesos_classe"],
            filtros=filtros
        )
        
        self.assertIsInstance(estrategia, str)
    
    def test_fluxo_sem_regioes(self):
        """Testa fluxo quando não há regiões identificadas"""
        produto = "produto teste"
        analise = analisar_produto_completo(produto)
        
        # Sem regiões
        mapa = gerar_mapa([])
        self.assertIsInstance(mapa, folium.Map)
        
        estrategia = gerar_estrategia_comercial(
            produto=produto,
            nicho=analise["nicho"],
            regioes=[],
            pesos_classe=analise["pesos_classe"]
        )
        
        self.assertIsInstance(estrategia, str)


class TestConsistenciaDados(unittest.TestCase):
    """Testes de consistência entre módulos"""
    
    def test_pois_consistentes_com_nicho(self):
        """Testa que POIs sugeridos são consistentes com o nicho"""
        analise = analisar_produto_completo("whey protein")
        
        # Para Fitness, deve ter POIs relacionados a gym/health
        pois = analise["pois_sugeridos"]
        self.assertTrue(any(p in ["gym", "health", "spa"] for p in pois))
    
    def test_pesos_classe_validos(self):
        """Testa que pesos de classe são sempre válidos"""
        produtos = ["whey", "fralda", "caderno", "shampoo", "ração"]
        
        for produto in produtos:
            analise = analisar_produto_completo(produto)
            pesos = analise["pesos_classe"]
            
            # Verifica que tem classes A, B, C
            self.assertIn("A", pesos)
            self.assertIn("B", pesos)
            self.assertIn("C", pesos)
            
            # Verifica que todos são positivos
            for peso in pesos.values():
                self.assertGreater(peso, 0)


if __name__ == "__main__":
    unittest.main()
